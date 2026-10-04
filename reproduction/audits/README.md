# Portable post-review audit reproduction

Expected release structure:

```
release/
  original/                    # exact contents of the stimulus package
    request_block_map.csv
    protocol_frozen.py
    frozen_analysis.py
    package_manifest.json
    ...
  audits/                      # exact contents of this directory
    reproduce_audits.py
    acquisition_by_attempt.csv
    acquisition_by_id.csv
    all_parser_selected_responses.jsonl
    answer_extraction_frozen.py
    reference/
    package_manifest.json
```

Run from any directory with Python 3.10+ (standard library only):

```
python audits/reproduce_audits.py
```

Or pass explicit paths:

```
python reproduce_audits.py --original /path/to/original --output /path/to/new_output
```

The script checks package hashes, validates all 44,800 scientific IDs against the frozen original allocation, and independently reconstructs ten CSV summaries from selected choices and physical-attempt lineage. It compares every value against `reference/` with numerical tolerance 2e-10. It writes the recomputed CSVs, all first-attempt block bounds, and `reproduction_checks.json`. No network, API credentials, full repository checkout, raw acquisition journals, SciPy, or new diagnostic-study results are required. The original package's `frozen_analysis.py` is hash-checked as provenance, but the portable bounds are computed independently using exact rational arithmetic.

Reproduced content:

- Acquisition summaries by model, module, condition, and detailed condition: first strict/accepted/extractable rates, failure reasons, retries and selected acceptance stages.
- Actor-specific independent-choice and cross-block pairing baselines within all model, rule, format, SAFE, wording, answer-mapping and display-order strata.
- Both SAFE values for every programmed partner and all tested capability probabilities.
- All 36 original contrast completion ranges using accepted first physical responses only, plus the original family-specific bounded Hoeffding radius. Every planned block is retained; later answers never fill failed first responses.
- Deterministic replay of all 1,012 selected extracted responses from their included text and answer maps.

Limits of this package:

1. It verifies numerical reconstruction from the exported records; it does not independently authenticate the service's original responses. The full hash-bound raw-journal provenance is retained in the research archive.
2. `acquisition_by_id.csv` supplies the separately audited retrospective first-response extractability flag. Reproducing that aggregation does not re-read all raw failed first-response text. Contemporaneous first acceptance, retries and all 36 bounds are reconstructed from `acquisition_by_attempt.csv`.
3. Parser replay is a reproducibility check, not independent human validation or a zero-error-rate estimate.
4. All these additions are post-review sensitivity/descriptive analyses. Completion ranges are not confidence intervals. The confidence enclosures require independent latent block vectors and well-defined binary first-attempt actions, even for failed responses. They do not require missing at random; family-wise coverage applies within each original family, not jointly across all 36 comparisons.
5. The baseline uses the same observed actor marginals; agreement does not independently establish a coordination mechanism or population welfare effect.
