"""Read-only supplemental source/manifest contract. No network or paid-adapter import."""
from __future__ import annotations
from contextlib import contextmanager, ExitStack
from pathlib import Path
from typing import Any
import runtime
import answer_recovery_source
import answer_recovery
from supplement_ledger import ProjectedLedger, require

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent
JOURNAL = 'supplemental_events.jsonl'
LOCK = 'supplement.lock'
KIND = 'MISSING_ONLY_EXTENDED_RESPONSE_SUPPLEMENT'
SUPPLEMENT_SOURCES = ('supplement_validation.py', 'supplement_ledger.py', 'supplement_contract.py',
                      'supplement_response.py', 'SUPPLEMENT_RESPONSE_POLICY.txt',
                      'supplement_transition_audit.py', 'supplement_transition_audit.json', 'export_completion.py',
                      'answer_extraction.py', 'ANSWER_EXTRACTION_POLICY.txt',
                      'answer_extraction_audit.py', 'answer_extraction_audit.json',
                      'answer_recovery.py', 'answer_recovery_source.py',
                      'answer_recovery_source_audit.py', 'answer_recovery_source_audit.json')
POLICY = {'original_order_rounds': True, 'one_attempt_per_remaining_id_per_round': True,
          'max_attempts_per_id': None, 'first_extractable_including_wrong': True,
          'strict_historical_answers_locked': True, 'historical_missing_selection': 'earliest_unambiguous_stop',
          'historical_max_tokens': 128, 'future_max_tokens': 512, 'extract_finish_reason': 'stop',
          'no_progress_settlements_before_pause': 50, 'shared_maximum_pauses': 12,
          'concurrency': 16, 'cumulative_cap_usd': '50',
          'metadata_save_delays_seconds': [.25, 1.0],
          'unchanged_prompts_models_reasoning_routes': True, 'no_new_scientific_ids': True}
INFERENCE_LABEL = ('User-authorized answer-extraction and missing-only supplementation: historical strict answers are locked; '
                   'remaining historical stop-finished answers use the earliest unambiguous extraction; '
                   'new missing-only requests use a fixed 512-token allowance and the first extractable answer. '
                   'Historical 128-token strict records and analyses remain immutable. This amended response policy '
                   'reuses the fixed allocation and analysis formulas and is not an independent replication.')


def hash_checked(path: Path, digest: str) -> None:
    require(path.is_file() and runtime.sha(path) == digest, 'bound_file_changed:' + path.name)


def source_binding(closure_path: Path, closure: dict) -> dict:
    """Bind both already-generated sensitivity exports without inspecting effects."""
    binding = {**closure['source_files_sha256'],
               closure_path.relative_to(REPO).as_posix(): runtime.sha(closure_path)}
    expected = {'analysis.json','logical_outcomes.csv','cell_summaries.csv','free_cells.csv',
                'contrasts.csv','prediction.csv','failed_attempts.csv','operational_audit.json'}
    for layer in ('strict_export','parsed_export'):
        folder = closure_path.parent / layer
        em = runtime.read(folder / 'export_manifest.json')
        require(em['manifest_sha256'] == closure['closure_sha256'] and
                em['scientific_manifest_sha256'] == closure['scientific_manifest_sha256'], 'source_export_identity')
        require(set(em['files_sha256']) == expected, 'source_export_inventory')
        binding[(folder/'export_manifest.json').relative_to(REPO).as_posix()] = runtime.sha(folder/'export_manifest.json')
        for name, digest in em['files_sha256'].items():
            hash_checked(folder/name, digest)
            binding[(folder/name).relative_to(REPO).as_posix()] = digest
    for name in ('extraction_attempts.jsonl','answer_selections.json','recovery_export_summary.json'):
        member = closure_path.parent / name
        require(member.is_file(), 'missing_source_projection:' + name)
        binding[member.relative_to(REPO).as_posix()] = runtime.sha(member)
    return binding


def baseline_from_verified(verified: tuple) -> dict:
    m, jobs, starts, settled, accepted, ledger, final, status, failures, fingerprints, operations = verified
    require(status['state'] == 'interrupted' and status['reason'] == 'KeyboardInterrupt'
            and not any(r['fatal'] for r in settled), 'source_not_operator_stopped_nonfatal')
    selected, _ = answer_recovery.project_answers(verified)
    tracker, pauses, pending = runtime.pause_state(settled, operations)
    require(pauses <= 12, 'source_pause_cap')
    reset = max([x['settled_count'] for x in operations if x['event'] == 'operational_pause_completed'], default=0)
    selected_attempts = {r['attempt_id'] for r in selected.values()}
    no_progress = 0
    for row in settled[reset:]:
        no_progress = 0 if row['attempt_id'] in selected_attempts else no_progress + 1
    settled_ids = {r['attempt_id'] for r in settled}
    unknown = [r for r in starts if r['attempt_id'] not in settled_ids]
    # Unknown source calls already occupy their complete reserve. These virtual
    # failure observations update only operational counters, never raw journals or cost.
    for row in unknown:
        tracker.observe({**row, 'reason': 'interrupted_unknown', 'retry_after_seconds': 0})
        no_progress += 1
    return {'occupied_usd': str(ledger.occupied), 'physical_started': len(starts), 'physical_settled': len(settled),
            'unknown_started_attempt_ids': [r['attempt_id'] for r in unknown],
            'tries': {j['id']: ledger.tries[j['id']] for j in jobs},
            'accepted_ids': [j['id'] for j in jobs if j['id'] in selected],
            'accepted_selection': selected,
            'strict_accepted_count': sum(r['selection_layer'] == 'strict' for r in selected.values()),
            'parsed_accepted_count': sum(r['selection_layer'] == 'parsed_recovery' for r in selected.values()),
            'fingerprints': fingerprints, 'pauses': pauses, 'pending_pause': pending, 'no_progress': no_progress,
            'tracker': {'recent': list(tracker.recent), 'consecutive': tracker.consecutive,
                        'trigger': tracker.trigger, 'retry_after': tracker.retry_after}}


def contained_file(relative: str, repo: Path = REPO) -> Path:
    require(isinstance(relative, str) and not Path(relative).is_absolute(), 'absolute_bound_path')
    path = (repo / relative).resolve()
    require(path.is_relative_to(repo.resolve()) and path != repo.resolve(), 'bound_path_escape')
    return path


def validate_manifest(run: Path) -> dict:
    run = Path(run).resolve()
    m = runtime.read(run / 'manifest.json')
    body = dict(m); claimed = body.pop('manifest_sha256')
    require(runtime.digest(runtime.compact(body).encode()) == claimed, 'manifest_changed')
    require(m['version'] == 2 and m['kind'] == KIND and m['policy'] == POLICY, 'manifest_policy')
    require(m['inference_label'] == INFERENCE_LABEL, 'inference_label_changed')
    require(set(m['supplement_sources']) == set(SUPPLEMENT_SOURCES), 'supplement_source_inventory')
    require(contained_file(m['run_relative']) == run, 'supplement_directory_binding')
    source = contained_file(m['source_run_relative'])
    require(source != run and not source.is_relative_to(run) and not run.is_relative_to(source), 'source_destination_overlap')
    for name, digest in m['supplement_sources'].items():
        require(Path(name).name == name, 'supplement_source_path')
        hash_checked(HERE / name, digest)
    for relative, digest in m['source_files_sha256'].items():
        hash_checked(contained_file(relative), digest)
    closure_path = contained_file(m['source_closure_relative'])
    closure = runtime.read(closure_path)
    require(closure['closure_sha256'] == m['source_closure_sha256'] and
            closure['source_run_relative'] == m['source_run_relative'], 'closure_binding')
    needed = source_binding(closure_path, closure)
    require(m['source_files_sha256'] == needed, 'complete_closed_source_inventory')
    required = {str((source/name).relative_to(REPO).as_posix()) for name in
                ('manifest.json','planned.jsonl','status.json','started.jsonl','attempts.jsonl')}
    require(required <= set(needed), 'missing_required_source_binding')
    require(m['scientific_count'] == len(m['planned_ids']) == len(set(m['planned_ids'])) == 48192 and
            set(m['baseline']['tries']) == set(m['planned_ids']), 'manifest_allocation')
    return m


@contextmanager
def source_locks(source: Path):
    """Current capped source outer lock before its runtime lock; no paid imports."""
    source = Path(source)
    with ExitStack() as stack:
        if (source / 'io_recovery_amendment.json').exists():
            stack.enter_context(runtime.execution_lock(source / 'io_supervisor.lock'))
        elif (source / 'supervisor_manifest.json').exists() or (source / 'supervisor_status.json').exists():
            stack.enter_context(runtime.execution_lock(source / 'supervisor.lock'))
        stack.enter_context(runtime.execution_lock(source / 'execution.lock'))
        yield


def load_bound_source(m: dict) -> tuple:
    """Caller owns source locks; bound byte hashes precede raw reply projection."""
    for relative, digest in m['source_files_sha256'].items():
        hash_checked(contained_file(relative), digest)
    closure, verified = answer_recovery_source.verify_closed_source_locked(contained_file(m['source_closure_relative']))
    require(closure['closure_sha256'] == m['source_closure_sha256'], 'closure_changed')
    scientific, jobs = verified[:2]
    require(scientific['manifest_sha256'] == m['scientific_manifest_sha256'], 'scientific_manifest_changed')
    require([j['id'] for j in jobs] == m['planned_ids'] and len(jobs) == m['scientific_count'], 'planned_ids_changed')
    require(baseline_from_verified(verified) == m['baseline'], 'baseline_projection_changed')
    return verified


def final_ledger_record(m: dict, ledger: ProjectedLedger, journal_sha: str | None) -> dict:
    return {'status': 'independently_reconciled', 'manifest_sha256': m['manifest_sha256'],
            'scientific_manifest_sha256': m['scientific_manifest_sha256'],
            'events_sha256': journal_sha, **ledger.summary()}


def verify_status(m: dict, ledger: ProjectedLedger, status: dict, terminal: bool = True) -> None:
    require(status.get('manifest_sha256') == m['manifest_sha256'] and
            status.get('scientific_manifest_sha256') == m['scientific_manifest_sha256'], 'status_manifest')
    if terminal:
        require(status.get('state') in runtime.TERMINAL, 'supplement_not_terminal')
    for k, v in ledger.summary().items():
        require(status.get(k) == v, 'status_projection:' + k)
    state = status.get('state')
    if state == 'complete':
        require(not ledger.missing_ids and not ledger.inflight and not ledger.fatal_reason, 'false_complete')
    elif state == 'halted_service':
        require(ledger.pauses == 12 and ledger.needs_pause and not ledger.inflight, 'false_service_halt')
    elif state == 'halted_budget':
        require(bool(ledger.missing_ids) and not ledger.inflight, 'false_budget_halt')
