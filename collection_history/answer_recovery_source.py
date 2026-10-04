"""Outcome-blind operator closure and separate strict/answer-extraction exports.
The interrupted source status, raw responses and original strict flags are immutable.
No paid runner, supervisor or recovery adapter is imported.
"""
from pathlib import Path
from contextlib import ExitStack,contextmanager
from datetime import datetime,timezone
from collections import Counter
import argparse,json
import runtime
import export_validation as frozen

HERE=Path(__file__).resolve().parent
REPO=HERE.parent.parent
KIND='OPERATOR_STOPPED_ANSWER_EXTRACTION_TRANSITION'
REASON='user_authorized_answer_extraction_transition'
STRICT_LAYER='strict_operator_stopped'
PARSED_LAYER='answer_extraction_recovery'
BACKOFF=(30,60,120,240,300)
RAW_NAMES=('manifest.json','planned.jsonl','status.json','started.jsonl','attempts.jsonl','operations.jsonl',
           'preflight.jsonl','io_recovery_amendment.json','io_supervisor.jsonl','io_supervisor_status.json',
           'io_metadata_retries.jsonl')

def require(ok,label):
    if not ok:raise ValueError('answer_recovery:'+label)

def relative(path):return Path(path).resolve().relative_to(REPO).as_posix()

def member(name):
    require(isinstance(name,str) and not Path(name).is_absolute(),'absolute_member')
    p=(REPO/name).resolve();require(p.is_relative_to(REPO) and p!=REPO,'member_escape');return p

@contextmanager
def source_locks(source):
    with runtime.execution_lock(Path(source)/'io_supervisor.lock'):
        with runtime.execution_lock(Path(source)/'execution.lock'):yield

def utc_ns(value):
    d=datetime.fromisoformat(value.replace('Z','+00:00'))
    require(d.tzinfo is not None,'naive_control_utc')
    q=d.astimezone(timezone.utc)-datetime(1970,1,1,tzinfo=timezone.utc)
    return (q.days*86400+q.seconds)*10**9+q.microseconds*1000

def verify_control(source,amendment,status):
    """Replay only the operational controller's hash-bound stop chain."""
    rows=runtime.lines(source/'io_supervisor.jsonl');previous=amendment['baseline_status'];pending=None;last=None;count=0
    seen=set()
    for event in rows:
        require(event['amendment_sha256']==amendment['amendment_sha256'],'control_amendment')
        if event['event']=='invocation_started':
            count+=1
            require(pending is None and count<=11 and event['index']==count and event['invocation_id'] not in seen,'control_start')
            seen.add(event['invocation_id'])
            require(event['original_manifest_sha256']==status['manifest_sha256'] and event['pre_status']==previous,'control_chain')
            deadline=utc_ns(previous['status']['utc'])+30*10**9 if last is None else last['resume_not_before_ns']
            require(last is None or last['resume_eligible'] is True,'control_nonresumable')
            require(event['started_ns']>=deadline,'control_backoff')
            pending=event
        elif event['event']=='invocation_finished':
            require(pending is not None and event['index']==pending['index'] and event['invocation_id']==pending['invocation_id'],'control_finish')
            after=event['post_status'];obj=after['status']
            fresh=(obj['manifest_sha256']==status['manifest_sha256'] and obj['pid']==pending['pid']
                   and previous['sha256']!=after['sha256'] and previous['mtime_ns']<after['mtime_ns']
                   and pending['started_ns']<=after['mtime_ns']<=event['ended_ns']
                   and pending['started_ns']<=utc_ns(obj['utc'])<=event['ended_ns'])
            require(fresh,'control_status_not_fresh')
            eligible=(event['exit_kind']=='system_exit' and type(event['exit_code']) is int and event['exit_code']==1
                      and obj['state']=='interrupted' and obj['reason']=='endpoint_metadata_unavailable')
            delay=BACKOFF[min(count-1,4)] if eligible else None
            require(event['resume_eligible'] is eligible and event['backoff_seconds']==delay
                    and event['resume_not_before_ns']==(event['ended_ns']+delay*10**9 if eligible else None),'control_predicate')
            previous=after;last=event;pending=None
        else:raise ValueError('answer_recovery:unknown_control_event')
    require(pending is None and last is not None and last['resume_eligible'] is False,'controller_not_closed')
    require(last['exit_kind']=='system_exit' and type(last['exit_code']) is int and last['exit_code']==1,'operator_exit_kind')
    require(previous['status']==status and previous['sha256']==runtime.sha(source/'status.json')
            and previous['size']==(source/'status.json').stat().st_size,'operator_status_bytes')
    closed=runtime.read(source/'io_supervisor_status.json')
    require(closed['state']=='stopped' and closed['reason']=='system_exit' and closed['runtime_state']=='interrupted'
            and closed['invocations']==count and closed['invocation_id']==last['invocation_id']
            and closed['pid']==status['pid'] and closed['amendment_sha256']==amendment['amendment_sha256']
            and utc_ns(closed['utc'])>=last['ended_ns'],'operator_supervisor_closure')
    return {'invocations':count,'invocation_cap':11,'last_invocation_id':last['invocation_id'],
            'exit_kind':last['exit_kind'],'exit_code':last['exit_code'],'source_state':'interrupted',
            'stop_reason':'KeyboardInterrupt','source_status_sha256':previous['sha256']}

def verify_snapshot_locked(source):
    """Same strict raw classification/accounting; no fabricated terminal status."""
    source=Path(source).resolve();status=runtime.read(source/'status.json')
    require(status.get('state')=='interrupted' and status.get('reason')=='KeyboardInterrupt','not_operator_stopped')
    require(not (source/'final_ledger.json').exists(),'unexpected_source_final_ledger')
    m,jobs=runtime.validate(source);frozen._scientific_identity(m,jobs)
    require(status['manifest_sha256']==m['manifest_sha256'],'status_manifest')
    starts=runtime.lines(source/'started.jsonl');settled=runtime.lines(source/'attempts.jsonl')
    ledger=runtime.Ledger(starts,settled)
    profiles={p['key']:p for p in m['profiles']};byid={j['id']:j for j in jobs+[runtime.compatibility(p) for p in m['profiles']]}
    failures,fingerprints=frozen._classifications(starts,settled,profiles,byid)
    require(runtime.accounting(starts,settled)==ledger.occupied,'independent_accounting')
    accepted={}
    for row in settled:
        if row['valid']:
            require(row['id'] not in accepted,'duplicate_strict_valid');accepted[row['id']]=row
    science_ids={j['id'] for j in jobs}
    require(not any(row['fatal'] for row in settled),'fatal_source_not_parse_recovery')
    require(status['scientific_planned']==len(jobs) and status['science_accepted']==sum(i in science_ids for i in accepted)
            and status['physical_started']==len(starts) and status['physical_settled']==len(settled)
            and status['inflight']==len(starts)-len(settled) and runtime.D(status['cumulative_occupied_usd'])==ledger.occupied,'status_projection')
    known=sum((runtime.D(row['charged_or_reserved_usd']) for row in settled if not row['cost_is_reserve']),runtime.D(0))
    final={'status':'independently_reconciled','prior_occupied_usd':str(runtime.PRIOR),
           'known_new_cost_usd':str(known),'unknown_new_reserved_usd':str(ledger.occupied-runtime.PRIOR-known),
           'cumulative_occupied_usd':str(ledger.occupied),'cumulative_cap_usd':str(runtime.CAP),
           'started_sha256':runtime.sha(source/'started.jsonl'),'settled_sha256':runtime.sha(source/'attempts.jsonl'),
           'manifest_sha256':m['manifest_sha256']}
    am=runtime.read(source/'io_recovery_amendment.json');body=dict(am);claimed=body.pop('amendment_sha256')
    require(runtime.digest(runtime.compact(body).encode())==claimed and am['original_manifest_sha256']==m['manifest_sha256'],'io_amendment')
    for name,record in am['copied_prefixes'].items():
        require(Path(name).name==name,'prefix_path')
        with (source/name).open('rb') as handle:prefix=handle.read(record['bytes'])
        require(len(prefix)==record['bytes'] and runtime.digest(prefix)==record['sha256'],'io_copied_prefix')
    require(all(i in accepted and accepted[i]['attempt_id']==aid for i,aid in am['retained_first_valid_attempts'].items()),'prior_first_valid_retention')
    original=source.parent/Path(am['original_run_path']).name
    require(original!=source and original.is_relative_to(REPO),'original_directory')
    for name,record in am['original_files'].items():
        p=(original/name).resolve();require(p.is_relative_to(original) and runtime.sha(p)==record['sha256'],'original_artifact_changed')
    for name,digest in am['recovery_sources'].items():
        require(Path(name).name==name and runtime.sha(HERE/name)==digest,'recovery_source_changed')
    control=verify_control(source,am,status)
    events=runtime.lines(source/'operations.jsonl');runtime.pause_state(settled,events)
    require(runtime.read(source/'status.json')==status,'source_changed_during_verify')
    return (m,jobs,starts,settled,accepted,ledger,final,status,failures,fingerprints,events),control,am,original

def close_source(source,output,observed_exit):
    """Create a separate, immutable closure after externally observed process exit."""
    source=Path(source).resolve();output=Path(output).resolve()
    require(source.parent==HERE and output.parent==HERE and source!=output and not output.exists(),'separate_new_closure_directory')
    require(observed_exit.get('observed') is True and observed_exit.get('exit_code')==1
            and observed_exit.get('session_id')==61507 and observed_exit.get('pid')==29312,'observed_exit_metadata')
    with source_locks(source):
        data,control,am,original=verify_snapshot_locked(source)
        require(data[7]['pid']==observed_exit['pid'],'observed_pid_binding')
        files={}
        def add(p):
            p=Path(p).resolve();require(p.is_relative_to(REPO) and p.is_file(),'source_binding_path')
            files[relative(p)]=runtime.sha(p)
        for name in RAW_NAMES:
            if (source/name).exists():add(source/name)
        for name in data[0]['sources']:add(HERE/name)
        for name in am['recovery_sources']:add(HERE/name)
        for name in am['original_files']:add(original/name)
        closure={'version':1,'kind':KIND,'reason':REASON,'source_run_relative':relative(source),
                 'scientific_manifest_sha256':data[0]['manifest_sha256'],'observed_process_exit':observed_exit,
                 'original_source_status':data[7],'controller_closure':control,'strict_ledger':data[6],
                 'unknown_started_attempt_ids':[row['attempt_id'] for row in data[2] if row['attempt_id'] not in data[5].settled],
                 'unknown_cost_policy':'Every unsettled physical start retains its full reserve and consumes its global attempt; no missing charge is treated as zero.',
                 'source_files_sha256':files,'source_verifier_sha256':runtime.sha(Path(__file__)),
                 'created_utc':runtime.now(),'source_files_modified':False,'model_calls':0,
                 'selection_sensitivity_plan':'Before effect inspection, preselect a descriptive sensitivity using the earliest unambiguous stop-finished eligible response across all available recorded attempts, including earlier parseable responses before a locked strict valid. Preserve the primary strict-lock selection; report earlier-parseable disagreements and apply the same formulas later without new sampling, stopping changes or expected-answer-based selection.',
                 'inference_label':'Operator-stopped strict policy; subsequent answer extraction is a separately labeled response-policy amendment, not an independent replication.'}
        closure['closure_sha256']=runtime.digest(runtime.compact(closure).encode())
        output.mkdir(exist_ok=False);frozen._write_once_or_identical(output/'operator_closure.json',frozen._bytes_json(closure))
        require(all(runtime.sha(member(n))==h for n,h in files.items()),'source_changed_during_closure')
        return closure

def verify_closed_source_locked(closure_path):
    closure_path=Path(closure_path).resolve();c=runtime.read(closure_path);body=dict(c);claimed=body.pop('closure_sha256')
    require(c['version']==1 and c['kind']==KIND and c['reason']==REASON
            and runtime.digest(runtime.compact(body).encode())==claimed,'closure_changed')
    require(runtime.sha(Path(__file__))==c['source_verifier_sha256'],'source_verifier_changed')
    require(all(runtime.sha(member(n))==h for n,h in c['source_files_sha256'].items()),'bound_source_changed')
    source=member(c['source_run_relative']);data,control,am,original=verify_snapshot_locked(source)
    observed=c['observed_process_exit']
    require(observed.get('observed') is True and observed.get('exit_code')==1 and observed.get('session_id')==61507
            and observed.get('pid')==29312==data[7]['pid'],'observed_exit_binding')
    required={relative(source/name) for name in RAW_NAMES if (source/name).exists()}
    required.update(relative(HERE/name) for name in data[0]['sources'])
    required.update(relative(HERE/name) for name in am['recovery_sources'])
    required.update(relative(original/name) for name in am['original_files'])
    require(set(c['source_files_sha256'])==required,'closure_source_inventory')
    require(data[0]['manifest_sha256']==c['scientific_manifest_sha256'] and data[7]==c['original_source_status']
            and data[6]==c['strict_ledger'] and control==c['controller_closure'],'closure_projection')
    require([r['attempt_id'] for r in data[2] if r['attempt_id'] not in data[5].settled]==c['unknown_started_attempt_ids'],'unknown_start_binding')
    return c,data

def verify_closed_source(closure_path):
    source=member(runtime.read(closure_path)['source_run_relative'])
    with source_locks(source):return verify_closed_source_locked(closure_path)

