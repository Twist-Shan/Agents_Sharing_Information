"""Render the five original paper figures from archived plotted values; no API calls.

The drawing functions retain the current paper layout and labels. The original
analysis is reproduced separately under reproduction/. Plotting from archived
metadata is not a substitute for rerunning those scientific checks.
"""
from pathlib import Path
import argparse,csv,json,math
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import FancyBboxPatch,FancyArrowPatch
from style import PALETTE as P, apply_style as _apply_style, style_axes
HERE=Path(__file__).resolve().parent
FONT_DIR=None
def apply_style(size=9.5):return _apply_style(size,font_dir=FONT_DIR)
MODELS=('luna','qwen','deepseek');NAMES={'luna':'Luna','qwen':'Qwen','deepseek':'DeepSeek'}
POLICY={'responsive':P['OliveTeal'],'independent':P['AegeanBlue'],'complement':P['Terracotta']}
DELTAS=('delta_table_safe4','delta_table_safe6','delta_prose_safe4','delta_prose_safe6');GRID=(.2,.35,.5,.65,.8)
def require(test,message):
    if not test:raise AssertionError(message)
result_meta=json.loads((HERE/'inputs/decision_results.json').read_text())
curve_meta=json.loads((HERE/'inputs/capability_choices.json').read_text())
interaction_meta=json.loads((HERE/'inputs/receipt_interaction.json').read_text())
data={'cohorts':{m:{'analysis':{'value_family_2':{},'primary_family_7':{}}} for m in MODELS}}
for row in result_meta['empirical_traces']:
    data['cohorts'][row['model']]['analysis'][row['family']][row['contrast']]={**row,'unresolved_blocks':0}
def capability_cells(_):return {(c['context'],c['safe'],c['p']):c for c in curve_meta['cells']}
def finish(fig,*args):
    if len(args)==6:
        out,name,sources,d,caption,metadata=args
        stem=out/name
        key='empirical_traces' if name=='decision_results' else 'cells'
        expected=result_meta[key] if name=='decision_results' else curve_meta[key]
        assert metadata[key]==expected
    else:stem,metadata,sources,caption=args
    fig.savefig(stem.with_suffix('.pdf'),facecolor='white')
    fig.savefig(stem.with_suffix('.png'),dpi=160,facecolor='white')
    stem.with_suffix('.json').write_text(json.dumps(metadata,indent=2)+'\n')
    plt.close(fig)
def interaction_cells(study):
    return {(r['encoding'],law):r[law] for r in interaction_meta['estimates_and_denominators'] if r.get('study')==study for law in ('R','S')}
def historical_inputs():return {},interaction_cells('Discovery')
def new_joint_cells(_):return interaction_cells('Validation')

def effect(ax,y,row,color,marker):
    require(row['point'] is not None and row['unresolved_blocks']==0,'incomplete_main_effect')
    ci=row['approximate_simultaneous_95_ci'];require(ci is not None and ci[0]<=row['point']<=ci[1],'missing_or_invalid_approximate_interval')
    point=100*row['point'];lo,hi=[100*v for v in ci]
    ax.errorbar(point,y,xerr=[[point-lo],[hi-point]],fmt=marker,color=color,ecolor=color,markersize=4.9,markeredgewidth=.65,markeredgecolor='white',capsize=2.2,elinewidth=1.2,zorder=3)
    return {'point':row['point'],'approximate_simultaneous_95_ci':ci,'n_blocks':row['n_blocks'],'family_size':row['family_size']}

def results(out,sources,data):
    apply_style(9.5)
    fig=plt.figure(figsize=(6.25,4.30));axes=[];traces=[]
    xs=(1.25,2.91,4.57);width=1.14
    for x,m in zip(xs,MODELS):
        fig.text((x+.63)/6.25,4.07/4.30,NAMES[m],fontsize=12,weight='bold',ha='center')
    fig.text(.025,3.74/4.30,'A  Response to partner policy',fontsize=10.5,weight='bold')
    fig.text(.025,2.14/4.30,'B  Same payoff lottery',fontsize=10.5,weight='bold')
    for row,(bottom,height) in enumerate(((2.52,1.05),(.67,1.33))):
        for col,(x,m) in enumerate(zip(xs,MODELS)):
            ax=fig.add_axes([x/6.25,bottom/4.30,width/6.25,height/4.30]);axes.append(ax)
            style_axes(ax,grid=None);ax.spines['left'].set_visible(False);ax.tick_params(axis='y',length=0,pad=5)
            ax.axvline(0,color=P['CoastalGray'],lw=.75,zorder=0)
            if row==0:
                ax.set_xlim(-80,80);ax.set_xticks([-50,0,50]);ax.set_ylim(-.55,1.55)
                labels=['With confirmation\nSAFE = 6','Without confirmation\nSAFE = 4'] if col==0 else ['','']
                ax.set_yticks([1,0],labels)
                rr=[(1,'responsive_safe6','responsive','o'),(0,'complement_safe4','complement','D')]
                family='value_family_2'
            else:
                ax.axvspan(-5,5,color=P['SandCream'],alpha=.45,zorder=-1,lw=0)
                ax.set_xlim(-25,30);ax.set_xticks([-20,0,20]);ax.set_ylim(-.55,3.55)
                ax.set_yticks([3,2,1,0],['Table · 4','Table · 6','Prose · 4','Prose · 6'] if col==0 else ['']*4)
                rr=[(y,n,'independent','o' if 'table' in n else 's') for y,n in zip((3,2,1,0),DELTAS)]
                family='primary_family_7'
            ax.text(1.075,1.04,'pp',transform=ax.transAxes,color=P['HarborSlate'],fontsize=9,ha='left')
            for y,n,policy,marker in rr:
                r=data['cohorts'][m]['analysis'][family][n]
                est=effect(ax,y,r,POLICY[policy],marker)
                traces.append({'model':m,'contrast':n,'family':family,**est})
                # A compact number column avoids placing labels over CIs.
                point=100*r['point'];label=f'{point:+.1f}' if abs(point)>1e-10 else '0.0'
                ax.text(1.075,y,label,transform=ax.get_yaxis_transform(),fontsize=9.5,ha='left',va='center',color=P['DeepNavy'])
    fig.text(.54,.066,'Change in JOIN choice: S − R (percentage points)',fontsize=10,ha='center')
    fig.text(.54,.017,'Approximate adjusted 95% intervals · shading: ±5 pp',fontsize=9,ha='center',color=P['HarborSlate'])
    caption=('Receipt effects under stated partner policies, with all three model interfaces shown on shared row scales. A reports both signed contrasts (responsive at SAFE=6 and complement at SAFE=4). B reports all four identical-lottery contrasts per interface; row labels identify table/prose presentation and SAFE payoff. Points and whiskers are paired estimates and approximate family-adjusted 95% difference intervals: two contrasts per interface in A and seven in B. Shading marks ±5 percentage points, not a joint equivalence verdict. Planned blocks: A,512/64/64; B,2048/128/128 for Luna/Qwen/DeepSeek. The complete tables retain conservative enclosures; no between-interface test is implied.')
    finish(fig,out,'decision_results',sources,data,caption,{'figure_kind':'terminal_empirical_estimates','main_models':list(MODELS),'empirical_traces':traces,'policy_colors':POLICY,'all_main_signed_and_independent_contrasts':True,'shared_x_limits_by_row':[[-80,80],[-25,30]],'no_new_inference':True})

def capability(out,sources,data,folder):
    apply_style(9.5);cells=capability_cells(folder);traces=[]
    require(all(r['missing']==0 for r in cells.values()),'linked_capability_incomplete')
    fig=plt.figure(figsize=(6.25,2.93));colors={4:P['AegeanBlue'],6:P['CoralRed']};markers={4:'o',6:'s'}
    for i,(context,title,x) in enumerate(zip(('minimal','full','card'),('Lottery only','Full task','Explicit payoffs'),(.53,2.48,4.43))):
        ax=fig.add_axes([x/6.25,.74/2.93,1.46/6.25,1.57/2.93]);style_axes(ax,grid=None)
        ax.set_xlim(.17,.84);ax.set_ylim(-4,106);ax.set_xticks([.2,.5,.8]);ax.set_yticks([0,50,100])
        ax.set_title(title,pad=12,loc='center',fontsize=11)
        if i==0:ax.set_ylabel('JOIN choices (%)')
        else:ax.tick_params(labelleft=False)
        for safe in (4,6):
            # Analytic optima are references, not added marginal uncertainty.
            threshold=safe/10
            ax.plot([.18,threshold,threshold,.83],[0,0,100,100],color=P['CoastalGray'],alpha=.7,lw=.8,ls=(0,(2,3)),zorder=1)
            rr=[cells[context,safe,p] for p in GRID];rates=[100*r['range'][0] for r in rr]
            ax.plot(GRID,rates,color=colors[safe],marker=markers[safe],ms=4.2,lw=1.55,ls='-' if safe==4 else (0,(4,2)),
                    markerfacecolor=colors[safe] if safe==4 else 'white',markeredgewidth=1.1,zorder=2 if safe==4 else 3)
            traces.extend({'context':context,'safe':safe,'p':p,**r} for p,r in zip(GRID,rr))
    fig.text(.53,.126,'Partner JOIN probability',fontsize=10,ha='center')
    handles=[Line2D([0],[0],color=colors[4],marker='o',lw=1.5,label='SAFE = 4'),
             Line2D([0],[0],color=colors[6],marker='s',markerfacecolor='white',lw=1.5,ls=(0,(4,2)),label='SAFE = 6'),
             Line2D([0],[0],color=P['CoastalGray'],lw=.9,ls=(0,(2,3)),label='Optimal choice')]
    fig.legend(handles=handles,loc='lower center',bbox_to_anchor=(.53,.006),ncol=3,fontsize=9.5,handlelength=2,columnspacing=1.5,handletextpad=.4)
    caption=('Luna choice rates for the same 64 prospectively linked blocks, with SAFE=4 and SAFE=6 overlaid in each context. The full-task and payoff-card conditions pool their balanced R/S and table/prose cells; probability one half uses only the linked64 core blocks, not the larger independent-policy sample. Curves connect empirical rates without marginal confidence intervals, and gray steps show analytic expected-payoff optima. The horizontal axis changes the stated partner probability, not time.')
    finish(fig,out,'capability_choices',sources,data,caption,{'figure_kind':'terminal_descriptive_choice_rates','linked_blocks_only':64,'contexts':['minimal','full','card'],'probability_grid':list(GRID),'cells':traces,'no_marginal_intervals_added':True,'not_a_temporal_trajectory':True,'line_encodings':{'safe4':'AegeanBlue solid circle','safe6':'CoralRed dashed open square'},'pooling':'Full/card: equal R/S x table/prose within linked blocks'})
def uncertainty(row,equivalence=None):
    if row['point'] is None:
        return row['finite_completion_range'],'finite completion bounds'
    if equivalence is not None:
        for key,label in [('approximate_tost_ci','prespecified 90.2% TOST interval'),
                          ('conservative_99_9_equivalence_bound','prespecified 99.9% zero-discordance bound')]:
            if key in equivalence:return equivalence[key],label
        return row['finite_completion_range'],'equivalence interval unavailable'
    if row['approximate_simultaneous_95_ci'] is not None:
        return row['approximate_simultaneous_95_ci'],'approximate family-adjusted 95% interval'
    if row['conservative_hoeffding_95_ci'] is not None:
        return row['conservative_hoeffding_95_ci'],'conservative family-adjusted 95% Hoeffding enclosure'
    return row['finite_completion_range'],'finite completion bounds only'

def draw_estimate(ax,y,row,color,marker='o',equivalence=None):
    bounds,kind=uncertainty(row,equivalence)
    a,b=[100*x for x in bounds]
    incomplete=row['point'] is None
    linestyle=(0,(3,2)) if 'Hoeffding' in kind or 'completion' in kind else '-'
    if a!=b:ax.plot([a,b],[y,y],color=color,lw=3 if incomplete else 1.35,ls=linestyle,solid_capstyle='butt')
    if row['point'] is not None:
        ax.scatter([100*row['point']],[y],s=34,color=color,marker=marker,zorder=3)
    return {'y':y,'point':row['point'],'bounds':bounds,'interval_type':kind,'n_blocks':row['n_blocks']}

def plot_interaction(analysis,out,sources):
    historical,old=historical_inputs();new=new_joint_cells(analysis)
    fig=plt.figure(figsize=(6.25,3.0))
    axes=[fig.add_axes([x,.23,.235,.54]) for x in (.09,.397,.704)]
    traces=[]
    for k,(ax,title,cells) in enumerate(zip(axes[:2],('A  Discovery','B  Validation'),(old,new))):
        ax.set_title(title,pad=12);style_axes(ax,grid=None)
        ax.set_xlim(-.22,1.22);ax.set_ylim(-3,103);ax.set_xticks([0,1],['R','S']);ax.set_yticks([0,50,100])
        if k==0:ax.set_ylabel('Joint JOIN (%)')
        else:ax.tick_params(labelleft=False)
        for e,color,marker,ls in [('table',P['AegeanBlue'],'o','-'),('prose',P['Terracotta'],'s',(0,(4,2)))]:
            ranges=[cells[e,law]['range'] for law in ('R','S')]
            if all(a==b for a,b in ranges):ax.plot([0,1],[100*a for a,b in ranges],color=color,marker=marker,ms=6 if e=='table' else 4,markerfacecolor='white' if e=='table' else color,lw=1.4,ls=ls)
            else:
                for x,(a,b) in enumerate(ranges):
                    x=x+(-.045 if e=='table' else .045)
                    if a==b:ax.scatter([x],[100*a],color=color,marker=marker,s=25)
                    else:ax.plot([x,x],[100*a,100*b],color=color,lw=4)
            traces.append({'study':title[3:],'encoding':e,'R':cells[e,'R'],'S':cells[e,'S']})
    ax=axes[2];ax.set_title('C  Paired effects',pad=12);style_axes(ax,grid=None)
    names=('tau_table','tau_prose','phi');rows=analysis['primary_family_7']
    extent=max(20,max(abs(v)*100 for n in names for v in uncertainty(rows[n])[0]));extent=math.ceil(extent/10)*10
    ax.set_xlim(-extent*1.1,extent*1.1);ax.set_xticks([-extent,0,extent]);ax.set_ylim(-.5,2.5);ax.axvline(0,color=P['CoastalGray'],lw=.8)
    ax.set_yticks([]);ax.spines['left'].set_visible(False);ax.set_xlabel('Effect (percentage points)',labelpad=8)
    for y,n,color,marker in zip((2,1,0),names,(P['AegeanBlue'],P['Terracotta'],P['HarborSlate']),('o','s','D')):
        traces.append({'contrast':n,**draw_estimate(ax,y,rows[n],color,marker)})
    handles=[Line2D([0],[0],color=P['AegeanBlue'],marker='o',markerfacecolor='white',lw=1.3,label='Table'),
             Line2D([0],[0],color=P['Terracotta'],marker='s',lw=1.3,ls=(0,(4,2)),label='Prose'),
             Line2D([0],[0],color=P['HarborSlate'],marker='D',lw=0,label='Table − prose')]
    fig.legend(handles=handles,loc='upper center',bbox_to_anchor=(.52,1.015),ncol=3,handlelength=1.6,columnspacing=1.8)
    caption=('The receipt-by-presentation pattern in historical discovery and independent validation: A–B show empirical joint-JOIN rates, without marginal confidence intervals. '
      'C shows the validation paired changes and their interaction with the frozen primary-family uncertainty; missing-response bounds or conservative enclosures remain explicitly identified in the source table.')
    finish(fig,out/'receipt_interaction',{'question':'Does the representation-dependent receipt effect transfer?',
        'historical_no_ci':True,'estimates_and_denominators':traces,'no_marginal_ci_invented':True,'display_offset_for_unresolved_rates':{'table':-.045,'prose':.045},
        'historical_source_sha256':interaction_meta['historical_source_sha256']},sources,caption)
def overview(out):
    # White background, Mediterranean colors.
    plt.rcParams.update({'font.family':'Times New Roman','pdf.fonttype':42,'ps.fonttype':42})
    C={'blue':'#2F88B8','teal':'#4FA58A','terra':'#E57D3F','slate':'#56627A','ink':'#25313B','gray':'#9AA3A6'}
    fig,ax=plt.subplots(figsize=(12,6.25));fig.patch.set_facecolor('white')
    ax.set(xlim=(0,12),ylim=(0,6.25));ax.axis('off');fig.subplots_adjust(0,0,1,1)
    def text(x,y,t,size=13,weight='normal',color=None,ha='left',va='center'):
        return ax.text(x,y,t,fontsize=size,fontweight=weight,color=color or C['ink'],ha=ha,va=va,linespacing=1.25)
    def box(x,y,w,h,color='slate',fill='white',lw=1):
        ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle='round,pad=0.015,rounding_size=0.09',facecolor=fill,edgecolor=C.get(color,color),lw=lw))
    def arrow(x,y,u,v,color='slate'):
        ax.add_patch(FancyArrowPatch((x,y),(u,v),arrowstyle='-|>',mutation_scale=13,color=C[color],lw=1.3))
    text(.15,5.98,'A   Two agents, one joint task',17,'bold')
    box(.15,5.17,11.65,.57,'gray','#F6F8F9')
    text(5.975,5.58,'Public status: the task can proceed.',13,ha='center')
    text(5.975,5.31,'Confirmation: both agents received task-status notices. This is not a promise to join.',13,ha='center')
    for x,name,col in [(0.25,'Agent A','blue'),(4.05,'Agent B','teal')]:
        box(x,3.7,3.15,1.32,col)
        text(x+.18,4.76,name,16,'bold',C[col]);text(x+.18,4.38,'Sees its own confirmation',14)
        text(x+.18,3.98,'Choose JOIN or SAFE',14,'bold')
    text(3.71,4.45,'+',19,'bold',ha='center')
    arrow(7.30,4.35,7.94,4.35)
    text(8.12,4.84,'Choices determine payoffs',15,'bold')
    for y,t in [(4.45,'Both JOIN: 10 points each'),(4.09,'Mismatch: JOIN gets 0; SAFE gets s'),(3.73,'Both SAFE: s each (s = 4 or 6)')]:text(8.12,y,t,13)
    text(.15,3.28,'B   Change what the agent knows about its partner',17,'bold')
    text(.28,2.90,'Given my confirmation, how likely is my partner to have one?',13)
    text(9.28,2.90,'R: ½   →   S: 1',17,'bold',C['blue'])
    rows=[(.15,'With confirmation','Partner joins only with confirmation','Partner JOIN: ½ → 1','Expected JOIN payoff: 5 → 10','SAFE → JOIN  (s = 6)','teal'),
          (4.10,'Random partner','Joins independently of confirmation','Partner JOIN: ½ → ½','Expected JOIN payoff: 5 → 5','Same lottery, same choice probabilities','blue'),
          (8.05,'Without confirmation','Partner joins only without confirmation','Partner JOIN: ½ → 0','Expected JOIN payoff: 5 → 0','JOIN → SAFE  (s = 4)','terra')]
    for x,head,rule,prob,val,pred,col in rows:
        box(x,.97,3.75,1.62,col)
        text(x+.17,2.34,head,15,'bold',C[col]);text(x+.17,2.03,rule,11.5)
        text(x+.17,1.71,prob,13);text(x+.17,1.40,val,13,'bold')
        text(x+1.875,1.08,pred,11.5,ha='center')
    text(.15,.58,'C   Evaluate three distinct questions',17,'bold')
    for x,t,c in [(2.0,'Adapt when payoffs change','teal'),(5.98,'Stay consistent when they do not','blue'),(9.92,'Does joint action improve payoff?','terra')]:
        text(x,.16,t,13,'bold',C[c],ha='center')
    fig.savefig(out/'task_schematic.pdf',facecolor='white')
    fig.savefig(out/'task_schematic.png',dpi=160,facecolor='white');plt.close(fig)

def joint_outcomes(out,rows):
    apply_style(9.5)
    fig,axs=plt.subplots(1,3,figsize=(6.25,2.8),gridspec_kw={'left':.15,'right':.965,'bottom':.28,'top':.77,'wspace':.25})
    specs=[('A  Joint participation','joint_join_range',100,P['AegeanBlue'],'Change (percentage points)',(-1,28),[0,10,20]),
           ('B  Mismatch','mismatch_range',100,P['Terracotta'],'Change (percentage points)',(-1,28),[0,10,20]),
           ('C  Mean payoff','pair_mean_score_range',1,P['HarborSlate'],'Change (points)',(-.22,1.02),[0,.4,.8])]
    labels=['Table · SAFE 4','Table · SAFE 6','Prose · SAFE 4','Prose · SAFE 6']
    for index,(ax,(title,field,scale,color,xlabel,xlim,ticks)) in enumerate(zip(axs,specs)):
        style_axes(ax,grid='x')
        ax.spines['left'].set_visible(False)
        ax.axvline(0,color=P['CoastalGray'],lw=.8,zorder=1)
        ax.axhline(1.5,color=P['CoastalGray'],alpha=.35,lw=.6)
        ax.set(xlim=xlim,ylim=(-.45,3.55),xticks=ticks,yticks=[3,2,1,0],yticklabels=labels if index==0 else [])
        ax.tick_params(axis='y',length=0,pad=5)
        ax.tick_params(axis='x',labelsize=9)
        ax.set_title(title,fontsize=10,pad=17)
        ax.set_xlabel(xlabel,fontsize=9,labelpad=8)
        for y,row in zip([3,2,1,0],rows):
            value=scale*row['delta_'+field]
            ax.plot([0,value],[y,y],color=color,alpha=.5,lw=2.6,solid_capstyle='round',zorder=2)
            ax.scatter([value],[y],s=26,color=color,edgecolor='white',linewidth=.7,zorder=3)
            # Direct values make small payoff changes readable without changing the zero baseline.
            label=f'{value:+.2f}'
            ax.annotate(label,(value,y),xytext=(5,7),textcoords='offset points',ha='left',va='center',fontsize=9,color=P['DeepNavy'])
    fig.text(.15,.94,'Joint action and its payoff consequences',weight='bold',fontsize=11.5,color=P['DeepNavy'])
    fig.text(.15,.035,'Luna · S − R · all four presentation–payoff conditions',fontsize=9,color=P['HarborSlate'])

    fig.savefig(out/'joint_outcomes.pdf',facecolor='white')
    fig.savefig(out/'joint_outcomes.png',dpi=160,facecolor='white')
    plt.close(fig)

def main():
    global FONT_DIR
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output',type=Path,default=HERE.parent/'outputs/figures')
    p.add_argument('--font-dir',type=Path)
    a=p.parse_args();FONT_DIR=a.font_dir
    out=a.output.resolve();out.mkdir(parents=True,exist_ok=True)
    results(out,[],data);capability(out,[],data,None)
    overview(out)
    with (HERE/'inputs/joint_outcomes_source.csv').open(newline='') as f:
        rows=[{k:v if k=='encoding' else float(v) for k,v in row.items()} for row in csv.DictReader(f)]
    joint_outcomes(out,rows)
    analysis={'primary_family_7':{r['contrast']:{'point':r['point'],'approximate_simultaneous_95_ci':r['bounds'],'n_blocks':r['n_blocks']} for r in interaction_meta['estimates_and_denominators'] if 'contrast' in r}}
    apply_style(9.5);plot_interaction(analysis,out,[])
    print('Rendered five figures:',out)
if __name__=='__main__':main()
