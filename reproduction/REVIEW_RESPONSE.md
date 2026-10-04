# Response to reviewer concerns W1–W5

The revision retains the identical-lottery control as its central contribution: the same information change has positive, zero, or negative payoff implications under specified partner policies. It does not claim the first decomposition of agent reasoning, a general coordination mechanism, or universal model behavior. This local supplement accompanies the revised manuscript; it is not a claim of public release.

## W1. Complete stimuli and numerical reproducibility

The manuscript now gives verbatim task examples, policy clauses, payoff presentations, and generation rules. `original/` contains all stimulus templates, all 44,800 request-to-block mappings and selected choices, exact request options, and frozen generation and analysis code. `wording_side_by_side.md` exposes the wording differences directly. The probability grid changes the independent partner's action probability, not confirmation delivery. No researcher-authored system message was submitted. Offline scripts reconstruct every request and all 36 original contrasts. The wording reversal remains visible; the revision does not certify the variants as psychologically equivalent or explain the reversal away.

## W2. Adaptation versus correct rule reports and decisions

A new study was fixed after review and before collection: 5,376 separate requests in 32 balanced blocks, using the primary model with uniform 512-token limits and reasoning effort `none`. Three independently elicited diagnostics ask for the partner's conditional rule, its current JOIN probability, or expected payoffs. Four action conditions are sampled separately. Diagnostics never filter action responses.

Rule reports are correct in all 768 cases; current-probability reports are correct in 727, but JOIN-payoff reports in only 347. All reported SAFE payoffs are correct. These descriptive differences identify a gap between elicitation tasks, not an observed reasoning sequence or proof that an erroneous action internally represented the correct rule. The manuscript now emphasizes deterministic, strictly dominated choices under joint delivery and preserves the asymmetric, wording-dependent directional result. The exact error frequencies are supplied without a new mechanism claim.

## W3. Incremental payoff assistance

The new action conditions retain the full task and a common panel layout. They successively supply the partner's action probability, its payoff lottery, and expected payoffs. The three fixed adjacent accuracy differences are +8.72, +1.82, and +27.60 percentage points. Approximate family-adjusted intervals exclude zero for the first and third, while the middle increment is inconclusive. All conservative Hoeffding intervals include zero; inference treats the 32 blocks, not the 768 condition pairs, as the independent units. Results therefore support the usefulness of explicit expected payoffs under the stated approximate analysis, without identifying arithmetic, attention, or ambiguity as the unique cause. Every condition and wording is retained in `new_experiment/exports/`.

## W4. Conditional pair outcomes and an independent-choice benchmark

The manuscript describes the paired requests as one-shot conditional choices without message exchange, sampled delivery trajectories, or feedback. The added benchmark preserves separate actor marginals within wording, label-mapping, and order strata. It reproduces increases in joint participation and mismatch in all four primary cells and the table/high-SAFE payoff decline. Payoff signs do not match in every cell. The benchmark is calculated from the same observations, is descriptive, and is not an independent replication or test of coordination. The payoff decomposition concerns the evaluated information state, not ex ante welfare across delivery states. Stratum data and cross-block pairings are included in `audits/`.

## W5. Acquisition histories, extraction, and missing first responses

The supplement reports first-attempt strict validity and acceptance, failures, retries, and final stages by condition. DeepSeek's first acceptance varies substantially by task; complete final coverage does not remove acquisition selection. All 1,012 selected extracted responses and the deterministic parser are provided for replay; the AI-assisted inspection is not a human validation or population error-rate estimate.

A retrospective sensitivity retains every planned block, uses only accepted first physical responses, and assigns arbitrary binary values to missing responses. All 36 original contrasts are archived. The three primary positive identical-lottery differences retain positive conservative lower bounds under the stated latent-choice and independent-block assumptions; the weakest lower bound is only 0.10 percentage points. The table-format joint-participation bound no longer excludes zero. No result-dependent sample extension or new test family is introduced.

The new study has complete final coverage and 19 missing first acquisition attempts: 16 local interruptions before dispatch and three transport failures. These remain distinct from model refusals. A separate offline audit independently reconstructs scoring and intervals without importing the experiment's analysis implementation. Commands and the verified software environment appear in `README.md`.
