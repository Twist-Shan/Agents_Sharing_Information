"""Unfrozen publication style: explicit Times New Roman and Mediterranean colors."""
from pathlib import Path
import hashlib
import json
import os

PALETTE = {
    'AegeanBlue': '#2F88B8', 'SeaSky': '#69B6D4', 'SunYellow': '#E6B43E',
    'Terracotta': '#E57D3F', 'OliveTeal': '#4FA58A', 'CoralRed': '#C85F62',
    'SandCream': '#F0DDA8', 'HarborSlate': '#56627A', 'DeepNavy': '#25313B',
    'LimestoneWhite': '#FBF8EF', 'CoastalGray': '#9AA3A6', 'EarthBrown': '#7C5D48',
}
BACKGROUND = '#FFFFFF'
_FONT_METADATA = None


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def apply_style(base_size=9.5, font_dir=None):
    """Fail if the four genuine Times New Roman faces cannot be found."""
    import matplotlib as mpl
    from matplotlib import font_manager as fm
    global _FONT_METADATA
    directory = Path(font_dir) if font_dir else Path(os.environ.get('WINDIR', 'C:/Windows'))/'Fonts'
    files = {'regular': 'times.ttf', 'bold': 'timesbd.ttf', 'italic': 'timesi.ttf', 'bold_italic': 'timesbi.ttf'}
    fonts = {}
    for face, filename in files.items():
        path = (directory/filename).resolve()
        if not path.is_file():
            raise FileNotFoundError('Times New Roman face required: ' + str(path))
        fm.fontManager.addfont(str(path))
        name = fm.FontProperties(fname=str(path)).get_name()
        if name != 'Times New Roman':
            raise ValueError('Unexpected font in ' + str(path) + ': ' + name)
        fonts[face] = {'path': str(path), 'sha256': digest(path), 'family': name}
    # Resolve rather than silently substituting a generic serif face.
    for face, weight, style in (('regular','normal','normal'), ('bold','bold','normal'),
                                ('italic','normal','italic'), ('bold_italic','bold','italic')):
        found = Path(fm.findfont(fm.FontProperties(family='Times New Roman', weight=weight, style=style),
                                fallback_to_default=False)).resolve()
        if digest(found) != fonts[face]['sha256']:
            raise ValueError('Times New Roman face resolution mismatch: ' + face)
    mpl.rcParams.update({
        'font.family': 'Times New Roman', 'font.serif': ['Times New Roman'], 'font.size': base_size,
        'axes.titlesize': base_size+0.5, 'axes.titleweight': 'bold', 'axes.titlelocation': 'left',
        'axes.labelsize': base_size, 'xtick.labelsize': base_size, 'ytick.labelsize': base_size,
        'legend.fontsize': base_size, 'legend.frameon': False,
        'text.color': PALETTE['DeepNavy'], 'axes.labelcolor': PALETTE['DeepNavy'],
        'xtick.color': PALETTE['DeepNavy'], 'ytick.color': PALETTE['DeepNavy'],
        'axes.edgecolor': PALETTE['CoastalGray'], 'axes.linewidth': .65,
        'axes.spines.top': False, 'axes.spines.right': False,
        'grid.color': PALETTE['CoastalGray'], 'grid.linewidth': .5, 'grid.alpha': .32,
        'axes.axisbelow': True, 'axes.unicode_minus': True,
        'figure.facecolor': BACKGROUND, 'axes.facecolor': BACKGROUND,
        'savefig.facecolor': BACKGROUND, 'savefig.edgecolor': 'none',
        'pdf.fonttype': 42, 'ps.fonttype': 42, 'svg.fonttype': 'none',
        'mathtext.fontset': 'custom', 'mathtext.rm': 'Times New Roman',
        'mathtext.it': 'Times New Roman:italic', 'mathtext.bf': 'Times New Roman:bold',
        'mathtext.bfit': 'Times New Roman:bold:italic', 'mathtext.cal': 'Times New Roman:italic',
        'mathtext.sf': 'Times New Roman', 'mathtext.tt': 'Times New Roman',
        'mathtext.fallback': None,
    })
    _FONT_METADATA = {'family': 'Times New Roman', 'base_size_points': base_size, 'faces': fonts}
    return _FONT_METADATA


def style_axes(ax, grid='y'):
    for side in ('top','right'):
        ax.spines[side].set_visible(False)
    for side in ('left','bottom'):
        ax.spines[side].set_color(PALETTE['CoastalGray'])
        ax.spines[side].set_linewidth(.65)
    ax.tick_params(length=3, width=.6, pad=4)
    ax.set_axisbelow(True)
    if grid:
        ax.grid(axis=grid, color=PALETTE['CoastalGray'], alpha=.32, linewidth=.5)
    return ax


def panel_label(ax, label, x=-.12, y=1.08):
    return ax.text(x, y, label, transform=ax.transAxes, fontsize=11, weight='bold',
                   ha='left', va='bottom', color=PALETTE['DeepNavy'])


def save_figure(fig, output_stem, sources=(), metadata=None, dpi=240, overwrite=False):
    """Save vector PDF, print-resolution PNG and hashes; never changes input files."""
    import matplotlib
    from matplotlib.text import Text
    if _FONT_METADATA is None:
        raise RuntimeError('Call apply_style() before saving')
    stem = Path(output_stem)
    paths = [stem.with_suffix('.pdf'), stem.with_suffix('.png'), stem.with_name(stem.name+'_provenance.json')]
    if not overwrite and any(path.exists() for path in paths):
        raise FileExistsError('Refusing existing Mediterranean figure: ' + str(stem))
    src = {str(Path(p).resolve()): digest(p) for p in sources}
    fig.set_facecolor(BACKGROUND)
    for ax in fig.axes:
        ax.set_facecolor(BACKGROUND)
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    clipped = []
    for item in fig.findobj(match=Text):
        if not item.get_visible() or not item.get_text().strip():
            continue
        box = item.get_window_extent(renderer)
        if box.x0 < -1 or box.y0 < -1 or box.x1 > fig.bbox.x1+1 or box.y1 > fig.bbox.y1+1:
            clipped.append(item.get_text())
    if clipped:
        raise ValueError('Text extends outside figure: ' + repr(clipped))
    stem.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(paths[0], metadata={'Creator': 'Mediterranean research figure', 'CreationDate': None, 'ModDate': None})
    fig.savefig(paths[1], dpi=dpi)
    if any(digest(path) != expected for path, expected in src.items()):
        raise RuntimeError('Input changed while rendering')
    record = {'style': 'Mediterranean palette; Times New Roman; pure white background', 'palette': PALETTE,
              'background_color': BACKGROUND, 'figure_and_axes_background': 'pure white',
              'font': _FONT_METADATA, 'figure_inches': [float(x) for x in fig.get_size_inches()],
              'matplotlib_version': matplotlib.__version__, 'source_sha256': src,
              'style_source_sha256': digest(__file__), 'metadata': metadata or {},
              'text_within_canvas_checked': True, 'visual_review': 'pending manual review',
              'output_sha256': {path.name: digest(path) for path in paths[:2]}}
    paths[2].write_text(json.dumps(record, indent=2, ensure_ascii=False)+'\n', encoding='utf-8')
    return record
