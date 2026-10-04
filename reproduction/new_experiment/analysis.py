"""Network-free analysis of independently elicited diagnoses and nested aids.

analyze(jobs, first_answers, final_answers): answer maps have logical IDs as keys
and parsed answer dicts as values. Missing/invalid answers are unresolved, never
deleted. This module never parses raw model text or requests additional answers.
"""
from __future__ import annotations
from collections import defaultdict
import json
import math
from pathlib import Path
import statistics
import protocol

ALPHA = .05
FAMILY_SIZE = 3
CONTRASTS = (('A1_minus_U', 'A1', 'U'), ('A2_minus_A1', 'A2', 'A1'), ('A3_minus_A2', 'A3', 'A2'))


def _rate(rows):
    n = len(rows)
    valid = sum(r['score']['valid'] for r in rows)
    correct = sum(r['score']['correct'] is True for r in rows)
    missing = n-valid
    out = dict(planned=n, valid=valid, missing=missing, correct=correct,
               observed_correct_over_planned=correct/n,
               latent_accuracy_completion_bounds=[correct/n, (correct+missing)/n],
               valid_only_accuracy=(correct/valid if valid else None),
               valid_only_accuracy_is_conditional=True)
    keys = sorted({k for r in rows for k in r['score']['components']})
    out['components'] = {k: dict(correct=sum(r['score']['components'].get(k) is True for r in rows),
                                 observed_correct_over_planned=sum(r['score']['components'].get(k) is True for r in rows)/n)
                         for k in keys}
    if rows[0]['job']['mode'] in protocol.ACTION_MODES:
        joins = sum(r['score']['normalized'] is not None and r['score']['normalized'].get('semantic_action') == 'JOIN' for r in rows)
        out.update(join_count=joins, join_over_planned=joins/n,
                   join_completion_bounds=[joins/n, (joins+missing)/n])
        observed_regret = sum((max(10*r['job']['metadata']['p'], r['job']['metadata']['safe']) -
                              (10*r['job']['metadata']['p'] if r['score']['normalized']['semantic_action'] == 'JOIN' else r['job']['metadata']['safe']))
                             for r in rows if r['score']['valid'])
        max_missing_regret = sum(abs(10*r['job']['metadata']['p']-r['job']['metadata']['safe'])
                                 for r in rows if not r['score']['valid'])
        out['mean_expected_regret_completion_bounds'] = [observed_regret/n, (observed_regret+max_missing_regret)/n]
    return out


def _groups(rows, fields):
    grouped = defaultdict(list)
    for row in rows:
        grouped[tuple(row['job']['mode'] if f == 'mode' else row['job']['metadata'][f] for f in fields)].append(row)
    return [dict(group=dict(zip(fields, key)), **_rate(value)) for key, value in sorted(grouped.items())]


def _clip(interval):
    return [max(-1., interval[0]), min(1., interval[1])]


def _contrast(jobs, scores, plus, minus):
    by_cell = defaultdict(dict)
    for job in jobs:
        if job['mode'] in (plus, minus):
            by_cell[job['metadata']['cell_id']][job['mode']] = job
    blocks = defaultdict(list)
    complete = True
    for cell, conditions in by_cell.items():
        if set(conditions) != {plus, minus}:
            raise ValueError('Unbalanced planned cell: '+cell)
        p, m = conditions[plus], conditions[minus]
        a, b = scores[p['id']]['correct'], scores[m['id']]['correct']
        lo = (int(a) if a is not None else 0)-(int(b) if b is not None else 1)
        hi = (int(a) if a is not None else 1)-(int(b) if b is not None else 0)
        if a is None or b is None:
            complete = False
        blocks[p['block_id']].append((lo, hi, p['metadata']['wording']))
    if len(blocks) != 32 or any(len(v) != 24 for v in blocks.values()):
        raise ValueError('Expected 32 complete planned blocks of 24 pairs each.')
    summaries = [dict(block_id=b, wording=vals[0][2], lower=statistics.mean(x[0] for x in vals),
                      upper=statistics.mean(x[1] for x in vals)) for b, vals in sorted(blocks.items())]
    bounds = [statistics.mean(x['lower'] for x in summaries), statistics.mean(x['upper'] for x in summaries)]
    out = dict(plus=plus, minus=minus, block_count=32, paired_cells=768,
               complete_response_pairs=complete, completion_bounds=bounds,
               estimate=(bounds[0] if complete else None), block_differences=summaries,
               approximate_simultaneous_95_ci=None, hoeffding_simultaneous_95_ci=None)
    if not complete:
        out['interval_status'] = 'Suppressed: unresolved responses; retain completion bounds.'
        return out
    # Equal-weight independent blocks, each bounded by [-1,1].
    radius = math.sqrt(2*math.log(2*FAMILY_SIZE/ALPHA)/32)
    out['hoeffding_simultaneous_95_ci'] = _clip([bounds[0]-radius, bounds[0]+radius])
    out['hoeffding_assumption'] = 'Independent blocks; does not require identical distributions.'
    strata = defaultdict(list)
    for row in summaries:
        strata[row['wording']].append(row['lower'])
    if set(strata) != {0, 1, 2, 3} or any(len(v) != 8 for v in strata.values()):
        raise ValueError('Four wording strata with eight blocks required.')
    components = [(1/4)**2*statistics.variance(v)/len(v) for v in strata.values()]
    variance = sum(components)
    out['standard_error'] = math.sqrt(variance)
    out['wording_means'] = {str(w): statistics.mean(v) for w, v in sorted(strata.items())}
    if variance <= 0:
        out['interval_status'] = 'Zero empirical variance: normal interval suppressed; bounded interval retained.'
        return out
    denominator = sum(v*v/7 for v in components)
    df = variance**2/denominator
    from scipy.stats import t
    critical = float(t.ppf(1-ALPHA/(2*FAMILY_SIZE), df))
    delta = critical*math.sqrt(variance)
    out.update(approximate_simultaneous_95_ci=_clip([bounds[0]-delta, bounds[0]+delta]),
               degrees_of_freedom=df, critical_value=critical,
               interval_status='Approximate four-wording-stratum Welch interval; Bonferroni family of three.',
               approximate_assumption='Independent blocks and a sufficiently accurate block-mean approximation; nuisance combinations pooled within each wording.')
    return out


def _panel(jobs, answers):
    unknown = set(answers)-{j['id'] for j in jobs}
    if unknown:
        raise ValueError('Answers contain unplanned IDs.')
    scores = {j['id']: protocol.score(j, answers.get(j['id'])) for j in jobs}
    rows = [dict(job=j, score=scores[j['id']]) for j in jobs]
    return dict(planned=len(jobs), valid=sum(s['valid'] for s in scores.values()),
                mode_rates=_groups(rows, ('mode',)),
                policy_law_rates=_groups(rows, ('mode', 'policy', 'law')),
                wording_policy_law_rates=_groups(rows, ('mode', 'wording', 'policy', 'law')),
                complete_cell_rates=_groups(rows, ('mode', 'wording', 'policy', 'law', 'safe', 'encoding')),
                aid_contrasts={name: _contrast(jobs, scores, plus, minus) for name, plus, minus in CONTRASTS},
                scored_rows=[dict(id=r['job']['id'], block_id=r['job']['block_id'], mode=r['job']['mode'],
                                  metadata=r['job']['metadata'], **r['score']) for r in rows])


def analyze(jobs, first_answers, final_answers):
    if len(jobs) != 5376 or len({j['id'] for j in jobs}) != 5376:
        raise ValueError('Expected the full frozen 5376-job plan, including missing IDs.')
    return dict(schema_version=1, first=_panel(jobs, first_answers), final=_panel(jobs, final_answers),
                estimand='Equal-weight response accuracy over the fixed 24-cell grid and four wordings.',
                primary_family=[x[0] for x in CONTRASTS],
                diagnostics_interpretation='Independent response tasks; no comprehension-conditioned action selection or within-response mechanism inference.',
                acquisition_interpretation='First physical response and final accepted-response policy are separately reported.',
                numerical_tolerance=1e-8)


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--first', type=Path, required=True)
    parser.add_argument('--final', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = analyze(protocol.generate(), json.loads(args.first.read_text(encoding='utf-8')),
                     json.loads(args.final.read_text(encoding='utf-8')))
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False), encoding='utf-8')
