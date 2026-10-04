"""Frozen independent diagnostics and nested decision aids; no network access."""
from __future__ import annotations
from collections import Counter
from itertools import product
from pathlib import Path
import hashlib
import importlib.util
import json
import math
import random

HERE = Path(__file__).resolve().parent
ORIGINAL_SHA256 = '6a7827d78213200b46c2048ab1ca62c9f2659a07f43aee287246851b9c185957'
assert hashlib.sha256((HERE/'original_protocol.py').read_bytes()).hexdigest() == ORIGINAL_SHA256
_spec = importlib.util.spec_from_file_location('receipt_original_protocol', HERE/'original_protocol.py')
_original = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_original)
SEEDS = dict(labels=19417, allocation=5939, analysis=8117)
N_BLOCKS = 32
MODES = ('U', 'D1', 'D2', 'D3', 'A1', 'A2', 'A3')
ACTION_MODES = ('U', 'A1', 'A2', 'A3')
POLICIES = ('responsive', 'independent', 'complement')
QUESTIONS = {
    'D1': ('According to the stated program, what is the partner\'s probability of JOIN '
           'when its own receipt is present and when it is absent? Report the program for both '
           'receipt states, even if one state is incompatible with your current observation. '
           'Return exactly one JSON object with keys "join_if_present" and "join_if_absent", '
           'each with a numerical probability. Do not include any other text.'),
    'D2': ('Given your current observations and the partner\'s stated program, what is the '
           'probability that the partner chooses JOIN? Return exactly one JSON object with key '
           '"partner_join_probability" and a numerical probability. Do not include any other text.'),
    'D3': ('Given your current observations and the partner\'s stated program, what is the '
           'expected score of each of your actions? Return exactly one JSON object with keys '
           '"join_expected_score" and "safe_expected_score", each with a numerical score. '
           'Do not include any other text.'),
}
NUMERIC_KEYS = {
    'D1': ('join_if_present', 'join_if_absent'),
    'D2': ('partner_join_probability',),
    'D3': ('join_expected_score', 'safe_expected_score'),
}


def compact(obj):
    return json.dumps(obj, sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False)


def probability(policy, law):
    if policy == 'independent':
        return .5
    return .5 if law == 'R' else (1. if policy == 'responsive' else 0.)


def summary_panel(m, mode):
    """Same header/rows/location for all arms; content nested, not token matched."""
    p, s = m['p'], m['safe']
    probability_text = 'Follows the stated partner program.' if mode == 'U' else f'{p:g}'
    lottery_text = ('Follows the stated scoring rule.' if mode in ('U', 'A1') else
                    f'10 points with probability {p:g}; 0 points with probability {1-p:g}.')
    expectation_text = ('Not separately summarized.' if mode != 'A3' else
                        f'JOIN = {10*p:g} points; SAFE = {s:g} points.')
    return ('Decision summary for the current observation\n'
            f'Partner JOIN probability: {probability_text}\n'
            f'JOIN score distribution: {lottery_text}\n'
            f'SAFE score distribution: {s:g} points for certain.\n'
            f'Expected scores: {expectation_text}')


def render(m, mode):
    old = _original.render(m)
    assert len(old) == 1 and old[0]['role'] == 'user'
    prefix, footer = old[0]['content'].rsplit('\n\n', 1)
    if mode in ACTION_MODES:
        content = prefix+'\n\n'+summary_panel(m, mode)+'\n\n'+footer
    else:
        content = prefix+'\n\n'+QUESTIONS[mode]
    return [{'role': 'user', 'content': content}]


def truth(m, mode, answer_map):
    if mode in ACTION_MODES:
        optimal = 'JOIN' if 10*m['p'] > m['safe'] else 'SAFE'
        return {'action': next(code for code, action in answer_map.items() if action == optimal)}
    if mode == 'D1':
        present, absent = {'responsive': (1., 0.), 'independent': (.5, .5), 'complement': (0., 1.)}[m['policy']]
        return {'join_if_present': present, 'join_if_absent': absent}
    if mode == 'D2':
        return {'partner_join_probability': m['p']}
    return {'join_expected_score': 10*m['p'], 'safe_expected_score': m['safe']}


def generate():
    rng = random.Random(SEEDS['labels'])
    jobs = []
    for b in range(N_BLOCKS):
        base = dict(block_index=b, wording=b % 4, mapping=(b//4) % 2,
                    display_order=(b//8) % 2, actor=(b//16) % 2,
                    operation=f'case-{rng.getrandbits(48):012x}')
        amap = {'X': 'JOIN', 'Y': 'SAFE'} if base['mapping'] == 0 else {'X': 'SAFE', 'Y': 'JOIN'}
        block_id = f'diagnostic-b{b:02d}'
        for policy, law, safe, encoding in product(POLICIES, ('R', 'S'), (4, 6), ('table', 'prose')):
            m = {**base, 'module': policy, 'policy': policy, 'law': law, 'safe': safe,
                 'encoding': encoding, 'p': probability(policy, law), 'block_id': block_id}
            cell = f'b{b:02d}-{policy}-{law}-s{safe}-{encoding}'
            for mode in MODES:
                metadata = {**m, 'mode': mode, 'cell_id': cell}
                jobs.append(dict(id=f'{cell}-{mode}', block_id=block_id, mode=mode,
                                 metadata=metadata, messages=render(m, mode),
                                 truth=truth(m, mode, amap), answer_map=amap.copy()))
    random.Random(SEEDS['allocation']).shuffle(jobs)
    assert len(jobs) == 5376 and len({j['id'] for j in jobs}) == 5376
    assert Counter(j['mode'] for j in jobs) == dict.fromkeys(MODES, 768)
    return jobs


def valid_answer(job, answer):
    """Schema alone: wrong finite numbers, including outside-domain, are accepted.

    Raw JSON duplicate keys and conflicting extracted objects must be rejected by
    the caller's deterministic parser before passing an ordinary Python dict.
    """
    if type(answer) is not dict:
        return False
    mode = job['mode']
    if mode in ACTION_MODES:
        return set(answer) == {'action'} and type(answer['action']) is str and answer['action'] in ('X', 'Y')
    keys = NUMERIC_KEYS[mode]
    return (set(answer) == set(keys) and
            all(type(answer[k]) is int or (type(answer[k]) is float and math.isfinite(answer[k])) for k in keys))


def score(job, answer):
    if not valid_answer(job, answer):
        return dict(valid=False, correct=None, components={}, normalized=None)
    if job['mode'] in ACTION_MODES:
        correct = answer['action'] == job['truth']['action']
        return dict(valid=True, correct=correct, components={'action': correct},
                    normalized={'action': answer['action'], 'semantic_action': job['answer_map'][answer['action']]})
    # Python integers are finite even when conversion to float would overflow.
    # Every target here lies in [0,10], so large integers are valid wrong values.
    components = {k: (False if type(answer[k]) is int and abs(answer[k]) > 100 else
                      abs(answer[k]-job['truth'][k]) <= 1e-8) for k in NUMERIC_KEYS[job['mode']]}
    return dict(valid=True, correct=all(components.values()), components=components,
                normalized={k: answer[k] for k in NUMERIC_KEYS[job['mode']]})


def freeze(directory=None):
    directory = Path(directory or HERE)
    directory.mkdir(parents=True, exist_ok=True)
    jobs = generate()
    blob = ''.join(compact(j)+'\n' for j in jobs).encode('utf-8')
    plan = dict(n_blocks=N_BLOCKS, n_calls=len(jobs), modes=list(MODES), seeds=SEEDS,
                original_protocol_sha256=ORIGINAL_SHA256,
                planned_sha256=hashlib.sha256(blob).hexdigest(),
                cells_per_block=24, response_tasks_independent=True,
                interpretation='Fixed finite four-wording mixture; no individual mechanism inference.')
    for name, data in [('planned.jsonl', blob), ('plan.json', (compact(plan)+'\n').encode())]:
        path = directory/name
        if path.exists() and path.read_bytes() != data:
            raise ValueError('Refusing to overwrite a different frozen artifact: '+str(path))
        path.write_bytes(data)
    return plan


if __name__ == '__main__':
    print(json.dumps(freeze(), indent=2))
