"""Data figures for the Track C report. Each figure states its conclusion in a title and labels what
the rational benchmark predicts, so it can be read without the text.

    Fig 2  fig_effects   main treatment effects of GPT-6 Luna (none) against the rational benchmark
    Fig 3  fig_values    perceived value of JOIN: who fails to condition (kappa > 0), and the 4.5 fingerprint
    Fig 4  fig_outside   response to the outside option, with and without stated values (theta)
    Fig 5  fig_prior     effect of the irrelevant prior by model and format (kappa x theta, pass-through)

Style matches Figure 1 (draw.io): warm neutrals, one clay accent, Segoe UI, thin axes, no gridlines.

    python report/scripts/fancy_report_figs.py      (reads extracted.json; writes report/figure/*.pdf)
"""
import argparse
import json
import os

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.lines import Line2D
from matplotlib.patches import Patch

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.normpath(os.path.join(HERE, '..', 'figure'))
PNG_OUT = None
X = json.load(open(os.path.join(HERE, 'extracted.json'), encoding='utf-8'))

INK, INK2, INK3, AXIS = '#1F1E1D', '#5E5D59', '#8A887F', '#B8B5AA'
BENCH = '#8A887F'
BASE, BASE_D = '#CBC8BE', '#9C998F'
CLAY, CLAY_L, CLAY_D = '#D97757', '#F0BCA6', '#9E4A30'
OTHER = '#ECEAE3'
# one colour per experiment, as in Figure 1: message = sky, prior = olive, outside option = clay
SKY, SKY_L = '#4F86BF', '#A9C6E4'
OLIVE, OLIVE_L, OLIVE_D = '#6F8A4E', '#B9C8A3', '#46592F'
SLATE = '#3F4E5E'

plt.rcParams.update({
    'font.family': 'Segoe UI', 'font.size': 7.8, 'axes.labelsize': 7.8, 'xtick.labelsize': 7.3,
    'ytick.labelsize': 7.5, 'legend.fontsize': 7.4, 'legend.frameon': False,
    'text.color': INK, 'axes.labelcolor': INK2, 'xtick.color': INK2, 'ytick.color': INK,
    'axes.edgecolor': AXIS, 'axes.linewidth': 0.6, 'axes.spines.top': False, 'axes.spines.right': False,
    'xtick.direction': 'out', 'ytick.direction': 'out', 'xtick.major.size': 2.5, 'ytick.major.size': 0,
    'xtick.major.width': 0.6, 'xtick.major.pad': 2.5, 'ytick.major.pad': 4,
    'mathtext.fontset': 'custom', 'mathtext.rm': 'Segoe UI', 'mathtext.it': 'Segoe UI:italic',
    'mathtext.bf': 'Segoe UI:bold', 'pdf.fonttype': 42, 'savefig.facecolor': 'white',
})
W = 6.5
NAME = {'luna': 'GPT-6 Luna (none)', 'luna_medium': 'GPT-6 Luna (medium)', 'sol': 'GPT-6 Sol (none)',
        'gemini': 'Gemini 3.8 Flash (minimal)', 'haiku': 'Claude Haiku 5.5 (off)', 'qwen': 'Qwen3.8 Omni Flash (off)',
        'deepseek': 'DeepSeek V4.1 Flash (off)', 'mistral': 'Mistral Small 4 (none)'}
BENCH_MK = dict(marker='D', ls='', mfc='white', mec=BENCH, mew=1.1, ms=5)


def title(fig, text, y=0.985):
    fig.text(0.008, y, text, fontsize=9, fontweight='bold', color=INK, va='top', ha='left')


def sub(ax, letter, text):
    ax.annotate(f'$\\bf{{{letter}}}$  {text}', (0, 1), xycoords='axes fraction', xytext=(0, 6),
                textcoords='offset points', fontsize=7.8, color=INK2, va='bottom', ha='left')


def rows(ax, names, ys, show=True):
    ax.set_yticks(ys)
    ax.set_yticklabels(names if show else [''] * len(ys))
    ax.spines['left'].set_visible(False)
    ax.set_ylim(min(ys) - 0.6, max(ys) + 0.6)


def save(fig, name):
    os.makedirs(OUT, exist_ok=True)
    fig.savefig(os.path.join(OUT, name + '.pdf'),
                metadata={'Creator': 'fancy_report_figs.py', 'CreationDate': None, 'ModDate': None})
    if PNG_OUT:
        os.makedirs(PNG_OUT, exist_ok=True)
        fig.savefig(os.path.join(PNG_OUT, name + '.png'), dpi=220)
    plt.close(fig)


# ============================================================================ Fig 2: main treatment effects
def fig_effects():
    eff = [('Message R → S: table, SAFE = 4', 8.20, 4.20, 12.21, 0),
           ('Message R → S: table, SAFE = 6', 3.81, -0.25, 7.87, 0),
           ('Message R → S: prose, SAFE = 4', 11.43, 7.50, 15.35, 0),
           ('Message R → S: prose, SAFE = 6', 12.21, 8.33, 16.08, 0),
           ('Prior 1/5 → 9/10: SAFE = 4', 12.9, 3.6, 22.1, 0),
           ('Safe payoff 4 → 6', -4.3, None, None, -100)]
    ys = np.array([6.4, 5.4, 4.4, 3.4, 2.4, 0.0])
    fig = plt.figure(figsize=(W, 2.55))
    title(fig, 'Irrelevant changes raise joining; the relevant change barely lowers it')
    L = fig.add_axes([0.385, 0.16, 0.075, 0.68])
    R = fig.add_axes([0.475, 0.16, 0.505, 0.68], sharey=L)
    for ax in (L, R):
        ax.set_ylim(-0.6, 7.4)
    L.set_xlim(-105, -95); L.set_xticks([-100])
    R.set_xlim(-6, 25); R.set_xticks([0, 10, 20])
    R.spines['left'].set_visible(False); R.tick_params(axis='y', length=0, labelleft=False)
    L.spines['left'].set_visible(False); L.spines['right'].set_visible(False)
    L.set_yticks(ys); L.set_yticklabels([e[0] for e in eff])
    for ax, x0, k in ((L, 1.0, 6.7), (R, 0.0, 1.0)):
        ax.plot([x0 - 0.02 * k, x0 + 0.02 * k], [-0.03, 0.03], transform=ax.transAxes, color=AXIS, lw=0.8,
                clip_on=False)
    R.axvline(0, color=AXIS, lw=0.6, zorder=0)
    # group headers in the label column
    for y, t in ((7.15, 'Should have no effect  (rational: 0)'), (0.85, 'Should lower joining by 100 pp  (rational: −100)')):
        fig.text(0.375, L.transData.transform((0, y))[1] / fig.bbox.height, t, ha='right', va='center',
                 fontsize=7.5, fontweight='bold', color=INK2)
    colors = [SKY, SKY, SKY, SKY, OLIVE, CLAY]
    for (lab, e, lo, hi, b), y, c in zip(eff, ys, colors):
        (L if b < -50 else R).plot(b, y, zorder=3, **BENCH_MK)
        if lo is not None:
            R.plot([lo, hi], [y, y], color=c, lw=1.1, zorder=2)
        R.plot(e, y, 'o', ms=5, color=c, zorder=4)
        R.text(max(e, hi if hi is not None else e) + 0.9, y, f'{e:+.1f}'.replace('-', '−'), va='center', fontsize=7.2, color=c)
    for t, c in zip(L.get_yticklabels(), colors):
        t.set_color(c)
    R.text(1.2, 0.0, 'rational −100: a gap of about 96 pp', va='center', fontsize=7.2, color=INK2, style='italic')
    R.set_xlabel('Effect on the joining rate of GPT-6 Luna (none), percentage points', x=0.38)
    R.legend(handles=[Line2D([], [], marker='o', ls='-', color=INK2, ms=5, lw=1.1, label='Estimate, 95% CI'),
                      Line2D([], [], **BENCH_MK, label='Rational benchmark')],
             loc='lower right', bbox_to_anchor=(1.0, 1.0), ncol=2, handletextpad=0.4, borderaxespad=0.1,
             columnspacing=1.4)
    save(fig, 'fig_effects')


# ============================================================================ Fig 3: perceived value of JOIN
ORDER8 = ['luna_medium', 'gemini', 'sol', 'deepseek', 'haiku', 'luna', 'qwen', 'mistral']


def fig_values():
    fig = plt.figure(figsize=(W, 2.85))
    title(fig, 'Five of eight models multiply the value of JOIN by probabilities that no longer matter')
    A = fig.add_axes([0.235, 0.27, 0.43, 0.53])
    B = fig.add_axes([0.705, 0.27, 0.275, 0.53], sharey=A)
    ys = np.arange(len(ORDER8))[::-1].astype(float)
    spec = [('correct', 'Correct, 5', BASE), ('half', '× ½ (message), 2.5', SKY),
            ('prior', '× prior, 1 or 4.5', OLIVE), ('both', 'Both', SLATE), ('other', 'Other', OTHER)]
    left = np.zeros(len(ORDER8))
    for key, lab, c in spec:
        v = np.array([X['fingerprint']['A'][m][key] for m in ORDER8])
        A.barh(ys, v, 0.62, left=left, color=c, ec='white', lw=0.6, label=lab, zorder=2)
        left += v
    rows(A, [NAME[m] for m in ORDER8], ys)
    A.set_xlim(0, 100); A.set_xticks([0, 50, 100]); A.set_xlabel('Share of answers (%)')
    sub(A, 'A', 'Reported value of JOIN (correct: 5)')
    for ax in (A, B):
        ax.axhline(4.5, color=BENCH, lw=0.7, ls=(0, (3, 2)), zorder=0)
    A.legend(loc='upper left', bbox_to_anchor=(-0.02, -0.25), ncol=5, handlelength=0.9, handleheight=0.9,
             columnspacing=0.9, handletextpad=0.3, borderaxespad=0)

    h = 0.3
    p20 = [X['fingerprint']['B'][m]['p20'] for m in ORDER8]
    p90 = [X['fingerprint']['B'][m]['p90'] for m in ORDER8]
    B.barh(ys + h / 2, p20, h, color=BASE, label='Prior 1/5', zorder=2)
    B.barh(ys - h / 2, p90, h, color=OLIVE, label='Prior 9/10', zorder=2)
    for y, v in zip(ys, p90):
        if v >= 3:
            B.text(v + 1.5, y - h / 2, f'{v:.0f}%', va='center', fontsize=7.1, color=OLIVE)
    B.spines['left'].set_visible(False); B.tick_params(axis='y', labelleft=False)
    B.set_xlim(0, 80); B.set_xticks([0, 40, 80]); B.set_xlabel('Answers equal to 4.5 (%)')
    sub(B, 'B', 'Answers of 4.5 = 5 × 9/10')
    B.text(79, 6, 'κ = 0: value\nJOIN correctly', ha='right', va='center', fontsize=7.1, color=INK3, linespacing=1.0)
    B.text(79, 1.5, 'κ > 0: fail\nto condition', ha='right', va='center', fontsize=7.1, color=SLATE,
           fontweight='bold', linespacing=1.0)
    B.legend(loc='center right', bbox_to_anchor=(1.0, 0.47), handlelength=0.9, handleheight=0.9,
             handletextpad=0.3, borderaxespad=0.1, labelspacing=0.3)
    save(fig, 'fig_values')


# ============================================================================ Fig 4: outside option
def fig_outside():
    D = X['choosing']; order = ['luna_medium', 'sol', 'gemini', 'haiku', 'deepseek', 'luna', 'mistral', 'qwen']
    theta = {'luna_medium': '1.00', 'sol': '0.99', 'gemini': '1.00', 'haiku': '0.59', 'deepseek': '0.48',
             'luna': '0.08', 'mistral': '0', 'qwen': '—'}
    fig = plt.figure(figsize=(W, 2.45))
    title(fig, 'A better outside option barely matters until the model states both values')
    ax = fig.add_axes([0.235, 0.16, 0.63, 0.64])
    ys = np.arange(len(order))[::-1]
    ax.axvline(100, color=BENCH, lw=0.8, ls=(0, (3, 2)), zorder=0)
    ax.axvline(0, color=AXIS, lw=0.6, zorder=0)
    for y, m in zip(ys, order):
        a, b = D[m]['oc_choice'], D[m]['oc_joint']
        ax.plot([a, b], [y, y], color=BASE, lw=1.4, solid_capstyle='butt', zorder=1)
        ax.plot(a, y, 'o', ms=5, mfc='white', mec=BASE_D, mew=1.1, zorder=2)
        ax.plot(b, y, 'o', ms=5, mfc=CLAY, mec=CLAY, zorder=3)
        ax.text(1.095, y, theta[m], transform=ax.get_yaxis_transform(), ha='center', va='center', clip_on=False,
                fontsize=7.6, color=CLAY if theta[m] not in ('1.00', '0.99') else INK2,
                fontweight='bold' if theta[m] not in ('1.00', '0.99') else 'normal')
    ax.text(1.095, ys[0] + 0.95, 'implied θ', transform=ax.get_yaxis_transform(), ha='center', va='center',
            clip_on=False, fontsize=7.4, color=INK2, fontweight='bold')
    rows(ax, [NAME[m] for m in order], ys)
    ax.set_xlim(-8, 108); ax.set_xticks([0, 25, 50, 75, 100])
    ax.set_xlabel('Drop in the joining rate when SAFE rises from 4 to 6 (pp)')
    ax.text(99, ys[-1] - 0.05, 'rational: 100', ha='right', va='center', fontsize=7.1, color=INK3, style='italic')
    ax.legend(handles=[Line2D([], [], marker='o', ls='', mfc='white', mec=BASE_D, mew=1.1, ms=5, label='Choice only'),
                       Line2D([], [], marker='o', ls='', mfc=CLAY, mec=CLAY, ms=5, label='States both values first')],
              loc='lower left', bbox_to_anchor=(0.0, 1.0), ncol=2, columnspacing=1.6, handletextpad=0.3,
              borderaxespad=0.15)
    save(fig, 'fig_outside')


# ============================================================================ Fig 5: effect of the prior by model and format
def fig_prior():
    C = X['choice']; models = ['luna', 'haiku', 'qwen', 'deepseek', 'mistral']
    conds = [('choice', 's4', 'Choice only, SAFE = 4', OLIVE),
             ('choice', 's6', 'Choice only, SAFE = 6', BASE_D),
             ('joint', 's4', 'States both values first, SAFE = 4', OLIVE_D)]
    fig = plt.figure(figsize=(W, 2.55))
    title(fig, 'The irrelevant prior moves choices as κ and θ predict')
    ax = fig.add_axes([0.235, 0.16, 0.745, 0.64])
    ys = np.arange(len(models))[::-1] * 1.0
    h = 0.24
    for k, (fmt, s, lab, c) in enumerate(conds):
        vals = [C[m][fmt][s]['p90'] - C[m][fmt][s]['p20'] for m in models]
        ax.barh(ys + (1 - k) * h, vals, h * 0.92, color=c, label=lab, zorder=2)
        for y, v in zip(ys, vals):
            if abs(v) >= 3:
                ax.text(v + 1.2, y + (1 - k) * h, f'{v:+.0f}'.replace('-', '−'), va='center', fontsize=6.9, color=c)
    ax.axvline(0, color=INK2, lw=0.8, zorder=1)
    ax.text(0.8, ys[-1] - 0.62, 'rational: 0', fontsize=7.1, color=INK3, style='italic', va='center')
    rows(ax, [NAME[m] for m in models], ys)
    ax.set_xlim(-5, 92); ax.set_xticks([0, 20, 40, 60, 80])
    ax.set_xlabel('Effect of moving the prior from 1/5 to 9/10 on the joining rate (pp)')
    ax.text(26, ys[0], '← θ ≈ 0.08: still responds when SAFE = 6', fontsize=7.1, color=INK2, va='center',
            style='italic')
    ax.text(45, ys[-1] + 0.5, 'stating values passes the valuation\nerror straight into choices ↓', fontsize=7.1,
            color=INK2, va='center', style='italic', linespacing=1.0)
    ax.legend(loc='lower left', bbox_to_anchor=(0.0, 1.0), ncol=3, handlelength=0.9, handleheight=0.9,
              columnspacing=1.2, handletextpad=0.3, borderaxespad=0.15)
    save(fig, 'fig_prior')


# ============================================================================ Fig 6: abstract lotteries
def fig_lotteries():
    D = X['choosing']; order = ['luna_medium', 'sol', 'gemini', 'haiku', 'deepseek', 'luna', 'mistral', 'qwen']
    fig = plt.figure(figsize=(W, 2.6))
    title(fig, 'Without the project story, models still pass over the sure option, until they state both values')
    A = fig.add_axes([0.235, 0.16, 0.355, 0.62])
    B = fig.add_axes([0.625, 0.16, 0.355, 0.62], sharey=A)
    ys = np.arange(len(order))[::-1]
    for ax in (A, B):
        ax.axvline(100, color=BENCH, lw=0.8, ls=(0, (3, 2)), zorder=0)
        ax.set_xlim(0, 108); ax.set_xticks([0, 50, 100]); ax.set_xlabel('Optimal choices (%)')
    for y, m in zip(ys, order):
        a, b = D[m]['acc_certain_better'], D[m]['acc_risky_better']
        A.plot([a, b], [y, y], color=BASE, lw=1.4, solid_capstyle='butt', zorder=1)
        A.plot(b, y, 'o', ms=5, mfc=INK2, mec=INK2, zorder=2)
        A.plot(a, y, 'D', ms=4.6, mfc=CLAY, mec=CLAY, zorder=3)
        c0, c1 = D[m]['lot_choice'], D[m]['lot_joint']
        B.plot([c0, c1], [y, y], color=BASE, lw=1.4, solid_capstyle='butt', zorder=1)
        B.plot(c0, y, 'o', ms=5, mfc='white', mec=BASE_D, mew=1.1, zorder=2)
        B.plot(c1, y, 'o', ms=5, mfc=CLAY, mec=CLAY, zorder=3)
    rows(A, [NAME[m] for m in order], ys)
    B.spines['left'].set_visible(False); B.tick_params(axis='y', labelleft=False)
    sub(A, 'A', 'Choice only, by which option is better')
    sub(B, 'B', 'All lotteries, by format')
    A.legend(handles=[Line2D([], [], marker='D', ls='', mfc=CLAY, mec=CLAY, ms=4.6, label='Sure amount better'),
                      Line2D([], [], marker='o', ls='', mfc=INK2, mec=INK2, ms=5, label='Risky option better')],
             loc='upper left', bbox_to_anchor=(0.0, 1.0), handletextpad=0.2, borderaxespad=0.1, labelspacing=0.3)
    B.legend(handles=[Line2D([], [], marker='o', ls='', mfc='white', mec=BASE_D, mew=1.1, ms=5, label='Choice only'),
                      Line2D([], [], marker='o', ls='', mfc=CLAY, mec=CLAY, ms=5, label='States both values first')],
             loc='upper left', bbox_to_anchor=(0.0, 1.0), handletextpad=0.2, borderaxespad=0.1, labelspacing=0.3)
    save(fig, 'fig_lotteries')


# ============================================================================ Fig 8: remedies and welfare
def fig_remedies():
    """GPT-6 Luna through three choice architectures (Table 4 of the earlier draft)."""
    arms = ['Choose directly', 'State both values first', 'Reason first (medium effort)']
    metrics = [('Effect of the irrelevant prior (pp)', [12.9, 18.0, 0.0], 0, (0, 22), OLIVE, [0, 10, 20]),
               ('Response to SAFE 4 → 6 (pp)', [4.3, 56.4, 100.0], 100, (0, 112), CLAY, [0, 50, 100]),
               ('Expected loss (points)', [0.48, 0.22, 0.0], 0, (0, 0.56), INK2, [0, 0.25, 0.5])]
    fig = plt.figure(figsize=(W, 1.95))
    title(fig, 'Stating values fixes the comparison but not the valuation; reasoning fixes both')
    ys = np.arange(len(arms))[::-1]
    xs = [0.235, 0.49, 0.745]
    for k, ((lab, vals, bench, lim, c, ticks), x0) in enumerate(zip(metrics, xs)):
        ax = fig.add_axes([x0, 0.2, 0.215, 0.56])
        ax.barh(ys, vals, 0.55, color=[c, c, c], alpha=1.0, zorder=2)
        ax.axvline(bench, color=BENCH, lw=0.8, ls=(0, (3, 2)), zorder=0)
        for y, v in zip(ys, vals):
            ax.text(v + lim[1] * 0.025, y, f'{v:.2f}' if lim[1] < 1 else f'{v:.0f}', va='center', fontsize=7.1,
                    color=c)
        rows(ax, arms, ys, show=(k == 0))
        ax.set_xlim(*lim); ax.set_xticks(ticks)
        ax.set_title(lab, fontsize=7.6, color=INK2, loc='left', pad=4)
    fig.text(0.985, 0.03, 'dashed: rational benchmark', ha='right', fontsize=7, color=INK3, style='italic')
    save(fig, 'fig_remedies')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Generate data figures for the Track C report.')
    parser.add_argument('--output', default=OUT, help='Output directory for PDF figures')
    parser.add_argument('--png-dir', default=None, help='Optional output directory for PNG previews')
    args = parser.parse_args()
    OUT = os.path.abspath(args.output)
    PNG_OUT = os.path.abspath(args.png_dir) if args.png_dir else None
    fig_effects(); fig_values(); fig_outside(); fig_prior(); fig_lotteries(); fig_remedies()
    print('ok')
