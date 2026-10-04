# Stimulus and reporting audit

## Conclusion

The reviewer is correct that the paper does not itself expose enough of its stimuli. The underlying frozen record does contain them: all 44,800 requests in the three published-model cohorts can be reconstructed exactly, joined to their analysis blocks, and matched to the final accepted answers. This is a reporting/packaging omission, not missing acquisition data. No new API calls are required to fix it.

The source check passed for all original request hashes and all terminal-export member hashes. The original 128-token request payload is distinct from the selected physical attempt: 512/2048-token completion layers retain identical messages but change the token ceiling. The export's `request_sha256` is the original frozen 128-token request hash. It must **not** be described as the selected physical attempt's hash.

## Sources

- Frozen generator: `Experiments/luna_revision/protocol.py`.
- Frozen allocation and exact submitted messages: `Experiments/luna_revision/validation/planned.jsonl`.
- Original payload contract: `Experiments/luna_revision/runtime.py`, function `payload`.
- Missing-only 512/2048 payload contracts: `supplement_response.py`, `ceiling2048_response.py`.
- Final three-model record: `Experiments/luna_revision/completion_2048_deepseek/terminal_export/`.
- Main analysis code: `Experiments/luna_revision/analysis.py`.
- Checksums for the audited source files: `audit_manifest.json`.

## What was actually submitted

Each request contains **one user message and no researcher-authored system message**. A hidden provider-side system prompt, if any, is not observable. The user message contains: case identifier; simultaneous-choice description; readiness/certificate/receipt construction; joint receipt probabilities; focal observations; common rules and the supplied conditional probability; partner policy; payoff rule; optional payoff card; expected-score objective; randomized X/Y action mapping; and JSON output instruction. Minimal lotteries omit the social environment and present the action lottery directly.

The original field names READY, certificate, and receipt must remain unchanged in the released stimuli even if the paper uses more accessible explanatory terms. Retrospectively replacing these words would release a stimulus that was not used.

All full-task requests explicitly supply: “conditional on your own receipt, the other receipt arrives with probability 1/2” (R) or “1” (S). Consequently, the original task is **not a clean test of independently deriving this conditional probability**. A new diagnostic should distinguish retrieving this supplied probability, applying the partner's rule, calculating expected score, and choosing an action. It should not call the first step unassisted Bayesian inference.

## Wording 3

The exact complement-policy clauses are:

| Wording | Exact clause |
|---|---|
| 0 | It chooses JOIN if and only if its own receipt did not arrive; otherwise it chooses SAFE. |
| 1 | Its action is SAFE when it has its receipt and JOIN when it does not. |
| 2 | Receipt absent means JOIN; receipt present means SAFE. |
| 3 | The program uses SAFE on receipt delivery and JOIN otherwise. |

On literal reading these four clauses prescribe the same policy. I found no reversed action mapping or erroneous partner-policy statement in wording 3. This is a source audit, not proof that every model interprets them identically. In particular, wording 1 and wording 3 both mention SAFE before JOIN, so action mention order alone is not established as the source of the reversal.

Wording 3 omits an explicit possessive such as "its own receipt" and says "on receipt delivery". Wording 2 also uses abbreviated "Receipt present/absent" phrasing, whereas wordings 0 and 1 state own/its. The intended referent is the programmed partner's receipt in this paragraph. This does not exclude ambiguity for a reader or model, and the audit must not be read as proof that ambiguity has been ruled out.

The four alternatives change the **whole task**. Wording 3 uses “deployment services,” “submissions,” and a compact “Scoring:” sentence, along with different objective and receipt-distribution language. Wording 0 uses modules, wording 1 control stations, wording 2 processing units. There was no isolated randomization of one policy clause. Do not attribute the reversal to a specific word, negation form, domain, or order without a new controlled intervention. `wording_side_by_side.md` and `exact_wording_components.csv` show each exact component side by side.

## Full-task probability grid

The receipt laws R/S remain unchanged at every grid point. The **independent** programmed partner is set to JOIN with probability p in {0.2, 0.35, 0.5, 0.65, 0.8}, independent of readiness, all deliveries, observations, and the focal action. The corresponding JOIN lottery is therefore 10 with probability p and 0 otherwise. The full task explicitly states p in the partner-policy paragraph.

For Luna, blocks 0–63 of the independent task supply p=0.5. `grid_full` adds the other four probabilities to those same blocks. Minimal lotteries and payoff cards use exactly the same block, wording, label mapping, label display order, p and SAFE value. Each block has 10 minimal requests, 40 full requests and 40 card requests: 90 linked requests. Only the first 64 independent blocks enter the capability comparison, not all 2,048 independent blocks. The supplementary cohorts use 32 linked blocks at p=0.5 only, with 18 requests per block. The linkage is an analysis cluster, not a conversation; separate requests have no shared context.

The payoff card appends both the lottery and its expected value. Its complete original text is present in `exact_prompt_examples.md` and the catalogue. It cannot by itself distinguish probability comprehension from arithmetic, salience, or reduced search within the prompt.

## Previously unreported conditions

JOIN rates below combine the two equally weighted encodings. Luna has 1,024 choices per R/S entry (512 independent blocks); supplementary models have 128 (64 blocks). These rows are descriptive reporting of all collected cells, not additional preregistered significance tests.

| Model | Policy / SAFE | R | S | S−R (pp) |
|---|---|---:|---:|---:|
| Luna | responsive / 4 | 40.72% | 72.36% | +31.64 |
| Luna | complement / 6 | 34.18% | 28.22% | −5.96 |
| Qwen | responsive / 4 | 17.19% | 64.06% | +46.88 |
| Qwen | complement / 6 | 13.28% | 40.62% | +27.34 |
| DeepSeek | responsive / 4 | 71.09% | 78.91% | +7.81 |
| DeepSeek | complement / 6 | 20.31% | 19.53% | −0.78 |

`all_programmed_condition_rates.csv` also includes the previously reported policies/payoffs and each encoding. The wording-specific file reports the complete fixed mixture. It is preferable to report the full table and keep the original two confirmatory directional contrasts distinct.

## Minimal-lottery outside-option sensitivity

The reviewer correctly notices descriptive reversals. For Luna, JOIN rates at SAFE=4 versus SAFE=6 are 42.19% vs 26.56% at p=.2; 62.50% vs 54.69% at p=.35; 78.12% vs 79.69% at p=.5; 84.38% vs 90.62% at p=.65; and 81.25% vs 90.62% at p=.8. Each rate has 64 observations in linked blocks. These are finite-sample differences. No claim of statistically established monotonicity violation follows without an explicitly labelled exploratory uncertainty analysis. `capability_grid_rates.csv` and `capability_outside_option_sensitivity.csv` provide every context/probability/payoff cell, including the countervailing and null-looking ones.

## Reproducibility package

This directory contains 3,488 complete user-message templates with only the random case identifier replaced by a placeholder, a 44,800-row mapping to exact case IDs and final outcomes, and the original model request settings. Run `python reconstruct_requests.py --verify` to reconstruct and hash-check **all** original payloads, offline. It requires only the Python standard library. No API key or request-sending code is included.

For an anonymous public supplement, include this directory, the frozen analysis code, the final block/contrast exports, all failed-attempt and acceptance-stage records with provider identifiers checked for privacy, and a README with exact commands and checksums. Link that archive from the paper. A local path alone is not an accessible anonymous archive. Do not claim that the current package includes every raw physical attempt; this audit packages stimuli and final mapping, while acceptance-process auditing is separate.

The main paper should state that reported uncertainty is conditional on these four fixed wording variants. Releasing the full stimuli strengthens auditability, but it does not convert four variants into a sample of all possible language.
