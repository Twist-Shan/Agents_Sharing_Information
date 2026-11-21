# Track C Report: Framing and Inattention in Delegated Choice

This directory contains the LaTeX source, compiled PDF, figures, and figure-generation scripts for the Behavioral Economics (Fall 2026, Track C) report:

**Framing and Inattention in Delegated Choice: Evidence from LLM Agents**  
Yuxuan Cai, Xingyu Peng, Liang Shan, and Aolin Zhang

## Contents

```text
report/
├── README.md
├── report.tex                   LaTeX source (10 pages excluding references; 12 pages total)
├── report.pdf                   Compiled PDF
├── figure/                      8 PDF figures included by report.tex
│   ├── fig_overview.pdf         Figure 1: Study overview (draw.io)
│   ├── fig_model.pdf            Figure 2: Two-step model (draw.io)
│   ├── fig_effects.pdf          Figure 3: Main treatment effects
│   ├── fig_values.pdf           Figure 4: Perceived value of JOIN (valuation-only)
│   ├── fig_outside.pdf          Figure 5: Response to the outside option
│   ├── fig_lotteries.pdf        Figure 6: Abstract lotteries
│   ├── fig_prior.pdf            Figure 7: Irrelevant prior effect by configuration and format
│   └── fig_remedies.pdf         Figure 8: Remedies and welfare comparison
└── scripts/
    ├── extracted.json           Summary statistics for Experiments 2 and 3 across 8 model configurations
    ├── clues_data.json          Additional Experiment 2/3 choice and valuation summaries
    ├── fancy_report_figs.py     Generates Figures 3–8 (`fig_effects` through `fig_remedies`)
    └── drawio/                  Diagram generators (`make_overview.py`, `make_fig1.py`), `.drawio` XMLs, and icon assets
```

## Coverage note

- **Experiment 1** (message-delivery framing, random and responsive partners, rule/payoff diagnostics, and targeted follow-up): full offline request/response reproduction lives in `../reproduction/` (`python scripts/reproduce.py`).
- **Experiments 2 and 3** (irrelevant prior, outside-option salience, abstract lotteries, and model/reasoning comparisons across eight OpenRouter configurations from 12–13 October 2026): summary statistics and figure inputs are archived here in `scripts/extracted.json` and `scripts/clues_data.json`.

## Rebuilding figures and the PDF

Generate the six data figures (writes PDFs to `report/figure/`):

```sh
python report/scripts/fancy_report_figs.py
```

Regenerate the two `draw.io` diagrams (requires draw.io Desktop installed at `C:\Program Files\draw.io\draw.io.exe`):

```sh
python report/scripts/drawio/make_overview.py
python report/scripts/drawio/make_fig1.py
```

Compile `report.pdf` cleanly with `pdflatex`:

```sh
cd report
pdflatex -interaction=nonstopmode report.tex
pdflatex -interaction=nonstopmode report.tex
```
