"""Independent stored-coefficient prediction check; standard library only.
Reads immutable terminal exports, never imports the original analysis or runner.
"""
from pathlib import Path
from collections import Counter, defaultdict
import argparse, csv, hashlib, json, math, re

FEATURES = {
    'payoff_only': ['intercept', '10p-safe'],
    'payoff_and_context': ['intercept', '10p-safe', 'full', 'card', 'S', 'prose',
                           'S*prose', 'full*(10p-safe)', 'card*(10p-safe)'],
}
TOLERANCE = {'absolute': 2e-12, 'relative': 2e-11}
METHOD = (
    'Independent arithmetic from terminal logical_outcomes.csv and the stored coefficients in analysis.json. '
    'The checker imports neither analysis.py nor fitting software and performs no refit. '
    'Only the first 64 full-cohort or 32 secondary linked blocks are used, including their core p=.5 rows. '
    'Wordings 0/1 train and 2/3 test; inverse cell counts equalize context x p x SAFE. '
    'Training weights sum to training N; test weights sum to one and are renormalized within context. '
    'Prediction logits are clipped to [-35,35], matching the declared numerical implementation. '
    'The separately reported training objective uses stable softplus and ridge coefficient 1 on nonintercepts; '
    'its gradient uses [-50,50] sigmoid clipping. Gradient magnitude is diagnostic only, with no new convergence gate. '
    'Missing anywhere in a cohort suppresses all prediction metrics; recorded failed fits are preserved, not refitted. '
    'This checks arithmetic and exported design consistency, not optimization success, stationarity or scientific assumptions.'
)


def require(value, label):
    if not value:
        raise ValueError('independent_prediction:' + label)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def encoded(value):
    return (json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + '\n').encode('utf-8')


def boolean(value):
    require(value in (True, False, 'True', 'False', 'true', 'false'), 'invalid_boolean')
    return value in (True, 'True', 'true')


def block(row):
    match = re.fullmatch(r'(free|independent|responsive|complement)-(\d{4})', row['block_id'])
    require(match is not None, 'block_id')
    return int(match.group(2))


def reconstruct(rows, allocation):
    require(allocation in ('full', 'cross'), 'allocation')
    n = 64 if allocation == 'full' else 32
    grid = (.2, .35, .5, .65, .8) if allocation == 'full' else (.5,)
    observed = {}
    nuisance = {}
    excluded = 0
    for row in rows:
        module = row['module']
        if module not in ('minimal', 'grid_full', 'payoff_card', 'independent'):
            continue
        b = block(row)
        if module == 'independent' and b >= n:
            excluded += 1
            continue
        require(0 <= b < n and row['block_id'] == f'independent-{b:04d}', 'linked_block_range')
        p = float(row['p']); safe = int(row['safe']); w = int(row['wording'])
        context = {'minimal': 'minimal', 'payoff_card': 'card'}.get(module, 'full')
        law = row['law']; encoding = row['encoding']
        require(p in grid and safe in (4, 6) and w in (0, 1, 2, 3), 'linked_condition')
        require(row['analysis_split'] == ('train' if w < 2 else 'test'), 'wording_split')
        require(module != 'independent' or p == .5, 'core_probability')
        require(module != 'grid_full' or p != .5, 'grid_probability')
        require((law, encoding) == ('none', 'none') if context == 'minimal'
                else law in ('R', 'S') and encoding in ('table', 'prose'), 'context_condition')
        fields = (w, int(row['mapping']), int(row['display_order']), int(row['actor']))
        require(b not in nuisance or nuisance[b] == fields, 'linked_nuisance_mismatch')
        nuisance[b] = fields
        valid = boolean(row['valid'])
        require(row['action'] in ('JOIN', 'SAFE') if valid else row['action'] in ('', None), 'action_validity')
        key = (b, context, p, safe, law, encoding)
        require(key not in observed, 'duplicate_linked_condition')
        observed[key] = {'block': b, 'context': context, 'p': p, 'safe': safe, 'law': law,
                         'encoding': encoding, 'wording': w, 'valid': valid,
                         'y': int(row['action'] == 'JOIN') if valid else None}
    expected = []
    for b in range(n):
        for p in grid:
            for safe in (4, 6):
                expected.append((b, 'minimal', p, safe, 'none', 'none'))
                for context in ('full', 'card'):
                    expected.extend((b, context, p, safe, law, encoding)
                                    for law in ('R', 'S') for encoding in ('table', 'prose'))
    require(set(observed) == set(expected), 'incomplete_or_extra_capability_design')
    require(Counter(v[0] for v in nuisance.values()) == Counter({w: n//4 for w in range(4)}), 'wording_block_balance')
    obs = [observed[key] for key in expected]
    return obs, {'linked_blocks': n, 'p_grid': list(grid), 'capability_observations': len(obs),
                 'linked_full_at_half_rows': n*8, 'excluded_unlinked_core_rows': excluded}


def features(row, enriched):
    x = 10*row['p'] - row['safe']
    if not enriched:
        return [1., x]
    full = float(row['context'] == 'full'); card = float(row['context'] == 'card')
    law = float(row['law'] == 'S'); prose = float(row['encoding'] == 'prose')
    return [1., x, full, card, law, prose, law*prose, full*x, card*x]


def weights(rows, total=1.):
    counts = Counter((r['context'], r['p'], r['safe']) for r in rows)
    require(bool(counts), 'empty_weighting_cells')
    return [total/(len(counts)*counts[r['context'], r['p'], r['safe']]) for r in rows]


def probability(z, limit):
    z = max(-limit, min(limit, z))
    return 1/(1+math.exp(-z))


def score(rows, coefficients, enriched):
    pp = [probability(math.fsum(a*b for a, b in zip(features(r, enriched), coefficients)), 35.) for r in rows]
    ww = weights(rows)
    losses = [-r['y']*math.log(p)-(1-r['y'])*math.log1p(-p) for r, p in zip(rows, pp)]
    briers = [(r['y']-p)**2 for r, p in zip(rows, pp)]
    return {'n': len(rows), 'log_loss': math.fsum(w*x for w, x in zip(ww, losses)),
            'brier': math.fsum(w*x for w, x in zip(ww, briers))}


def training_diagnostic(rows, coefficients, enriched):
    ww = weights(rows, len(rows)); xs = [features(r, enriched) for r in rows]
    z = [math.fsum(a*b for a, b in zip(x, coefficients)) for x in xs]
    residual = [w*(probability(t, 50.)-r['y']) for w, t, r in zip(ww, z, rows)]
    gradient = [math.fsum(x[k]*e for x, e in zip(xs, residual)) + (coefficients[k] if k else 0.)
                for k in range(len(coefficients))]
    objective = math.fsum(w*(max(t, 0.)+math.log1p(math.exp(-abs(t)))-r['y']*t)
                          for w, t, r in zip(ww, z, rows)) + .5*math.fsum(b*b for b in coefficients[1:])
    return {'ridge_objective': objective, 'gradient': gradient,
            'gradient_infinity_norm': max(abs(g) for g in gradient),
            'gradient_is_pass_fail_gate': False, 'refitted': False}


def check_cohort(rows, cohort):
    result = cohort['analysis']; prediction = result['prediction']; errors = []
    obs, design = reconstruct(rows, cohort['allocationprofile'])
    train = [r for r in obs if r['wording'] < 2]; test = [r for r in obs if r['wording'] >= 2]
    valid_count = sum(boolean(r['valid']) for r in rows)
    require(result['scientific_planned'] == len(rows) and result['scientific_valid'] == valid_count, 'cohort_counts')
    complete = valid_count == len(rows)
    require(result['status'] == ('complete' if complete else 'incomplete_keep_all_planned_bounds'), 'cohort_completion_label')
    output = {**design, 'training_n': len(train), 'test_n': len(test), 'scientific_valid': valid_count,
              'scientific_planned': len(rows), 'stored_prediction_status': prediction['status'], 'models': {}}
    if not complete:
        require(prediction['status'] == 'not_computed_missing_planned_responses' and not prediction.get('models'), 'missing_fit_not_suppressed')
        output.update(status='verified_prediction_not_computed_for_incomplete_cohort', passed=True, errors=[])
        return output
    require(prediction['status'] == 'fixed_heldout_wording_prediction', 'prediction_status')
    require(prediction['train_wordings'] == [0, 1] and prediction['test_wordings'] == [2, 3], 'reported_split')
    require(prediction['feature_sets'] == FEATURES, 'reported_feature_sets')
    require(prediction['training_n'] == len(train) and prediction['test_n'] == len(test), 'reported_sample_sizes')
    require(set(prediction['models']) == set(FEATURES), 'model_inventory')
    def compare(name, actual, reported):
        require(isinstance(reported, (int, float)) and math.isfinite(reported), 'nonfinite_reported_metric')
        if not math.isclose(actual, reported, abs_tol=TOLERANCE['absolute'], rel_tol=TOLERANCE['relative']):
            errors.append({'metric': name, 'recomputed': actual, 'reported': reported})
    for label, fit in prediction['models'].items():
        if fit['status'] == 'optimization_failed':
            require('coefficients' not in fit and 'test_log_loss' not in fit and 'test_brier' not in fit, 'failed_fit_has_metrics')
            output['models'][label] = {'status': 'recorded_optimization_failure_not_refitted', 'message': fit.get('message'),
                                        'numerical_metrics_checked': False}
            continue
        require(fit['status'] == 'fit', 'fit_status')
        beta = fit['coefficients']; enriched = label == 'payoff_and_context'
        require(len(beta) == len(FEATURES[label]) and all(isinstance(x, (int, float)) and math.isfinite(x) for x in beta), 'coefficients')
        overall = score(test, beta, enriched)
        compare(label+'.log_loss', overall['log_loss'], fit['test_log_loss'])
        compare(label+'.brier', overall['brier'], fit['test_brier'])
        contexts = {r['context']: r for r in fit['by_context']}
        require(len(fit['by_context']) == 3 and set(contexts) == {'minimal', 'full', 'card'}, 'context_metric_inventory')
        by_context = []
        for context in ('minimal', 'full', 'card'):
            calculated = score([r for r in test if r['context'] == context], beta, enriched)
            require(contexts[context]['n'] == calculated['n'], 'context_metric_n')
            for metric in ('log_loss', 'brier'):
                compare(label+'.'+context+'.'+metric, calculated[metric], contexts[context][metric])
            by_context.append({'context': context, **calculated})
        output['models'][label] = {'status': 'stored_coefficients_checked', 'coefficients': beta,
                                  'test': overall, 'by_context': by_context,
                                  'training_diagnostic': training_diagnostic(train, beta, enriched),
                                  'numerical_metrics_checked': True}
    output.update(status='checked', passed=not errors, errors=errors)
    return output


def report_run(export_dir, output=None):
    export_dir = Path(export_dir).resolve()
    paths = {name: export_dir/name for name in ('analysis.json', 'logical_outcomes.csv', 'export_manifest.json')}
    hashes = {name: sha(path) for name, path in paths.items()}
    manifest = json.loads(paths['export_manifest.json'].read_text(encoding='utf-8'))
    require(manifest.get('status') == 'passed', 'export_not_verified')
    require(all(manifest['files_sha256'].get(n) == hashes[n] for n in ('analysis.json', 'logical_outcomes.csv')), 'export_hash_binding')
    analysis = json.loads(paths['analysis.json'].read_text(encoding='utf-8'))
    require(analysis['manifest_sha256'] == manifest['manifest_sha256'], 'manifest_identity')
    with paths['logical_outcomes.csv'].open(encoding='utf-8', newline='') as handle:
        rows = list(csv.DictReader(handle))
    require(len({r['runtime_id'] for r in rows}) == len(rows), 'duplicate_runtime_id')
    require(set(r['model_key'] for r in rows) == set(analysis['cohorts']), 'cohort_inventory')
    results = {}
    for key, cohort in analysis['cohorts'].items():
        subset = [r for r in rows if r['model_key'] == key]
        require(len(subset) == (38016 if cohort['allocationprofile'] == 'full' else 3392), 'fixed_cohort_allocation')
        results[key] = check_cohort(subset, cohort)
    require(all(sha(path) == hashes[name] for name, path in paths.items()), 'inputs_changed')
    report = {'status': 'independent_stored_coefficient_prediction_check', 'passed': all(r['passed'] for r in results.values()),
              'manifest_sha256': manifest['manifest_sha256'], 'execution_layer': analysis.get('execution_layer'),
              'input_sha256': hashes, 'checker_sha256': sha(__file__), 'method': METHOD,
              'comparison_tolerance': TOLERANCE, 'cohorts': results, 'model_calls': 0, 'refits': 0}
    target = Path(output).resolve() if output else export_dir.parent/'independent_prediction_check.json'
    require(not target.exists() and not target.is_relative_to(export_dir), 'output_must_be_new_outside_export')
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open('xb') as handle:
        handle.write(encoded(report))
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--export', type=Path, required=True)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    answer = report_run(args.export, args.output)
    print(json.dumps({'passed': answer['passed'], 'cohorts': list(answer['cohorts']), 'model_calls': 0}))
    raise SystemExit(0 if answer['passed'] else 1)
