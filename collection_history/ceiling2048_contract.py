"""Frozen 2048-token, DeepSeek-only completion contract; no paid imports."""
from contextlib import contextmanager
from pathlib import Path
import runtime
import ceiling2048_source as source_module
from ceiling2048_ledger import ProjectedLedger, require

HERE=Path(__file__).resolve().parent
REPO=HERE.parent.parent
JOURNAL='supplemental_events.jsonl'
LOCK='supplement.lock'
KIND='USER_AUTHORIZED_DEEPSEEK_2048_COMPLETION'
TERMINAL=set(runtime.TERMINAL)|{'eligible_complete'}
CORE_SOURCES=('ceiling2048_validation.py','ceiling2048_ledger.py','ceiling2048_contract.py',
              'ceiling2048_response.py','ceiling2048_source.py','export_ceiling2048.py')
SUPPLEMENT_SOURCES=CORE_SOURCES+('CEILING2048_AMENDMENT.txt','ceiling2048_audit.py','ceiling2048_audit.json','ceiling2048_source_audit.py','ceiling2048_source_audit.json','export_ceiling2048_audit.py','export_ceiling2048_audit.json',
                              'answer_extraction.py','ANSWER_EXTRACTION_POLICY.txt',
                              'answer_extraction_audit.py','answer_extraction_audit.json')
POLICY={'original_order_rounds':True,'one_attempt_per_remaining_id_per_round':True,
        'max_attempts_per_id':None,'first_extractable_including_wrong':True,
        'historical_answers_locked':True,'historical_max_tokens':[128,512],
        'future_max_tokens':2048,'extract_finish_reason':'stop','active_models':['deepseek'],
        'main_models':['luna','qwen','deepseek'],'deferred_models':['claude'],
        'deferral_reason':'User requested no further Sonnet spending before behavioral outcomes were inspected.',
        'no_progress_settlements_before_pause':50,'shared_maximum_pauses':12,
        'concurrency':16,'cumulative_cap_usd':'50','metadata_save_delays_seconds':[.25,1.0],
        'unchanged_prompts_models_reasoning_routes':True,'no_new_scientific_ids':True}
INFERENCE_LABEL=('User-authorized acquisition amendment: retain all existing128/512-token answers, including wrong answers; '
                 'make fixed2048-token missing-only calls for DeepSeek with unchanged prompts, model, provider and disabled-thinking contract. '
                 'Luna and Qwen are already complete. Sonnet is deferred for cost before inspecting behavioral effects. '
                 'All four original cohorts and failures remain archived; main-text claims concern Luna, Qwen and DeepSeek. '
                 'This is amended acquisition on the original allocation, not an independent replication.')

def contained_file(relative,repo=REPO):
    require(isinstance(relative,str) and not Path(relative).is_absolute(),'absolute_bound_path')
    path=(repo/relative).resolve()
    require(path.is_relative_to(repo.resolve()) and path!=repo.resolve(),'bound_path_escape')
    return path

def hash_checked(path,digest):
    require(path.is_file() and runtime.sha(path)==digest,'bound_file_changed:'+path.name)

@contextmanager
def source_locks(source):
    source=Path(source)
    with runtime.execution_lock(source/'supplement.lock'),runtime.execution_lock(source/'execution.lock'):
        yield

def source_binding(closure_path,closure):
    result=dict(closure['source_files_sha256'])
    for name,digest in closure['verification_sources'].items():result[(HERE/name).relative_to(REPO).as_posix()]=digest
    result[closure_path.relative_to(REPO).as_posix()]=runtime.sha(closure_path)
    return result

def validate_manifest(run):
    run=Path(run).resolve();m=runtime.read(run/'manifest.json')
    body=dict(m);claim=body.pop('manifest_sha256')
    require(runtime.digest(runtime.compact(body).encode())==claim,'manifest_changed')
    require(m['version']==3 and m['kind']==KIND and m['policy']==POLICY,'manifest_policy')
    require(m['inference_label']==INFERENCE_LABEL,'inference_label_changed')
    require(set(m['supplement_sources'])==set(SUPPLEMENT_SOURCES),'supplement_source_inventory')
    require(contained_file(m['run_relative'])==run,'run_directory_binding')
    source=contained_file(m['source_run_relative'])
    require(source!=run and not source.is_relative_to(run) and not run.is_relative_to(source),'source_destination_overlap')
    for name,digest in m['supplement_sources'].items():
        require(Path(name).name==name,'source_path');hash_checked(HERE/name,digest)
    for relative,digest in m['source_files_sha256'].items():hash_checked(contained_file(relative),digest)
    closure_path=contained_file(m['source_closure_relative']);closure=runtime.read(closure_path)
    require(closure['closure_sha256']==m['source_closure_sha256'] and closure['source_run_relative']==m['source_run_relative'],'closure_binding')
    require(source_binding(closure_path,closure)==m['source_files_sha256'],'source_binding_inventory')
    require(m['scientific_count']==len(m['planned_ids'])==len(set(m['planned_ids']))==48192,'scientific_allocation')
    require(set(m['baseline']['tries'])==set(m['planned_ids']),'baseline_allocation')
    return m

def load_bound_source(m):
    for relative,digest in m['source_files_sha256'].items():hash_checked(contained_file(relative),digest)
    closure,verified,baseline=source_module.verify_closed_source_locked(contained_file(m['source_closure_relative']))
    require(closure['closure_sha256']==m['source_closure_sha256'],'closure_changed')
    require(verified.scientific_manifest['manifest_sha256']==m['scientific_manifest_sha256'],'scientific_manifest_changed')
    require([j['id'] for j in verified.jobs]==m['planned_ids'],'planned_ids_changed')
    require(baseline==m['baseline'],'baseline_projection_changed')
    return verified

def make_ledger(m,jobs,profiles,events=()):
    return ProjectedLedger(m['baseline'],jobs,profiles,events,
                           cap_usd=m['policy']['cumulative_cap_usd'],active_models=m['policy']['active_models'])

def final_ledger_record(m,ledger,journal_sha):
    return {'status':'independently_reconciled','manifest_sha256':m['manifest_sha256'],
            'scientific_manifest_sha256':m['scientific_manifest_sha256'],
            'events_sha256':journal_sha,**ledger.summary()}

def verify_status(m,ledger,status,terminal=True):
    require(status.get('manifest_sha256')==m['manifest_sha256'] and status.get('scientific_manifest_sha256')==m['scientific_manifest_sha256'],'status_manifest')
    if terminal:require(status.get('state') in TERMINAL,'completion_not_terminal')
    for key,value in ledger.summary().items():require(status.get(key)==value,'status_projection:'+key)
    state=status.get('state')
    if state=='eligible_complete':require(not ledger.eligible_missing_ids and not ledger.inflight and not ledger.fatal_reason,'false_eligible_completion')
    elif state=='complete':require(not ledger.missing_ids and not ledger.inflight and not ledger.fatal_reason,'false_full_completion')
    elif state=='halted_service':require(ledger.pauses==12 and ledger.needs_pause and not ledger.inflight,'false_service_halt')
    elif state=='halted_budget':require(bool(ledger.eligible_missing_ids) and not ledger.inflight,'false_budget_halt')