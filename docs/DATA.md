# Scientific data and coverage

## Original experiment

`reproduction/original/` contains 3,488 exact stimulus templates, mappings for 44,800 requests, final selected choices, request options, block contributions, and stored contrasts. The primary model contributes 38,016 choices; Qwen and DeepSeek each contribute 3,392. Frozen protocol and analysis code are preserved.

`reproduction/audits/` includes request-level and physical-attempt acquisition tables, reference sensitivity results, and raw text for all 1,012 selected extracted responses. It does not contain every raw failed historical response. First-attempt extractability is an audited input field, not a new reinterpretation of missing text.

## Independent diagnostic experiment

`reproduction/new_experiment/run_v2/` contains the fixed schedule, manifest, scientific response journal, acquisition starts and settlements, operational events, and terminal accounting. `exports/` retains first and final outcomes, all condition summaries, contrasts, and lineage.

The allocation is 32 blocks × 24 task cells × 7 response conditions. All final responses remain, including valid wrong answers. Sixteen local interruptions before dispatch and three transport failures are retained in first-attempt records; these are not incorrect model answers. Recovery did not change scientific messages or replace accepted answers.

Historical identities, routes, settings, and prices record collection conditions; they are not a live model catalogue.

## Targeted follow-up

`reproduction/targeted_followup/` contains the prospectively frozen 5,632-request schedule, acquisition journals, original science code, all final and first-attempt exports, and an independent scoring check. The three allocations are 3,072 framing/core-replication requests, 1,024 minimal-referent requests, and 1,536 explicit-probability payoff-transfer requests. Action and payoff reports are separate calls. Valid wrong answers are retained.

## Integrity and exclusions

`reproduction/PACKAGE_SHA256.json` verifies the original 106 scientific files and the added targeted-follow-up archive. Git line-ending conversion is disabled to preserve the frozen bytes. Figure inputs contain plotted metadata; figure adaptations and historical code hashes have their own provenance files.

API keys, account preflight responses, browser state, font binaries, virtual environments, unrelated drafts, the manuscript, and the excluded Sonnet cohort are absent. Generated verification and plotting outputs are ignored by Git.

The archive supports numerical reconstruction of the samples; it does not establish provider stationarity, a unique internal mechanism, or universal model performance. Component READMEs retain the statistical and collection limitations.
