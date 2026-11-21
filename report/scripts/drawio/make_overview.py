"""Figure 1 (study overview) as a draw.io diagram: a row-aligned grid.

Left panel:    the economic decision (LLM agent and programmed partner, JOIN vs SAFE, rational rule).
Middle panel:  one card per experiment, the single phrase that changes (colour-coded).
Right panel:   on the same row, rational benchmark vs GPT-6 Luna as mini bars on one shared axis,
               plus the diagnosis (kappa or theta).
Each experiment therefore reads as one row: what changes -> what should happen -> what happens -> why.

    python report/scripts/drawio/make_overview.py   # writes overview.drawio and exports ../../figure/fig_overview.pdf
"""
import base64
import html
import os
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
ICONS = os.path.join(HERE, 'icons_color')
DRAWIO = r'C:\Program Files\draw.io\draw.io.exe'
FONT, MONO, MATH = 'Segoe UI', 'Consolas', 'Cambria'
INK, INK2, INK3 = '#1F1E1D', '#5E5D59', '#8A887F'
PANEL, CARD_LINE = '#F4F2EB', '#E6E2D8'
BENCH = '#C9C5BA'
COL = {'sky': ('#4F86BF', '#E3EDF7'), 'olive': ('#6F8A4E', '#E7EDDD'), 'clay': ('#D97757', '#F9E3D9')}

cells, _id = [], [1]


def nid():
    _id[0] += 1
    return f'n{_id[0]}'


def st(**kw):
    base = {'html': 1, 'whiteSpace': 'wrap', 'fontFamily': FONT, 'fontColor': INK, 'fontSize': 10.5,
            'strokeWidth': 1, 'spacing': 0}
    base.update(kw)
    return ';'.join(f'{k}={v}' for k, v in base.items()) + ';'


def box(x, y, w, h, value='', **kw):
    cells.append(f'<mxCell id="{nid()}" value="{html.escape(value, quote=True)}" style="{st(**kw)}" vertex="1" parent="1">'
                 f'<mxGeometry x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" as="geometry"/></mxCell>')


def text(x, y, w, h, value, **kw):
    kw.setdefault('strokeColor', 'none'); kw.setdefault('fillColor', 'none')
    kw.setdefault('align', 'left'); kw.setdefault('verticalAlign', 'middle')
    box(x, y, w, h, value, **kw)


def line(x1, y1, x2, y2, color=INK3, width=1.2, arrow='block', dashed=0):
    cells.append(f'<mxCell id="{nid()}" value="" style="{st(endArrow=arrow, endFill=1, endSize=5, strokeColor=color, strokeWidth=width, dashed=dashed, rounded=0)}" edge="1" parent="1">'
                 f'<mxGeometry relative="1" as="geometry"><mxPoint x="{x1:.1f}" y="{y1:.1f}" as="sourcePoint"/>'
                 f'<mxPoint x="{x2:.1f}" y="{y2:.1f}" as="targetPoint"/></mxGeometry></mxCell>')


def icon(cx, cy, size, name):
    data = base64.b64encode(open(os.path.join(ICONS, name + '.png'), 'rb').read()).decode()
    box(cx - size / 2, cy - size / 2, size, size, '', shape='image', image=f'data:image/png,{data}',
        imageAspect=1, aspect='fixed', strokeColor='none', fillColor='none')


def m(s):
    return f'<font face="{MATH}"><i>{s}</i></font>'


def header(x, num, label):
    box(x, 0, 19, 19, f'<b>{num}</b>', shape='ellipse', fillColor=INK, strokeColor='none', fontColor='#FFFFFF',
        fontSize=10.5, align='center', verticalAlign='middle')
    text(x + 26, 0, 260, 19, f'<b>{label}</b>', fontSize=12.5)


W = 800
P1, P2, P3 = (0, 236), (268, 528), (560, 800)
YT, YB = 30, 360
ROWS = [38, 136, 234]
RH = 88

for (x0, x1) in (P1, P2, P3):
    box(x0, YT, x1 - x0, YB - YT, '', rounded=1, arcSize=4, fillColor=PANEL, strokeColor='none')
header(P1[0], '1', 'The decision')
header(P2[0], '2', 'What we change in the prompt')
header(P3[0], '3', 'Change in how often the agent joins')

# ------------------------------------------------------------------ panel 1: the decision
for cx, ic, name, sub in ((52, 'ai_ink', 'LLM agent', '8 models'), (184, 'partner_ink', 'Partner', 'a program')):
    box(cx - 28, 74, 56, 56, '', shape='ellipse', fillColor='#FFFFFF', strokeColor=CARD_LINE)
    icon(cx, 102, 30, ic)
    text(cx - 45, 134, 90, 30, f'<b>{name}</b><br><font color="{INK2}" style="font-size:9.5px">{sub}</font>',
         align='center', fontSize=10.5)
line(82, 102, 103, 102, color=INK3, width=1, arrow='none', dashed=1)
line(154, 102, 133, 102, color=INK3, width=1, arrow='none', dashed=1)
icon(118, 98, 24, 'project_ink')
text(83, 114, 70, 14, 'joint project', align='center', fontSize=9, fontColor=INK3)
for k, (ic, lab, desc) in enumerate((('join_ink', 'JOIN', '10 if both join, else 0'),
                                     ('safe_ink', 'SAFE', f'{m("s")} points for sure'))):
    y = 184 + 44 * k
    box(P1[0] + 14, y, 208, 36, '', rounded=1, arcSize=30, fillColor='#FFFFFF', strokeColor=CARD_LINE)
    icon(P1[0] + 36, y + 18, 20, ic)
    text(P1[0] + 54, y, 164, 36, f'<b>{lab}</b>&nbsp;&nbsp;<font color="{INK2}">{desc}</font>', fontSize=10.5)
text(P1[0] + 10, 286, 216, 50,
     f'Rational: join if 10 · {m("p")} &gt; {m("s")}<br><font color="{INK2}" style="font-size:9.5px">'
     f'here {m("p")} = ½: join when {m("s")} = 4, not when {m("s")} = 6</font>', align='center', fontSize=11)

# ------------------------------------------------------------------ panels 2 and 3, one row per experiment
rows = [dict(c='sky', ic='envelope_sky', exp='Exp. 1', title='Uninformative message',
             change='Chance the partner also got the message: <b>50% → 100%</b>',
             should='<b>irrelevant</b>: partner joins 50% anyway',
             bench=0, bench_lab='0, no change', obs=(3.8, 12.2), obs_lab='+4 to +12',
             diag=f'→ error in valuing JOIN ({m("κ")} &gt; 0)'),
        dict(c='olive', ic='project_olive', exp='Exp. 2', title='Outdated prior',
             change='Earlier chance the project would go ahead: <b>20% → 90%</b>',
             should='<b>irrelevant</b>: project already confirmed',
             bench=0, bench_lab='0, no change', obs=(0, 12.9), obs_lab='+13',
             diag=f'→ error in valuing JOIN ({m("κ")} &gt; 0)'),
        dict(c='clay', ic='safe_clay', exp='Exp. 3', title='Better outside option',
             change='Payoff of SAFE: <b>4 → 6 points</b>',
             should="<b>relevant</b>: 6 beats JOIN's expected 5",
             bench=-100, bench_lab='−100, always SAFE', obs=(-4.3, 0), obs_lab='−4',
             diag=f'→ SAFE barely weighed ({m("θ")} ≈ 0.08)')]
# shared horizontal scale for the result cards: -100 .. +20 pp
RX0 = P3[0] + 12; RW = P3[1] - P3[0] - 24
BX0, BX1 = RX0 + 74, RX0 + RW - 12
ZERO = BX0 + (BX1 - BX0) * 100 / 120
X = lambda v: ZERO + (BX1 - BX0) * v / 120
for y, r in zip(ROWS, rows):
    c, ct = COL[r['c']]
    # panel 2 card: what changes, and whether it should matter
    x0 = P2[0] + 12; w = P2[1] - P2[0] - 24
    box(x0, y, w, RH, '', rounded=1, arcSize=8, fillColor='#FFFFFF', strokeColor=CARD_LINE)
    box(x0 + 10, y + 24, 38, 38, '', shape='ellipse', fillColor=ct, strokeColor='none')
    icon(x0 + 29, y + 43, 21, r['ic'])
    text(x0 + 58, y + 8, w - 66, 18, f'<b>{r["title"]}</b>', fontSize=11.5)
    text(x0 + w - 50, y + 7, 42, 14, f'<b>{r["exp"]}</b>', align='right', fontSize=9, fontColor=c)
    text(x0 + 58, y + 28, w - 64, 28, r['change'].replace('<b>', f'<b><font color="{c}">').replace('</b>', '</font></b>'),
         fontSize=9.8, fontColor=INK2, verticalAlign='top')
    box(x0 + 58, y + 60, w - 66, 20, r['should'], rounded=1, arcSize=40,
        fillColor='#F2F0E9', strokeColor='none', fontSize=9.2, fontColor=INK2, align='left', verticalAlign='middle',
        spacingLeft=8)
    line(P2[1] - 10, y + RH / 2, P3[0] + 10, y + RH / 2, color=INK3, width=1.2)
    # panel 3 card: rational vs GPT-6 Luna on the shared scale
    box(RX0, y, RW, RH, '', rounded=1, arcSize=8, fillColor='#FFFFFF', strokeColor=CARD_LINE)
    for k, (lab, lc) in enumerate((('Rational', INK3), ('GPT-6 Luna', c))):
        text(RX0 + 10, y + 9 + 18 * k, 64, 14, f'<b>{lab}</b>' if k else lab, fontSize=9.2, fontColor=lc)
    yb, yo = y + 12, y + 30
    for yy in (yb, yo):
        box(X(-100), yy + 3, X(20) - X(-100), 3, '', fillColor='#EEEBE3', strokeColor='none')
    if r['bench'] < 0:
        box(X(r['bench']), yb, ZERO - X(r['bench']), 9, '', fillColor=BENCH, strokeColor='none')
        text(X(r['bench']) + 3, yb - 2, 100, 13, r['bench_lab'], fontSize=8.8, fontColor=INK)
    else:
        box(ZERO - 1.5, yb, 3, 9, '', fillColor=BENCH, strokeColor='none')
        text(ZERO - 86, yb - 2, 80, 13, r['bench_lab'], align='right', fontSize=8.8, fontColor=INK2)
    lo, hi = r['obs']
    box(X(lo), yo, max(X(hi) - X(lo), 2.5), 9, '', fillColor=c, strokeColor='none')
    lab_x = (X(lo) if lo < 0 else ZERO) - 56
    text(lab_x, yo - 2, 50, 13, f'<b>{r["obs_lab"]}</b>', align='right', fontSize=9.4, fontColor=c)
    line(ZERO, y + 7, ZERO, y + 46, color=INK3, width=0.8, arrow='none')
    text(RX0 + 10, y + 60, RW - 16, 20, r['diag'], fontSize=10, fontColor=INK)
# the shared axis under the result cards
ya = ROWS[-1] + RH + 10
line(X(-100), ya, X(20), ya, color=INK3, width=0.8, arrow='none')
for v, lab in ((-100, '−100'), (-50, '−50'), (0, '0'), (20, '+20')):
    line(X(v), ya, X(v), ya + 4, color=INK3, width=0.8, arrow='none')
    text(X(v) - 20, ya + 5, 40, 12, lab, align='center', fontSize=8.6, fontColor=INK2)
text(RX0 + 4, ya - 6, 70, 26, 'pp change<br>in joining', fontSize=8.4, fontColor=INK3, align='left')

box(0, 0, W, YB + 2, '', fillColor='none', strokeColor='none')   # fixed canvas for --crop

xml = ('<mxfile host="drawio" agent="make_overview.py"><diagram id="ov" name="Overview">'
       '<mxGraphModel dx="800" dy="600" grid="0" gridSize="10" guides="1" tooltips="1" connect="0" arrows="1" fold="1" '
       'page="0" pageScale="1" pageWidth="827" pageHeight="1169" math="0" shadow="0" background="#ffffff"><root>'
       '<mxCell id="0"/><mxCell id="1" parent="0"/>' + ''.join(cells) + '</root></mxGraphModel></diagram></mxfile>')
src = os.path.join(HERE, 'overview.drawio')
open(src, 'w', encoding='utf-8').write(xml)
out = os.path.normpath(os.path.join(HERE, '..', '..', 'figure', 'fig_overview.pdf'))
subprocess.run([DRAWIO, '-x', '-f', 'pdf', '--crop', '-o', out, src], check=True)
print('canvas', W, 'x', YB + 2)
