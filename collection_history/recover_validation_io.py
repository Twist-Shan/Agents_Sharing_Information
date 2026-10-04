"""Separate outcome-blind recovery of original IDs after a local I/O exception.
No preparation or paid execution occurs on import. Original files are immutable.
"""
from pathlib import Path
from contextlib import ExitStack
from collections import Counter
import argparse, hashlib, json, os, time, uuid
import runtime
import supervise_validation as supervisor

HERE=Path(__file__).resolve().parent
AMENDMENT='io_recovery_amendment.json'
JOURNAL='io_supervisor.jsonl'
STATUS='io_supervisor_status.json'
LOCK='io_supervisor.lock'
IO_LOG='io_metadata_retries.jsonl'
AUDIT='recover_validation_io_audit.json'
AUDIT_SOURCE='recover_validation_io_audit.py'
NOTE='IO_RECOVERY_AMENDMENT.txt'
COPIED=('manifest.json','planned.jsonl','started.jsonl','attempts.jsonl','operations.jsonl','preflight.jsonl')
APPEND_ONLY=('started.jsonl','attempts.jsonl','operations.jsonl','preflight.jsonl')
SAVE_DELAYS=(.25,1.0)
MAX_INVOCATIONS=11
START_FIELDS=('id','model_key','attempt_id','attempt','request_sha256','reserve_usd')
SETTLED_FIELDS=START_FIELDS+('valid','fatal','reason','charged_or_reserved_usd','cost_is_reserve','retry_after_seconds')


def require(value,label):
    if not value:raise ValueError('io_recovery:'+label)


def file_record(path):
    path=Path(path)
    return {'sha256':runtime.sha(path),'bytes':path.stat().st_size}


def prefix_matches(path,record):
    path=Path(path)
    if not path.is_file() or path.stat().st_size<record['bytes']:return False
    h=hashlib.sha256();remaining=record['bytes']
    with path.open('rb') as stream:
        while remaining:
            chunk=stream.read(min(1024*1024,remaining))
            if not chunk:return False
            remaining-=len(chunk);h.update(chunk)
    return h.hexdigest()==record['sha256']


def projected_rows(path,fields):
    """Parse only to project operational fields; never retain or report choices."""
    output=[]
    if not Path(path).exists():return output
    with Path(path).open(encoding='utf-8') as stream:
        for line in stream:
            row=json.loads(line)
            output.append({k:row[k] for k in fields if k in row})
    return output


def operational_state(run,jobs,profiles):
    starts=projected_rows(run/'started.jsonl',START_FIELDS)
    settled=projected_rows(run/'attempts.jsonl',SETTLED_FIELDS)
    ledger=runtime.Ledger(starts,settled)
    require(runtime.accounting(starts,settled)==ledger.occupied,'ledger_reconciliation')
    byid={j['id']:j for j in jobs}
    byid.update({j['id']:j for j in (runtime.compatibility(p) for p in profiles)})
    prof={p['key']:p for p in profiles}
    for row in starts:
        require(row['id'] in byid,'unknown_started_id')
        job=byid[row['id']];body=runtime.payload(prof[row['model_key']],job)
        require(job['model_key']==row['model_key'] and row['request_sha256']==runtime.digest(runtime.compact(body).encode()),'started_request_changed')
        require(runtime.D(row['reserve_usd'])==runtime.reserve(prof[row['model_key']],body),'started_reserve_changed')
    accepted={r['id']:r['attempt_id'] for r in settled if r.get('valid') is True}
    require(set(accepted)==ledger.accepted,'accepted_flag_schema')
    unknown=[r['attempt_id'] for r in starts if r['attempt_id'] not in ledger.settled]
    missing=[{'id':j['id'],'request_sha256':j['request_sha256'],'attempts_used':ledger.tries[j['id']],
              'attempts_remaining':3-ledger.tries[j['id']]} for j in jobs if j['id'] not in accepted]
    events=runtime.lines(run/'operations.jsonl')
    _,pauses,pending=runtime.pause_state(settled,events)
    return {'starts':starts,'settled':settled,'ledger':ledger,'accepted':accepted,'unknown':unknown,
            'missing':missing,'pauses':pauses,'pending_pause':pending}


class MetadataSave:
    """Retry only atomic metadata saves, never requests or journal appends."""
    def __init__(self,original,root,emit,sleep=time.sleep):
        self.original=original;self.root=Path(root).resolve();self.emit=emit;self.sleep=sleep
        self.allowed={self.root/name for name in ('status.json','final_ledger.json',STATUS)}
    def __call__(self,path,value):
        path=Path(path).resolve()
        if path not in self.allowed:return self.original(path,value)
        for index in range(len(SAVE_DELAYS)+1):
            try:return self.original(path,value)
            except PermissionError as exc:
                # Exception messages and absolute paths are deliberately omitted.
                retry=index<len(SAVE_DELAYS)
                self.emit({'event':'metadata_permission_error','utc':runtime.now(),'pid':os.getpid(),
                           'basename':path.name,'errno':exc.errno,'winerror':getattr(exc,'winerror',None),
                           'stage':'atomic_metadata_save','save_attempt':index+1,'will_retry':retry})
                if not retry:raise
                self.sleep(SAVE_DELAYS[index])


def original_binding(original):
    """Requires the original supervisor and execution locks held by the caller."""
    frozen,jobs=runtime.validate(original)
    state=runtime.read(original/'status.json')
    require(state.get('state')=='halted_fatal' and state.get('reason')=='PermissionError','original_not_io_fatal')
    require(state.get('manifest_sha256')==frozen['manifest_sha256'],'original_status_manifest')
    old=supervisor.verify_amendment(original)
    rows=runtime.lines(original/supervisor.JOURNAL)
    count,last=supervisor.validate_history(rows,old['amendment_sha256'],frozen['manifest_sha256'])
    require(count==1 and supervisor.MAX_INVOCATIONS-count==MAX_INVOCATIONS,'unexpected_original_supervisor_count')
    start=next(r for r in reversed(rows) if r['event']=='invocation_started')
    require(last and last.get('resume_eligible') is False and last.get('exit_kind')=='system_exit'
            and type(last.get('exit_code')) is int and last['exit_code']==1,'original_supervisor_not_final')
    snapshot=supervisor.status_snapshot(original/'status.json')
    require(supervisor.match_snapshot(snapshot,last['post_status']) and supervisor.fresh_status(start['pre_status'],snapshot,start,last['ended_ns'],frozen['manifest_sha256']),'original_terminal_not_fresh')
    closed=runtime.read(original/supervisor.STATUS)
    require(closed.get('state')=='stopped' and closed.get('reason')=='system_exit'
            and closed.get('invocations')==count and closed.get('amendment_sha256')==old['amendment_sha256']
            and closed.get('invocation_id')==last['invocation_id'],'original_supervisor_closure')
    em=runtime.read(original/'terminal_export/export_manifest.json')
    ea=runtime.read(original/'terminal_export/operational_audit.json')
    require(em.get('status')=='passed' and em.get('manifest_sha256')==frozen['manifest_sha256'],'original_export_not_verified')
    require(ea.get('status')=='passed_terminal_export' and ea.get('manifest_sha256')==frozen['manifest_sha256']
            and ea.get('exporter_sha256')==runtime.sha(HERE/'export_validation.py'),'original_export_audit_binding')
    paths=[*COPIED,'status.json','final_ledger.json',supervisor.MANIFEST,supervisor.JOURNAL,supervisor.STATUS,
           'terminal_export/export_manifest.json']
    for name,digest in ea['input_sha256'].items():
        require(Path(name).name==name and runtime.sha(original/name)==digest,'original_export_input_changed')
    for name,digest in em['files_sha256'].items():
        require(Path(name).name==name and runtime.sha(original/'terminal_export'/name)==digest,'original_export_member_changed')
        paths.append('terminal_export/'+name)
    dm=runtime.read(original/'operational_diagnostics/diagnostics_manifest.json')
    require(dm.get('status')=='passed' and dm.get('model_calls')==0 and dm.get('manifest_sha256')==frozen['manifest_sha256']
            and dm.get('export_manifest_sha256')==runtime.sha(original/'terminal_export/export_manifest.json')
            and dm.get('source_sha256')==runtime.sha(HERE/'operational_diagnostics.py'),'original_operational_diagnostics_binding')
    paths.append('operational_diagnostics/diagnostics_manifest.json')
    for name,digest in dm['files_sha256'].items():
        require(Path(name).name==name and runtime.sha(original/'operational_diagnostics'/name)==digest,'original_operational_diagnostic_changed')
        paths.append('operational_diagnostics/'+name)
    binding={name:file_record(original/name) for name in dict.fromkeys(paths)}
    info=operational_state(original,jobs,frozen['profiles'])
    require(not any(r.get('fatal') for r in info['settled']),'original_fatal_response_prevents_recovery')
    final=runtime.read(original/'final_ledger.json')
    require(final.get('status')=='independently_reconciled' and runtime.D(final['cumulative_occupied_usd'])==info['ledger'].occupied,'original_final_ledger')
    valid=sum(not i.endswith('|compatibility') for i in info['accepted'])
    require(state['science_accepted']==valid and state['physical_started']==len(info['starts'])
            and state['physical_settled']==len(info['settled']) and state['inflight']==len(info['unknown']),'original_operational_counts')
    require(em['scientific_valid']==valid and em['scientific_planned']==len(jobs),'original_export_counts')
    return frozen,jobs,state,binding,info,old


def source_records():
    audit=runtime.read(HERE/AUDIT)
    require(audit.get('passed') is True and audit.get('model_calls')==0 and audit.get('live_journals_read') is False,'recovery_audit_not_passed')
    for name in (Path(__file__).name,AUDIT_SOURCE,'runtime.py','supervise_validation.py'):
        require(audit.get('source_sha256',{}).get(name)==runtime.sha(HERE/name),'recovery_audit_stale:'+name)
    return {name:runtime.sha(HERE/name) for name in (Path(__file__).name,AUDIT_SOURCE,AUDIT,NOTE,
            'supervise_validation.py','supervise_validation_audit.py','supervisor_synthetic_audit.json','export_validation.py','operational_diagnostics.py')}


def prepare(original,recovery):
    original=Path(original).resolve();recovery=Path(recovery).resolve()
    require(not recovery.exists() and recovery.parent==HERE and recovery.name=='io_recovery' and original.parent==HERE and original!=recovery,'new_separate_directory_required')
    sources=source_records()
    with ExitStack() as locks:
        locks.enter_context(runtime.execution_lock(original/supervisor.LOCK))
        locks.enter_context(runtime.execution_lock(original/'execution.lock'))
        frozen,jobs,state,binding,info,old=original_binding(original)
        require(info['ledger'].occupied<=runtime.CAP,'budget_already_exceeded')
        recovery.mkdir(exist_ok=False)
        for name in COPIED:
            with (recovery/name).open('xb') as output:output.write((original/name).read_bytes())
        base={**state,'state':'interrupted','reason':'io_recovery_prepared','utc':runtime.now(),'pid':os.getpid()}
        runtime.save(recovery/'status.json',base)
        amendment={'version':1,'kind':'SEPARATE_OUTCOME_BLIND_IO_RECOVERY','prepared_utc':runtime.now(),
           'original_run_path':str(original),'recovery_run_path':str(recovery),
           'original_manifest_sha256':frozen['manifest_sha256'],'original_sources':frozen['sources'],
           'original_files':binding,'original_terminal_status':state,'copied_prefixes':{name:binding[name] for name in COPIED},
           'recovery_sources':sources,'original_supervisor_amendment_sha256':old['amendment_sha256'],
           'original_supervisor_invocations':1,'remaining_supervisor_invocations':MAX_INVOCATIONS,
           'backoff_seconds':list(supervisor.BACKOFF),'metadata_save_delays':list(SAVE_DELAYS),
           'baseline_status':supervisor.status_snapshot(recovery/'status.json'),
           'retained_first_valid_attempts':info['accepted'],'original_unsettled_attempt_ids':info['unknown'],
           'remaining_missing':info['missing'],
           'eligible_ids_in_original_order':[r['id'] for r in info['missing'] if r['attempts_remaining']>0],
           'exhausted_ids_in_original_order':[r['id'] for r in info['missing'] if r['attempts_remaining']==0],
           'original_occupied_usd':str(info['ledger'].occupied),'cumulative_cap_usd':str(runtime.CAP),
           'original_pause_count':info['pauses'],'original_pending_pause':info['pending_pause'],
           'failure_cause':'PermissionError observed; exact failing filesystem operation unresolved. A pre-submission status snapshot is plausible, not established.',
           'scientific_changes':False,'execution_policy_amended':True,
           'inference_label':'Prespecified scientific contrasts under an outcome-blind amended execution policy; original incomplete terminal outputs retained.'}
        amendment['amendment_sha256']=runtime.digest(runtime.compact(amendment).encode())
        runtime.save(recovery/AMENDMENT,amendment)
        require(all(file_record(original/name)==record for name,record in binding.items()),'original_changed_during_prepare')
        require(all(file_record(recovery/name)==binding[name] for name in COPIED),'copy_not_byte_identical')
        print(runtime.compact({'status':'io_recovery_prepared','amendment_sha256':amendment['amendment_sha256'],
          'original_scientific_valid':state['science_accepted'],'remaining_missing':len(info['missing']),
          'eligible':len(amendment['eligible_ids_in_original_order']),'unsettled':len(info['unknown']),
          'remaining_supervisor_invocations':MAX_INVOCATIONS}),flush=True)
        return amendment


def verify_recovery(recovery):
    recovery=Path(recovery).resolve();amendment=runtime.read(recovery/AMENDMENT)
    body=dict(amendment);claimed=body.pop('amendment_sha256')
    require(runtime.digest(runtime.compact(body).encode())==claimed,'amendment_changed')
    require(amendment['version']==1 and amendment['kind']=='SEPARATE_OUTCOME_BLIND_IO_RECOVERY'
            and amendment['scientific_changes'] is False and amendment['execution_policy_amended'] is True,'amendment_kind')
    require(amendment['remaining_supervisor_invocations']==MAX_INVOCATIONS and amendment['original_supervisor_invocations']==1
            and amendment['backoff_seconds']==list(supervisor.BACKOFF) and amendment['metadata_save_delays']==list(SAVE_DELAYS),'recovery_limits_changed')
    require(amendment['recovery_run_path']==str(recovery) and amendment['cumulative_cap_usd']==str(runtime.CAP),'recovery_path_or_budget_changed')
    original=Path(amendment['original_run_path']).resolve()
    require(original!=recovery and original.parent==HERE and recovery.parent==HERE and recovery.name=='io_recovery','original_directory_collision')
    require(amendment['recovery_sources']==source_records(),'recovery_source_changed')
    for name,record in amendment['original_files'].items():
        require(file_record(original/name)==record,'original_artifact_changed:'+name)
    require(set(amendment['copied_prefixes'])==set(COPIED),'copied_inventory_changed')
    for name,record in amendment['copied_prefixes'].items():
        require(record==amendment['original_files'][name] and prefix_matches(recovery/name,record),'copied_prefix_changed:'+name)
        if name not in APPEND_ONLY:require(file_record(recovery/name)==record,'fixed_copy_changed:'+name)
    frozen,jobs=runtime.validate(recovery)
    require(frozen['manifest_sha256']==amendment['original_manifest_sha256'] and frozen['sources']==amendment['original_sources'],'scientific_freeze_changed')
    initial=operational_state(original,jobs,frozen['profiles'])
    require(not any(r.get('fatal') for r in initial['settled']),'original_fatal_response_prevents_recovery')
    require(initial['accepted']==amendment['retained_first_valid_attempts'] and initial['missing']==amendment['remaining_missing']
            and initial['unknown']==amendment['original_unsettled_attempt_ids'],'original_lineage_changed')
    require([r['id'] for r in initial['missing'] if r['attempts_remaining']>0]==amendment['eligible_ids_in_original_order']
            and [r['id'] for r in initial['missing'] if r['attempts_remaining']==0]==amendment['exhausted_ids_in_original_order'],'recovery_allocation_changed')
    info=operational_state(recovery,jobs,frozen['profiles'])
    require(all(info['accepted'].get(k)==v for k,v in initial['accepted'].items()),'first_valid_replaced')
    allowed=set(amendment['eligible_ids_in_original_order'])
    allowed.update(runtime.compatibility(p)['id'] for p in frozen['profiles'] if runtime.compatibility(p)['id'] not in initial['accepted'])
    require(all(r['id'] in allowed for r in info['starts'][len(initial['starts']):]),'new_attempt_outside_original_missing')
    require(info['pauses']>=initial['pauses'],'pause_counter_reset')
    require(str(initial['ledger'].occupied)==amendment['original_occupied_usd'] and initial['pauses']==amendment['original_pause_count']
            and initial['pending_pause']==amendment['original_pending_pause'],'initial_operational_limits_changed')
    state=runtime.read(recovery/'status.json')
    require(state.get('manifest_sha256')==frozen['manifest_sha256'],'recovery_status_manifest')
    return amendment


def recovery_summary(recovery):
    """Operational provenance only; never runs the controller or scientific analysis.
    Production callers hold the recovery outer lock. Offline bundles must verify
    these records statically and must not import or execute this paid adapter.
    """
    recovery=Path(recovery).resolve();amendment=verify_recovery(recovery)
    rows=runtime.lines(recovery/JOURNAL)
    starts=[r for r in rows if r.get('event')=='invocation_started']
    return {'amendment_sha256':amendment['amendment_sha256'],
            'original_terminal_status':amendment['original_terminal_status'],
            'baseline_status':amendment['baseline_status']['status'],
            'original_files':amendment['original_files'],
            'copied_prefixes':amendment['copied_prefixes'],
            'original_unknown_attempts':len(amendment['original_unsettled_attempt_ids']),
            'original_missing':len(amendment['remaining_missing']),
            'original_eligible':len(amendment['eligible_ids_in_original_order']),
            'original_exhausted':len(amendment['exhausted_ids_in_original_order']),
            'original_supervisor_invocations':1,'recovery_invocations_started':len(starts),
            'recovery_invocation_cap':MAX_INVOCATIONS,
            'terminal_closure_verified':False,
            'interpretation':'Lineage summary only; final supervisor closure requires separate static verification.'}


def execute(recovery):
    recovery=Path(recovery).resolve()
    require(recovery.parent==HERE and recovery.name=='io_recovery','specific_recovery_directory_required')
    with runtime.execution_lock(recovery/LOCK):
        amendment=verify_recovery(recovery)
        rows=runtime.lines(recovery/JOURNAL)
        original_save=runtime.save;original_getpass=runtime.getpass;original_limit=supervisor.MAX_INVOCATIONS
        cache=supervisor.CachedGetpass(original_getpass)
        adapter=MetadataSave(original_save,recovery,lambda event:runtime.append(recovery/IO_LOG,event))
        def report(value):
            value={**value,'utc':runtime.now(),'pid':os.getpid(),'amendment_sha256':amendment['amendment_sha256']}
            adapter(recovery/STATUS,value);print(runtime.compact(value),flush=True)
        runtime.save=adapter;runtime.getpass=cache;supervisor.MAX_INVOCATIONS=MAX_INVOCATIONS
        try:
            return supervisor.controller(rows=rows,baseline=amendment['baseline_status'],amendment_sha=amendment['amendment_sha256'],
                manifest_sha=amendment['original_manifest_sha256'],invoke=lambda:runtime.execute(recovery),
                snapshot=lambda:supervisor.status_snapshot(recovery/'status.json'),emit=lambda event:runtime.append(recovery/JOURNAL,event),
                report=report,now_ns=time.time_ns,sleep=time.sleep,pid=os.getpid(),new_id=lambda:uuid.uuid4().hex,
                verify=lambda:verify_recovery(recovery))
        finally:
            runtime.save=original_save;runtime.getpass=original_getpass;supervisor.MAX_INVOCATIONS=original_limit;cache.clear()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    mode=parser.add_mutually_exclusive_group(required=True);mode.add_argument('--prepare',action='store_true');mode.add_argument('--execute',action='store_true')
    parser.add_argument('--original',type=Path,default=HERE/'validation');parser.add_argument('--recovery',type=Path,default=HERE/'io_recovery')
    args=parser.parse_args()
    try:
        if args.prepare:prepare(args.original,args.recovery);return 0
        return 0 if execute(args.recovery)=='complete' else 1
    except KeyboardInterrupt:
        print(runtime.compact({'io_recovery':'stopped','reason':'KeyboardInterrupt'}),flush=True);return 1
    except BaseException as exc:
        print(runtime.compact({'io_recovery':'stopped','exception_type':type(exc).__name__,
              'errno':getattr(exc,'errno',None),'winerror':getattr(exc,'winerror',None)}),flush=True);return 1


if __name__=='__main__':raise SystemExit(main())
