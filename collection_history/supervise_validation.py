"""Narrow metadata-interruption supervisor; the frozen runtime is unchanged.
Only --execute calls the paid runner. The adapter never reads response journals.
"""
from pathlib import Path
from datetime import datetime, timezone
import argparse, getpass, hashlib, json, os, time, uuid
import runtime

HERE = Path(__file__).resolve().parent
MANIFEST = 'supervisor_manifest.json'
JOURNAL = 'supervisor.jsonl'
STATUS = 'supervisor_status.json'
LOCK = 'supervisor.lock'
AUDIT_SOURCE = 'supervise_validation_audit.py'
AUDIT_RESULT = 'supervisor_synthetic_audit.json'
MAX_INVOCATIONS = 12
BACKOFF = (30, 60, 120, 240, 300)
REASON = 'endpoint_metadata_unavailable'


def require(value, label):
    if not value:
        raise ValueError(label)


def utc_ns(value):
    parsed = datetime.fromisoformat(value.replace('Z', '+00:00'))
    require(parsed.tzinfo is not None, 'status_time_not_timezone_aware')
    # Avoid float conversion rounding in invocation-boundary checks.
    delta = parsed.astimezone(timezone.utc) - datetime(1970, 1, 1, tzinfo=timezone.utc)
    return (delta.days * 86400 + delta.seconds) * 10**9 + delta.microseconds * 1000


def status_snapshot(path):
    """Read an atomically stable status-file version, never an attempt journal."""
    path = Path(path)
    first = path.stat(); raw = path.read_bytes(); last = path.stat()
    signature = lambda s: (s.st_dev, s.st_ino, s.st_mtime_ns, s.st_size)
    require(signature(first) == signature(last), 'status_changed_during_read')
    status = json.loads(raw.decode('utf-8'))
    require(isinstance(status, dict), 'status_not_object')
    return {'sha256': hashlib.sha256(raw).hexdigest(), 'mtime_ns': last.st_mtime_ns,
            'size': last.st_size, 'file_id': [last.st_dev, last.st_ino], 'status': status}


def match_snapshot(a, b):
    return all(a.get(k) == b.get(k) for k in ('sha256', 'mtime_ns', 'size', 'file_id', 'status'))


def fresh_status(before, after, invocation, ended_ns, manifest_sha):
    if after is None:
        return False
    state = after.get('status', {})
    try:
        status_time = utc_ns(state['utc'])
        return (state.get('manifest_sha256') == manifest_sha
                and type(state.get('pid')) is int and state['pid'] == invocation['pid']
                and before['sha256'] != after['sha256']
                and before['mtime_ns'] < after['mtime_ns']
                and invocation['started_ns'] <= after['mtime_ns'] <= ended_ns
                and invocation['started_ns'] <= status_time <= ended_ns
                and bool(invocation.get('invocation_id')))
    except (KeyError, TypeError, ValueError, OverflowError):
        return False


def fresh_metadata_exit(before, after, invocation, ended_ns, manifest_sha, kind, code):
    """The sole automatic-resume predicate; status bytes alone are insufficient."""
    return (kind == 'system_exit' and type(code) is int and code == 1
            and fresh_status(before, after, invocation, ended_ns, manifest_sha)
            and after['status'].get('state') == 'interrupted'
            and after['status'].get('reason') == REASON)


def validate_history(rows, amendment_sha, manifest_sha):
    """Starts consume the persistent limit; unfinished invocations block restart."""
    starts = []; last_end = None; pending = None
    for row in rows:
        require(row.get('amendment_sha256') == amendment_sha, 'supervisor_journal_manifest_mismatch')
        if row.get('event') == 'invocation_started':
            require(pending is None, 'unfinished_previous_supervisor_invocation')
            require(len(starts) < MAX_INVOCATIONS and row.get('index') == len(starts) + 1,
                    'supervisor_counter_invalid')
            require(row.get('original_manifest_sha256') == manifest_sha, 'supervisor_original_manifest_mismatch')
            require(row.get('invocation_id') and row['invocation_id'] not in {r['invocation_id'] for r in starts},
                    'supervisor_invocation_id_invalid')
            if last_end is not None:
                require(last_end.get('resume_eligible') is True, 'invocation_after_nonresumable_exit')
                require(match_snapshot(row['pre_status'], last_end['post_status']), 'supervisor_status_chain_broken')
                require(row['started_ns'] >= last_end['resume_not_before_ns'], 'supervisor_backoff_not_respected')
            starts.append(row); pending = row
        elif row.get('event') == 'invocation_finished':
            require(pending is not None and row.get('index') == pending['index']
                    and row.get('invocation_id') == pending['invocation_id'], 'supervisor_finish_without_start')
            require(row.get('ended_ns', 0) >= pending['started_ns'], 'supervisor_time_reversed')
            eligible = fresh_metadata_exit(pending['pre_status'], row.get('post_status'), pending,
                                          row['ended_ns'], manifest_sha, row.get('exit_kind'), row.get('exit_code'))
            require(row.get('resume_eligible') is eligible, 'supervisor_resume_evidence_invalid')
            delay = BACKOFF[min(pending['index'] - 1, len(BACKOFF) - 1)] if eligible else None
            require(row.get('backoff_seconds') == delay, 'supervisor_backoff_modified')
            require(row.get('resume_not_before_ns') == (row['ended_ns'] + delay * 10**9 if eligible else None),
                    'supervisor_deadline_modified')
            last_end = row; pending = None
        else:
            raise ValueError('unknown_supervisor_journal_event')
    require(pending is None, 'unfinished_previous_supervisor_invocation')
    return len(starts), last_end


def controller(*, rows, baseline, amendment_sha, manifest_sha, invoke, snapshot,
               emit, report, now_ns, sleep, pid, new_id, verify):
    """Dependency-injected control only; no response classification or editing."""
    count, last = validate_history(rows, amendment_sha, manifest_sha)
    expected = baseline if last is None else last.get('post_status')
    if last is not None and last.get('resume_eligible') is not True:
        report({'state': 'stopped', 'reason': 'previous_nonresumable_exit', 'invocations': count})
        return 'previous_nonresumable_exit'
    require(expected is not None, 'missing_expected_runtime_status')
    require(match_snapshot(snapshot(), expected), 'runtime_status_changed_outside_supervisor')
    deadline = (utc_ns(baseline['status']['utc']) + BACKOFF[0] * 10**9 if last is None
                else last['resume_not_before_ns'])
    while count < MAX_INVOCATIONS:
        verify()
        while now_ns() < deadline:
            report({'state': 'waiting', 'invocations': count, 'resume_not_before_ns': deadline})
            sleep(min(60, max(0, deadline - now_ns()) / 1e9))
        verify()
        before = snapshot()
        require(match_snapshot(before, expected), 'runtime_status_changed_outside_supervisor')
        count += 1
        invocation = {'event': 'invocation_started', 'index': count, 'invocation_id': new_id(),
                      'pid': pid, 'started_ns': now_ns(), 'amendment_sha256': amendment_sha,
                      'original_manifest_sha256': manifest_sha, 'pre_status': before}
        emit(invocation)
        report({'state': 'invocation_running', 'invocations': count,
                'invocation_id': invocation['invocation_id'], 'pid': pid})
        kind = 'returned'; code = None; exception_type = None
        try:
            invoke()
        except SystemExit as exc:
            kind = 'system_exit'; code = exc.code if type(exc.code) is int else None
        except KeyboardInterrupt:
            kind = 'keyboard_interrupt'; exception_type = 'KeyboardInterrupt'
        except BaseException as exc:
            kind = 'unexpected_exception'; exception_type = type(exc).__name__
        ended = now_ns(); after = None; snapshot_error = None
        try:
            after = snapshot()
        except Exception as exc:
            snapshot_error = type(exc).__name__
        eligible = fresh_metadata_exit(before, after, invocation, ended, manifest_sha, kind, code)
        delay = BACKOFF[min(count - 1, len(BACKOFF) - 1)] if eligible else None
        finish = {'event': 'invocation_finished', 'index': count,
                  'invocation_id': invocation['invocation_id'], 'amendment_sha256': amendment_sha,
                  'ended_ns': ended, 'exit_kind': kind, 'exit_code': code,
                  'exception_type': exception_type, 'snapshot_error_type': snapshot_error,
                  'post_status': after, 'resume_eligible': eligible,
                  'backoff_seconds': delay,
                  'resume_not_before_ns': ended + delay * 10**9 if eligible else None}
        emit(finish)
        if not eligible:
            state = after.get('status', {}).get('state') if after else None
            verified_terminal = (kind == 'returned' and state in runtime.TERMINAL
                                 and fresh_status(before, after, invocation, ended, manifest_sha))
            stop = state if verified_terminal else kind
            report({'state': 'stopped', 'reason': stop, 'runtime_state': state,
                    'invocations': count, 'invocation_id': invocation['invocation_id']})
            return stop
        expected = after; deadline = finish['resume_not_before_ns']
    report({'state': 'stopped', 'reason': 'supervisor_invocation_limit', 'invocations': count})
    return 'supervisor_invocation_limit'


class CachedGetpass:
    """Only the module interface used by runtime; the key stays in memory."""
    GetPassWarning = getpass.GetPassWarning

    def __init__(self, original):
        self._original = original
        self._key = None

    def getpass(self, prompt='Password: '):
        if self._key is None:
            self._key = self._original.getpass(prompt)
        return self._key

    def clear(self):
        self._key = None
        self._original = None


def verify_amendment(run):
    run = Path(run)
    manifest = runtime.read(run / MANIFEST)
    body = dict(manifest); claimed = body.pop('amendment_sha256')
    require(runtime.digest(runtime.compact(body).encode()) == claimed, 'supervisor_manifest_modified')
    require(manifest['version'] == 1 and manifest['max_invocations'] == MAX_INVOCATIONS
            and manifest['backoff_seconds'] == list(BACKOFF), 'supervisor_policy_modified')
    require(runtime.sha(run / 'manifest.json') == manifest['original_manifest_file_sha256'],
            'original_manifest_file_changed')
    for name, expected in manifest['supervisor_sources'].items():
        require(runtime.sha(HERE / name) == expected, 'supervisor_source_changed:' + name)
    frozen, _ = runtime.validate(run)
    require(frozen['manifest_sha256'] == manifest['original_manifest_sha256']
            and frozen['sources'] == manifest['original_sources'], 'original_freeze_changed')
    require(manifest['run_path'] == str(run.resolve()), 'supervisor_run_path_changed')
    return manifest


def prepare(run):
    run = Path(run).resolve()
    with runtime.execution_lock(run / LOCK):
        with runtime.execution_lock(run / 'execution.lock'):
            require(not (run / MANIFEST).exists() and not (run / JOURNAL).exists()
                    and not (run / STATUS).exists(), 'supervisor_already_prepared')
            frozen, _ = runtime.validate(run)
            baseline = status_snapshot(run / 'status.json'); state = baseline['status']
            require(state.get('state') == 'interrupted' and state.get('reason') == REASON
                    and state.get('manifest_sha256') == frozen['manifest_sha256'], 'baseline_not_metadata_interruption')
            require(state.get('inflight') == 0 and state.get('physical_started') == state.get('physical_settled'),
                    'baseline_has_unsettled_calls')
            audit = runtime.read(HERE / AUDIT_RESULT)
            require(audit.get('passed') is True and audit.get('model_calls') == 0
                    and audit.get('scientific_journals_read') is False, 'supervisor_audit_not_passed')
            require(audit.get('wrapper_sha256') == runtime.sha(Path(__file__))
                    and audit.get('audit_source_sha256') == runtime.sha(HERE / AUDIT_SOURCE), 'supervisor_audit_stale')
            sources = {name: runtime.sha(HERE / name) for name in (Path(__file__).name, AUDIT_SOURCE, AUDIT_RESULT)}
            amendment = {'version': 1, 'prepared_utc': runtime.now(), 'run_path': str(run),
                         'original_manifest_sha256': frozen['manifest_sha256'],
                         'original_manifest_file_sha256': runtime.sha(run / 'manifest.json'),
                         'original_sources': frozen['sources'], 'supervisor_sources': sources,
                         'baseline_status': baseline, 'manual_resumptions_before_amendment': 3,
                         'confirmed_metadata_interruptions_before_amendment': 4,
                         'max_invocations': MAX_INVOCATIONS, 'backoff_seconds': list(BACKOFF),
                         'journal': JOURNAL, 'status_file': STATUS, 'lock_file': LOCK,
                         'rationale': 'Bound repeated endpoint-metadata availability recovery without changing the frozen scientific runner, requests, attempt limits, first-valid rule, operational pause deadlines or stopping rules.',
                         'automatic_resume_rule': 'Only caught SystemExit(1), exact interrupted/endpoint_metadata_unavailable and fresh status SHA/mtime/UTC with matching manifest and current invocation PID. Invocation IDs bind before/after evidence in the separate journal.',
                         'credential_policy': 'Original hidden-TTY gate and getpass warning remain. Read once through original getpass, cache identical credential in memory only, restore module binding and clear adapter on exit.',
                         'crash_policy': 'A started but unfinished supervisor invocation blocks restart; no automatic repair.',
                         'scientific_changes': False}
            amendment['amendment_sha256'] = runtime.digest(runtime.compact(amendment).encode())
            runtime.save(run / MANIFEST, amendment)
            print(runtime.compact({'status': 'supervisor_prepared', 'amendment_sha256': amendment['amendment_sha256'],
                                   'baseline_science_accepted': state.get('science_accepted'),
                                   'baseline_physical_started': state.get('physical_started'),
                                   'max_invocations': MAX_INVOCATIONS}), flush=True)
            return amendment


def execute(run):
    run = Path(run).resolve()
    with runtime.execution_lock(run / LOCK):
        amendment = verify_amendment(run)
        rows = runtime.lines(run / JOURNAL)
        validate_history(rows, amendment['amendment_sha256'], amendment['original_manifest_sha256'])
        original = runtime.getpass
        cache = CachedGetpass(original)
        def report(value):
            value = {**value, 'utc': runtime.now(), 'pid': os.getpid(),
                     'amendment_sha256': amendment['amendment_sha256']}
            runtime.save(run / STATUS, value)
            print(runtime.compact(value), flush=True)
        runtime.getpass = cache
        try:
            return controller(rows=rows, baseline=amendment['baseline_status'],
                              amendment_sha=amendment['amendment_sha256'], manifest_sha=amendment['original_manifest_sha256'],
                              invoke=lambda: runtime.execute(run), snapshot=lambda: status_snapshot(run / 'status.json'),
                              emit=lambda event: runtime.append(run / JOURNAL, event), report=report,
                              now_ns=time.time_ns, sleep=time.sleep, pid=os.getpid(), new_id=lambda: uuid.uuid4().hex,
                              verify=lambda: verify_amendment(run))
        finally:
            runtime.getpass = original
            cache.clear()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--prepare', action='store_true')
    group.add_argument('--execute', action='store_true')
    parser.add_argument('--run', type=Path, default=HERE / 'validation')
    args = parser.parse_args()
    try:
        if args.prepare:
            prepare(args.run); return 0
        return 0 if execute(args.run) == 'complete' else 1
    except KeyboardInterrupt:
        print(runtime.compact({'supervisor': 'stopped', 'reason': 'KeyboardInterrupt'}), flush=True); return 1
    except BaseException as exc:
        print(runtime.compact({'supervisor': 'stopped', 'exception_type': type(exc).__name__}), flush=True); return 1


if __name__ == '__main__':
    raise SystemExit(main())
