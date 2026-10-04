"""Offline export of a separately authorized extended-response supplement.
The original scientific formulas are reused. Capped exports are immutable.
This module must never import the paid supplement/recovery/supervisor adapters.
"""
from pathlib import Path
from dataclasses import dataclass
from collections import Counter
from contextlib import ExitStack
import argparse, json
import runtime
import export_validation as frozen_export

HERE=Path(__file__).resolve().parent
LAYER='parsed_fixed512_extended_response'
POLICY=('User-authorized revised response policy: preserve all original strict valids; recover earliest unambiguous stop-finished answers only for strict-missing IDs; then make missing-only fixed512 calls with the same prompts/routes/none reasoning. Raw strict flags remain unchanged, unknown reserves are retained, and this is not an independent replication.')


def require(value,label):
    if not value:raise ValueError('completion_export:'+label)


@dataclass
class CompletionVerification:
    manifest: dict
    scientific_manifest: dict
    jobs: list
    started: list
    settled: list
    accepted: dict
    tries: dict
    final: dict
    status: dict
    failures: list
    fingerprints: dict
    input_sha256: dict
    source_binding: dict
    operational_context: dict


def _overlay_selection(row):
    return {'action':row['accepted_action'],'attempt_id':row['attempt_id'],'attempt':row['attempt'],
            'selection_layer':'supplement_strict' if row['valid'] else 'supplement_parsed',
            'strict_reason':row['reason'],'rule':row['acceptance_rule'],
            'content_sha256':row['extraction']['content_sha256'] if row.get('extraction') else None}


def render_payloads(v):
    """Apply the unchanged frozen formulas to one all-planned first-valid map."""
    import analysis
    manifest=v.manifest;scientific=v.scientific_manifest;jobs=v.jobs
    capped_ids=set(v.source_binding['capped_first_valid_attempt_ids'])
    capped_tries=v.source_binding['capped_tries_by_id']
    cohorts={};lineage=[];cellrows=[];freerows=[];contrasts=[];predictions=[]
    for profile in scientific['profiles']:
        key=profile['key'];allocation='full' if key=='luna' else 'cross'
        subset=[j for j in jobs if j['model_key']==key]
        normalized=[frozen_export._normalize_job(j) for j in subset]
        outcomes={frozen_export._normalize_job(j)['id']:{'valid':True,'action':v.accepted[j['id']]['action']}
                  for j in subset if j['id'] in v.accepted}
        result=analysis.analyze(normalized,outcomes,{'model_key':key,'allocationprofile':allocation})
        inherited=list(result['inference_assumptions'])
        require(inherited and 'at most three' in inherited[0],'unexpected_frozen_policy_metadata')
        result['inference_assumptions']=[POLICY,*inherited[1:]]
        result['inherited_capped_policy_statement']=inherited[0]
        result['execution_layer']=LAYER
        cohorts[key]={'profile':profile,'allocationprofile':allocation,'analysis':result}
        for job in subset:
            m=job['metadata'];selected=v.accepted.get(job['id']);valid=selected is not None
            layer=selected['selection_layer'] if valid else 'unresolved'
            lineage.append(dict(model_key=key,logical_id=frozen_export._normalize_job(job)['id'],runtime_id=job['id'],
                block_id=job['block_id'],module=job['module'],wording=m['wording'],analysis_split=m['analysis_split'],
                policy=m['policy'],law=m['law'],encoding=m['encoding'],safe=m['safe'],actor=m['actor'],p=m['p'],
                mapping=m['mapping'],display_order=m['display_order'],expected=job['expected'],valid=valid,
                action=selected['action'] if valid else None,
                correct=(selected['action']==job['expected']) if valid and job['expected'] is not None else None,
                physical_attempts=v.tries.get(job['id'],0),selected_attempt_id=selected['attempt_id'] if valid else None,
                selected_attempt=selected['attempt'] if valid else None,request_sha256=job['request_sha256'],
                selected_source_layer=layer,original_strict_reason=selected['strict_reason'] if valid else None,
                extraction_rule=selected['rule'] if valid else None,content_sha256=selected['content_sha256'] if valid else None,
                capped_physical_attempts=capped_tries.get(job['id'],0),
                supplement_physical_attempts=v.tries.get(job['id'],0)-capped_tries.get(job['id'],0)))
        cellrows.extend({'model_key':key,**r} for r in result['summaries'])
        freerows.extend({'model_key':key,**r} for r in result['free_cells'])
        for family in ('primary_family_7','value_family_2','capability_family_3'):
            contrasts.extend({'model_key':key,'family':family,'contrast':name,**row} for name,row in result[family].items())
        predictions.extend({'model_key':key,'predictor':name,**row} for name,row in result['prediction'].get('models',{}).items())
    settled_ids={r['attempt_id'] for r in v.settled};bymodel={}
    for profile in scientific['profiles']:
        key=profile['key'];starts=[r for r in v.started if r['model_key']==key];rows=[r for r in v.settled if r['model_key']==key]
        valid=[v.accepted[j['id']] for j in jobs if j['model_key']==key and j['id'] in v.accepted]
        elapsed=sorted(r['elapsed_seconds'] for r in rows if runtime.finite_nonnegative(r.get('elapsed_seconds')))
        known=sum((runtime.D(r['charged_or_reserved_usd']) for r in rows if not r['cost_is_reserve']),runtime.D(0))
        used=sum((runtime.D(r['charged_or_reserved_usd']) for r in rows),runtime.D(0))+sum(
            (runtime.D(r['reserve_usd']) for r in starts if r['attempt_id'] not in settled_ids),runtime.D(0))
        bymodel[key]={'planned_scientific':sum(j['model_key']==key for j in jobs),'valid_scientific':len(valid),
            'physical_started':len(starts),'physical_settled':len(rows),'settlement_reasons':dict(sorted(Counter(r['reason'] for r in rows).items())),
            'first_valid_attempts':dict(sorted(Counter(r['attempt'] for r in valid).items())),
            'known_cost_usd':str(known),'unknown_reserved_usd':str(used-known),'new_occupied_usd':str(used),
            'elapsed_seconds_min':elapsed[0] if elapsed else None,'elapsed_seconds_max':elapsed[-1] if elapsed else None,
            'elapsed_seconds_median':(elapsed[(len(elapsed)-1)//2]+elapsed[len(elapsed)//2])/2 if elapsed else None,
            'observed_nonempty_fingerprint':v.fingerprints.get(key)}
    capped_final=v.source_binding['capped_final_ledger']
    known=runtime.D(capped_final['known_new_cost_usd'])+runtime.D(v.final['overlay_known_cost_usd'])
    unknown=runtime.D(capped_final['unknown_new_reserved_usd'])+runtime.D(v.final['overlay_unknown_reserved_usd'])
    prior=runtime.D(capped_final['prior_occupied_usd']);cumulative=runtime.D(v.final['cumulative_occupied_usd'])
    require(prior==runtime.PRIOR and prior+known+unknown==cumulative,'normalized_ledger_reconciliation')
    require(sum((runtime.D(row['known_cost_usd']) for row in bymodel.values()),runtime.D(0))==known
            and sum((runtime.D(row['unknown_reserved_usd']) for row in bymodel.values()),runtime.D(0))==unknown,'normalized_model_cost_reconciliation')
    normalized_ledger={'status':'independently_reconciled','prior_occupied_usd':str(prior),
        'known_new_cost_usd':str(known),'unknown_new_reserved_usd':str(unknown),
        'cumulative_occupied_usd':str(cumulative),'cumulative_cap_usd':str(runtime.CAP),
        'manifest_sha256':manifest['manifest_sha256'],'scientific_manifest_sha256':scientific['manifest_sha256'],
        'scope':'Combined capped and supplemental physical attempts counted exactly once; original prior cost added once.'}
    audit={'status':'passed_terminal_export','execution_layer':LAYER,'response_policy':POLICY,
        'manifest_sha256':manifest['manifest_sha256'],'scientific_manifest_sha256':scientific['manifest_sha256'],
        'execution_state':v.status['state'],'execution_reason':v.status.get('reason'),
        'gate':'terminal status plus supplement outer/execution and capped-source locks; no paid adapter imported',
        'scientific_planned':len(jobs),'scientific_valid':sum(r['valid'] for r in lineage),
        'capped_scientific_valid':v.source_binding['capped_operational_audit']['scientific_valid'],
        'supplement_new_valid_scientific':v.operational_context['overlay_valid_scientific'],
        'source_parsed_recovered_scientific':v.operational_context['source_parsed_recovered_scientific'],
        'fixed_new_max_tokens':512,
        'scientific_missing':sum(not r['valid'] for r in lineage),'physical_started':len(v.started),
        'physical_settled':len(v.settled),'unsettled_reservations':len(v.started)-len(v.settled),
        'failures_preserved':len(v.failures),'known_wrong_responses_retained':sum(r['correct'] is False for r in lineage),
        'input_path_base':'repository','input_sha256':v.input_sha256,'frozen_sources':scientific['sources'],'supplement_sources':manifest['supplement_sources'],
        'exporter_sha256':runtime.sha(Path(__file__)),'ledger':normalized_ledger,'supplement_final_ledger':v.final,'by_model':bymodel,
        'operational_pauses':v.operational_context['shared_pauses_used'],
        'completed_operational_pauses':v.operational_context['source_pauses_used']+v.operational_context['supplement_completed_pause_count'],
        'source_binding':v.source_binding,'operational_context':v.operational_context,
        'checks':['immutable capped source and static I/O recovery provenance','same regenerated scientific allocation and request hashes',
                  'independent global attempt and first-valid event replay without a three-attempt cap',
                  'separate original128 and new512 identity/provider/no-thinking/strict-schema and extracted-selection checks',
                  'all planned denominators and unchanged frozen numerical formulas','independent cumulative accounting without duplicate baseline cost'],
        'inference_limit':'Supplemental estimates concern the extended-response policy. Completion does not prove temporal stability, block independence or absence of latency selection; capped results remain a separate immutable layer.'}
    data={'manifest_sha256':manifest['manifest_sha256'],'scientific_manifest_sha256':scientific['manifest_sha256'],
          'execution_layer':LAYER,'response_policy':POLICY,'cohorts':cohorts}
    contents={'analysis.json':frozen_export._bytes_json(data),'logical_outcomes.csv':frozen_export._csv_bytes(lineage),
        'cell_summaries.csv':frozen_export._csv_bytes(cellrows),'free_cells.csv':frozen_export._csv_bytes(freerows),
        'contrasts.csv':frozen_export._csv_bytes(contrasts),'prediction.csv':frozen_export._csv_bytes(predictions),
        'failed_attempts.csv':frozen_export._csv_bytes(v.failures),'operational_audit.json':frozen_export._bytes_json(audit)}
    artifact={'status':'passed','manifest_sha256':manifest['manifest_sha256'],
        'scientific_manifest_sha256':scientific['manifest_sha256'],'execution_layer':LAYER,
        'files_sha256':{n:runtime.digest(b) for n,b in contents.items()},'scientific_planned':len(jobs),
        'scientific_valid':audit['scientific_valid'],'scientific_missing':audit['scientific_missing'],
        'capped_scientific_valid':audit['capped_scientific_valid'],'supplement_new_valid_scientific':audit['supplement_new_valid_scientific']}
    contents['export_manifest.json']=frozen_export._bytes_json(artifact)
    return contents,audit,artifact



def independently_replay(verified,manifest,events):
    """Independent chronological ID/round/first-valid/cost fold, without old Ledger.
    The pure projected ledger separately checks detailed service-pause semantics.
    """
    scientific,jobs,old_starts,old_settled,old_accepted,old_ledger,*_=verified
    import supplement_response
    byid={j['id']:j for j in jobs};profiles={p['key']:p for p in scientific['profiles']}
    tries=Counter({j['id']:old_ledger.tries[j['id']] for j in jobs})
    accepted={i:dict(v) for i,v in manifest['baseline']['accepted_selection'].items()};baseline_selected={i:dict(v) for i,v in accepted.items()};started={r['attempt_id']:r for r in old_starts};settled={r['attempt_id']:r for r in old_settled}
    require(len(started)==len(old_starts) and len(settled)==len(old_settled)<=len(started),'baseline_attempt_inventory')
    extra_starts=[];extra_settled=[];inflight=[];round_ids=None;cursor=0;round_number=0;fatal=False
    occupied=runtime.D(old_ledger.occupied)
    for sequence,event in enumerate(events,1):
        require(type(event.get('sequence')) is int and event['sequence']==sequence,'independent_event_sequence')
        kind=event['event']
        if kind=='round_started':
            require(not fatal and round_ids is None and not inflight,'independent_round_state')
            wanted=[j['id'] for j in jobs if j['id'] not in accepted]
            require(event['ids']==wanted and wanted and event['round']==round_number+1,'independent_round_membership')
            round_number+=1;round_ids=wanted;cursor=0
        elif kind=='round_completed':
            require(round_ids is not None and event['round']==round_number and cursor==len(round_ids) and not inflight,'independent_round_completion')
            round_ids=None;cursor=0
        elif kind=='attempt_started':
            row=event['row'];ident=row['id'];aid=row['attempt_id']
            require(not fatal and round_ids is not None and cursor<len(round_ids) and ident==round_ids[cursor],'independent_start_order')
            require(ident in byid and ident not in accepted and aid not in started,'independent_start_membership')
            require(type(row['attempt']) is int and row['attempt']==tries[ident]+1 and aid==ident+'|try'+str(row['attempt']),'independent_global_attempt')
            job=byid[ident];profile=profiles[job['model_key']];body=supplement_response.payload(profile,job)
            bound=supplement_response.reserve(profile,body)
            require(row['model_key']==job['model_key'] and row['source_request_sha256']==job['request_sha256']
                    and row['request_sha256']==runtime.digest(runtime.compact(body).encode()),'independent_request_identity')
            require(runtime.D(row['reserve_usd'])==bound and bound.is_finite() and bound>=0,'independent_start_reserve')
            require(occupied+bound<=runtime.CAP and len(inflight)<16,'independent_start_capacity')
            require(all(started[i]['id']!=ident for i in inflight),'independent_duplicate_inflight')
            tries[ident]+=1;occupied+=bound;started[aid]=row;extra_starts.append(row);inflight.append(aid);cursor+=1
        elif kind=='attempt_settled':
            row=event['row'];aid=row['attempt_id'];ident=row['id']
            require(aid in started and aid not in settled and inflight and inflight[0]==aid,'independent_settlement_order')
            start=started[aid]
            require(all(row.get(k)==start.get(k) for k in ('id','model_key','attempt','attempt_id','request_sha256','source_request_sha256','reserve_usd','utc')),'independent_settlement_identity')
            require(all(type(row.get(k)) is bool for k in ('valid','fatal','cost_is_reserve','accepted')),'independent_settlement_flags')
            charge=runtime.D(row['charged_or_reserved_usd']);bound=runtime.D(start['reserve_usd'])
            require(charge.is_finite() and charge>=0 and (not row['cost_is_reserve'] or charge==bound),'independent_settlement_cost')
            if row['accepted']:
                require(ident not in accepted and tries[ident]==row['attempt'],'independent_first_valid_replacement')
                accepted[ident]=_overlay_selection(row)
            fatal=fatal or row['fatal'];settled[aid]=row;extra_settled.append(row);inflight.pop(0);occupied+=charge-bound
        else:
            require(kind in ('preflight','operational_pause','operational_pause_completed'),'independent_unknown_event')
    combined_starts=old_starts+extra_starts;combined_settled=old_settled+extra_settled
    independently_summed=runtime.PRIOR+sum((runtime.D(settled[aid]['charged_or_reserved_usd']) if aid in settled
        else runtime.D(row['reserve_usd']) for aid,row in started.items()),runtime.D(0))
    overlay_sum=runtime.D(old_ledger.occupied)+sum((runtime.D(settled[row['attempt_id']]['charged_or_reserved_usd'])
        if row['attempt_id'] in settled else runtime.D(row['reserve_usd']) for row in extra_starts),runtime.D(0))
    require(occupied==independently_summed==overlay_sum,'independent_cumulative_accounting')
    require(all(accepted.get(k)==v for k,v in baseline_selected.items()),'independent_source_selection_changed')
    return combined_starts,combined_settled,accepted,dict(tries),occupied


def verify_locked(run):
    """Verify the separately frozen parsed-response/fixed-512 supplement.
    Caller owns supplement.lock then execution.lock; source remains interrupted.
    """
    import supplement_contract as contract
    from supplement_ledger import ProjectedLedger
    import answer_recovery_source
    run=Path(run).resolve();status=runtime.read(run/'status.json')
    require(status.get('state') in runtime.TERMINAL,'not_terminal')
    manifest=contract.validate_manifest(run)
    require(manifest.get('version')==2,'parsed_policy_version')
    require(manifest['supplement_sources'].get(Path(__file__).name)==runtime.sha(Path(__file__)),'exporter_not_source_bound')
    source=contract.contained_file(manifest['source_run_relative'])
    closure_path=contract.contained_file(manifest['source_closure_relative'])
    with contract.source_locks(source):
        verified=contract.load_bound_source(manifest)
        scientific,jobs,old_starts,old_settled,old_accepted,old_ledger,old_final,old_status,old_failures,old_fingerprints,old_events=verified
        closure=runtime.read(closure_path)
        require(closure['closure_sha256']==manifest['source_closure_sha256'],'source_closure_binding')
        audits={}
        for label in ('strict_export','parsed_export'):
            export=closure_path.parent/label;em=runtime.read(export/'export_manifest.json')
            require(em.get('status')=='passed' and em.get('manifest_sha256')==closure['closure_sha256'],'source_export_identity')
            for name,digest in em['files_sha256'].items():
                require(Path(name).name==name and runtime.sha(export/name)==digest,'source_export_member_changed')
            audit=runtime.read(export/'operational_audit.json')
            require(audit.get('status')=='passed_operator_closed_export'
                    and audit['source_files_sha256']==closure['source_files_sha256'],'source_audit_binding')
            audits[label]=audit
        require(audits['strict_export']['scientific_valid']==old_status['science_accepted']
                and audits['parsed_export']['scientific_valid']==len(manifest['baseline']['accepted_ids']),'source_selection_count_binding')
        events=runtime.lines(run/contract.JOURNAL)
        ledger=ProjectedLedger(manifest['baseline'],jobs,scientific['profiles'],events)
        contract.verify_status(manifest,ledger,status,terminal=True)
        final=runtime.read(run/'final_ledger.json')
        journal_sha=runtime.sha(run/contract.JOURNAL) if (run/contract.JOURNAL).exists() else None
        require(final==contract.final_ledger_record(manifest,ledger,journal_sha),'supplement_final_ledger_changed')
        starts,settled,accepted,tries,occupied=independently_replay(verified,manifest,events)
        require(occupied==ledger.occupied and tries==dict(ledger.tries),'projected_ledger_disagreement')
        require(set(accepted)==ledger.accepted,'projected_first_valid_disagreement')
        require(all(accepted.get(i)==_overlay_selection(row) for i,row in ledger.newly_accepted_rows.items()),'projected_selected_row_disagreement')
        failures=list(old_failures)
        for row in ledger.settled:
            if not row['valid']:
                failures.append({k:row.get(k) for k in ('attempt_id','id','model_key','attempt','reason','fatal','http_status','elapsed_seconds','charged_or_reserved_usd','cost_is_reserve','utc','settled_utc')})
        paths=dict(manifest['source_files_sha256'])
        for name in ('manifest.json','status.json',contract.JOURNAL,'final_ledger.json'):
            path=run/name
            if path.exists():paths[path.relative_to(contract.REPO).as_posix()]=runtime.sha(path)
        for name,digest in manifest['supplement_sources'].items():
            paths[(contract.HERE/name).relative_to(contract.REPO).as_posix()]=digest
        am=runtime.read(source/'io_recovery_amendment.json')
        original=source.parent/Path(am['original_run_path']).name
        source_binding={'source_run_relative':manifest['source_run_relative'],
            'source_closure_relative':manifest['source_closure_relative'],'operator_closure':closure,
            'capped_scientific_manifest_sha256':scientific['manifest_sha256'],
            'capped_export_manifest_sha256':runtime.sha(closure_path.parent/'strict_export/export_manifest.json'),
            'parsed_export_manifest_sha256':runtime.sha(closure_path.parent/'parsed_export/export_manifest.json'),
            'capped_terminal_status':old_status,'capped_final_ledger':old_final,'capped_operational_audit':audits['strict_export'],
            'parsed_source_operational_audit':audits['parsed_export'],
            'capped_first_valid_attempt_ids':[row['attempt_id'] for row in old_accepted.values()],
            'source_accepted_selection':manifest['baseline']['accepted_selection'],
            'capped_tries_by_id':{j['id']:old_ledger.tries[j['id']] for j in jobs},
            'source_recovery_provenance':None,'source_io_amendment':am,
            'original_source_directory':original.relative_to(contract.REPO).as_posix(),
            'original_capped_outputs_retained':True}
        context={'shared_pauses_used':ledger.pauses,'source_pauses_used':manifest['baseline']['pauses'],
            'supplement_pause_count':sum(e['event']=='operational_pause' for e in events),
            'supplement_completed_pause_count':sum(e['event']=='operational_pause_completed' for e in events),
            'rounds_started':ledger.round,'overlay_started':len(ledger.starts),'overlay_settled':len(ledger.settled),
            'overlay_valid_scientific':len(ledger.newly_accepted_rows),'no_progress':ledger.no_progress,
            'source_strict_scientific':audits['strict_export']['scientific_valid'],
            'source_parsed_recovered_scientific':audits['parsed_export']['parsed_recovered_scientific'],
            'source_unsettled_reservations':len(old_starts)-len(old_settled),'fixed_new_max_tokens':512,
            'source_scope':'Interrupted strict source and separately parsed recovery retained. New missing-only calls use fixed512 response limit and audited stop-only extraction; all physical costs and unknown reserves are counted once.'}
        require(runtime.read(run/'status.json')==status,'terminal_status_changed_during_verification')
        require(all(runtime.sha(contract.contained_file(n))==h for n,h in paths.items()),'input_changed_during_verification')
        return CompletionVerification(manifest,scientific,jobs,starts,settled,accepted,tries,final,status,
            failures,ledger.fingerprints,paths,source_binding,context)


def verify_terminal(run):
    """Public locked, terminal-only read API for document/figure/export readers."""
    import supplement_contract as contract
    run=Path(run).resolve()
    require(runtime.read(run/'status.json').get('state') in runtime.TERMINAL,'not_terminal')
    with runtime.execution_lock(run/contract.LOCK):
        with runtime.execution_lock(run/'execution.lock'):
            return verify_locked(run)


def export_run(run,output=None):
    import supplement_contract as contract
    run=Path(run).resolve();output=Path(output).resolve() if output else run/'terminal_export'
    require(runtime.read(run/'status.json').get('state') in runtime.TERMINAL,'not_terminal')
    with runtime.execution_lock(run/contract.LOCK):
        with runtime.execution_lock(run/'execution.lock'):
            verified=verify_locked(run)
            source=contract.contained_file(verified.manifest['source_run_relative'])
            original=contract.contained_file(verified.source_binding['original_source_directory'])
            require(all(output!=base and not output.is_relative_to(base) for base in (source,original)),'cannot_write_into_preserved_source')
            contents,audit,artifact=render_payloads(verified)
            require(all(runtime.sha(contract.contained_file(n))==h for n,h in verified.input_sha256.items()),'input_changed_during_analysis')
            output.mkdir(parents=True,exist_ok=True)
            for name,payload in contents.items():frozen_export._write_once_or_identical(output/name,payload)
            require(all(runtime.sha(contract.contained_file(n))==h for n,h in verified.input_sha256.items()),'input_changed_during_export')
            return artifact


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run',type=Path,required=True);parser.add_argument('--output',type=Path)
    args=parser.parse_args();print(runtime.compact(export_run(args.run,args.output)))
