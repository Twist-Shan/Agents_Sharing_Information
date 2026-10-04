"""Separate answer extraction and strict/parsed exports for a verified stopped source.
Raw strict source verification is independently frozen in answer_recovery_source.py.
No paid execution adapter is imported.
"""
from answer_recovery_source import *

def project_answers(data):
    """Strict valids are fixed before any failed-format attempt is considered."""
    import answer_extraction
    manifest,jobs,starts,settled,strict,*_=data
    profiles={p['key']:p for p in manifest['profiles']};byid={j['id']:j for j in jobs}
    selected={i:{'action':row['action'],'attempt_id':row['attempt_id'],'attempt':row['attempt'],
                 'selection_layer':'strict','strict_reason':row['reason'],'rule':'original_strict_valid',
                 'content_sha256':None} for i,row in strict.items() if i in byid}
    candidates=[]
    for row in sorted(settled,key=lambda r:(r['id'],r['attempt'])):
        if row['id'] not in byid or row['id'] in strict:continue
        decision={'accepted':False,'reason':'ineligible_strict_failure','rule':None,'content_sha256':None,'action':None}
        if row['reason']=='invalid_schema' and row['fatal'] is False and not row.get('worker_error'):
            job=byid[row['id']];profile=profiles[job['model_key']]
            require(runtime.classify(row,profile,job,runtime.D(row['reserve_usd']))==(False,None,'invalid_schema',False),'candidate_safety_reclassification')
            choice=row['response']['choices'][0];message=choice['message']
            if choice['finish_reason']=='stop':
                decision=answer_extraction.extract_content(message.get('content'),job['answer_map'],finish_reason='stop')
        record={'id':row['id'],'model_key':row['model_key'],'attempt_id':row['attempt_id'],'attempt':row['attempt'],
                'strict_reason':row['reason'],'selected':False,**decision}
        if decision['accepted'] and row['id'] not in selected:
            selected[row['id']]={'action':decision['action'],'attempt_id':row['attempt_id'],'attempt':row['attempt'],
                'selection_layer':'parsed_recovery','strict_reason':row['reason'],'rule':decision['rule'],
                'content_sha256':decision['content_sha256']}
            record['selected']=True
        candidates.append(record)
    return selected,candidates

def render_layer(closure,data,selected,layer,parser_hashes=None,candidates=None):
    import analysis
    manifest,jobs,starts,settled,strict,ledger,final,status,failures,fingerprints,events=data
    policy=('Original strict first-valid response policy stopped by the user before planned completion; all planned IDs and unknown reserves remain.'
            if layer==STRICT_LAYER else
            'User-authorized answer-extraction amendment: retain all existing strict valids, including wrong answers; for strict-missing IDs only, select the earliest recorded unambiguous stop-finished safe response. No original raw flags are rewritten. This is a different response policy, not an independent replication.')
    cohorts={};lineage=[];cells=[];free=[];contrasts=[];predictions=[]
    for profile in manifest['profiles']:
        key=profile['key'];subset=[j for j in jobs if j['model_key']==key];allocation='full' if key=='luna' else 'cross'
        outcomes={frozen._normalize_job(j)['id']:{'valid':True,'action':selected[j['id']]['action']} for j in subset if j['id'] in selected}
        result=analysis.analyze([frozen._normalize_job(j) for j in subset],outcomes,{'model_key':key,'allocationprofile':allocation})
        inherited=result['inference_assumptions'][0];result['inference_assumptions']=[policy,*result['inference_assumptions'][1:]]
        result['inherited_capped_policy_statement']=inherited;result['execution_layer']=layer
        cohorts[key]={'profile':profile,'allocationprofile':allocation,'analysis':result}
        for j in subset:
            m=j['metadata'];s=selected.get(j['id'])
            lineage.append({'model_key':key,'logical_id':frozen._normalize_job(j)['id'],'runtime_id':j['id'],
                'block_id':j['block_id'],'module':j['module'],**{k:m[k] for k in ('wording','analysis_split','policy','law','encoding','safe','actor','p','mapping','display_order')},
                'expected':j['expected'],'valid':s is not None,'action':s['action'] if s else None,
                'correct':s['action']==j['expected'] if s and j['expected'] is not None else None,
                'physical_attempts':ledger.tries[j['id']],'selected_attempt_id':s['attempt_id'] if s else None,
                'selected_attempt':s['attempt'] if s else None,'request_sha256':j['request_sha256'],
                'selected_source_layer':s['selection_layer'] if s else 'unresolved',
                'original_strict_reason':s['strict_reason'] if s else None,'extraction_rule':s['rule'] if s else None,
                'content_sha256':s['content_sha256'] if s else None})
        cells.extend({'model_key':key,**r} for r in result['summaries']);free.extend({'model_key':key,**r} for r in result['free_cells'])
        for family in ('primary_family_7','value_family_2','capability_family_3'):
            contrasts.extend({'model_key':key,'family':family,'contrast':name,**r} for name,r in result[family].items())
        predictions.extend({'model_key':key,'predictor':name,**r} for name,r in result['prediction'].get('models',{}).items())
    science_ids={j['id'] for j in jobs};nstrict=sum(i in science_ids for i in strict)
    audit={'status':'passed_operator_closed_export','execution_layer':layer,'response_policy':policy,
        'manifest_sha256':closure['closure_sha256'],'scientific_manifest_sha256':manifest['manifest_sha256'],
        'operator_closure_sha256':closure['closure_sha256'],'source_execution_state':status['state'],
        'source_execution_reason':status['reason'],'scientific_planned':len(jobs),'scientific_valid':len(selected),
        'scientific_missing':len(jobs)-len(selected),'strict_scientific_valid':nstrict,
        'parsed_recovered_scientific':len(selected)-nstrict,'physical_started':len(starts),'physical_settled':len(settled),
        'unsettled_reservations':len(starts)-len(settled),'ledger':final,'raw_failures_preserved':len(failures),
        'source_files_sha256':closure['source_files_sha256'],'exporter_sha256':runtime.sha(Path(__file__)),
        'parser_sources_sha256':parser_hashes or {},'operational_pauses':sum(e['event']=='operational_pause' for e in events),
        'model_calls':0,'source_modified':False,'statistical_formulas_unchanged':True}
    obj={'manifest_sha256':closure['closure_sha256'],'scientific_manifest_sha256':manifest['manifest_sha256'],
         'execution_layer':layer,'response_policy':policy,'cohorts':cohorts}
    contents={'analysis.json':frozen._bytes_json(obj),'logical_outcomes.csv':frozen._csv_bytes(lineage),
        'cell_summaries.csv':frozen._csv_bytes(cells),'free_cells.csv':frozen._csv_bytes(free),
        'contrasts.csv':frozen._csv_bytes(contrasts),'prediction.csv':frozen._csv_bytes(predictions),
        'failed_attempts.csv':frozen._csv_bytes(failures),'operational_audit.json':frozen._bytes_json(audit)}
    artifact={'status':'passed','manifest_sha256':closure['closure_sha256'],'scientific_manifest_sha256':manifest['manifest_sha256'],
              'execution_layer':layer,'scientific_planned':len(jobs),'scientific_valid':len(selected),'scientific_missing':len(jobs)-len(selected),
              'files_sha256':{n:runtime.digest(b) for n,b in contents.items()}}
    contents['export_manifest.json']=frozen._bytes_json(artifact)
    return contents,artifact

def export_closed(closure_path,output=None):
    closure_path=Path(closure_path).resolve();output=Path(output).resolve() if output else closure_path.parent
    source=member(runtime.read(closure_path)['source_run_relative'])
    require(output!=source and not output.is_relative_to(source),'cannot_write_source')
    with source_locks(source):
        closure,data=verify_closed_source_locked(closure_path)
        science_ids={j['id'] for j in data[1]}
        strict={i:{'action':r['action'],'attempt_id':r['attempt_id'],'attempt':r['attempt'],'selection_layer':'strict',
                   'strict_reason':r['reason'],'rule':'original_strict_valid','content_sha256':None}
                for i,r in data[4].items() if i in science_ids}
        parser_audit=runtime.read(HERE/'answer_extraction_audit.json')
        require(parser_audit.get('passed') is True and parser_audit.get('model_calls')==0
                and parser_audit.get('live_journals_read') is False,'parser_audit_not_passed')
        for name in ('answer_extraction.py','ANSWER_EXTRACTION_POLICY.txt','answer_extraction_audit.py','answer_recovery.py'):
            require(parser_audit.get('source_sha256',{}).get(name)==runtime.sha(HERE/name),'parser_audit_stale:'+name)
        parser_hashes={n:runtime.sha(HERE/n) for n in ('answer_extraction.py','ANSWER_EXTRACTION_POLICY.txt','answer_extraction_audit.py','answer_extraction_audit.json')}
        parsed,candidates=project_answers(data);result={}
        for name,selected,layer in (('strict_export',strict,STRICT_LAYER),('parsed_export',parsed,PARSED_LAYER)):
            contents,artifact=render_layer(closure,data,selected,layer,parser_hashes if name=='parsed_export' else {})
            folder=output/name;folder.mkdir(parents=True,exist_ok=True)
            for n,payload in contents.items():frozen._write_once_or_identical(folder/n,payload)
            result[name]=artifact
        frozen._write_once_or_identical(output/'extraction_attempts.jsonl',(''.join(runtime.compact(x)+'\n' for x in candidates)).encode())
        frozen._write_once_or_identical(output/'answer_selections.json',frozen._bytes_json(parsed))
        result.update({'closure_sha256':closure['closure_sha256'],'parser_sources_sha256':parser_hashes,
                       'source_files_unchanged':True,'model_calls':0})
        require(all(runtime.sha(member(n))==h for n,h in closure['source_files_sha256'].items()),'source_changed_during_export')
        frozen._write_once_or_identical(output/'recovery_export_summary.json',frozen._bytes_json(result))
        return result

if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__);sub=ap.add_subparsers(dest='command',required=True)
    close=sub.add_parser('close');close.add_argument('--source',type=Path,required=True);close.add_argument('--output',type=Path,required=True)
    close.add_argument('--observed-exit',type=Path,required=True)
    export=sub.add_parser('export');export.add_argument('--closure',type=Path,required=True);export.add_argument('--output',type=Path)
    args=ap.parse_args()
    result=close_source(args.source,args.output,runtime.read(args.observed_exit)) if args.command=='close' else export_closed(args.closure,args.output)
    print(runtime.compact({'status':'passed','closure_sha256':result.get('closure_sha256'),'model_calls':0}))
