"""Figure 1 (conceptual framework) as a draw.io diagram, exported to PDF with the draw.io CLI.

A 2 x 2 grid. Top row: the two-step model of the decision (valuation with kappa, choice with theta).
Bottom row: the test that pins down each parameter, with the rational benchmark and GPT-6 Luna.
Warm neutrals, one clay accent, Segoe UI with Cambria for mathematics.

    python report/scripts/drawio/make_fig1.py       # writes fig1.drawio and exports ../../figure/fig_model.pdf
"""
import html
import os
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
DRAWIO = r'C:\Program Files\draw.io\draw.io.exe'
FONT, MATH = 'Segoe UI', 'Cambria'
INK, INK2, INK3 = '#1F1E1D', '#5E5D59', '#8A887F'
LINE, HEAD, CELL = '#E2DFD6', '#EFECE3', '#FAF9F5'
CLAY = '#D97757'

cells, _id = [], [1]


def nid():
    _id[0] += 1
    return f'n{_id[0]}'


def st(**kw):
    base = {'html': 1, 'whiteSpace': 'wrap', 'fontFamily': FONT, 'fontColor': INK, 'fontSize': 11,
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


def line(x1, y1, x2, y2, color=INK3, width=1, arrow='block'):
    cells.append(f'<mxCell id="{nid()}" value="" style="{st(endArrow=arrow, endFill=1, endSize=6, strokeColor=color, strokeWidth=width, rounded=0)}" edge="1" parent="1">'
                 f'<mxGeometry relative="1" as="geometry"><mxPoint x="{x1:.1f}" y="{y1:.1f}" as="sourcePoint"/>'
                 f'<mxPoint x="{x2:.1f}" y="{y2:.1f}" as="targetPoint"/></mxGeometry></mxCell>')


def m(s):   # inline mathematics in Cambria italic
    return f'<font face="{MATH}"><i>{s}</i></font>'


W = 800
C = [(120, 445), (475, 800)]             # the two columns
yK, hK = 0, 44                            # task row
yM, hM = 58, 74                           # model row
yT, hT = 150, 112                         # test row

text(0, yK, 110, hK, '<b>TASK</b>', fontColor=INK3, fontSize=9.5)
box(C[0][0], yK, C[1][1] - C[0][0], hK, '', rounded=1, arcSize=14, fillColor=CELL, strokeColor=LINE)
text(C[0][0] + 16, yK + 4, C[1][1] - C[0][0] - 32, hK - 8,
     f'Choose <b>JOIN</b>: 10 points if the partner joins (probability {m("p")}), otherwise 0; '
     f'or <b>SAFE</b>: {m("s")} points for sure.<br>'
     f'<font color="{INK2}">{m("q")}: a probability stated in the prompt that should not matter '
     f'(an outdated prior; whether the partner received a message)</font>', fontSize=10.5)
text(0, yM, 110, hM, '<b>MODEL</b>', fontColor=INK3, fontSize=9.5)
text(0, yT, 110, hT, '<b>TEST</b>', fontColor=INK3, fontSize=9.5)

model = [('1', 'Valuation', f'{m("V")} = 10 · {m("p")} · {m("q")}<sup>{m("κ")}</sup>', f'rational: {m("κ")} = 0'),
         ('2', 'Choice', f'JOIN if {m("V")} &gt; {m("θ")} · {m("s")}', f'rational: {m("θ")} = 1')]
for (x0, x1), (num, title, formula, note) in zip(C, model):
    box(x0, yM, x1 - x0, hM, '', rounded=1, arcSize=10, fillColor=HEAD, strokeColor='none')
    box(x0 + 14, yM + 13, 18, 18, f'<b>{num}</b>', shape='ellipse', fillColor=INK, strokeColor='none',
        fontColor='#FFFFFF', fontSize=10, align='center', verticalAlign='middle')
    text(x0 + 40, yM + 10, 120, 24, f'<b>{title}</b>', fontSize=12.5)
    text(x0 + 14, yM + 40, x1 - x0 - 28, 26, formula, fontSize=15, fontFamily=MATH)
    text(x1 - 130, yM + 10, 116, 24, note, fontSize=10, fontColor=INK2, align='right')
line(C[0][1] + 4, yM + hM / 2, C[1][0] - 4, yM + hM / 2)

tests = [(f'Change an irrelevant probability {m("q")}<br>(a message, an outdated prior)', '0 pp', '+4 to +13 pp',
          f'⇒ {m("κ")} &gt; 0: failure to condition'),
         (f'Raise the outside option {m("s")}<br>from 4 to 6', '−100 pp', '−4 pp',
          f'⇒ {m("θ")} ≈ 0.08: opportunity-cost neglect')]
for (x0, x1), (what, bench, obs, verdict) in zip(C, tests):
    w = x1 - x0
    box(x0, yT, w, hT, '', rounded=1, arcSize=6, fillColor=CELL, strokeColor=LINE)
    text(x0 + 16, yT + 8, w - 32, 30, what, fontSize=10.5, fontColor=INK2, verticalAlign='top')
    half = (w - 32) / 2
    for k, (lab, val, col) in enumerate((('rational', bench, INK), ('GPT-6 Luna', obs, CLAY))):
        text(x0 + 16 + k * half, yT + 42, half, 12, lab, fontSize=9, fontColor=INK3 if k == 0 else CLAY,
             verticalAlign='top')
        text(x0 + 16 + k * half, yT + 54, half, 24, f'<b>{val}</b>', fontSize=17, fontColor=col, verticalAlign='top')
    text(x0 + 16, yT + 84, w - 32, 20, f'<b>{verdict}</b>', fontSize=11, fontColor=CLAY)
    line(x0 + w / 2, yM + hM + 2, x0 + w / 2, yT - 2, color=LINE, width=1, arrow='none')

box(0, 0, W, yT + hT + 2, '', fillColor='none', strokeColor='none')   # fixed canvas for --crop

xml = ('<mxfile host="drawio" agent="make_fig1.py"><diagram id="fig1" name="Figure 1">'
       '<mxGraphModel dx="800" dy="600" grid="0" gridSize="10" guides="1" tooltips="1" connect="0" arrows="1" fold="1" '
       'page="0" pageScale="1" pageWidth="827" pageHeight="1169" math="0" shadow="0" background="#ffffff"><root>'
       '<mxCell id="0"/><mxCell id="1" parent="0"/>' + ''.join(cells) + '</root></mxGraphModel></diagram></mxfile>')
src = os.path.join(HERE, 'fig1.drawio')
open(src, 'w', encoding='utf-8').write(xml)
out = os.path.normpath(os.path.join(HERE, '..', '..', 'figure', 'fig_model.pdf'))
subprocess.run([DRAWIO, '-x', '-f', 'pdf', '--crop', '-o', out, src], check=True)
print('canvas', W, 'x', yT + hT + 2)
