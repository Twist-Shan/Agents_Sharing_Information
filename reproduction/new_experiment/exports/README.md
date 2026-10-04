# Independent diagnostics and nested aid experiment: offline export

The experiment contains 5,376 planned requests. This export was generated only
after terminal status `complete` and successful acquisition of the
execution OS lock. Every frozen source hash, request hash, recorded response
classification, status count, journal hash, and terminal ledger was replayed.
No API calls were made by this exporter.

## Reproduce

Use the archived new_experiment directory containing protocol.py,
original_protocol.py, analysis.py, runtime.py, export_results.py, profiles.json,
PLAN.md, and the `run_v2` acquisition directory. The analysis requires Python
with SciPy installed. From that directory run:

```
python verify.py
python export_results.py --run run_v2 --output reproduced_exports
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

Frozen manifest: `e0fef9f4f24caf21b865833fffa706a745f789e1977dbb1ab936c1901caeb8ce`.
