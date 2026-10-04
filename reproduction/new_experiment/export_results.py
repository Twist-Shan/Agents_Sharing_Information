"""Terminal-only offline replay and export. This file performs no network calls.

Do not use this as a progress monitor. It refuses to read outcome journals until
the acquisition status is terminal and the execution OS lock can be acquired.
"""
from __future__ import annotations
from collections import Counter, defaultdict
from decimal import Decimal
from pathlib import Path
import argparse
import csv
import hashlib
import json
import sys

import analysis
import protocol
import runtime as r

HERE=Path(__file__).resolve().parent


def check(condition, message):
    if not condition:
        raise ValueError(message)


def write_json(path, obj):
    path.write_text(json.dumps(obj,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')


def flatten(row, prefix=''):
    out={}
    for key,value in row.items():
        label=prefix+key
        if isinstance(value,dict):
            out.update(flatten(value,label+'.'))
        elif isinstance(value,(list,tuple)):
            out[label]=json.dumps(value,ensure_ascii=False,separators=(',',':'),allow_nan=False)
        else:
            out[label]=value
    return out


def write_csv(path, rows):
    flat=[flatten(row) for row in rows]
    fields=list(dict.fromkeys(k for row in flat for k in row))
    with path.open('w',encoding='utf-8-sig',newline='') as handle:
        writer=csv.DictWriter(handle,fieldnames=fields)
        writer.writeheader()
        writer.writerows(flat)


def replay(run, manifest, jobs, status):
    """Called only while holding the terminal execution lock."""
    started=r.lines(run/'started.jsonl')
    settled=r.lines(run/'attempts.jsonl')
    ledger=r.Ledger(started,settled)
    profiles={p['key']:p for p in manifest['profiles']}
    all_jobs={j['id']:j for j in jobs}
    all_jobs.update({c['id']:c for c in (r.compatibility(p) for p in profiles.values())})
    start_by_id={s['attempt_id']:s for s in started}
    settled_by_id={s['attempt_id']:s for s in settled}
    check(len(start_by_id)==len(started),'Duplicate physical start IDs.')
    check(len(settled_by_id)==len(settled),'Duplicate physical settlement IDs.')
    check(set(settled_by_id)<=set(start_by_id),'Settlement without a start.')
    for row in started:
        check(row['id'] in all_jobs,'Unplanned started ID.')
        job=all_jobs[row['id']]
        check(row['model_key']==job['model_key'],'Started model-key mismatch.')
        p=profiles[row['model_key']]
        request=r.payload(p,job)
        check(row['request_sha256']==r.digest(r.compact(request).encode()),'Started request hash changed.')
        check(Decimal(row['reserve_usd'])==r.reserve(p,request),'Started reservation changed.')
    fingerprints={}
    for row in settled:
        if row.get('reason')=='interrupted_unknown':
            check(row['valid'] is False and row['action'] is None and row['fatal'] is False and row['cost_is_reserve'] is True,
                  'Invalid crash-unknown record.')
            check(Decimal(row['charged_or_reserved_usd'])==Decimal(row['reserve_usd']),'Crash unknown reserve was released.')
            continue
        p=profiles[row['model_key']]
        job=all_jobs[row['id']]
        classified=r.classify(row,p,job,Decimal(row['reserve_usd']))
        valid,answer,reason,fatal=classified
        if 'worker_error' in row:
            valid,answer,reason,fatal=False,None,'fatal_worker_exception',True
        obj=r.object_or_empty(row.get('response'))
        fp=obj.get('system_fingerprint')
        if obj.get('model') in p['allowed_models'] and obj.get('provider')==p['provider_name'] and fp is not None:
            previous=fingerprints.get(row['model_key'])
            if previous is None:
                fingerprints[row['model_key']]=fp
            elif fp!=previous:
                valid,answer,reason,fatal=False,None,'fatal_fingerprint_drift',True
        check((valid,answer,reason,fatal)==(row['valid'],row['action'],row['reason'],row['fatal']),
              'Classification replay differs: '+row['attempt_id'])
        cost,reserved=r.cost_value(row,Decimal(row['reserve_usd']))
        check(cost==Decimal(row['charged_or_reserved_usd']) and reserved==row['cost_is_reserve'],
              'Cost replay differs: '+row['attempt_id'])
    independently_occupied=r.accounting(started,settled)
    check(ledger.occupied==independently_occupied,'Independent and runtime accounting differ.')
    check(Decimal(status['cumulative_occupied_usd'])==independently_occupied,'Status cost differs from journals.')
    check(status['physical_started']==len(started) and status['physical_settled']==len(settled),'Status physical counts differ.')
    check(status['inflight']==len(started)-len(settled),'Status inflight count differs.')
    final_ledger=r.read(run/'final_ledger.json')
    check(final_ledger['status']=='independently_reconciled','Terminal ledger is not reconciled.')
    check(final_ledger['manifest_sha256']==manifest['manifest_sha256'],'Terminal ledger belongs to another manifest.')
    check(final_ledger['started_sha256']==(r.sha(run/'started.jsonl') if (run/'started.jsonl').exists() else None),'Started journal changed after terminal ledger.')
    check(final_ledger['settled_sha256']==(r.sha(run/'attempts.jsonl') if (run/'attempts.jsonl').exists() else None),'Settlement journal changed after terminal ledger.')
    check(Decimal(final_ledger['cumulative_occupied_usd'])==independently_occupied,'Terminal-ledger total differs.')
    science_ids={j['id'] for j in jobs}
    first={}
    final={}
    lineage=[]
    settlements_by_logical=defaultdict(list)
    starts_by_logical=defaultdict(list)
    for row in settled:
        settlements_by_logical[row['id']].append(row)
    for row in started:
        starts_by_logical[row['id']].append(row)
    for job in jobs:
        ident=job['id']
        attempts=sorted(starts_by_logical[ident],key=lambda s:s['attempt'])
        responses=sorted(settlements_by_logical[ident],key=lambda s:s['attempt'])
        first_row=next((row for row in responses if row['attempt']==1),None)
        accepted=[row for row in responses if row['valid']]
        check(len(accepted)<=1,'Multiple accepted answers for one scientific ID.')
        if first_row is not None and first_row['valid']:
            first[ident]=first_row['action']
        if accepted:
            final[ident]=accepted[0]['action']
        lineage.append(dict(id=ident,block_id=job['block_id'],mode=job['mode'],metadata=job['metadata'],
                            physical_started=len(attempts),physical_settled=len(responses),
                            first_attempt_reason=(first_row['reason'] if first_row else ('unsettled' if attempts else 'unissued')),
                            first_attempt_valid=bool(first_row and first_row['valid']),
                            accepted_attempt=(accepted[0]['attempt'] if accepted else None),
                            final_valid=bool(accepted),
                            failure_reasons=[row['reason'] for row in responses if not row['valid']],
                            physical_attempt_ids=[row['attempt_id'] for row in attempts],
                            accepted_request_sha256=(accepted[0]['request_sha256'] if accepted else None)))
    check(set(final)==(ledger.accepted & science_ids),'Accepted answer map differs from ledger.')
    check(status['science_accepted']==len(final),'Status scientific count differs.')
    if status['state']=='complete':
        check(len(final)==len(jobs),'Complete terminal status with unresolved scientific IDs.')
    known=sum((Decimal(x['charged_or_reserved_usd']) for x in settled if not x['cost_is_reserve']),Decimal(0))
    unknown=independently_occupied-r.PRIOR-known
    check(known==Decimal(final_ledger['known_new_cost_usd']) and unknown==Decimal(final_ledger['unknown_new_reserved_usd']),
          'Known/unknown cost partition differs.')
    cost_summary=dict(terminal_state=status['state'],terminal_reason=status.get('reason'),
                      planned=len(jobs),first_started_attempt_valid=len(first),final_valid=len(final),
                      unresolved=len(jobs)-len(final),physical_started=len(started),physical_settled=len(settled),
                      compatibility_starts=sum(s['id'].endswith('|compatibility') for s in started),
                      scientific_starts=sum(s['id'] in science_ids for s in started),
                      interrupted_started_attempts=sum(s['reason']=='interrupted_unknown' for s in settled),
                      interruption_interpretation='Interrupted starts have no recorded response; these are operational missingness, not model refusals or incorrect answers. See IO_RECOVERY.md for any independently documented pre-dispatch event.',
                      prior_occupied_usd=str(r.PRIOR),known_new_cost_usd=str(known),
                      unknown_new_reserved_usd=str(unknown),cumulative_occupied_usd=str(independently_occupied),
                      cumulative_cap_usd=str(r.CAP),budget_remaining_usd=str(r.CAP-independently_occupied),
                      failure_counts=dict(Counter(s['reason'] for s in settled if not s['valid'])),
                      accepted_attempt_counts=dict(Counter(str(x['accepted_attempt']) for x in lineage if x['final_valid'])),
                      returned_models=sorted({str(r.object_or_empty(s.get('response')).get('model')) for s in settled if s.get('response')}),
                      returned_providers=sorted({str(r.object_or_empty(s.get('response')).get('provider')) for s in settled if s.get('response')}),
                      replay_checks='Source/request hashes, status counts, every settled classification, both ledger sums and terminal journal hashes agree.')
    attempt_rows=[]
    for s in started:
        end=settled_by_id.get(s['attempt_id'])
        job=all_jobs[s['id']]
        obj=r.object_or_empty(end.get('response')) if end else {}
        usage=r.object_or_empty(obj.get('usage'))
        attempt_rows.append(dict(id=s['id'],attempt=s['attempt'],attempt_id=s['attempt_id'],
                                 mode=job.get('mode','compatibility'),metadata=job['metadata'],
                                 request_sha256=s['request_sha256'],reserve_usd=s['reserve_usd'],
                                 valid=end.get('valid') if end else False,
                                 reason=end.get('reason') if end else 'unsettled',
                                 charged_or_reserved_usd=end['charged_or_reserved_usd'] if end else s['reserve_usd'],
                                 cost_is_reserve=end['cost_is_reserve'] if end else True,
                                 http_status=end.get('http_status') if end else None,
                                 response_object_recorded=bool(end and isinstance(end.get('response'),dict)),
                                 interrupted_start_without_recorded_response=bool(end and end.get('reason')=='interrupted_unknown'),
                                 elapsed_seconds=end.get('elapsed_seconds') if end else None,
                                 returned_model=obj.get('model'),returned_provider=obj.get('provider'),
                                 prompt_tokens=usage.get('prompt_tokens'),completion_tokens=usage.get('completion_tokens'),
                                 reasoning_tokens=r.object_or_empty(usage.get('completion_tokens_details')).get('reasoning_tokens')))
    return first,final,lineage,attempt_rows,cost_summary


def export(run, output):
    # This must precede any scientific outcome/journal access.
    check((run/'status.json').exists(),'No terminal status exists; refusing to read results.')
    status=r.read(run/'status.json')
    check(status.get('state') in r.TERMINAL,'Collection is active/nonterminal; refusing to read results.')
    with r.execution_lock(run/'execution.lock'):
        status=r.read(run/'status.json')
        check(status.get('state') in r.TERMINAL,'Collection status changed; refusing to read results.')
        manifest,jobs=r.validate(run)
        check(status.get('manifest_sha256')==manifest['manifest_sha256'],'Status manifest mismatch.')
        first,final,lineage,attempt_rows,cost_summary=replay(run,manifest,jobs,status)
        result=analysis.analyze(jobs,first,final)
        # The frozen analysis API uses the short key "first". Clarify its target
        # at export because a reserved start may precede actual HTTP dispatch.
        result['acquisition_interpretation']='First started acquisition attempt and final accepted-response policy are separately reported. An interrupted reservation without a recorded response is missing in the first panel, not a model error; no response is imputed.'
        result['first_panel_definition']='The attempt==1 entry for every planned ID; it may be unissued, interrupted before dispatch, transport-failed, schema-invalid, or valid. Only a recorded valid answer supplies an observed correctness value.'
        output.mkdir(parents=True,exist_ok=True)
        write_json(output/'first_answers.json',first)
        write_json(output/'final_answers.json',final)
        write_json(output/'analysis.json',result)
        write_json(output/'acquisition_summary.json',cost_summary)
        write_json(output/'request_lineage.json',lineage)
        write_csv(output/'request_lineage.csv',lineage)
        write_csv(output/'physical_attempts.csv',attempt_rows)
        contrast_rows=[]
        block_rows=[]
        for panel in ('first','final'):
            current=result[panel]
            write_csv(output/f'{panel}_scored_requests.csv',current['scored_rows'])
            for table in ('mode_rates','policy_law_rates','wording_policy_law_rates','complete_cell_rates'):
                write_csv(output/f'{panel}_{table}.csv',current[table])
            for name,contrast in current['aid_contrasts'].items():
                row={k:v for k,v in contrast.items() if k!='block_differences'}
                contrast_rows.append(dict(response_policy=panel,contrast=name,**row))
                block_rows.extend(dict(response_policy=panel,contrast=name,**row) for row in contrast['block_differences'])
        write_csv(output/'aid_contrasts.csv',contrast_rows)
        write_csv(output/'aid_block_differences.csv',block_rows)
        # Cell-level action comparisons remain descriptive (no new inferential family).
        sensitivity_rows=[]
        for panel in ('first','final'):
            cells=result[panel]['complete_cell_rates']
            grouped=defaultdict(dict)
            for row in cells:
                g=row['group']
                if g['mode'] not in protocol.ACTION_MODES:
                    continue
                key=(g['mode'],g['wording'],g['policy'],g['safe'],g['encoding'])
                grouped[key][g['law']]=row
            for key,value in sorted(grouped.items()):
                rr,ss=value['R'],value['S']
                lower=ss['join_completion_bounds'][0]-rr['join_completion_bounds'][1]
                upper=ss['join_completion_bounds'][1]-rr['join_completion_bounds'][0]
                sensitivity_rows.append(dict(response_policy=panel,**dict(zip(('mode','wording','policy','safe','encoding'),key)),
                                             r_planned=rr['planned'],s_planned=ss['planned'],r_valid=rr['valid'],s_valid=ss['valid'],
                                             r_join_over_planned=rr['join_over_planned'],s_join_over_planned=ss['join_over_planned'],
                                             difference_estimate=(lower if rr['missing']==ss['missing']==0 else None),
                                             difference_completion_lower=lower,difference_completion_upper=upper,
                                             interpretation='Descriptive; no cell-level significance or equivalence claim.'))
        write_csv(output/'descriptive_rs_sensitivity.csv',sensitivity_rows)
        provenance=dict(manifest_sha256=manifest['manifest_sha256'],planned_sha256=manifest['planned_sha256'],
                        frozen_sources=manifest['sources'],status=status,
                        started_sha256=r.sha(run/'started.jsonl') if (run/'started.jsonl').exists() else None,
                        attempts_sha256=r.sha(run/'attempts.jsonl') if (run/'attempts.jsonl').exists() else None,
                        export_script_sha256=r.sha(Path(__file__)),analysis_seed=protocol.SEEDS['analysis'],
                        operational_amendments={name:r.sha(HERE/name) for name in ('IO_RECOVERY.md','io_recovery.py','io_recovery_audit.json') if (HERE/name).exists()},
                        paid_calls_by_export=0,terminal_lock_verified=True)
        write_json(output/'export_provenance.json',provenance)
        readme=f'''# Independent diagnostics and nested aid experiment: offline export

The experiment contains 5,376 planned requests. This export was generated only
after terminal status `{status['state']}` and successful acquisition of the
execution OS lock. Every frozen source hash, request hash, recorded response
classification, status count, journal hash, and terminal ledger was replayed.
No API calls were made by this exporter.

## Reproduce

Use the archived new_experiment directory containing protocol.py,
original_protocol.py, analysis.py, runtime.py, export_results.py, profiles.json,
PLAN.md, and the `{run.name}` acquisition directory. The analysis requires Python
with SciPy installed. From that directory run:

```
python verify.py
python export_results.py --run {run.name} --output reproduced_exports
```

To recompute scientific summaries from the exported parsed answer maps alone:

```
python analysis.py --first first_answers.json --final final_answers.json --output recomputed_analysis.json
```

The full-journal command also verifies parsing and acquisition lineage. The
answer-map command does not independently verify source response extraction.
Raw journals may be large; they must not be replaced by the aggregate CSVs for
an independent acquisition audit. No credentials are required for either path.

## File guide

- analysis.json contains all scientific results, including first and final panels.
- first_answers.json contains only valid **first started acquisition attempts**.
  A start is logged before HTTP dispatch. An interrupted reservation may therefore
  have no actual model response. It remains unresolved in that panel even if a
  later attempt succeeds; it is not counted as a model refusal or wrong answer.
- final_answers.json contains the first accepted valid response for every resolved
  logical ID. Wrong but schema-valid answers are retained.
- *_scored_requests.csv links every planned ID to its scored components, block,
  stimulus metadata, and normalized answer. Unresolved IDs remain rows.
- *_mode_rates.csv, *_policy_law_rates.csv, *_wording_policy_law_rates.csv, and
  *_complete_cell_rates.csv retain every prespecified condition and denominator.
- aid_contrasts.csv reports exactly the three adjacent aid comparisons, with
  simultaneous approximate 95% intervals and independent-block Hoeffding bounds.
- aid_block_differences.csv provides every paired analysis block needed to
  independently recalculate those contrasts and uncertainty estimates.
- descriptive_rs_sensitivity.csv reports all action-arm R/S JOIN-rate differences
  by wording, policy, SAFE and encoding without a new significance claim.
- request_lineage.* and physical_attempts.csv expose first validity, failure cause,
  retries, accepted attempt, token counts, request hashes, and costs.
- acquisition_summary.json and export_provenance.json bind the results to the
  terminal ledger and immutable acquisition/source hashes.

## Interpretation

Observed-correct/planned rates are lower completion bounds when responses are
missing. Valid-only rates are explicitly conditional. Completion intervals are
missing-outcome bounds, **not confidence intervals**; when complete, present the
point estimate rather than displaying a misleading zero-width range. The three
primary comparisons average 24 task cells per block and use four wording strata.
Normal intervals are suppressed under zero empirical variance or missing paired
answers; bounded sensitivity intervals remain where complete data permit them.
The additional cell tables are descriptive and are not a significance search.

The file physical_attempts.csv preserves the runner's legacy filename, but its
rows are **started acquisition attempts**, not necessarily executed model calls.
Consult `response_object_recorded` and
`interrupted_start_without_recorded_response`; absence of a recorded response does
not by itself establish whether a request reached the provider. IO_RECOVERY.md
documents the local status-file failure after 1,152 accepted scientific answers:
16 starts were reserved before the failing snapshot and had not been dispatched
by that code path. Their full unknown-cost reserves and attempt counts were
retained conservatively. The amendment changed only local atomic-save retries.
Those reservations are operational missingness, not evidence of model failure.

The first and final panels target different response-acceptance policies and do
not establish that missingness is random. Diagnostics were independently elicited;
they never filter action observations or identify an individual response's hidden
reasoning. Aid effects may reflect several changes, including salience and
calculation assistance. No result-based sample expansion or stopping was used.

Frozen manifest: `{manifest['manifest_sha256']}`.
'''
        (output/'README.md').write_text(readme,encoding='utf-8')
        # Exclude the hash manifest itself to avoid a self-referential digest.
        files={p.name:r.sha(p) for p in sorted(output.iterdir()) if p.is_file() and p.name!='files_sha256.json'}
        write_json(output/'files_sha256.json',files)
    return dict(exported=True,output=str(output),terminal_state=status['state'],
                first_valid=len(first),final_valid=len(final),planned=len(jobs),
                cumulative_occupied_usd=cost_summary['cumulative_occupied_usd'],paid_calls=0)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run',type=Path,default=HERE/'run_v2')
    parser.add_argument('--output',type=Path,default=HERE/'exports')
    args=parser.parse_args()
    print(json.dumps(export(args.run.resolve(),args.output.resolve()),indent=2))
