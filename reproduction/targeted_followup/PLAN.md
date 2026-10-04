# Targeted review follow-up: prospective analysis and acquisition plan

This file is frozen before any study responses. The prior occupied budget is $43.68265773418 including unknown costs at reservation bounds; the cumulative cap is $50. All calls use OpenRouter openai/gpt-6-luna, OpenAI provider only, reasoning effort none, 512 output tokens, no API seed or temperature override. Metadata and responses must verify identity, zero reasoning tokens, and cost bounds. No new model is included.

## Allocation and questions

Exactly 5,632 scientific requests plus one compatibility request. Every request is independent. No significance-dependent extension, correctness-based retries, or diagnostic filtering. The first schema-valid answer is retained even when wrong. Up to three identical attempts handle operational/schema failures. All issued attempts, missing outcomes, known costs and unknown reserves are retained. Fatal policy or identity failure stops issuing requests and drains the current wave. Routine service pauses and remaining budget are enforced by runtime.py.

1. Framing/core replication: 128 independent blocks, crossing three frames (exact original, matched partner, matched non-partner device), R/S, SAFE=4/6 and table/prose. Total 3,072. Four original wording variants, label mapping, display order and actor are balanced. The original arm is a fresh exact-template replication of the fixed independent partner with p=0.5. The matched arms both use TAKE/SAFE, identical numeric information and paragraph structure; agency/role substitutions distinguish a programmed partner from a sensor. This estimates the effect of these particular descriptions, not an abstract causal effect of social cognition. It does not compare the original arm to the device arm as a matched contrast.
2. Referent edit: 64 independent blocks restricted to original wording 3, crossing original versus 'partner\'s own receipt', R/S, SAFE=4/6 and table/prose. Total 1,024. Mapping, order and actor balanced. The only edited text is the complement-rule clause recorded in protocol.py. Tests whether explicitly identifying whose receipt changes the protocol response; no claim that any ambiguity is its unique mechanism.
3. Explicit-probability payoff transfer: 32 blocks crossing eight fixed payoff recipes, three contexts (full R, full S, stripped lottery), and two independent response tasks (action, two expected scores). Total 1,536. Four original wordings, mapping, order and table/prose fully crossed; actor A fixed. Two anchor recipes use p=0.5, 10/0 payoffs and SAFE=4/6. Six novel recipes vary p and positive/negative scores, with no ties. All full-context prompts explicitly give the current partner action probability; no expected value is supplied. Lottery contexts are shorter by design: the comparison tests context dependence, not a pure length-controlled mechanism. Novel recipes are held-out from earlier studies, not from model pretraining.

Identifier seed 27183, schedule seed 104729, reserved analysis seed 65537; none date-derived. Fixed schedule interleaves studies and conditions. No inference is based on a diagnostic response preceding an action because requests are independent.

## Eight primary comparisons, one family

1-4: S minus R JOIN probability in the exact original frame, separately for SAFE=4/6 and table/prose.
5: (S-R in matched partner) minus (S-R in matched device), averaged equally over the four SAFE/format combinations.
6: (S-R with explicit own referent) minus (S-R with original clause), equally averaged over the four SAFE/format combinations.
7: Both-payoffs-correct rate in stripped lottery minus the mean of full R and full S, equally averaged over all eight recipes.
8: Both-payoffs-correct rate in full S minus full R, equally averaged over all eight recipes.

All comparisons are two-sided. The independent analysis unit is the matched block. For studies with multiple wordings, use equal wording-stratum weights, estimated variance sum(w_h^2*s_h^2/n_h), and Welch-Satterthwaite degrees of freedom. The referent experiment has one wording stratum. Report point estimates, approximate t intervals with Bonferroni family size 8, and bounded Hoeffding intervals using the same family. Block support widths are 2 for contrasts 1-4 and 7-8, and 4 for interactions 5-6. No significance-only filtering, equivalence claim from a null result, or pooling with previous experimental families. The small diagnostic experiments can have wide finite-sample bounds.

Missing outcomes are never imputed as observed choices. Primary observed estimates require all component outcomes in a block; report the number retained. Independently derive adversarial point-estimate bounds by assigning each missing primitive binary outcome 0/1 according to its coefficient; show both first-attempt and final-answer bounds. Complete-case intervals are labeled conditional if any missing block. Collection must be terminal before outcome analysis.

## Complete descriptive reporting

Publish every framing/referent cell's JOIN rate, accuracy and mean expected regret (optimal expected score minus chosen expected score), plus both-payoff accuracy, action accuracy and regret by transfer recipe/context. Show all four wording variants where available. Report the six novel recipes separately as a prespecified descriptive subset, without another primary test family.

Retain all numeric errors. For full contexts, compare wrong JOIN reports with correct expected value, receipt-discounted whole value q*EV, receipt-discounted success probability q*p, prior-discounted whole value 0.2*EV and prior-discounted success probability 0.2*p. These are descriptive matches within 1e-8, may overlap, and never identify hidden reasoning. q=0.5 in R and 1 in S. Full R/S contrasts share the same supplied action probability and payoffs.

## Scope

The studies concern independent one-step model choices under described incentives. The agent-pair experiment contains simultaneous independent submissions, not communication, learning or negotiated coordination. Expected regret is an objective consequence under the instructed expected-score objective, not a claim about human risk preference. The repository contains implementation details; the manuscript must retain design, allocation, exclusions, uncertainty and limitations necessary for assessment.
