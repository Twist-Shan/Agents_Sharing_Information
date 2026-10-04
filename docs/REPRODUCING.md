# Reproduction workflows

Use the root `python scripts/reproduce.py` command after installing `requirements.txt`. Verified versions: Python 3.12.7, NumPy 1.26.4, SciPy 1.13.1, Matplotlib 3.9.2.

The entry point checks all archived hashes, copies the package to a new output directory, and executes:

| Component | Command | Check |
|---|---|---|
| original | `reconstruct_requests.py --verify` | 44,800 exact payload hashes |
| original | `recompute_results.py` | All 36 contrasts and both uncertainty calculations |
| audits | `reproduce_audits.py` | First-attempt bounds, pairing baseline, and extraction replay |
| new_experiment | `export_results.py` | Terminal journal, selected answers, and condition results |
| new_experiment | `audit_and_figures/independent_result_audit.py` | Independent scoring, intervals, settings, and accounting |

Commands run inside the copied component directories. Full arguments are visible in `scripts/reproduce.py`. Existing output directories are not overwritten: use `--output outputs/second_run` to repeat. Successful completion writes `PASSED.json`; intermediate exports remain in that output directory. User-site packages are disabled and network connections are blocked in child analyses. No collection entry point runs.

## Figure generation

See [the figure guide](../figures/README.md). The original five figures use archived plotted inputs; their estimates are checked by the scientific reproduction workflow. The diagnostic figure verifies its terminal export before rendering. Drawing scripts do not refit estimates or introduce tests.

## Fresh collection

Historical collection code is retained for inspection, including recovery and extraction. It depends on historical run layouts and amendment locks and is not a turnkey new experiment. The diagnostic runner preserves the implementation of the separate fixed study.

Fresh paid collection requires a new fixed design, verified model/provider/settings and prices, and a new budget ledger. Do not resume the archived run or reuse its accounting as a fresh spending allocation. Offline reproduction does not require credentials.
