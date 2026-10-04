"""Publication figure for terminal independent-diagnostic and nested-aid results.

This script must not be used as an acquisition-progress monitor. It reads the
terminal export provenance before opening analysis.json and refuses incomplete
final mode rates, rather than labelling a lower completion bound as accuracy.

Default use, only after terminal export:
    python plot_new_diagnostics.py

Portable use:
    python plot_new_diagnostics.py --input exported/analysis.json \
        --output figures/diagnostics_aids --font-dir /path/to/times/fonts

There are no model calls and no fitted/interpolated response curves. Orders,
colors and axis limits were fixed before reading this experiment's outcomes.
"""
from __future__ import annotations

from pathlib import Path
import argparse
import hashlib
import json
import math

HERE = Path(__file__).resolve().parent
MODES = ('D1', 'D2', 'D3', 'U', 'A1', 'A2', 'A3')
TERMINAL = {'complete', 'halted_fatal', 'halted_budget', 'halted_service', 'attempts_exhausted'}

# The diagnostic rows are separate questions, not arrows in a reasoning chain.
PANEL_A = (
    ('D1', "Partner's rule"),
    ('D2', 'Chance partner joins'),
    ('D3', 'Expected payoffs'),
    ('U', 'Choose an action'),
)
# The plus signs describe nested supplied information, not sequential calls.
PANEL_B = (
    ('U', 'Control'),
    ('A1', '+ Chance partner joins'),
    ('A2', '+ Payoff lottery'),
    ('A3', '+ Expected payoffs'),
)


def check(condition, reason):
    if not condition:
        raise ValueError(reason)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load_terminal_results(input_path, provenance_path):
    """Check terminal metadata before any scientific outcome access."""
    check(provenance_path.is_file(), 'Terminal export provenance is required before reading outcomes.')
    provenance = json.loads(provenance_path.read_text(encoding='utf-8'))
    status = provenance.get('status', {})
    check(status.get('state') in TERMINAL, 'Acquisition is nonterminal; refusing to read analysis results.')
    check(provenance.get('terminal_lock_verified') is True,
          'The exporter has not verified the terminal execution lock.')
    check(input_path.is_file(), 'Terminal analysis.json does not exist.')
    data = json.loads(input_path.read_text(encoding='utf-8'))
    final = data['final']
    check(final['planned'] == 5376, 'Unexpected fixed allocation; do not silently change the figure sample.')
    check(final['valid'] == final['planned'],
          'Unresolved final outcomes remain: this accuracy figure must be redesigned to show completion bounds.')
    check(status['science_accepted'] == final['valid'], 'Terminal status and analysis counts disagree.')
    check(len(final['mode_rates']) == 7, 'Expected all seven independently sampled response modes.')
    modes = {row['group']['mode']: row for row in final['mode_rates']}
    check(set(modes) == set(MODES), 'Missing, duplicate or unplanned response modes.')
    for mode, row in modes.items():
        check(row['planned'] == row['valid'] == 768 and row['missing'] == 0,
              'Mode '+mode+' has incomplete or unequal planned denominators.')
        check(type(row['correct']) is int and 0 <= row['correct'] <= row['planned'], 'Invalid correct count.')
        actual = row['correct']/row['planned']
        check(math.isclose(actual, row['observed_correct_over_planned'], abs_tol=1e-12),
              'Correct count and stored rate disagree for '+mode)
        check(all(math.isclose(actual, x, abs_tol=1e-12) for x in row['latent_accuracy_completion_bounds']),
              'Complete final data must have point-valued completion bounds.')
    return data, modes, provenance


def render(input_path, output_stem, font_dir=None, provenance_path=None, overwrite=False):
    provenance_path = provenance_path or input_path.parent/'export_provenance.json'
    # No Matplotlib activity or scientific-data read occurs before this guard.
    data, modes, provenance = load_terminal_results(input_path, provenance_path)
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.ticker import PercentFormatter
    import style_local as style

    style.apply_style(base_size=9.5, font_dir=font_dir)
    palette = style.PALETTE
    colors = {'D1':palette['AegeanBlue'], 'D2':palette['AegeanBlue'],
              'D3':palette['AegeanBlue'], 'U':palette['HarborSlate'],
              'A1':palette['AegeanBlue'], 'A2':palette['OliveTeal'],
              'A3':palette['Terracotta']}
    fig = plt.figure(figsize=(7.1, 3.0), facecolor='white')
    # Matching physical plot sizes; each half reserves the same label region.
    boxes = ([.218, .225, .252, .61], [.718, .225, .252, .61])
    axes = [fig.add_axes(box) for box in boxes]
    for ax, rows in zip(axes, (PANEL_A, PANEL_B)):
        vals = [100*modes[mode]['correct']/modes[mode]['planned'] for mode, _ in rows]
        positions = list(range(4))
        ax.barh(positions, vals, height=.48,
                color=[colors[mode] for mode, _ in rows], edgecolor='none', zorder=3)
        ax.set_xlim(0, 100)
        ax.set_ylim(3.65, -.65)
        ax.set_yticks(positions, [label for _, label in rows])
        ax.set_xticks([0, 25, 50, 75, 100])
        ax.xaxis.set_major_formatter(PercentFormatter(xmax=100, decimals=0))
        ax.set_xlabel('Correct responses', labelpad=8)
        style.style_axes(ax, grid='x')
        ax.spines['left'].set_visible(False)
        ax.tick_params(axis='y', length=0, pad=7, labelsize=9.3)
        ax.tick_params(axis='x', labelsize=8.7, pad=4)
        # One compact value per condition; never add invented marginal intervals.
        for y, value in zip(positions, vals):
            inside = value >= 78
            ax.text(value-3.0 if inside else value+3.0, y, f'{value:.1f}%',
                    ha='right' if inside else 'left', va='center',
                    color='white' if inside else palette['DeepNavy'],
                    fontsize=9.1, fontweight='normal', zorder=4)
    for x, letter, title in ((.037,'A','Separate questions'),(.537,'B','Nested decision aids')):
        fig.text(x,.923,letter,fontsize=12,fontweight='bold',ha='left',va='center')
        fig.text(x+.041,.923,title,fontsize=11,fontweight='bold',ha='left',va='center')

    values = {mode:{key:row[key] for key in ('planned','valid','missing','correct','observed_correct_over_planned',
                                           'latent_accuracy_completion_bounds','components')}
              for mode,row in modes.items()}
    metadata = {
        'input_schema_version':data.get('schema_version'),
        'response_policy':'final accepted response for every planned ID',
        'mode_order_fixed_before_outcomes':list(MODES),
        'panel_A': [{'mode':mode,'label':label} for mode,label in PANEL_A],
        'panel_B': [{'mode':mode,'label':label} for mode,label in PANEL_B],
        'mode_values':values,
        'mode_colors':colors,
        'axes_percent_limits':[0,100],
        'panel_axes_rectangles':boxes,
        'marginal_confidence_intervals':'Not estimated or plotted. These rates are descriptive.',
        'paired_aid_contrasts_reported_separately':data['final']['aid_contrasts'],
        'diagnostic_interpretation':data.get('diagnostics_interpretation'),
        'diagnostic_tasks_connected_by_arrows':False,
        'missingness_policy':'Refuse to label incomplete-data lower completion bounds as accuracy.',
        'allocation':{'blocks':32,'cells_per_block':24,'independent_requests_per_mode':768,'total_requests':5376},
        'terminal_state':provenance['status']['state'],
        'frozen_manifest_sha256':provenance['manifest_sha256'],
        'frozen_planned_sha256':provenance['planned_sha256'],
        'paid_calls_by_plot':0,
    }
    result = style.save_figure(fig,output_stem,
                              sources=(input_path,provenance_path,Path(__file__),HERE/'style_local.py'),
                              metadata=metadata,dpi=320,overwrite=overwrite)
    plt.close(fig)
    caption = (
        'Independently elicited responses and the effect of decision aids. '
        '(A) Separate requests report the partner\'s rule, infer its action probability, '
        'report expected payoffs, or choose an action. (B) Action accuracy after successively '
        'adding the partner\'s JOIN probability, the payoff lottery, and expected payoffs to '
        'the same task. Each rate covers 768 planned responses across 32 fixed blocks. '
        'Rates are descriptive; uncertainty for the three adjacent aid contrasts is reported '
        'separately. Panel A does not trace reasoning within a response.\n'
    )
    output_stem.with_name(output_stem.name+'_caption.txt').write_text(caption,encoding='utf-8')
    return result


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--input',type=Path,default=HERE/'new_experiment/exports/analysis.json')
    p.add_argument('--provenance',type=Path)
    p.add_argument('--output',type=Path,default=HERE/'paper/figure/diagnostics_aids')
    p.add_argument('--font-dir',type=Path)
    p.add_argument('--overwrite',action='store_true')
    args = p.parse_args()
    result = render(args.input,args.output,args.font_dir,args.provenance,args.overwrite)
    print(json.dumps({'status':'rendered_pending_visual_review','figure_inches':result['figure_inches'],
                      'outputs':list(result['output_sha256']),'paid_calls':0},indent=2))
