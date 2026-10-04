"""Design and results together: targeted-review figures from terminal exports."""
from pathlib import Path
import json,csv,argparse
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch,FancyArrowPatch
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.lines import Line2D
from style import PALETTE as P,apply_style,style_axes,save_figure
HERE=Path(__file__).resolve().parent
B=P['AegeanBlue'];T=P['Terracotta'];G=P['OliveTeal'];N=P['DeepNavy'];S=P['HarborSlate']

def label(fig,x,y,text):fig.text(x,y,text,fontsize=10,weight='bold',va='top')
def box(ax,x,y,w,h,text,color=B):
    ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle='round,pad=0.025,rounding_size=0.03',fc='white',ec=color,lw=1.1))
    ax.text(x+w/2,y+h/2,text,ha='center',va='center',fontsize=9,color=N)
def arrow(ax,a,b,color=S):ax.add_patch(FancyArrowPatch(a,b,arrowstyle='-|>',mutation_scale=9,color=color,lw=1.1))
def interval(ax,y,point,approx,cons,color,marker='o'):
    if cons is not None:ax.plot(np.array(cons)*100,[y,y],c=color,lw=.7,alpha=.65)
    if approx is not None:ax.plot(np.array(approx)*100,[y,y],c=color,lw=2.2)
    ax.plot(point*100,y,marker=marker,color=color,ms=4.5,mec='white',mew=.5)
def save(fig,out,name,source,extra):
    save_figure(fig,out/name,sources=[source,HERE/'inputs/stored_contrasts.csv',HERE/'inputs/all_programmed_condition_rates_by_wording.csv'],metadata=extra,overwrite=True)
    plt.close(fig)

def render(source,out,font_dir=None):
    d=json.loads(source.read_text(encoding='utf-8'));assert d['planned']==5632
    apply_style(9,font_dir=font_dir)
    pri={r['name']:r for r in d['primary']};cells=d['cells']
    old=list(csv.DictReader((HERE/'inputs/stored_contrasts.csv').open(encoding='utf-8-sig')))
    old={r['contrast']:r for r in old if r['model_key']=='luna'}
    words=list(csv.DictReader((HERE/'inputs/all_programmed_condition_rates_by_wording.csv').open(encoding='utf-8-sig')))
    def cell(*key):return next(r for r in cells if tuple(r['cell'])==key)
    # Figure 1 follow-up: a simple intervention strip above matched results.
    fig=plt.figure(figsize=(6.5,3.05))
    a=fig.add_axes([.02,.75,.96,.23]);a.set_xlim(0,10);a.set_ylim(0,1);a.axis('off')
    box(a,.05,.18,2.4,.60,'Partner joins: 50%',B)
    arrow(a,(2.55,.48),(3.05,.48))
    box(a,3.15,.18,2.7,.60,'JOIN: 10 or 0  ·  SAFE: 4 or 6',B)
    arrow(a,(5.95,.48),(6.4,.48))
    box(a,6.5,.18,3.35,.60,'R → S: same payoff lottery',T)
    ax=fig.add_axes([.17,.22,.39,.42]);style_axes(ax,'x');ax.axvline(0,c=S,lw=.8)
    keys=[(4,'table'),(6,'table'),(4,'prose'),(6,'prose')]
    for i,(s,e) in enumerate(keys):
        r=old[f'delta_{e}_safe{s}'];interval(ax,3-i+.10,float(r['point']),json.loads(r['approximate_simultaneous_95_ci']),json.loads(r['conservative_hoeffding_95_ci']),B)
        r=pri[f'core_s{s}_{e}'];interval(ax,3-i-.10,r['estimate'],r['approx_ci'],r['hoeffding_ci'],T,'s')
    ax.set_yticks(range(4),[f'{e.title()} · SAFE {s}' for s,e in keys[::-1]])
    ax.tick_params(axis='y',length=0);ax.spines['left'].set_visible(False)
    ax.set_xlim(-38,50);ax.set_ylim(-.5,3.5);ax.set_xticks([-25,0,25,50]);ax.set_xlabel('Change in JOIN (pp)')
    label(fig,.025,.69,'A  Original and fresh replication')
    ax.legend(handles=[Line2D([],[],marker='o',color=B,lw=0,label='Original'),Line2D([],[],marker='s',color=T,lw=0,label='Fresh')],loc='upper center',bbox_to_anchor=(.5,-.30),ncol=2,handletextpad=.3,columnspacing=1.1,fontsize=8)
    ax=fig.add_axes([.69,.22,.27,.42]);style_axes(ax,'y')
    for f,c,mark in [('partner',B,'o'),('device',G,'s')]:
        rates=[np.mean([cell('framing',f,l,s,e)['join'] for s in (4,6) for e in ('table','prose')])*100 for l in ('R','S')]
        ax.plot([0,1],rates,marker=mark,c=c,lw=1.4,ms=5,label=f.title())
    ax.set_xticks([0,1],['Independent R','Joint S'],fontsize=8);ax.set_xlim(-.2,1.2);ax.set_ylim(0,100);ax.set_yticks([0,50,100]);ax.set_ylabel('Risky choice (%)')
    ax.legend(loc='upper center',bbox_to_anchor=(.5,-.30),ncol=2,fontsize=8,handlelength=1.1,columnspacing=.8)
    label(fig,.64,.69,'B  Matched descriptions')
    save(fig,out,'same_payoff_controls',source,{'primary':d['primary'][:5],'matched_cells':[r for r in cells if r['cell'][0]=='framing'],'intervals':'approximate thick; Hoeffding thin; matched rates descriptive'})
    # Policy figure: incentives, wording sensitivity, then isolated referent edit.
    fig=plt.figure(figsize=(6.5,2.65))
    label(fig,.02,.96,'A  Payoff implications')
    a=fig.add_axes([.02,.17,.30,.62]);a.set_xlim(0,1);a.set_ylim(0,1);a.axis('off')
    a.text(0,.95,'Partner joins...',weight='bold',fontsize=9)
    a.text(0,.70,'with confirmation',color=G);a.text(0,.45,'without confirmation',color=T)
    a.text(.98,.70,'50% → 100%',ha='right',color=G);a.text(.98,.45,'50% → 0%',ha='right',color=T)
    a.text(0,.14,'R → S changes its action probability',fontsize=8,color=S)
    label(fig,.355,.96,'B  Original wording variants')
    ax=fig.add_axes([.40,.23,.23,.54]);style_axes(ax,'y');ax.axhline(0,c=S,lw=.8)
    for policy,s,c in [('responsive',6,G),('complement',4,T)]:
        yy=[]
        for w in range(4):
            found={r['law']:float(r['join_rate']) for r in words if r['model']=='luna' and r['policy']==policy and int(r['safe'])==s and int(r['wording'])==w and r['encoding']=='all'}
            yy.append((found['S']-found['R'])*100)
        ax.plot(range(4),yy,'o-',c=c,ms=4,lw=1.2)
    ax.set_xticks(range(4),['0','1','2','3']);ax.set_xlabel('Wording');ax.set_ylabel('Change in JOIN (pp)');ax.set_ylim(-65,75);ax.set_yticks([-50,0,50])
    label(fig,.69,.96,'C  Minimal referent edit')
    ax=fig.add_axes([.74,.23,.23,.54]);style_axes(ax,'y')
    for edit,c,mark,title in [('original',S,'o','Original'),('explicit_own',B,'s',"Partner’s own")]:
        yy=[np.mean([cell('referent',edit,l,s,e)['join'] for s in (4,6) for e in ('table','prose')])*100 for l in ('R','S')]
        ax.plot([0,1],yy,c=c,marker=mark,ms=5,lw=1.4,label=title)
    ax.set_xticks([0,1],['R','S']);ax.set_xlim(-.2,1.2);ax.set_ylim(0,100);ax.set_yticks([0,50,100]);ax.set_ylabel('JOIN (%)')
    ax.legend(loc='upper center',bbox_to_anchor=(.5,-.17),fontsize=8,handlelength=1.0,ncol=1,labelspacing=.10,borderaxespad=0)
    save(fig,out,'policy_referent',source,{'interaction':pri['explicit_own_minus_original_protocol_effect'],'rates':'descriptive; all four payoff-format cells pooled'})
    # Explicit-probability transfer: compact common-key matrices, every recipe.
    fig=plt.figure(figsize=(6.5,3.10))
    recipes=[(.5,10,0,4),(.5,10,0,6),(.1,12,-2,0),(.3,12,-2,1),(.6,8,-4,4),(.9,8,-4,6),(.4,15,-5,4),(.7,15,-5,7)]
    cmap=LinearSegmentedColormap.from_list('MediterraneanAccuracy',[P['SandCream'],P['SeaSky'],B])
    labels=[f'{p:g}   |   {h:g} / {l:g}   |   {s:g}' for p,h,l,s in recipes]
    for pos,(task,title) in enumerate([('payoffs','A  Report both expected scores'),('action','B  Choose the better action')]):
        ax=fig.add_axes([.29+pos*.345,.20,.255,.64])
        vals=np.array([[cell('payoff_transfer',i,c,task)['correct'] for c in ('full_R','full_S','lottery')] for i in range(8)])
        im=ax.imshow(vals,vmin=0,vmax=1,cmap=cmap,aspect='auto')
        ax.set_xticks([0,1,2],['Full R','Full S','Lottery']);ax.tick_params(length=0)
        ax.set_yticks(range(8),labels if pos==0 else ['']*8,fontsize=8.5)
        for x in [.5,1.5]:ax.axvline(x,c='white',lw=2)
        for y in np.arange(.5,7.5):ax.axhline(y,c='white',lw=2)
        ax.axhline(1.5,c=S,lw=1);[s.set_visible(False) for s in ax.spines.values()]
        label(fig,.24+pos*.36,.97,title)
    fig.text(.015,.86,'p   |   JOIN high / low   |   SAFE',fontsize=8.5,color=S)
    fig.text(.012,.71,'Original\nanchors',fontsize=8,color=S)
    fig.text(.012,.43,'New\ncombinations',fontsize=8,color=S)
    cax=fig.add_axes([.33,.075,.52,.027]);cb=fig.colorbar(im,cax=cax,orientation='horizontal',ticks=[0,.5,1]);cb.ax.set_xticklabels(['0%','50%','100% correct']);cb.outline.set_visible(False);cb.ax.tick_params(length=0,labelsize=8)
    save(fig,out,'payoff_transfer',source,{'recipes':recipes,'cells':[r for r in cells if r['cell'][0]=='payoff_transfer'],'rates':'descriptive; each cell 32 independent calls'})

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--input',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--font-dir',type=Path);a=p.parse_args();a.output.mkdir(parents=True,exist_ok=True);render(a.input,a.output,a.font_dir)
