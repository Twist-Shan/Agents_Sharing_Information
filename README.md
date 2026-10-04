# Agents Sharing Information

Code repository for **Same Payoffs, Different Choices: How Shared Information Shapes Agent Collaboration**.

This repository contains experimental protocols, analysis, diagnostic tasks, and figure code for studying how language-model agents use information about a partner. Scientific responses are included so results can be reproduced on a CPU without an API key.

**Start here:** [Quick start](#installation-and-quick-start) · [Reproduction guide](docs/REPRODUCING.md) · [Paper figures](figures/README.md) · [Data and scope](docs/DATA.md) · [Validation](docs/VALIDATION.md)

## Research problem

Two agents choose between joining a task and taking a guaranteed alternative. Joining earns 10 points if the partner also joins and zero otherwise; the alternative earns a fixed score. The experiment changes what an agent knows about the delivery of information to its partner.

| Partner policy | Effect of a higher probability that the partner received confirmation |
|---|---|
| Joins only with confirmation | Joining becomes more attractive |
| Joins independently of confirmation | The payoff lottery stays identical |
| Joins only without confirmation | Joining becomes less attractive |

These controls separate **adaptation to a partner**, **consistent choices under identical payoffs**, and **the payoff consequences of joint participation**. A separate study diagnoses rule reports, payoff reports, and decisions with progressively more explicit assistance. Model–model pairs are separate one-shot choices, not conversations.

## Repository structure

```text
Agents_Sharing_Information/
├── README.md
├── requirements.txt              Numerical and plotting dependencies
├── scripts/reproduce.py          Offline reproduction entry point
├── docs/                         Reproduction, data, and validation
├── figures/                      Portable figure code and plotted inputs
├── reproduction/
│   ├── original/                 Original task, choices, and comparisons
│   ├── audits/                   Missingness, extraction, and pairing
│   └── new_experiment/           Independent diagnostics and decision aids
└── collection_history/           Historical acquisition and recovery code
```

Frozen scientific files retain their original layout and checksums. The entry point runs analyses in an output copy, leaving these inputs unchanged.

## Installation and quick start

Use **Python 3.12**. A CPU is sufficient for analysis and plotting.

```sh
git clone https://github.com/Twist-Shan/Agents_Sharing_Information.git
cd Agents_Sharing_Information
python -m venv .venv
```

Activate with `source .venv/bin/activate` on Linux/macOS or `.\.venv\Scripts\Activate.ps1` in PowerShell. Then run:

```sh
python -m pip install -r requirements.txt
python scripts/reproduce.py
```

Results go to `outputs/reproduction/`. For subsequent runs, specify a new `--output` directory. The workflow checks hashes, reconstructs original requests and comparisons, replays acquisition audits, and independently scores the diagnostic study. Network connections are blocked in analysis subprocesses.

## Experiments

| Study | Code and inputs | Scope |
|---|---|---|
| Partner policies and identical-payoff controls | [Original study](reproduction/original/README.md) | Primary-model experiment; smaller Qwen and DeepSeek replications |
| Rule reports, payoff reports, and incremental aids | [Diagnostic plan](reproduction/new_experiment/PLAN.md) | Separate fixed allocation; GPT-6 Luna, reasoning effort `none` |
| Missingness, extraction, and independent pairing | [Audits](reproduction/audits/README.md) | Retained failures and descriptive sensitivity checks |

The original study contains 44,800 selected choices; the diagnostic study contains 5,376 separate requests in 32 balanced blocks. The latter was specified after review and before collecting its responses. Seeds are not date-derived.

## Paper figures

```sh
python figures/render_paper_figures.py
python reproduction/new_experiment/audit_and_figures/plot_new_diagnostics.py --input reproduction/new_experiment/exports/analysis.json --output outputs/figures/diagnostics_aids
```

These commands generate all six figures with white backgrounds and the Mediterranean palette. Exact typography requires Times New Roman; font files are not distributed. Both plotters accept `--font-dir`. See the [figure guide](figures/README.md).

## Data and interpretation

Scientific inputs and response records are bundled for offline verification. Credentials, account preflights, unrelated drafts, the manuscript, font binaries, and the excluded Sonnet cohort are omitted. Generated outputs are ignored by Git. [Data coverage](docs/DATA.md) explains which historical and diagnostic records are included.

Separate rule reports do not reveal the reasoning behind another response. Approximate and conservative uncertainty estimates are both retained. Paired payoffs are conditional on the evaluated information state, not welfare across all delivery outcomes. Model and wording differences limit generalization.

## Citation and licensing

Identify the repository commit and cite the accompanying paper, **Same Payoffs, Different Choices: How Shared Information Shapes Agent Collaboration**, when using these materials. Publication metadata will be added when available. This preparation does not grant a new software license; dependency, provider, and font terms continue to apply.
