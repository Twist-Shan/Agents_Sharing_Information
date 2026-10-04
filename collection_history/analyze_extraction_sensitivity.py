"""Offline, preselected earliest-extractable sensitivity; never changes main data."""
from pathlib import Path
from collections import Counter
from contextlib import ExitStack
import argparse
import runtime
import export_validation
import export_completion
import answer_extraction
import analysis
import terminal_reader

HERE=Path(__file__).resolve().parent
REPO=HERE.parent.parent
POLICY=('Descriptive sensitivity selected before scientific-effect inspection: take the earliest '
        'eligible unambiguous stop-finished answer among all recorded attempts for each original ID, '
        'including an earlier parseable answer preceding a locked strict-valid answer. '
        'Main selections and all raw records remain unchanged. No added requests or sample selection.')


def select_earliest(jobs,settled):
    """Only IDs, mappings, checked eligibility and text enter selection; no expected key."""
    maps={j['id']:j['answer_map'] for j in jobs}
    earliest={}
    for row in sorted(settled,key=lambda r:(r['id'],r['attempt'])):
        ident=row['id']
        if ident not in maps or ident in earliest or row.get('fatal') or row.get('worker_error'):
            continue
        if row['valid']:
            action=row['action'];rule='strict'
        elif row['reason']=='invalid_schema':
            choice=row['response']['choices'][0]
            extraction=answer_extraction.extract_content(choice['message'].get('content'),maps[ident],choice['finish_reason'])
            if not extraction['accepted']:continue
            action=extraction['action'];rule=extraction['rule']
        else:continue
        earliest[ident]={'action':action,'attempt_id':row['attempt_id'],'attempt':row['attempt'],'rule':rule}
    return earliest


def render(verified):
    """Input has already passed the final raw-contract and accounting verifier."""
    chosen=select_earliest(verified.jobs,verified.settled)
    export_completion.require(set(chosen)==set(verified.accepted),'sensitivity_coverage_changed')
    lineages=[];cohorts={};counts={}
    for p in verified.scientific_manifest['profiles']:
        key=p['key'];jobs=[j for j in verified.jobs if j['model_key']==key]
        normalized=[export_validation._normalize_job(j) for j in jobs]
        actions={export_validation._normalize_job(j)['id']:{'valid':True,'action':chosen[j['id']]['action']}
                 for j in jobs if j['id'] in chosen}
        a=analysis.analyze(normalized,actions,{'model_key':key,'allocationprofile':'full' if key=='luna' else 'cross'})
        inherited=a['inference_assumptions'][0]
        a['inference_assumptions']=[POLICY,*a['inference_assumptions'][1:]]
        a['inherited_capped_policy_statement']=inherited
        a['execution_layer']='uniform_earliest_extractable_sensitivity'
        cohorts[key]={'analysis':a}
        c=Counter(planned=len(jobs),valid=sum(j['id'] in chosen for j in jobs),selected_attempt_changes=0,action_disagreements=0)
        for j in jobs:
            main=verified.accepted.get(j['id']);other=chosen.get(j['id'])
            changed=main is not None and main['attempt_id']!=other['attempt_id']
            disagreement=main is not None and main['action']!=other['action']
            c['selected_attempt_changes']+=int(changed);c['action_disagreements']+=int(disagreement)
            lineages.append({'model_key':key,'runtime_id':j['id'],'valid':main is not None,
                'main_attempt_id':main['attempt_id'] if main else None,'main_action':main['action'] if main else None,
                'sensitivity_attempt_id':other['attempt_id'] if other else None,'sensitivity_action':other['action'] if other else None,
                'sensitivity_rule':other['rule'] if other else None,'selected_attempt_changed':changed,'action_disagreement':disagreement})
        counts[key]=dict(c)
    result={'status':'passed','execution_layer':'uniform_earliest_extractable_sensitivity',
            'response_policy':POLICY,'manifest_sha256':verified.manifest['manifest_sha256'],
            'scientific_manifest_sha256':verified.scientific_manifest['manifest_sha256'],
            'preselected_plan':verified.source_binding['operator_closure'].get('selection_sensitivity_plan'),
            'main_selections_modified':False,'model_calls':0,'equal_observed_id_coverage':True,
            'counts':counts,'cohorts':cohorts,
            'response_token_ceiling_history':terminal_reader.token_history(verified),
            'main_models':verified.manifest.get('policy',{}).get('main_models',list(cohorts)),
            'deferred_models':verified.manifest.get('policy',{}).get('deferred_models',[]),
            'limitation':'This sensitivity concerns recorded-answer selection; it does not identify unobserved answers, repair time-varying service effects or remove the disclosed mixed acquisition history.'}
    contents={'sensitivity_analysis.json':export_validation._bytes_json(result),
              'sensitivity_selections.csv':export_validation._csv_bytes(lineages)}
    manifest={'status':'passed','manifest_sha256':verified.manifest['manifest_sha256'],
              'files_sha256':{n:runtime.digest(b) for n,b in contents.items()},
              'script_sha256':runtime.sha(Path(__file__)),'analysis_sha256':runtime.sha(HERE/'analysis.py'),
              'parser_sha256':runtime.sha(HERE/'answer_extraction.py'),'model_calls':0,
              'input_sha256':verified.input_sha256,
              'source_sha256':{**{n:runtime.sha(HERE/n) for n in ('analyze_extraction_sensitivity.py','analysis.py','answer_extraction.py')},
                               **terminal_reader.source_hashes(verified)}}
    contents['sensitivity_manifest.json']=export_validation._bytes_json(manifest)
    return contents,counts


def report_run(run,output=None):
    run=Path(run).resolve();output=Path(output).resolve() if output else run/'extraction_sensitivity'
    with terminal_reader.verified_run(run) as (verified,contract,exporter):
        terminal_reader.guard_output(verified,contract,run,output)
        closure=verified.source_binding['operator_closure']
        export_completion.require(bool(closure.get('selection_sensitivity_plan')),'missing_preselected_sensitivity_plan')
        contents,counts=render(verified)
        output.mkdir(parents=True,exist_ok=True)
        for name,blob in contents.items():export_validation._write_once_or_identical(output/name,blob)
    return {'status':'passed','model_calls':0,'counts':counts,'output':str(output)}

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--run',type=Path,required=True);parser.add_argument('--output',type=Path)
    args=parser.parse_args();print(runtime.compact(report_run(args.run,args.output)))
