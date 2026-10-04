"""Offline terminal-only exporter for the frozen decision-value validation.
No network, no behavioral reads while the runner is active, no source mutation.
"""
from pathlib import Path
from collections import Counter,defaultdict
from decimal import Decimal
import argparse,csv,hashlib,io,json,math
import runtime

D=Decimal
HERE=Path(__file__).resolve().parent


def require(condition,label):
    if not condition:raise ValueError('terminal_export:'+label)


def _bytes_json(value):
    return (runtime.compact(value)+'\n').encode('utf-8')


def _csv_bytes(rows):
    if not rows:return b''
    fields=list(dict.fromkeys(k for row in rows for k in row))
    output=io.StringIO(newline='');writer=csv.DictWriter(output,fieldnames=fields,lineterminator='\n')
    writer.writeheader()
    for row in rows:
        writer.writerow({k:runtime.compact(v) if isinstance(v,(list,dict)) else v for k,v in row.items()})
    return output.getvalue().encode('utf-8')


def _write_once_or_identical(path,payload):
    if path.exists():
        require(path.read_bytes()==payload,'existing_export_differs:'+path.name)
        return
    with path.open('xb') as handle:handle.write(payload)


def _normalize_job(job):
    prefix=job['model_key']+'|'
    require(job['id'].startswith(prefix),'logical_model_prefix')
    return {**{k:v for k,v in job.items() if k not in ('model_key','request_sha256')},'id':job['id'][len(prefix):]}


def _scientific_identity(manifest,jobs):
    # Runtime hashes verify bytes; regeneration also checks metadata, mappings,
    # unique condition IDs, and the exact deterministic scientific allocation.
    import protocol
    for profile in manifest['profiles']:
        key=profile['key'];subset=[_normalize_job(j) for j in jobs if j['model_key']==key]
        regenerated=protocol.generate({'model_key':key,'allocationprofile':'full' if key=='luna' else 'cross'})
        require(subset==regenerated,'scientific_regeneration:'+key)


def _classifications(started,settled,profiles,byid):
    seen_fp={};failures=[]
    for row in started:
        require(row['id'] in byid,'unknown_start')
        job=byid[row['id']];profile=profiles[job['model_key']]
        require(row['model_key']==job['model_key'],'start_model')
        body=runtime.payload(profile,job)
        require(row['request_sha256']==runtime.digest(runtime.compact(body).encode()),'start_payload')
        require(D(row['reserve_usd'])==runtime.reserve(profile,body),'start_reserve')
    for row in settled:
        require(type(row.get('valid')) is bool and type(row.get('fatal')) is bool and type(row.get('cost_is_reserve')) is bool,'settlement_boolean_schema')
        job=byid[row['id']];profile=profiles[job['model_key']];bound=D(row['reserve_usd'])
        if row.get('reason')=='interrupted_unknown':
            require(row['valid'] is False and row['action'] is None and row['fatal'] is False and row['cost_is_reserve'] is True,'crash_unknown_schema')
            require(D(row['charged_or_reserved_usd'])==bound,'crash_unknown_reserve')
            require(not row.get('response'),'crash_unknown_has_response')
        else:
            expected=runtime.classify(row,profile,job,bound)
            if row.get('worker_error'):
                require(isinstance(row['worker_error'],str),'worker_error_type')
                expected=(False,None,'fatal_worker_exception',True)
            obj=runtime.object_or_empty(row.get('response'));fp=obj.get('system_fingerprint')
            if obj.get('model') in profile['allowed_models'] and obj.get('provider')==profile['provider_name'] and fp is not None:
                key=profile['key']
                if key not in seen_fp:seen_fp[key]=fp
                elif fp!=seen_fp[key]:expected=(False,None,'fatal_fingerprint_drift',True)
            require(expected==(row['valid'],row['action'],row['reason'],row['fatal']),'raw_response_classification:'+row['attempt_id'])
            charged,reserved=runtime.cost_value(row,bound)
            require(D(row['charged_or_reserved_usd'])==charged and row['cost_is_reserve']==reserved,'raw_response_cost')
        if not row['valid']:
            failures.append({k:row.get(k) for k in ('attempt_id','id','model_key','attempt','reason','fatal','http_status','elapsed_seconds','charged_or_reserved_usd','cost_is_reserve','utc','settled_utc')})
    return failures,seen_fp


def _verify_locked(run):
    # This function is called only while owning the same OS lock as execution.
    before=runtime.read(run/'status.json')
    require(before.get('state') in runtime.TERMINAL,'not_terminal')
    raw_manifest=runtime.read(run/'manifest.json')
    require(all(Path(n).name==n and not Path(n).is_absolute() for n in raw_manifest.get('sources',{})),'source_path_outside_revision')
    manifest,jobs=runtime.validate(run)
    require(before.get('manifest_sha256')==manifest['manifest_sha256'],'status_manifest')
    _scientific_identity(manifest,jobs)
    started=runtime.lines(run/'started.jsonl');settled=runtime.lines(run/'attempts.jsonl')
    ledger=runtime.Ledger(started,settled)
    profiles={p['key']:p for p in manifest['profiles']}
    byid={j['id']:j for j in jobs+[runtime.compatibility(p) for p in manifest['profiles']]}
    require(len(byid)==len(jobs)+len(profiles),'compatibility_identity_collision')
    failures,fingerprints=_classifications(started,settled,profiles,byid)
    independently_summed=runtime.accounting(started,settled)
    require(independently_summed==ledger.occupied,'independent_accounting')
    accepted={}
    for row in settled:
        if row['valid']:
            require(row['id'] not in accepted,'duplicate_valid_logical_id')
            accepted[row['id']]=row
    known=sum((D(r['charged_or_reserved_usd']) for r in settled if not r['cost_is_reserve']),D(0))
    unknown=ledger.occupied-runtime.PRIOR-known
    final=runtime.read(run/'final_ledger.json')
    required={'status':'independently_reconciled','prior_occupied_usd':str(runtime.PRIOR),
              'known_new_cost_usd':str(known),'unknown_new_reserved_usd':str(unknown),
              'cumulative_occupied_usd':str(ledger.occupied),'cumulative_cap_usd':str(runtime.CAP),
              'started_sha256':runtime.sha(run/'started.jsonl') if (run/'started.jsonl').exists() else None,
              'settled_sha256':runtime.sha(run/'attempts.jsonl') if (run/'attempts.jsonl').exists() else None,
              'manifest_sha256':manifest['manifest_sha256']}
    require(final==required,'final_ledger_mismatch')
    science_ids={j['id'] for j in jobs};naccepted=sum(i in science_ids for i in accepted)
    require(before['scientific_planned']==len(jobs) and before['science_accepted']==naccepted,'status_science_counts')
    require(before['physical_started']==len(started) and before['physical_settled']==len(settled),'status_physical_counts')
    require(before['inflight']==len(started)-len(settled),'status_inflight')
    require(D(before['cumulative_occupied_usd'])==ledger.occupied,'status_cost')
    if before['state']=='complete':
        require(len(started)==len(settled),'complete_has_unsettled')
        require(all(j['id'] in accepted or ledger.tries[j['id']]==3 for j in jobs),'complete_has_unattempted_science')
        require(all(runtime.compatibility(p)['id'] in accepted for p in manifest['profiles']),'complete_missing_compatibility')
        require(not any(r['fatal'] for r in settled),'complete_has_fatal_response')
    events=runtime.lines(run/'operations.jsonl')
    tracker,pauses,pending=runtime.pause_state(settled,events)
    require(runtime.read(run/'status.json')==before,'terminal_status_changed_during_read')
    return manifest,jobs,started,settled,accepted,ledger,final,before,failures,fingerprints,events


def export_run(run,output=None):
    run=Path(run).resolve();output=Path(output).resolve() if output else run/'terminal_export'
    require((run/'status.json').exists(),'status_missing')
    # Inspect only state before locking. Scientific journals are never read if
    # a running process owns the lock or the state is not terminal.
    require(runtime.read(run/'status.json').get('state') in runtime.TERMINAL,'not_terminal')
    with runtime.execution_lock(run/'execution.lock'):
        data=_verify_locked(run)
        manifest,jobs,started,settled,accepted,ledger,final,status,failures,fingerprints,events=data
        import analysis
        cohorts={};lineage=[];cellrows=[];freerows=[];contrasts=[];predictions=[]
        for profile in manifest['profiles']:
            key=profile['key'];profile_name='full' if key=='luna' else 'cross';subset=[j for j in jobs if j['model_key']==key]
            normalized=[_normalize_job(j) for j in subset]
            outcomes={_normalize_job(j)['id']:{'valid':True,'action':accepted[j['id']]['action']} for j in subset if j['id'] in accepted}
            result=analysis.analyze(normalized,outcomes,{'model_key':key,'allocationprofile':profile_name})
            cohorts[key]={'profile':profile,'allocationprofile':profile_name,'analysis':result}
            for job in subset:
                m=job['metadata'];selected=accepted.get(job['id']);valid=selected is not None
                lineage.append(dict(model_key=key,logical_id=_normalize_job(job)['id'],runtime_id=job['id'],block_id=job['block_id'],module=job['module'],
                    wording=m['wording'],analysis_split=m['analysis_split'],policy=m['policy'],law=m['law'],encoding=m['encoding'],safe=m['safe'],actor=m['actor'],p=m['p'],
                    mapping=m['mapping'],display_order=m['display_order'],expected=job['expected'],valid=valid,action=selected['action'] if valid else None,
                    correct=(selected['action']==job['expected']) if valid and job['expected'] is not None else None,
                    physical_attempts=ledger.tries[job['id']],selected_attempt_id=selected['attempt_id'] if valid else None,
                    selected_attempt=selected['attempt'] if valid else None,request_sha256=job['request_sha256']))
            cellrows.extend({'model_key':key,**row} for row in result['summaries'])
            freerows.extend({'model_key':key,**row} for row in result['free_cells'])
            for family in ('primary_family_7','value_family_2','capability_family_3'):
                contrasts.extend({'model_key':key,'family':family,'contrast':name,**row} for name,row in result[family].items())
            predictions.extend({'model_key':key,'predictor':name,**row} for name,row in result['prediction'].get('models',{}).items())
        bymodel={}
        for profile in manifest['profiles']:
            key=profile['key'];ss=[r for r in started if r['model_key']==key];rr=[r for r in settled if r['model_key']==key]
            valid=[r for r in rr if r['valid'] and not r['id'].endswith('|compatibility')]
            elapsed=sorted(r['elapsed_seconds'] for r in rr if runtime.finite_nonnegative(r.get('elapsed_seconds')))
            known=sum((D(r['charged_or_reserved_usd']) for r in rr if not r['cost_is_reserve']),D(0))
            used=sum((D(r['charged_or_reserved_usd']) for r in rr),D(0))+sum((D(r['reserve_usd']) for r in ss if r['attempt_id'] not in ledger.settled),D(0))
            bymodel[key]={'planned_scientific':sum(j['model_key']==key for j in jobs),'valid_scientific':len(valid),'physical_started':len(ss),'physical_settled':len(rr),
                'settlement_reasons':dict(sorted(Counter(r['reason'] for r in rr).items())),
                'first_valid_attempts':dict(sorted(Counter(r['attempt'] for r in valid).items())),
                'known_cost_usd':str(known),'unknown_reserved_usd':str(used-known),'new_occupied_usd':str(used),
                'elapsed_seconds_min':elapsed[0] if elapsed else None,'elapsed_seconds_max':elapsed[-1] if elapsed else None,
                'elapsed_seconds_median':(elapsed[(len(elapsed)-1)//2]+elapsed[len(elapsed)//2])/2 if elapsed else None,
                'observed_nonempty_fingerprint':fingerprints.get(key)}
        input_names=['manifest.json','planned.jsonl','status.json','started.jsonl','attempts.jsonl','final_ledger.json','operations.jsonl','preflight.jsonl']
        audit={'status':'passed_terminal_export','manifest_sha256':manifest['manifest_sha256'],'execution_state':status['state'],'execution_reason':status.get('reason'),
               'gate':'terminal state plus acquired runner OS lock; persistent lock-file existence is not liveness',
               'scientific_planned':len(jobs),'scientific_valid':sum(r['valid'] for r in lineage),'scientific_missing':sum(not r['valid'] for r in lineage),
               'physical_started':len(started),'physical_settled':len(settled),'unsettled_reservations':len(started)-len(settled),
               'failures_preserved':len(failures),'known_wrong_responses_retained':sum(r['correct'] is False for r in lineage),
               'operational_pauses':sum(e['event']=='operational_pause' for e in events),
               'completed_operational_pauses':sum(e['event']=='operational_pause_completed' for e in events),
               'input_sha256':{name:runtime.sha(run/name) for name in input_names if (run/name).exists()},
               'frozen_sources':manifest['sources'],'exporter_sha256':runtime.sha(Path(__file__)),
               'ledger':final,'by_model':bymodel,
               'checks':['frozen source and manifest hashes','scientific job regeneration and request hashes','unique starts/settlements and first valid <=3 attempts',
                         'raw response identity/provider/no-thinking/schema/cost reclassification','all planned denominators and missing bounds','independent terminal ledger reconciliation'],
               'inference_limit':'A completed export does not prove model stationarity, independence of block response vectors, or absence of latency selection.'}
        contents={'analysis.json':_bytes_json({'manifest_sha256':manifest['manifest_sha256'],'cohorts':cohorts}),
                  'logical_outcomes.csv':_csv_bytes(lineage),'cell_summaries.csv':_csv_bytes(cellrows),'free_cells.csv':_csv_bytes(freerows),
                  'contrasts.csv':_csv_bytes(contrasts),'prediction.csv':_csv_bytes(predictions),'failed_attempts.csv':_csv_bytes(failures),
                  'operational_audit.json':_bytes_json(audit)}
        # Recheck journal bytes after analysis before committing a reproducible export.
        require(all(runtime.sha(run/n)==h for n,h in audit['input_sha256'].items()),'input_changed_during_export')
        output.mkdir(parents=True,exist_ok=True)
        for name,payload in contents.items():_write_once_or_identical(output/name,payload)
        artifact={'status':'passed','manifest_sha256':manifest['manifest_sha256'],'files_sha256':{n:runtime.digest(b) for n,b in contents.items()},
                  'scientific_planned':audit['scientific_planned'],'scientific_valid':audit['scientific_valid'],'scientific_missing':audit['scientific_missing']}
        _write_once_or_identical(output/'export_manifest.json',_bytes_json(artifact))
        return artifact

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--run',required=True,type=Path);parser.add_argument('--output',type=Path)
    args=parser.parse_args();print(runtime.compact(export_run(args.run,args.output)))
