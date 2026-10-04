"""Pure terminal exporter for fixed2048 DeepSeek-only completion.
Old128/512 sources and all four original cohorts remain immutable and archived.
"""
from pathlib import Path
from collections import Counter
import argparse
import runtime
import export_validation as frozen_export
from export_completion import CompletionVerification

HERE=Path(__file__).resolve().parent
LAYER='parsed_fixed2048_deepseek_completion'
MAIN_MODELS=('luna','qwen','deepseek')
DEFERRED_MODELS=('claude',)
TOKEN_CEILINGS={'strict':128,'parsed_recovery':128,'supplement_strict':512,'supplement_parsed':512,
                'ceiling2048_strict':2048,'ceiling2048_parsed':2048}
POLICY=('User-authorized acquisition amendment: preserve all previously accepted128/512-token answers, including wrong answers; '
        'use fixed2048-token requests only for unresolved DeepSeek IDs with unchanged scientific prompts, model/provider and disabled thinking. '
        'Sonnet is deferred for cost before behavioral effects are inspected. All four planned cohorts remain archived; '
        'main-text claims concern Luna, Qwen and DeepSeek. This is amended acquisition, not an independent replication.')


def require(value,label):
    if not value:raise ValueError('ceiling2048_export:'+label)


def _selection(row):
    return {'action':row['accepted_action'],'attempt_id':row['attempt_id'],'attempt':row['attempt'],
            'selection_layer':'ceiling2048_strict' if row['valid'] else 'ceiling2048_parsed',
            'strict_reason':row['reason'],'rule':row['acceptance_rule'],
            'content_sha256':row['extraction']['content_sha256'] if row.get('extraction') else None}


def render_payloads(v):
    """Apply the unchanged frozen formulas to one all-planned first-valid map."""
    import analysis
    manifest=v.manifest;scientific=v.scientific_manifest;jobs=v.jobs
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
        result['presentation_role']='deferred_operational_appendix' if key in DEFERRED_MODELS else 'primary' if key=='luna' else 'secondary_replication'
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
                supplement_physical_attempts=v.tries.get(job['id'],0)-capped_tries.get(job['id'],0),
                ceiling2048_physical_attempts=v.tries.get(job['id'],0)-manifest['baseline']['tries'][job['id']],
                selected_request_token_ceiling=TOKEN_CEILINGS.get(layer)))
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
    known=sum((runtime.D(row['known_cost_usd']) for row in bymodel.values()),runtime.D(0))
    unknown=sum((runtime.D(row['unknown_reserved_usd']) for row in bymodel.values()),runtime.D(0))
    prior=runtime.PRIOR;cumulative=runtime.D(v.final['cumulative_occupied_usd'])
    require(prior+known+unknown==cumulative,'flat_ledger_reconciliation')
    require(runtime.D(manifest['baseline']['occupied_usd'])+runtime.D(v.final['overlay_known_cost_usd'])
            +runtime.D(v.final['overlay_unknown_reserved_usd'])==cumulative,'source_plus2048_reconciliation')
    normalized_ledger={'status':'independently_reconciled','prior_occupied_usd':str(prior),
        'known_new_cost_usd':str(known),'unknown_new_reserved_usd':str(unknown),
        'cumulative_occupied_usd':str(cumulative),'cumulative_cap_usd':str(manifest['policy']['cumulative_cap_usd']),
        'manifest_sha256':manifest['manifest_sha256'],'scientific_manifest_sha256':scientific['manifest_sha256'],
        'scope':'Flat deduplicated128/512/2048 physical inventory; each started attempt and the historical prior are counted exactly once.'}
    audit={'status':'passed_terminal_export','execution_layer':LAYER,'response_policy':POLICY,
        'manifest_sha256':manifest['manifest_sha256'],'scientific_manifest_sha256':scientific['manifest_sha256'],
        'execution_state':v.status['state'],'execution_reason':v.status.get('reason'),
        'gate':'true terminal or eligible_complete plus new and stopped512 source locks, followed by inherited source verification; no paid adapter imported',
        'scientific_planned':len(jobs),'scientific_valid':sum(r['valid'] for r in lineage),
        'capped_scientific_valid':v.source_binding['capped_operational_audit']['scientific_valid'],
        'supplement_new_valid_scientific':v.operational_context['total_supplement_valid_scientific'],
        'fixed512_new_valid_scientific':v.operational_context['source512_new_valid_scientific'],
        'ceiling2048_new_valid_scientific':v.operational_context['overlay_valid_scientific'],
        'source_parsed_recovered_scientific':v.operational_context['source_parsed_recovered_scientific'],
        'fixed_new_max_tokens':2048,'response_token_ceiling_history':[128,512,2048],
        'main_models':list(MAIN_MODELS),'deferred_models':list(DEFERRED_MODELS),
        'eligible_missing':v.final['eligible_missing'],'deferred_missing':v.final['deferred_missing'],
        'main_scientific_planned':sum(r['model_key'] in MAIN_MODELS for r in lineage),
        'main_scientific_valid':sum(r['model_key'] in MAIN_MODELS and r['valid'] for r in lineage),
        'scientific_missing':sum(not r['valid'] for r in lineage),'physical_started':len(v.started),
        'physical_settled':len(v.settled),'unsettled_reservations':len(v.started)-len(v.settled),
        'failures_preserved':len(v.failures),'known_wrong_responses_retained':sum(r['correct'] is False for r in lineage),
        'input_path_base':'repository','input_sha256':v.input_sha256,'frozen_sources':scientific['sources'],'supplement_sources':manifest['supplement_sources'],
        'exporter_sha256':runtime.sha(Path(__file__)),'ledger':normalized_ledger,'supplement_final_ledger':v.final,'by_model':bymodel,
        'operational_pauses':v.operational_context['shared_pauses_used'],
        'completed_operational_pauses':v.operational_context['completed_operational_pauses'],
        'source_binding':v.source_binding,'operational_context':v.operational_context,
        'checks':['immutable operator-stopped128/512 sources and separately frozen2048 DeepSeek-only amendment',
                  'same48192 logical IDs and frozen formulas for all four archived cohorts',
                  'independent active-model round/order/global-attempt and first-accepted replay',
                  'unchanged identity/provider/none reasoning with actual2048 payload bounds',
                  'all unknown-start reserves retained and flat cumulative accounting without duplicate inherited costs',
                  'Sonnet deferral changes main-text presentation only; all48 planned contrasts remain archived'],
        'inference_limit':'Estimates concern the disclosed128/512/2048 acquisition history. Sonnet remains user-deferred and absent from main claims; its planned denominators and incomplete results remain archived. Eligible completion does not imply complete coverage of every original cohort, temporal stability, block independence or absence of availability selection.'}
    data={'manifest_sha256':manifest['manifest_sha256'],'scientific_manifest_sha256':scientific['manifest_sha256'],
          'execution_layer':LAYER,'response_policy':POLICY,'response_token_ceiling_history':[128,512,2048],
          'main_models':list(MAIN_MODELS),'deferred_models':list(DEFERRED_MODELS),'cohorts':cohorts}
    contents={'analysis.json':frozen_export._bytes_json(data),'logical_outcomes.csv':frozen_export._csv_bytes(lineage),
        'cell_summaries.csv':frozen_export._csv_bytes(cellrows),'free_cells.csv':frozen_export._csv_bytes(freerows),
        'contrasts.csv':frozen_export._csv_bytes(contrasts),'prediction.csv':frozen_export._csv_bytes(predictions),
        'failed_attempts.csv':frozen_export._csv_bytes(v.failures),'operational_audit.json':frozen_export._bytes_json(audit)}
    artifact={'status':'passed','manifest_sha256':manifest['manifest_sha256'],
        'scientific_manifest_sha256':scientific['manifest_sha256'],'execution_layer':LAYER,
        'files_sha256':{n:runtime.digest(b) for n,b in contents.items()},'scientific_planned':len(jobs),
        'scientific_valid':audit['scientific_valid'],'scientific_missing':audit['scientific_missing'],
        'capped_scientific_valid':audit['capped_scientific_valid'],'supplement_new_valid_scientific':audit['supplement_new_valid_scientific'],
        'fixed512_new_valid_scientific':audit['fixed512_new_valid_scientific'],
        'ceiling2048_new_valid_scientific':audit['ceiling2048_new_valid_scientific'],
        'eligible_missing':audit['eligible_missing'],'deferred_missing':audit['deferred_missing'],
        'main_models':list(MAIN_MODELS),'deferred_models':list(DEFERRED_MODELS)}
    contents['export_manifest.json']=frozen_export._bytes_json(artifact)
    return contents,audit,artifact


def independently_replay(source,manifest,events):
    """Independent chronological fold of active-model2048 attempts onto flat128/512 records."""
    import ceiling2048_response as response
    jobs=source.jobs;profiles={p['key']:p for p in source.scientific_manifest['profiles']};byid={j['id']:j for j in jobs}
    policy=manifest['policy'];active=set(policy['active_models']);cap=runtime.D(policy['cumulative_cap_usd'])
    require(active and active<=set(profiles) and policy['future_max_tokens']==2048,'active_policy')
    require(manifest['baseline']['accepted_selection']==source.accepted
            and manifest['baseline']['tries']==source.tries,'source_baseline_projection')
    tries=Counter(source.tries);accepted={i:dict(row) for i,row in source.accepted.items()}
    locked={i:dict(row) for i,row in accepted.items()}
    started={r['attempt_id']:r for r in source.started};settled={r['attempt_id']:r for r in source.settled}
    require(len(started)==len(source.started) and len(settled)==len(source.settled)
            and set(settled)<=set(started),'baseline_attempt_inventory')
    occupied=runtime.D(source.final['cumulative_occupied_usd'])
    require(occupied==runtime.D(manifest['baseline']['occupied_usd']),'source_occupied_projection')
    extra_starts=[];extra_settled=[];inflight=[];round_ids=None;cursor=0;round_number=0;fatal=False
    for sequence,event in enumerate(events,1):
        require(type(event.get('sequence')) is int and event['sequence']==sequence,'event_sequence')
        kind=event['event']
        if kind=='round_started':
            require(not fatal and round_ids is None and not inflight,'round_state')
            wanted=[j['id'] for j in jobs if j['id'] not in accepted and j['model_key'] in active]
            require(event['ids']==wanted and wanted and event['round']==round_number+1,'active_round_membership')
            round_number+=1;round_ids=wanted;cursor=0
        elif kind=='round_completed':
            require(round_ids is not None and event['round']==round_number and cursor==len(round_ids) and not inflight,'round_completion')
            round_ids=None;cursor=0
        elif kind=='attempt_started':
            row=event['row'];ident=row['id'];aid=row['attempt_id']
            require(not fatal and round_ids is not None and cursor<len(round_ids) and ident==round_ids[cursor],'start_order')
            require(ident in byid and ident not in accepted and aid not in started
                    and byid[ident]['model_key'] in active,'start_membership')
            require(type(row['attempt']) is int and row['attempt']==tries[ident]+1
                    and aid==ident+'|try'+str(row['attempt']),'global_attempt')
            job=byid[ident];profile=profiles[job['model_key']];body=response.payload(profile,job);bound=response.reserve(profile,body)
            require(row['model_key']==job['model_key'] and row['source_request_sha256']==job['request_sha256']
                    and row['request_sha256']==runtime.digest(runtime.compact(body).encode()),'request_identity')
            require(runtime.D(row['reserve_usd'])==bound and bound.is_finite() and bound>=0,'start_reserve')
            require(occupied+bound<=cap and len(inflight)<policy['concurrency'],'start_capacity')
            require(all(started[i]['id']!=ident for i in inflight),'duplicate_inflight')
            tries[ident]+=1;occupied+=bound;started[aid]=row;extra_starts.append(row);inflight.append(aid);cursor+=1
        elif kind=='attempt_settled':
            row=event['row'];aid=row['attempt_id'];ident=row['id']
            require(aid in started and aid not in settled and inflight and inflight[0]==aid,'settlement_order')
            start=started[aid]
            require(all(row.get(k)==start.get(k) for k in ('id','model_key','attempt','attempt_id','request_sha256','source_request_sha256','reserve_usd','utc')),'settlement_identity')
            require(all(type(row.get(k)) is bool for k in ('valid','fatal','cost_is_reserve','accepted')),'settlement_flags')
            charge=runtime.D(row['charged_or_reserved_usd']);bound=runtime.D(start['reserve_usd'])
            require(charge.is_finite() and charge>=0 and (not row['cost_is_reserve'] or charge==bound),'settlement_cost')
            if row['accepted']:
                require(ident not in accepted and tries[ident]==row['attempt'],'first_accepted_replacement')
                accepted[ident]=_selection(row)
            fatal=fatal or row['fatal'];settled[aid]=row;extra_settled.append(row);inflight.pop(0);occupied+=charge-bound
        else:
            require(kind in ('preflight','operational_pause','operational_pause_completed'),'unknown_event')
    flat=runtime.PRIOR+sum((runtime.D(settled[aid]['charged_or_reserved_usd']) if aid in settled
                            else runtime.D(row['reserve_usd']) for aid,row in started.items()),runtime.D(0))
    extra=runtime.D(source.final['cumulative_occupied_usd'])+sum((runtime.D(settled[r['attempt_id']]['charged_or_reserved_usd'])
         if r['attempt_id'] in settled else runtime.D(r['reserve_usd']) for r in extra_starts),runtime.D(0))
    require(occupied==flat==extra,'independent_cumulative_accounting')
    require(all(accepted.get(i)==row for i,row in locked.items()),'historical_selection_changed')
    return source.started+extra_starts,source.settled+extra_settled,accepted,dict(tries),occupied


def verify_locked(run):
    """Caller owns new supplement.lock then execution.lock; nested source locks preserve lineage."""
    import ceiling2048_contract as contract
    run=Path(run).resolve();status=runtime.read(run/'status.json')
    require(status.get('state') in contract.TERMINAL,'not_terminal')
    manifest=contract.validate_manifest(run)
    require(manifest['version']==3 and manifest['supplement_sources'].get(Path(__file__).name)==runtime.sha(__file__),'exporter_binding')
    require(tuple(manifest['policy']['main_models'])==MAIN_MODELS
            and tuple(manifest['policy']['deferred_models'])==DEFERRED_MODELS,'presentation_scope')
    source_run=contract.contained_file(manifest['source_run_relative'])
    with contract.source_locks(source_run):
        source=contract.load_bound_source(manifest)
        scientific=source.scientific_manifest;jobs=source.jobs
        closure_path=contract.contained_file(manifest['source_closure_relative']);closure=runtime.read(closure_path)
        require(closure['closure_sha256']==manifest['source_closure_sha256'],'source_closure_binding')
        events=runtime.lines(run/contract.JOURNAL)
        ledger=contract.make_ledger(manifest,jobs,scientific['profiles'],events)
        contract.verify_status(manifest,ledger,status,terminal=True)
        final=runtime.read(run/'final_ledger.json')
        eventsha=runtime.sha(run/contract.JOURNAL) if (run/contract.JOURNAL).exists() else None
        require(final==contract.final_ledger_record(manifest,ledger,eventsha),'final_ledger_projection')
        starts,settled,accepted,tries,occupied=independently_replay(source,manifest,events)
        require(occupied==ledger.occupied and tries==dict(ledger.tries) and set(accepted)==ledger.accepted,'independent_ledger_disagreement')
        require(all(accepted.get(i)==_selection(r) for i,r in ledger.newly_accepted_rows.items()),'new_selection_disagreement')
        failures=list(source.failures)
        for row in ledger.settled:
            if not row['valid']:
                failures.append({k:row.get(k) for k in ('attempt_id','id','model_key','attempt','reason','fatal','http_status','elapsed_seconds','charged_or_reserved_usd','cost_is_reserve','utc','settled_utc')})
        paths=dict(manifest['source_files_sha256'])
        for name in ('manifest.json','status.json',contract.JOURNAL,'final_ledger.json'):
            path=run/name
            if path.exists():paths[path.relative_to(contract.REPO).as_posix()]=runtime.sha(path)
        for name,digest in manifest['supplement_sources'].items():
            paths[(contract.HERE/name).relative_to(contract.REPO).as_posix()]=digest
        for name,digest in closure.get('verification_sources',{}).items():
            require(Path(name).name==name and runtime.sha(contract.HERE/name)==digest,'source_verification_source_changed')
            relative=(contract.HERE/name).relative_to(contract.REPO).as_posix()
            require(relative not in paths or paths[relative]==digest,'input_hash_conflict');paths[relative]=digest
        binding={**source.source_binding,
                 'source512_run_relative':manifest['source_run_relative'],
                 'source512_closure_relative':manifest['source_closure_relative'],
                 'source512_operator_closure':closure,'source512_manifest_sha256':source.manifest['manifest_sha256'],
                 'source512_original_status':source.status,'source512_derived_final_ledger':source.final,
                 'source512_accepted_count':len(source.accepted),
                 'source512_physical_started':len(source.started),'source512_physical_settled':len(source.settled),
                 'source512_final_ledger_written':False}
        old_new=source.operational_context['overlay_valid_scientific'];new=len(ledger.newly_accepted_rows)
        strict=source.operational_context['source_strict_scientific'];parsed=source.operational_context['source_parsed_recovered_scientific']
        require(strict+parsed+old_new==len(source.accepted) and len(source.accepted)+new==len(accepted),'accepted_layer_totals')
        context={'shared_pauses_used':ledger.pauses,'source_pauses_used':manifest['baseline']['pauses'],
                 'supplement_pause_count':sum(e['event']=='operational_pause' for e in events),
                 'supplement_completed_pause_count':sum(e['event']=='operational_pause_completed' for e in events),
                 'completed_operational_pauses':ledger.pauses-int(ledger.pending_pause is not None),
                 'rounds_started':ledger.round,'overlay_started':len(ledger.starts),'overlay_settled':len(ledger.settled),
                 'overlay_valid_scientific':new,'source512_new_valid_scientific':old_new,
                 'total_supplement_valid_scientific':old_new+new,'no_progress':ledger.no_progress,
                 'source_strict_scientific':strict,'source_parsed_recovered_scientific':parsed,
                 'source_unsettled_reservations':len(source.started)-len(source.settled),
                 'fixed_new_max_tokens':2048,'active_models':list(manifest['policy']['active_models']),
                 'main_models':list(MAIN_MODELS),'deferred_models':list(DEFERRED_MODELS),
                 'eligible_missing':len(ledger.eligible_missing_ids),
                 'deferred_missing':len(ledger.missing_ids)-len(ledger.eligible_missing_ids),
                 'source_scope':'Flat preserved128/512 inventory plus separately authorized DeepSeek-only2048 calls; Sonnet remains deferred and all original planned IDs remain archived.'}
        require(runtime.read(run/'status.json')==status,'terminal_status_changed')
        require(all(runtime.sha(contract.contained_file(n))==h for n,h in paths.items()),'verified_inputs_changed')
        return CompletionVerification(manifest,scientific,jobs,starts,settled,accepted,tries,final,status,
                                      failures,ledger.fingerprints,paths,binding,context)


def verify_terminal(run):
    import ceiling2048_contract as contract
    run=Path(run).resolve()
    require(runtime.read(run/'status.json').get('state') in contract.TERMINAL,'not_terminal')
    with runtime.execution_lock(run/contract.LOCK):
        with runtime.execution_lock(run/'execution.lock'):
            return verify_locked(run)


def export_run(run,output=None):
    import ceiling2048_contract as contract
    run=Path(run).resolve();output=Path(output).resolve() if output else run/'terminal_export'
    require(runtime.read(run/'status.json').get('state') in contract.TERMINAL,'not_terminal')
    with runtime.execution_lock(run/contract.LOCK):
        with runtime.execution_lock(run/'execution.lock'):
            v=verify_locked(run)
            preserved=[contract.contained_file(v.manifest['source_run_relative']),
                       contract.contained_file(v.source_binding['source_run_relative']),
                       contract.contained_file(v.source_binding['original_source_directory'])]
            require(all(output!=base and not output.is_relative_to(base) for base in preserved),'preserved_source_output')
            contents,audit,artifact=render_payloads(v)
            require(all(runtime.sha(contract.contained_file(n))==h for n,h in v.input_sha256.items()),'input_changed_before_export')
            output.mkdir(parents=True,exist_ok=True)
            for name,payload in contents.items():frozen_export._write_once_or_identical(output/name,payload)
            require(all(runtime.sha(contract.contained_file(n))==h for n,h in v.input_sha256.items()),'input_changed_during_export')
            return artifact


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run',type=Path,required=True);parser.add_argument('--output',type=Path)
    args=parser.parse_args();print(runtime.compact(export_run(args.run,args.output)))
