"""Pure replay of missing-only supplemental attempts; never performs I/O or HTTP.

The capped source ledger is an immutable baseline, counted once.  This ledger
deliberately does not use runtime.Ledger's three-attempt scientific policy.
"""
from __future__ import annotations
from collections import Counter, deque
from copy import deepcopy
from decimal import Decimal
from typing import Any, Mapping, Sequence
import math
import runtime
import supplement_response as response

D = Decimal
START_FIELDS = ('id', 'model_key', 'attempt', 'attempt_id', 'request_sha256', 'source_request_sha256', 'reserve_usd', 'utc')


def require(condition: bool, label: str) -> None:
    if not condition:
        raise runtime.FatalRun('supplement:' + label)


def independent_accounting(baseline: Mapping[str, Any], starts: Sequence[dict], settled: Sequence[dict]) -> Decimal:
    by_start = {r['attempt_id']: r for r in starts}
    by_settled = {r['attempt_id']: r for r in settled}
    require(len(by_start) == len(starts) and len(by_settled) == len(settled), 'duplicate_accounting_id')
    require(set(by_settled) <= set(by_start), 'orphan_settlement')
    return D(baseline['occupied_usd']) + sum((D(by_settled[i]['charged_or_reserved_usd'])
        if i in by_settled else D(r['reserve_usd']) for i, r in by_start.items()), D(0))


class ProjectedLedger:
    """Validate exact chronological events, request identity, first-valid locking,
    source-order rounds, cumulative reservations, and shared operational pauses.
    ``accepted`` contains IDs; ``newly_accepted_rows`` holds overlay first valids.
    Raw strict-512 classification and effective answer extraction remain separate.
    """
    def __init__(self, baseline: dict, jobs: Sequence[dict], profiles: Sequence[dict], events: Sequence[dict] = ()):
        self.baseline = deepcopy(baseline)
        self.jobs = list(jobs)
        self.byid = {j['id']: j for j in jobs}
        self.profiles = {p['key']: p for p in profiles}
        require(len(self.byid) == len(jobs), 'duplicate_scientific_id')
        require(set(baseline['accepted_ids']) <= set(self.byid), 'baseline_unknown_accepted')
        require(len(set(baseline['accepted_ids'])) == len(baseline['accepted_ids']), 'baseline_duplicate_accepted')
        require(set(baseline['tries']) == set(self.byid), 'baseline_try_membership')
        require(all(type(n) is int and 0 <= n <= 3 for n in baseline['tries'].values()), 'baseline_try_range')
        self.tries = Counter(baseline['tries'])
        self.accepted = set(baseline['accepted_ids'])
        self.newly_accepted_rows: dict[str, dict] = {}
        self.occupied = D(baseline['occupied_usd'])
        require(self.occupied.is_finite() and 0 <= self.occupied <= runtime.CAP, 'baseline_cost')
        self.fingerprints = deepcopy(baseline['fingerprints'])
        self.starts: list[dict] = []
        self.settled: list[dict] = []
        self.start_map: dict[str, dict] = {}
        self.settled_map: dict[str, dict] = {}
        self.events: list[dict] = []
        self.round = 0
        self.round_ids: list[str] | None = None
        self.round_cursor = 0
        self.pauses = baseline['pauses']
        require(type(self.pauses) is int and 0 <= self.pauses <= 12, 'baseline_pause_count')
        self.pending_pause: dict | None = deepcopy(baseline.get('pending_pause'))
        self.tracker = runtime.PauseTracker()
        t = baseline['tracker']
        require(len(t['recent']) <= 50 and all(type(x) is bool for x in t['recent']), 'baseline_tracker')
        self.tracker.recent = deque(t['recent'], maxlen=50)
        self.tracker.consecutive = t['consecutive']
        self.tracker.trigger = deepcopy(t['trigger'])
        self.tracker.retry_after = t['retry_after']
        self.no_progress = baseline['no_progress']
        require(type(self.no_progress) is int and self.no_progress >= 0, 'baseline_no_progress')
        self.progress_trigger = None if self.no_progress < 50 else {'source_tail': True}
        self.fatal_reason: str | None = None
        for event in events:
            self.apply(event)
        require(self.occupied == independent_accounting(baseline, self.starts, self.settled), 'independent_cost_mismatch')

    @property
    def inflight(self) -> list[dict]:
        return [r for r in self.starts if r['attempt_id'] not in self.settled_map]

    @property
    def needs_pause(self) -> bool:
        return self.pending_pause is not None or self.tracker.trigger is not None or self.progress_trigger is not None

    @property
    def missing_ids(self) -> list[str]:
        return [j['id'] for j in self.jobs if j['id'] not in self.accepted]

    def classified(self, result: dict, job: dict, bound: Decimal) -> tuple[dict, dict]:
        decision = response.classify(result, self.profiles[job['model_key']], job, bound)
        fatal_override = None
        if result.get('worker_error'):
            require(isinstance(result['worker_error'], str), 'worker_error_type')
            fatal_override = 'fatal_worker_exception'
        fingerprints = deepcopy(self.fingerprints)
        profile = self.profiles[job['model_key']]
        obj = runtime.object_or_empty(result.get('response'))
        fp = obj.get('system_fingerprint')
        if obj.get('model') in profile['allowed_models'] and obj.get('provider') == profile['provider_name'] and fp is not None:
            if profile['key'] not in fingerprints:
                fingerprints[profile['key']] = fp
            elif fingerprints[profile['key']] != fp:
                fatal_override = 'fatal_fingerprint_drift'
        if fatal_override:
            decision = {'strict': (False, None, fatal_override, True), 'accepted': False,
                        'accepted_action': None, 'acceptance_rule': None, 'extraction': None}
        return decision, fingerprints

    def _start(self, row: dict) -> None:
        require(not self.fatal_reason and not self.needs_pause, 'start_after_stop_or_pause_trigger')
        require(self.round_ids is not None and self.round_cursor < len(self.round_ids), 'start_outside_round')
        ident = row['id']
        require(ident == self.round_ids[self.round_cursor] and ident not in self.accepted, 'round_order_or_retry_after_valid')
        require(ident in self.byid and row['model_key'] == self.byid[ident]['model_key'], 'unknown_start')
        require(not any(r['id'] == ident for r in self.inflight), 'duplicate_inflight_id')
        attempt = row['attempt']
        require(type(attempt) is int and attempt == self.tries[ident] + 1, 'global_attempt_number')
        require(row['attempt_id'] == ident + '|try' + str(attempt), 'attempt_id')
        require(row['attempt_id'] not in self.start_map, 'duplicate_start')
        body = response.payload(self.profiles[row['model_key']], self.byid[ident])
        bound = response.reserve(self.profiles[row['model_key']], body)
        require(row['source_request_sha256'] == self.byid[ident]['request_sha256'], 'source_request_changed')
        require(row['request_sha256'] == runtime.digest(runtime.compact(body).encode()), 'request_changed')
        require(D(row['reserve_usd']) == bound, 'reserve_changed')
        require(self.occupied + bound <= runtime.CAP, 'start_over_budget')
        require(len(self.inflight) < 16, 'concurrency_exceeded')
        self.starts.append(row)
        self.start_map[row['attempt_id']] = row
        self.tries[ident] = attempt
        self.occupied += bound
        self.round_cursor += 1

    def _settle(self, row: dict) -> None:
        aid = row['attempt_id']
        require(aid in self.start_map and aid not in self.settled_map, 'settlement_identity')
        start = self.start_map[aid]
        require(all(row[k] == start[k] for k in START_FIELDS), 'settlement_start_mismatch')
        require(self.inflight[0]['attempt_id'] == aid, 'settlement_not_issued_order')
        require(all(type(row.get(k)) is bool for k in ('valid', 'accepted', 'fatal', 'cost_is_reserve')), 'settlement_boolean_schema')
        bound = D(start['reserve_usd'])
        if row['reason'] == 'interrupted_unknown':
            require((row['valid'], row['action'], row['fatal'], row['cost_is_reserve']) == (False, None, False, True), 'unknown_schema')
            require(not row.get('response') and not row.get('worker_error'), 'unknown_has_response')
            require((row['accepted'], row['accepted_action'], row['acceptance_rule'], row['extraction']) == (False, None, None, None), 'unknown_acceptance')
            charged, reserved = bound, True
        else:
            expected, fingerprints = self.classified(row, self.byid[row['id']], bound)
            require(expected['strict'] == (row['valid'], row['action'], row['reason'], row['fatal']), 'classification_changed')
            require(all(row[k] == expected[k] for k in ('accepted','accepted_action','acceptance_rule','extraction')), 'extraction_changed')
            charged, reserved = runtime.cost_value(row, bound)
            self.fingerprints = fingerprints
        require(D(row['charged_or_reserved_usd']) == charged and row['cost_is_reserve'] == reserved, 'cost_changed')
        require(charged.is_finite() and charged >= 0, 'invalid_cost')
        if row['accepted']:
            require(row['id'] not in self.accepted and self.tries[row['id']] == row['attempt'], 'retry_after_valid')
            self.accepted.add(row['id'])
            self.newly_accepted_rows[row['id']] = row
            self.no_progress = 0
        else:
            self.no_progress += 1
        if self.no_progress >= 50 and self.progress_trigger is None:
            self.progress_trigger = {'attempt_id': aid, 'consecutive_without_new_valid': self.no_progress}
        self.tracker.observe(row)
        if row['fatal'] and self.fatal_reason is None:
            self.fatal_reason = row['reason']
        self.occupied += charged - bound
        self.settled.append(row)
        self.settled_map[aid] = row

    def apply(self, event: dict) -> None:
        require(type(event.get('sequence')) is int and event['sequence'] == len(self.events) + 1, 'event_sequence')
        require(isinstance(event.get('utc'), str), 'event_timestamp')
        kind = event['event']
        if kind == 'attempt_started':
            self._start(event['row'])
        elif kind == 'attempt_settled':
            self._settle(event['row'])
        elif kind == 'round_started':
            require(not self.fatal_reason and not self.inflight and self.round_ids is None and not self.needs_pause, 'round_start_state')
            require(event['round'] == self.round + 1 and event['ids'] == self.missing_ids and bool(event['ids']), 'round_membership')
            self.round += 1
            self.round_ids = list(event['ids'])
            self.round_cursor = 0
        elif kind == 'round_completed':
            require(self.round_ids is not None and event['round'] == self.round and not self.inflight and self.round_cursor == len(self.round_ids), 'round_incomplete')
            self.round_ids = None
            self.round_cursor = 0
        elif kind == 'operational_pause':
            require(not self.fatal_reason and not self.inflight and self.needs_pause and self.pending_pause is None, 'pause_state')
            require(type(event['pause']) is int and event['pause'] == self.pauses + 1 <= 12, 'pause_count')
            delay = max(self.tracker.retry_after, (60, 120, 240, 300)[min(event['pause'] - 1, 3)])
            require(event['seconds'] == delay and event['settled_count'] == len(self.settled), 'pause_delay_or_position')
            require(event['trigger'] == {'transport': self.tracker.trigger, 'no_progress': self.progress_trigger}, 'pause_trigger')
            require(event['model_key'] in self.profiles and math.isfinite(event['until_unix']), 'pause_metadata')
            self.pauses += 1
            self.pending_pause = event
        elif kind == 'operational_pause_completed':
            require(self.pending_pause is not None and event['pause'] == self.pending_pause['pause'] and event['settled_count'] == len(self.settled), 'pause_completion')
            require(event['completed_unix'] >= self.pending_pause['until_unix'], 'pause_finished_early')
            self.pending_pause = None
            self.tracker.reset()
            self.no_progress = 0
            self.progress_trigger = None
        elif kind == 'preflight':
            require(event.get('kind') in ('account', 'endpoint'), 'preflight_kind')
        else:
            require(False, 'unknown_event')
        self.events.append(event)

    def summary(self) -> dict:
        independent = independent_accounting(self.baseline, self.starts, self.settled)
        require(independent == self.occupied, 'independent_cost_mismatch')
        known = sum((D(r['charged_or_reserved_usd']) for r in self.settled if not r['cost_is_reserve']), D(0))
        return {'source_occupied_usd': self.baseline['occupied_usd'],
                'overlay_known_cost_usd': str(known),
                'overlay_unknown_reserved_usd': str(self.occupied - D(self.baseline['occupied_usd']) - known),
                'cumulative_occupied_usd': str(self.occupied), 'cumulative_cap_usd': str(runtime.CAP),
                'scientific_planned': len(self.jobs), 'science_accepted': len(self.accepted),
                'scientific_missing': len(self.missing_ids), 'overlay_started': len(self.starts),
                'overlay_settled': len(self.settled), 'inflight': len(self.inflight),
                'source_strict_accepted': self.baseline.get('strict_accepted_count', len(self.baseline['accepted_ids'])),
                'source_parsed_accepted': self.baseline.get('parsed_accepted_count', 0),
                'overlay_strict_accepted': sum(r['valid'] for r in self.newly_accepted_rows.values()),
                'overlay_parsed_accepted': sum(not r['valid'] for r in self.newly_accepted_rows.values()),
                'source_physical_started': self.baseline['physical_started'],
                'source_physical_settled': self.baseline['physical_settled'],
                'shared_pauses_used': self.pauses, 'round': self.round,
                'no_progress': self.no_progress, 'fatal_reason': self.fatal_reason}
