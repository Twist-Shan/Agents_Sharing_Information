# Targeted follow-up

Three independent controls address the limits of the original interpretation:

| Study | Allocation | Question |
|---|---:|---|
| Original replication and matched framing | 128 blocks × 24 conditions = 3,072 | Does the identical-lottery effect recur, and does it differ between a partner and a non-partner device description? |
| Minimal referent edit | 64 blocks × 16 conditions = 1,024 | Does specifying the partner's own receipt change the response to the complementary policy? |
| Explicit-probability payoff transfer | 32 blocks × 48 conditions = 1,536 | Can the model evaluate and choose when action probability is explicit and rewards/losses change? |

The allocation totals **5,632 requests** using GPT-6 Luna with reasoning effort `none`. The [prospective plan](PLAN.md) defines one family of eight primary comparisons. All answers are independent calls; valid wrong answers are retained. No model, sample, or wording is selected by its result.

## Offline reproduction

Use the repository's root `python scripts/reproduce.py` command. It works in an output copy and blocks network access. This component then runs:

```sh
python analysis.py --run run --output PATH_TO_NEW_OUTPUT
python audit_independent.py --run run --exports PATH_TO_NEW_OUTPUT
```

The frozen analysis checks source and schedule hashes, verifies terminal journals, replays answer acceptance, and exports all first/final comparisons and condition summaries. The independent audit re-parses accepted response text and reconstructs payoff scores, means, paired estimates, and both interval calculations without importing the scoring/analysis module.

`original_regret.py` separately reconstructs descriptive mean expected regret from the earlier experiment; it introduces no new tests. The original paper's inference families are unchanged.

## Archive contents

- `run/`: frozen manifest and schedule, scientific starts/responses, terminal status and accounting.
- `exports/`: all final and first-attempt results and independent checks.
- `protocol.py`, `analysis.py`, `runtime.py`, `verify.py`, `PLAN.md`, `profiles.json`, `original_protocol.py`: original frozen science and acquisition sources.
- `audit_independent.py`, `original_regret.py`: additional offline validation and descriptive reporting.

Account preflights and credentials are excluded. Never resume this historical run for new collection: its terminal state, budget, and endpoint metadata belong to the archived study. A new paid study needs a new fixed design and current interface/budget verification.

These experiments test one-step choices under particular descriptions. Matching word count and numeric structure does not isolate a general social-cognition mechanism. A useful payoff summary does not demonstrate learning or a hidden reasoning pathway. Full-context versus lottery prompts are not length-matched. All uncertainty and missingness results are retained.
