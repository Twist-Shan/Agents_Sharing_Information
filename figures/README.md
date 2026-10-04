# Paper figures

`render_paper_figures.py` is a portable extraction of the drawing code used for the five original figures, with the final terminology edits preserved. Its `inputs/` contains the archived plotted values. Full numerical reproduction is separate under `reproduction/`. No scientific estimates are refitted by this drawing script.

Run from the repository root:

```
python figures/render_paper_figures.py
python reproduction/new_experiment/audit_and_figures/plot_new_diagnostics.py --input reproduction/new_experiment/exports/analysis.json --output outputs/figures/diagnostics_aids
```

Both scripts support `--font-dir`. Exact typography needs all four genuine Times New Roman faces (`times.ttf`, `timesbd.ttf`, `timesi.ttf`, `timesbi.ttf`). They are normally found in Windows/Fonts; font files are not distributed. White backgrounds and the Mediterranean palette are retained. The diagnostic figure verifies terminal acquisition before plotting. PDF metadata may differ between renderings.

## Targeted follow-up figures

```sh
python figures/targeted/render_targeted.py --input reproduction/targeted_followup/exports/final.json --output outputs/figures
```

`targeted/` pairs design diagrams with the original and fresh comparisons, a minimal referent edit, and payoff-report/action heatmaps over every fixed recipe. It accepts `--font-dir`, uses terminal exported results, and writes PDF/PNG plus source hashes. Original and new inferential families remain separate; marginal rates are labeled descriptive.
