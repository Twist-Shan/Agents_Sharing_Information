# Shared-information choice experiment: offline reproduction materials

This package contains the exact stimuli and selected choices for the three cohorts reported in the paper: 38,016 primary-model choices and 3,392 choices per supplementary model. It contains no credentials, account records, or request-sending code. Every script runs without network access.

## Reconstruct exact stimuli (Python standard library only)

```
python reconstruct_requests.py --verify
python reconstruct_requests.py --id "luna|independent-b0000-qR-etable-s4-a0-p0.5"
python reconstruct_requests.py --output reconstructed_original128.jsonl
```

The 3,488 templates replace only the random case identifier with `{operation}`. `request_block_map.csv` restores this value and associates each exact user message with its logical ID, block, condition, expected action, final selected answer, acceptance rule, and selected physical-attempt ID. `request_options.json` provides the original non-secret API settings. There was one user message and no researcher-authored system message. Every reconstructed message and original payload is checked against its SHA-256 hash.

`request_sha256` in the original terminal export denotes the **original frozen 128-token payload**, also explicitly named `frozen128_request_sha256` in the mapping. It is not the payload hash of every later retry. The 512/2048-token stages preserved the message and changed the token allowance; `selected_request_token_ceiling` records the selected stage. A choice's `selected_attempt_id` is the key for joining the separate acquisition audit, which is outside this stimulus package. This package does not purport to contain raw text from every failed physical attempt.

## Recompute all 36 planned contrasts and their paired uncertainty

Requires SciPy; verified with Python 3, SciPy 1.13.1. The included frozen analysis also uses NumPy (verified 1.26.4), but the independent recomputation below does not import it.

```
python recompute_results.py
```

The script first verifies all packaged source checksums and reconstructs all 44,800 payloads. It then reconstructs individual paired block contributions from final selected choices, independently of `frozen_analysis.py`. For each of 12 contrasts per model, it compares the point estimate, block count, stratified standard error, Welch degrees of freedom, family-adjusted approximate interval, and Hoeffding interval against the original terminal export. Outputs are written to `recomputed/`. Floating-point agreement is checked within 2e-10. No new contrast is silently promoted to confirmatory status.

`terminal_block_contributions.csv` contains the independently reconstructed contributions. Every row names its model, contrast, analysis block, nuisance stratum, and scalar paired difference. The seven primary contrasts share a family; the two directional and three capability contrasts form their original separate families. Capability contrasts use wording strata; other contrasts use the original balanced nuisance strata. Reusing one block across different outcomes does not imply those outcomes are independent.

`all_programmed_condition_rates*.csv` adds complete descriptive condition reporting, including responsive/SAFE=4 and complement/SAFE=6. `capability_grid_rates.csv` and `capability_outside_option_sensitivity.csv` show the full probability-by-SAFE grid. These additional descriptives are not newly preregistered significance tests.

## Design details

`exact_prompt_examples.md` contains verbatim full messages; `wording_side_by_side.md` and `exact_wording_components.csv` expose the four wording variants. `protocol_frozen.py` preserves the original generator. Full-task prompts explicitly supply the conditional probability of the partner's receipt; independent-partner grid conditions additionally state its JOIN probability. The grid changes that programmed action probability, not the receipt law. `AUDIT.md` explains these interpretation boundaries and the linkage among minimal/full/card requests.

These materials reproduce the reported finite fixed-wording sample and its accepted-response distribution. Reproducing numerical calculations does not validate independent-response assumptions, provider stationarity, universal model claims, or an identified cognitive mechanism. No public archive URL is asserted by this local package.
