"""User-authorized2048-token DeepSeek-only missing completion. No original runtime globals are replaced.

Development of this file is not preparation or authorization to launch.  Prepare
only after the stopped source is separately closed and verified; execute only that audited,
hashed preparation. Secrets stay in memory behind the original hidden-TTY gate.
"""
from __future__ import annotations
from concurrent.futures import ThreadPoolExecutor
from contextlib import ExitStack
from decimal import Decimal
from pathlib import Path
import argparse
import getpass
import os
import sys
import time
import warnings
import runtime
import ceiling2048_source as source_module
import ceiling2048_response as response
from ceiling2048_ledger import ProjectedLedger, require
import ceiling2048_contract as contract

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent
D = Decimal
AUDIT = 'ceiling2048_audit.json'
NEW_SOURCES = contract.SUPPLEMENT_SOURCES


def metadata_save(path: Path, value: dict) -> None:
    """Retry only atomic JSON metadata replacement; never retry a journal append."""
    require(path.name in ('status.json', 'final_ledger.json'), 'metadata_target')
    for attempt in range(3):
        try:
            runtime.save(path, value)
            return
        except PermissionError:
            if attempt == 2:
                raise
            time.sleep((.25, 1.0)[attempt])


def source_records() -> dict:
    # These focused audits cover their stated modules; the immutable manifest
    # additionally binds the runner, contract and export source without claiming
    # that response-ledger fixtures validate all downstream numerical results.
    for filename in (AUDIT, 'ceiling2048_source_audit.json', 'export_ceiling2048_audit.json', 'answer_extraction_audit.json'):
        audit=runtime.read(HERE/filename)
        require(audit.get('passed') is True and audit.get('model_calls')==0,'audit_not_passed:'+filename)
        for name,digest in audit['source_sha256'].items():
            require(Path(name).name==name and runtime.sha(HERE/name)==digest,'audit_stale:'+name)
    return {name:runtime.sha(HERE/name) for name in NEW_SOURCES}


def prepare(closure_path: Path, run: Path) -> dict:
    closure_path, run = Path(closure_path).resolve(), Path(run).resolve()
    require(run.parent == HERE and not run.exists(), 'new_separate_run_required')
    sources = source_records()
    closure = runtime.read(closure_path)
    source = contract.contained_file(closure['source_run_relative'])
    require(source.parent == HERE and source != run, 'source_destination_overlap')
    with contract.source_locks(source):
        closure, verified, baseline = source_module.verify_closed_source_locked(closure_path)
        scientific, jobs = verified.scientific_manifest, verified.jobs
        binding = contract.source_binding(closure_path, closure)
        require(len(jobs) == 48192, 'source_allocation_count')
        m = {'version': 3, 'kind': contract.KIND, 'prepared_utc': runtime.now(),
             'run_relative': run.relative_to(REPO).as_posix(),
             'source_run_relative': source.relative_to(REPO).as_posix(),
             'source_closure_relative': closure_path.relative_to(REPO).as_posix(),
             'source_closure_sha256': closure['closure_sha256'],
             'scientific_manifest_sha256': scientific['manifest_sha256'], 'scientific_count': len(jobs),
             'planned_ids': [j['id'] for j in jobs], 'baseline': baseline,
             'policy': contract.POLICY, 'inference_label': contract.INFERENCE_LABEL,
             'source_files_sha256': binding, 'supplement_sources': sources,
             'authorization': 'User explicitly increased future output allowance to2048, then deferred Sonnet due cost and requested completion of the other models before paper drafting. Luna and Qwen are complete; only DeepSeek missing IDs are eligible. All prior answers remain locked, prompts/routes/no-thinking stay fixed, cumulative cap remainsUSD50, and no behavioral effects were inspected to choose this amendment.'}
        m['manifest_sha256'] = runtime.digest(runtime.compact(m).encode())
        run.mkdir(exist_ok=False)
        with runtime.execution_lock(run / contract.LOCK), runtime.execution_lock(run / 'execution.lock'):
            runtime.save(run / 'manifest.json', m)
            ledger = contract.make_ledger(m,jobs,scientific['profiles'])
            metadata_save(run / 'status.json', {'state': 'prepared', 'reason': None, 'utc': runtime.now(),
                'pid': os.getpid(), 'manifest_sha256': m['manifest_sha256'],
                'scientific_manifest_sha256': m['scientific_manifest_sha256'], **ledger.summary()})
        require(all(runtime.sha(contract.contained_file(n)) == h for n, h in binding.items()), 'source_changed_during_prepare')
    print(runtime.compact({'status': 'supplement_prepared', 'manifest_sha256': m['manifest_sha256'],
        'planned': len(jobs), 'missing': len(ledger.missing_ids), 'eligible_missing':len(ledger.eligible_missing_ids), 'occupied_usd': str(ledger.occupied)}), flush=True)
    return m


def _execute_locked(run: Path, m: dict, verified: tuple) -> str:
    scientific, jobs = verified.scientific_manifest, verified.jobs
    profiles = {p['key']: p for p in scientific['profiles']}
    previous = runtime.read(run / 'status.json')
    require(previous.get('state') not in contract.TERMINAL, 'terminal_supplement_cannot_resume')
    require(previous.get('manifest_sha256') == m['manifest_sha256'], 'prior_status_manifest')
    events = runtime.lines(run / contract.JOURNAL)
    ledger = contract.make_ledger(m,jobs,scientific['profiles'],events)
    state, reason, key = 'interrupted', None, None

    def emit(event_name: str, **fields) -> dict:
        event = {'sequence': len(ledger.events) + 1, 'event': event_name, 'utc': runtime.now(), **fields}
        # The durable event precedes the in-memory transition. Partial/corrupt
        # append is not retried and makes replay fail closed.
        runtime.append(run / contract.JOURNAL, event)
        ledger.apply(event)
        return event

    def snapshot() -> None:
        value = {'state': state, 'reason': reason, 'utc': runtime.now(), 'pid': os.getpid(),
                 'manifest_sha256': m['manifest_sha256'],
                 'scientific_manifest_sha256': m['scientific_manifest_sha256'], **ledger.summary()}
        if state in contract.TERMINAL:
            disk = runtime.lines(run / contract.JOURNAL)
            require(disk == ledger.events, 'terminal_event_reconciliation')
            replayed = contract.make_ledger(m,jobs,scientific['profiles'],disk)
            require(replayed.summary() == ledger.summary(), 'terminal_projection_reconciliation')
            digest = runtime.sha(run / contract.JOURNAL) if (run / contract.JOURNAL).exists() else None
            metadata_save(run / 'final_ledger.json', contract.final_ledger_record(m, replayed, digest))
        metadata_save(run / 'status.json', value)
        print(runtime.compact({'status': state, 'accepted': len(ledger.accepted), 'missing': len(ledger.missing_ids),
            'eligible_missing':len(ledger.eligible_missing_ids),'deferred_missing':len(ledger.missing_ids)-len(ledger.eligible_missing_ids),
            'overlay_settled': len(ledger.settled), 'shared_pauses': ledger.pauses,
            'occupied_usd': str(ledger.occupied), 'reason': reason}), flush=True)

    def endpoint_check(profile: dict, after_pause: int | None = None) -> None:
        ep = runtime.endpoint(profile)
        emit('preflight', kind='endpoint', model_key=profile['key'], endpoint=ep, after_pause=after_pause)

    def do_pause(profile: dict) -> bool:
        nonlocal state, reason
        if ledger.pending_pause is None:
            if ledger.pauses >= 12:
                state, reason = 'halted_service', 'maximum_cumulative_operational_pauses'
                snapshot()
                return False
            count = ledger.pauses + 1
            delay = max(ledger.tracker.retry_after, (60, 120, 240, 300)[min(count - 1, 3)])
            emit('operational_pause', pause=count, model_key=profile['key'], seconds=delay,
                 until_unix=time.time() + delay, settled_count=len(ledger.settled),
                 trigger={'transport': ledger.tracker.trigger, 'no_progress': ledger.progress_trigger})
        state = 'paused'
        snapshot()
        pause = ledger.pending_pause
        time.sleep(max(0, pause['until_unix'] - time.time()))
        endpoint_check(profiles[pause['model_key']], pause['pause'])
        emit('operational_pause_completed', pause=pause['pause'], settled_count=len(ledger.settled), completed_unix=time.time())
        state = 'running'
        snapshot()
        return True

    try:
        # A crash after durable start consumes that global attempt and its entire
        # reserve. It can never be silently erased or reissued under the same ID.
        for start in list(ledger.inflight):
            emit('attempt_settled', row={**start, 'valid': False, 'action': None, 'reason': 'interrupted_unknown',
                'fatal': False, 'charged_or_reserved_usd': start['reserve_usd'], 'cost_is_reserve': True,
                'settled_utc': runtime.now(), 'accepted': False, 'accepted_action': None,
                'acceptance_rule': None, 'extraction': None})
        if ledger.fatal_reason:
            state, reason = 'halted_fatal', 'fatal_journal_prevents_resume'
            snapshot()
            return state
        if not ledger.eligible_missing_ids:
            state = 'eligible_complete' if ledger.missing_ids else 'complete'
            snapshot()
            return state
        if not sys.stdin.isatty():
            raise runtime.PreflightUnavailable('hidden_tty_required')
        with warnings.catch_warnings():
            warnings.simplefilter('error', getpass.GetPassWarning)
            key = getpass.getpass('OpenRouter key (hidden): ')
        if not key.strip():
            raise runtime.PreflightUnavailable('empty_key')
        account = runtime.http('key', key)
        require(account.get('http_status') == 200, 'account_preflight_failed')
        details = runtime.object_or_empty(runtime.object_or_empty(account.get('response')).get('data'))
        emit('preflight', kind='account', account={k: details.get(k) for k in ('usage', 'limit', 'limit_remaining')})
        # All retained cohorts retain their original provider/price/no-thinking
        # contracts; only profiles with missing science need fresh endpoint GETs.
        needed = {ledger.byid[i]['model_key'] for i in ledger.eligible_missing_ids}
        for profile in scientific['profiles']:
            if profile['key'] in needed:
                endpoint_check(profile)
        state = 'running'
        snapshot()
        with ThreadPoolExecutor(max_workers=16) as pool:
            while ledger.eligible_missing_ids:
                if ledger.needs_pause:
                    selected = ledger.pending_pause['model_key'] if ledger.pending_pause else ledger.byid[ledger.eligible_missing_ids[0]]['model_key']
                    if not do_pause(profiles[selected]):
                        return state
                if ledger.round_ids is None:
                    emit('round_started', round=ledger.round + 1, ids=ledger.eligible_missing_ids)
                remaining = ledger.round_ids[ledger.round_cursor:]
                if not remaining:
                    emit('round_completed', round=ledger.round)
                    continue
                ids = remaining[:16]
                wave_jobs = [ledger.byid[i] for i in ids]
                bodies = [response.payload(profiles[j['model_key']], j) for j in wave_jobs]
                bounds = [response.reserve(profiles[j['model_key']], body) for j, body in zip(wave_jobs, bodies)]
                if ledger.occupied + sum(bounds, D(0)) > ledger.cap:
                    state, reason = 'halted_budget', 'cumulative_wave_reservation'
                    snapshot()
                    return state
                starts = []
                for job, body, bound in zip(wave_jobs, bodies, bounds):
                    attempt = ledger.tries[job['id']] + 1
                    start = {'id': job['id'], 'model_key': job['model_key'], 'attempt': attempt,
                        'attempt_id': job['id'] + '|try' + str(attempt), 'utc': runtime.now(),
                        'request_sha256': runtime.digest(runtime.compact(body).encode()),
                        'source_request_sha256': job['request_sha256'], 'reserve_usd': str(bound)}
                    emit('attempt_started', row=start)
                    starts.append(start)
                # No live status polling is necessary: status metadata is written
                # only between waves and progress is also emitted on stdout.
                futures = [pool.submit(runtime.http, 'chat/completions', key, body) for body in bodies]
                delay, had_transport = .25, False
                for job, start, future in zip(wave_jobs, starts, futures):
                    try:
                        result = future.result()
                    except Exception as exc:
                        result = {'http_status': None, 'response': None, 'worker_error': type(exc).__name__, 'retry_after_seconds': 0}
                    bound = D(start['reserve_usd'])
                    decision, _ = ledger.classified(result, job, bound)
                    valid, action, why, fatal = decision['strict']
                    charged, reserved = runtime.cost_value(result, bound)
                    emit('attempt_settled', row={**start, **result, 'valid': valid, 'action': action,
                        'reason': why, 'fatal': fatal, 'charged_or_reserved_usd': str(charged),
                        'cost_is_reserve': reserved, 'settled_utc': runtime.now(),
                        **{k: decision[k] for k in ('accepted','accepted_action','acceptance_rule','extraction')}})
                    had_transport |= why == 'transport'
                    if runtime.finite_nonnegative(result.get('retry_after_seconds')):
                        delay = max(delay, result['retry_after_seconds'])
                snapshot()
                if ledger.fatal_reason:
                    state, reason = 'halted_fatal', ledger.fatal_reason
                    snapshot()
                    return state
                if ledger.round_cursor == len(ledger.round_ids):
                    emit('round_completed', round=ledger.round)
                if not ledger.eligible_missing_ids:
                    # Completion needs no additional request or service pause.
                    # Response-level fatal conditions above still take priority.
                    break
                if ledger.needs_pause:
                    if not do_pause(profiles[wave_jobs[-1]['model_key']]):
                        return state
                else:
                    time.sleep(max(delay, 2 if had_transport else .25))
        state, reason = ('eligible_complete' if ledger.missing_ids else 'complete'), None
        snapshot()
        return state
    except (KeyboardInterrupt, runtime.PreflightUnavailable) as exc:
        state, reason = 'interrupted', str(exc) if isinstance(exc, runtime.PreflightUnavailable) else 'KeyboardInterrupt'
        snapshot()
        return state
    except BaseException as exc:
        state = 'halted_fatal'
        reason = str(exc) if isinstance(exc, runtime.FatalRun) else type(exc).__name__
        if key:
            reason = reason.replace(key, '[REDACTED]')
        snapshot()
        return state
    finally:
        key = None


def execute(run: Path) -> str:
    run = Path(run).resolve()
    # Reject an immutable capped directory before creating even a new lock file.
    require(run.parent == HERE and (run / 'manifest.json').is_file(), 'supplement_target')
    require(runtime.read(run / 'manifest.json').get('kind') == contract.KIND, 'supplement_target_kind')
    with runtime.execution_lock(run / contract.LOCK), runtime.execution_lock(run / 'execution.lock'):
        m = contract.validate_manifest(run)
        require(runtime.read(run / 'status.json').get('state') not in contract.TERMINAL, 'terminal_supplement_cannot_resume')
        source = contract.contained_file(m['source_run_relative'])
        with contract.source_locks(source):
            verified = contract.load_bound_source(m)
            return _execute_locked(run, m, verified)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--prepare', action='store_true')
    group.add_argument('--execute', action='store_true')
    parser.add_argument('--source-closure', type=Path, default=HERE / 'ceiling2048_source' / 'operator_closure.json')
    parser.add_argument('--run', type=Path, default=HERE / 'completion_2048_deepseek')
    args = parser.parse_args()
    try:
        if args.prepare:
            prepare(args.source_closure, args.run)
            return 0
        return 0 if execute(args.run) in ('complete','eligible_complete') else 1
    except BaseException as exc:
        print(runtime.compact({'supplement': 'stopped', 'exception_type': type(exc).__name__,
            'errno': getattr(exc, 'errno', None), 'winerror': getattr(exc, 'winerror', None)}), flush=True)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
