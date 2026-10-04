"""Synthetic, network-free protocol and statistical checks before acquisition."""
from collections import Counter
import hashlib
import json
import math
from pathlib import Path
import protocol
import analysis

HERE = Path(__file__).resolve().parent


def run():
    jobs = protocol.generate()
    assert jobs == protocol.generate()
    assert len(jobs) == 5376
    assert Counter(j['mode'] for j in jobs) == dict.fromkeys(protocol.MODES, 768)
    bases = {j['block_id']: tuple(j['metadata'][k] for k in ('wording', 'mapping', 'display_order', 'actor')) for j in jobs}
    assert len(bases) == len(set(bases.values())) == 32
    assert Counter(j['metadata']['wording'] for j in jobs) == dict.fromkeys(range(4), 1344)
    for j in jobs:
        m = j['metadata']
        original = protocol._original.render(m)[0]['content']
        prefix, footer = original.rsplit('\n\n', 1)
        assert j['messages'][0]['content'].startswith(prefix+'\n\n')
        assert j['messages'] == protocol.render(m, j['mode'])
        if j['mode'] in protocol.ACTION_MODES:
            assert j['messages'][0]['content'].endswith(footer)
            assert j['messages'][0]['content'].count('Decision summary for the current observation') == 1
        else:
            assert j['messages'][0]['content'] == prefix+'\n\n'+protocol.QUESTIONS[j['mode']]
        target_p = .5 if m['law'] == 'R' or m['policy'] == 'independent' else (1. if m['policy'] == 'responsive' else 0.)
        assert m['p'] == target_p
        assert protocol.score(j, j['truth'])['correct'] is True
        assert not protocol.valid_answer(j, None)
        assert not protocol.valid_answer(j, {'other': 0})
        if j['mode'] not in protocol.ACTION_MODES:
            for bad in (True, float('nan'), float('inf'), '0.5'):
                changed = dict(j['truth']); changed[next(iter(changed))] = bad
                assert not protocol.valid_answer(j, changed)
            wrong = {k: 987.0 for k in j['truth']}
            assert protocol.valid_answer(j, wrong)
            assert protocol.score(j, wrong)['correct'] is False
            huge = {k: 10**1000 for k in j['truth']}
            assert protocol.valid_answer(j, huge)
            assert protocol.score(j, huge)['correct'] is False
            assert protocol.score(j, huge)['normalized'] == huge
        else:
            wrong = {'action': 'Y' if j['truth']['action'] == 'X' else 'X'}
            assert protocol.valid_answer(j, wrong)
            assert protocol.score(j, wrong)['correct'] is False
    # Common panel row order and literal placeholders, nested additions only.
    for cell in ('b00-responsive-R-s4-table', 'b17-complement-S-s6-prose'):
        linked = {j['mode']: j for j in jobs if j['metadata']['cell_id'] == cell}
        panels = {mode: protocol.summary_panel(linked[mode]['metadata'], mode).splitlines() for mode in protocol.ACTION_MODES}
        assert all(len(rows) == 5 for rows in panels.values())
        assert panels['U'][0] == panels['A3'][0]
        assert panels['U'][2:] == panels['A1'][2:]
        assert panels['A1'][:2] == panels['A2'][:2]
        assert panels['A1'][3:] == panels['A2'][3:]
        assert panels['A2'][:4] == panels['A3'][:4]
    oracle = {j['id']: j['truth'] for j in jobs}
    perfect = analysis.analyze(jobs, oracle, oracle)
    for panel in ('first', 'final'):
        assert perfect[panel]['valid'] == 5376
        assert all(x['observed_correct_over_planned'] == 1 for x in perfect[panel]['mode_rates'])
        for c in perfect[panel]['aid_contrasts'].values():
            assert c['estimate'] == 0 and c['completion_bounds'] == [0, 0]
            assert c['approximate_simultaneous_95_ci'] is None
            assert c['hoeffding_simultaneous_95_ci'][0] < 0 < c['hoeffding_simultaneous_95_ci'][1]
    # Remove one action. The planned denominator is unchanged and the correct
    # action could be either 0 or 1: both adjacent contrast bounds propagate it.
    missing = dict(oracle)
    target = next(j for j in jobs if j['mode'] == 'A1')
    del missing[target['id']]
    partial = analysis.analyze(jobs, missing, oracle)
    rates = {r['group']['mode']: r for r in partial['first']['mode_rates']}
    assert rates['A1']['planned'] == 768 and rates['A1']['valid'] == 767
    assert rates['A1']['latent_accuracy_completion_bounds'] == [767/768, 1.]
    c = partial['first']['aid_contrasts']['A1_minus_U']
    assert math.isclose(c['completion_bounds'][0], -1/768) and c['completion_bounds'][1] == 0
    assert c['estimate'] is None and c['approximate_simultaneous_95_ci'] is None
    assert partial['first']['aid_contrasts']['A3_minus_A2']['estimate'] == 0
    empty = analysis.analyze(jobs, {}, {})
    assert empty['final']['valid'] == 0
    assert all(x['latent_accuracy_completion_bounds'] == [0, 1] for x in empty['final']['mode_rates'])
    assert all(c['completion_bounds'] == [-1, 1] for c in empty['final']['aid_contrasts'].values())
    # Hand-coded nonzero contrasts, constant within a block but heterogeneous
    # across blocks within every wording stratum, exercise the Welch intervals.
    known = dict(oracle)
    for j in jobs:
        if j['mode'] not in protocol.ACTION_MODES:
            continue
        b = j['metadata']['block_index']
        correct = {'U': b % 3 == 0, 'A1': b % 3 != 2, 'A2': True, 'A3': True}[j['mode']]
        if not correct:
            known[j['id']] = {'action': 'Y' if j['truth']['action'] == 'X' else 'X'}
    effects = analysis.analyze(jobs, known, known)['final']['aid_contrasts']
    assert math.isclose(effects['A1_minus_U']['estimate'], 11/32)
    assert math.isclose(effects['A2_minus_A1']['estimate'], 10/32)
    assert effects['A3_minus_A2']['estimate'] == 0
    for name in ('A1_minus_U', 'A2_minus_A1'):
        c = effects[name]
        assert c['approximate_simultaneous_95_ci'][0] < c['estimate'] < c['approximate_simultaneous_95_ci'][1]
        assert 7 <= c['degrees_of_freedom'] <= 28
    # Check the normal variance formula independently from block vectors.
    c = effects['A1_minus_U']
    vv = []
    for w in range(4):
        values = [int(b % 3 == 1) for b in range(32) if b % 4 == w]
        mean = sum(values)/8
        vv.append(sum((x-mean)**2 for x in values)/7/8/16)
    assert math.isclose(c['standard_error']**2, sum(vv))
    expected_df = sum(vv)**2/sum(x*x/7 for x in vv)
    assert math.isclose(c['degrees_of_freedom'], expected_df)
    # A scientific wrong answer must never be confused with a missing response.
    all_wrong = {j['id']: ({'action': 'Y' if j['truth']['action'] == 'X' else 'X'}
                           if j['mode'] in protocol.ACTION_MODES else {k: 987. for k in j['truth']}) for j in jobs}
    wrong = analysis.analyze(jobs, all_wrong, all_wrong)
    assert wrong['final']['valid'] == 5376
    assert all(r['observed_correct_over_planned'] == 0 for r in wrong['final']['mode_rates'])
    # Outputs must be JSON serializable with no NaN or infinity.
    json.dumps(perfect, allow_nan=False)
    json.dumps(partial, allow_nan=False)
    json.dumps(empty, allow_nan=False)
    json.dumps(effects, allow_nan=False)
    return dict(passed=True, tests=['deterministic allocation', 'all nuisance combinations',
                'original prefix identity', 'truth tables', 'schema independent of correctness',
                'nested summary panel', 'perfect oracle and ceiling handling',
                'partial/fully missing planned denominators', 'hand-computed contrasts',
                'independent variance/df check', 'wrong answers retained', 'finite JSON outputs'],
                scientific_requests=5376, paid_calls=0,
                planned_sha256=hashlib.sha256(''.join(protocol.compact(j)+'\n' for j in jobs).encode()).hexdigest())


if __name__ == '__main__':
    result = run()
    (HERE/'verification.json').write_text(json.dumps(result, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(result, indent=2))
