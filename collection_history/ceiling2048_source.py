"""Separate closure of an operator-stopped512 supplement; no paid adapter imports.

Old status/journals/final-ledger files are never written. The verified value is
the frozen exporter's CompletionVerification with an explicitly interrupted
status and a separately derived ledger, not a fabricated terminal export.
"""
from pathlib import Path
from contextlib import contextmanager
from copy import deepcopy
import argparse,json
import runtime
import supplement_contract as old_contract
from supplement_ledger import ProjectedLedger
import export_completion

HERE=Path(__file__).resolve().parent
REPO=HERE.parent.parent
KIND='OPERATOR_STOPPED_512_BEFORE_FIXED_2048'
OBSERVED_EXIT={'observed':True,'session_id':75027,'pid':35820,'exit_code':1,
               'evidence':'Parent directly observed the original PTY session exit after operator Ctrl-C; observer439 was terminated.'}

def require(ok,label):
 if not ok:raise ValueError('ceiling2048_source:'+label)
def relative(path):return Path(path).resolve().relative_to(REPO).as_posix()
def member(name):
 require(isinstance(name,str) and not Path(name).is_absolute(),'absolute_path')
 p=(REPO/name).resolve();require(p.is_relative_to(REPO) and p!=REPO,'path_escape');return p

@contextmanager
def source_locks(source):
 """The caller's512 source outer lock precedes its execution lock."""
 source=Path(source).resolve()
 require(source.parent==HERE and (source/'manifest.json').is_file(),'source_directory')
 require(runtime.read(source/'manifest.json').get('kind')==old_contract.KIND,'source_kind')
 with runtime.execution_lock(source/'supplement.lock'):
  with runtime.execution_lock(source/'execution.lock'):yield

def baseline_from_verified(verified,ledger):
 """Carry every physical cost once; observe only newly unresolved512 starts."""
 settled_ids={r['attempt_id'] for r in verified.settled}
 unknown=[r for r in verified.started if r['attempt_id'] not in settled_ids]
 newly_unknown=list(ledger.inflight)
 require({r['attempt_id'] for r in newly_unknown}<={r['attempt_id'] for r in unknown},'unknown_membership')
 tracker=deepcopy(ledger.tracker);no_progress=ledger.no_progress;trigger=deepcopy(ledger.progress_trigger)
 for row in newly_unknown:
  tracker.observe({**row,'reason':'interrupted_unknown','retry_after_seconds':0})
  no_progress+=1
  if no_progress>=50 and trigger is None:
   trigger={'attempt_id':row['attempt_id'],'consecutive_without_new_valid':no_progress,'source_unknown':True}
 selected=deepcopy(verified.accepted)
 strict=sum(r['selection_layer'] in ('strict','supplement_strict') for r in selected.values())
 require(all(r['selection_layer'] in ('strict','parsed_recovery','supplement_strict','supplement_parsed') for r in selected.values()),'selected_source_layer')
 return {'occupied_usd':str(ledger.occupied),'physical_started':len(verified.started),'physical_settled':len(verified.settled),
         'unknown_started_attempt_ids':[r['attempt_id'] for r in unknown],
         'newly_observed_unknown_attempt_ids':[r['attempt_id'] for r in newly_unknown],
         'tries':dict(verified.tries),'accepted_ids':[j['id'] for j in verified.jobs if j['id'] in selected],
         'accepted_selection':selected,'strict_accepted_count':strict,'parsed_accepted_count':len(selected)-strict,
         'fingerprints':deepcopy(verified.fingerprints),'pauses':ledger.pauses,
         'pending_pause':deepcopy(ledger.pending_pause),'no_progress':no_progress,'progress_trigger':trigger,
         'tracker':{'recent':list(tracker.recent),'consecutive':tracker.consecutive,
                    'trigger':deepcopy(tracker.trigger),'retry_after':tracker.retry_after}}

def verify_snapshot_locked(run):
 """Caller holds512 outer/execution locks. Nested128/IO locks retain old order."""
 run=Path(run).resolve();status=runtime.read(run/'status.json')
 require(status.get('state')=='interrupted' and status.get('reason')=='KeyboardInterrupt','not_operator_interrupted')
 require(status.get('pid')==OBSERVED_EXIT['pid'],'observed_exit_pid')
 require(not (run/'final_ledger.json').exists(),'unexpected_old_final_ledger')
 manifest=old_contract.validate_manifest(run)
 require(manifest['version']==2,'not_frozen512_policy')
 source=old_contract.contained_file(manifest['source_run_relative'])
 closure_path=old_contract.contained_file(manifest['source_closure_relative'])
 with old_contract.source_locks(source):
  raw=old_contract.load_bound_source(manifest)
  scientific,jobs,old_starts,old_settled,old_accepted,old_ledger,old_final,old_status,old_failures,old_fingerprints,old_events=raw
  events=runtime.lines(run/old_contract.JOURNAL)
  ledger=ProjectedLedger(manifest['baseline'],jobs,scientific['profiles'],events)
  old_contract.verify_status(manifest,ledger,status,terminal=False)
  require(ledger.fatal_reason is None and not any(r['fatal'] for r in ledger.settled),'fatal_history_cannot_continue')
  starts,settled,accepted,tries,occupied=export_completion.independently_replay(raw,manifest,events)
  require(occupied==ledger.occupied and tries==dict(ledger.tries),'independent_cost_or_tries')
  require(set(accepted)==ledger.accepted and all(accepted.get(i)==export_completion._overlay_selection(row)
          for i,row in ledger.newly_accepted_rows.items()),'independent_accepted_selection')
  require(all(accepted.get(i)==v for i,v in manifest['baseline']['accepted_selection'].items()),'historical_first_answers_changed')
  closure=runtime.read(closure_path);audits={}
  for layer in ('strict_export','parsed_export'):
   folder=closure_path.parent/layer;em=runtime.read(folder/'export_manifest.json')
   require(em['status']=='passed' and em['manifest_sha256']==closure['closure_sha256'],'prior_export_identity')
   for name,digest in em['files_sha256'].items():
    require(Path(name).name==name and runtime.sha(folder/name)==digest,'prior_export_hash')
   a=runtime.read(folder/'operational_audit.json')
   require(a['status']=='passed_operator_closed_export' and a['source_files_sha256']==closure['source_files_sha256'],'prior_audit_binding')
   audits[layer]=a
  require(audits['strict_export']['scientific_valid']==old_status['science_accepted']
          and audits['parsed_export']['scientific_valid']==len(manifest['baseline']['accepted_ids']),'prior_coverage')
  paths=dict(manifest['source_files_sha256'])
  for name in ('manifest.json','status.json',old_contract.JOURNAL):
   paths[relative(run/name)]=runtime.sha(run/name)
  for name,digest in manifest['supplement_sources'].items():paths[relative(HERE/name)]=digest
  failures=list(old_failures)
  for row in ledger.settled:
   if not row['valid']:
    failures.append({k:row.get(k) for k in ('attempt_id','id','model_key','attempt','reason','fatal','http_status','elapsed_seconds','charged_or_reserved_usd','cost_is_reserve','utc','settled_utc')})
  amendment=runtime.read(source/'io_recovery_amendment.json');original=source.parent/Path(amendment['original_run_path']).name
  binding={'source_run_relative':manifest['source_run_relative'],'source_closure_relative':manifest['source_closure_relative'],
           'operator_closure':closure,'capped_scientific_manifest_sha256':scientific['manifest_sha256'],
           'capped_export_manifest_sha256':runtime.sha(closure_path.parent/'strict_export/export_manifest.json'),
           'parsed_export_manifest_sha256':runtime.sha(closure_path.parent/'parsed_export/export_manifest.json'),
           'capped_terminal_status':old_status,'capped_final_ledger':old_final,
           'capped_operational_audit':audits['strict_export'],'parsed_source_operational_audit':audits['parsed_export'],
           'capped_first_valid_attempt_ids':[r['attempt_id'] for r in old_accepted.values()],
           'source_accepted_selection':manifest['baseline']['accepted_selection'],
           'capped_tries_by_id':{j['id']:old_ledger.tries[j['id']] for j in jobs},
           'source_recovery_provenance':None,'source_io_amendment':amendment,
           'original_source_directory':relative(original),'original_capped_outputs_retained':True}
  context={'shared_pauses_used':ledger.pauses,'source_pauses_used':manifest['baseline']['pauses'],
           'supplement_pause_count':sum(e['event']=='operational_pause' for e in events),
           'supplement_completed_pause_count':sum(e['event']=='operational_pause_completed' for e in events),
           'rounds_started':ledger.round,'overlay_started':len(ledger.starts),'overlay_settled':len(ledger.settled),
           'overlay_valid_scientific':len(ledger.newly_accepted_rows),'no_progress':ledger.no_progress,
           'source_strict_scientific':audits['strict_export']['scientific_valid'],
           'source_parsed_recovered_scientific':audits['parsed_export']['parsed_recovered_scientific'],
           'source_unsettled_reservations':len(old_starts)-len(old_settled),'fixed_new_max_tokens':512,
           'source_scope':'Operator-stopped512 phase; derived ledger only. No prior terminal state is invented.'}
  final=old_contract.final_ledger_record(manifest,ledger,runtime.sha(run/old_contract.JOURNAL))
  verified=export_completion.CompletionVerification(manifest,scientific,jobs,starts,settled,accepted,tries,final,status,
              failures,ledger.fingerprints,paths,binding,context)
  baseline=baseline_from_verified(verified,ledger)
  require(runtime.read(run/'status.json')==status and all(runtime.sha(member(n))==h for n,h in paths.items()),'source_changed_during_verify')
  return verified,baseline

def close_source(run,output_dir):
 run=Path(run).resolve();output=Path(output_dir).resolve()
 require(run.parent==HERE and output.parent==HERE and run!=output and not output.exists(),'separate_new_closure_required')
 audit=runtime.read(HERE/'ceiling2048_source_audit.json')
 require(audit.get('passed') is True and audit.get('model_calls')==0 and audit.get('real_outcomes_read') is False,'source_audit_not_passed')
 for name,digest in audit['source_sha256'].items():require(Path(name).name==name and runtime.sha(HERE/name)==digest,'source_audit_stale')
 with source_locks(run):
  verified,baseline=verify_snapshot_locked(run)
  closure={'version':1,'kind':KIND,'created_utc':runtime.now(),'source_run_relative':relative(run),
           'source_manifest_sha256':verified.manifest['manifest_sha256'],
           'scientific_manifest_sha256':verified.scientific_manifest['manifest_sha256'],
           'observed_process_exit':OBSERVED_EXIT,'original_source_status':verified.status,
           'derived_source_ledger':verified.final,'baseline':baseline,'source_files_sha256':verified.input_sha256,
           'verification_sources':{n:runtime.sha(HERE/n) for n in ('ceiling2048_source.py','ceiling2048_source_audit.py','ceiling2048_source_audit.json')},
           'source_files_modified':False,'old_final_ledger_written':False,'model_calls':0,
           'unknown_policy':'All128/512 unresolved starts retain their previous reserves. Only newly unknown512 starts are newly observed by the next-phase operational counters.',
           'inference_label':'A further missing-only output-budget amendment; original128 and512 records and accepted answers are retained. No independent replication or complete-source claim.'}
  closure['closure_sha256']=runtime.digest(runtime.compact(closure).encode())
  output.mkdir(exist_ok=False);runtime.save(output/'operator_closure.json',closure)
  require(all(runtime.sha(member(n))==h for n,h in verified.input_sha256.items()),'source_changed_during_closure')
  return closure

def verify_closed_source_locked(closure_path):
 """Caller holds the stopped512 supplement.lock then execution.lock."""
 closure_path=Path(closure_path).resolve();c=runtime.read(closure_path);body=dict(c);claimed=body.pop('closure_sha256')
 require(c['version']==1 and c['kind']==KIND and runtime.digest(runtime.compact(body).encode())==claimed,'closure_identity')
 expected={'ceiling2048_source.py','ceiling2048_source_audit.py','ceiling2048_source_audit.json'}
 require(set(c['verification_sources'])==expected,'verification_source_inventory')
 for name,digest in c['verification_sources'].items():require(runtime.sha(HERE/name)==digest,'verification_source_changed')
 for name,digest in c['source_files_sha256'].items():require(runtime.sha(member(name))==digest,'closed_source_changed')
 require(c['observed_process_exit']==OBSERVED_EXIT and c['source_files_modified'] is False
         and c['old_final_ledger_written'] is False and c['model_calls']==0,'closure_preservation_contract')
 verified,baseline=verify_snapshot_locked(member(c['source_run_relative']))
 require(c['source_files_sha256']==verified.input_sha256 and c['baseline']==baseline,'closure_inventory_or_baseline')
 require(c['source_manifest_sha256']==verified.manifest['manifest_sha256']
         and c['scientific_manifest_sha256']==verified.scientific_manifest['manifest_sha256']
         and c['original_source_status']==verified.status and c['derived_source_ledger']==verified.final,'closure_projection')
 return c,verified,baseline

def verify_closed_source(closure_path):
 source=member(runtime.read(closure_path)['source_run_relative'])
 with source_locks(source):return verify_closed_source_locked(closure_path)

if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);g=p.add_mutually_exclusive_group(required=True)
 g.add_argument('--close',action='store_true');g.add_argument('--verify',type=Path)
 p.add_argument('--source',type=Path,default=HERE/'completion_supplement');p.add_argument('--output',type=Path,default=HERE/'ceiling2048_source')
 a=p.parse_args()
 if a.close:c=close_source(a.source,a.output);b=c['baseline']
 else:c,_,b=verify_closed_source(a.verify)
 print(runtime.compact({'status':'operator_closed_source_verified','closure_sha256':c['closure_sha256'],
     'scientific_accepted':len(b['accepted_ids']),'scientific_missing':len(b['tries'])-len(b['accepted_ids']),
     'occupied_usd':b['occupied_usd'],'unknown_starts':len(b['unknown_started_attempt_ids']),
     'newly_observed_unknowns':len(b['newly_observed_unknown_attempt_ids']),'shared_pauses':b['pauses']}))
