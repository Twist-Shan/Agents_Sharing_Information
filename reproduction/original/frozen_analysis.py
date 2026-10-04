"""Prespecified all-planned block analysis; never selects observations by choice.
Approximate intervals require independent block vectors and a stable first-valid
response policy within the prespecified mixture. Pure transport pauses do not
alone cancel inference; identity failure, missingness and drift remain explicit.
"""
from collections import defaultdict
import math
import numpy as np
from scipy.stats import t, norm
from scipy.optimize import minimize

ALPHA=.05
EQUIVALENCE_MARGIN=.05
TOST_ALPHA=.049
ZERO_DISCORDANCE_ALPHA=.001
PRIMARY_NAMES=('tau_table','tau_prose','phi','delta_table_safe4','delta_table_safe6','delta_prose_safe4','delta_prose_safe6')


def _a(job,outcomes):
    obj=outcomes.get(job['id'])
    if isinstance(obj,str): value=obj
    elif isinstance(obj,dict) and obj.get('valid') is True:
        value=obj.get('action')
        if value not in ('JOIN','SAFE'):raise ValueError('valid outcome lacks decoded action')
    else:value=None
    if value is not None and value not in ('JOIN','SAFE'):raise ValueError('outcomes must use decoded JOIN/SAFE')
    return (float(value=='JOIN'),)*2 if value is not None else (0.,1.)


def _lin(terms):
    lo=hi=0.
    for coef,(a,b) in terms:
        lo+=coef*(a if coef>=0 else b)
        hi+=coef*(b if coef>=0 else a)
    return lo,hi


def _joint(a,b):
    if a==(0.,0.) or b==(0.,0.):return (0.,0.)
    if a==b==(1.,1.):return (1.,1.)
    return (0.,1.)


def _stratum(meta,free=False):
    return (meta['wording'],meta['mapping'],meta['display_order'],meta['free_safe'] if free else meta['actor'])


def _moments(rows):
    cells=defaultdict(list)
    for cell,lo,hi in rows:
        assert lo==hi
        cells[cell].append(lo)
    n=len(rows);v=den=0.
    for xs in cells.values():
        k=len(xs)
        if k<2:return None
        part=(k/n)**2*float(np.var(xs,ddof=1))/k
        v+=part;den+=part*part/(k-1)
    if v<=0:return None
    return math.sqrt(v),v*v/den


def estimate(rows,support,family_size,complete):
    n=len(rows)
    if not n:raise ValueError('empty contrast')
    lo=sum(r[1] for r in rows)/n;hi=sum(r[2] for r in rows)/n
    result=dict(n_blocks=n,finite_completion_range=[lo,hi],point=lo if lo==hi else None,
                unresolved_blocks=sum(r[1]!=r[2] for r in rows),support=list(support),
                family_size=family_size,approximate_simultaneous_95_ci=None,
                conservative_hoeffding_95_ci=None,se=None,df=None)
    if not complete or lo!=hi:return result
    radius=(support[1]-support[0])*math.sqrt(math.log(2*family_size/ALPHA)/(2*n))
    result['conservative_hoeffding_95_ci']=[max(support[0],lo-radius),min(support[1],hi+radius)]
    moment=_moments(rows)
    if moment is None:
        result['approximation_note']='No estimated variance or too few within-stratum replicates; use conservative enclosure, not a zero-width interval.'
        return result
    se,df=moment;crit=float(t.ppf(1-ALPHA/(2*family_size),df))
    result.update(se=se,df=df,approximate_simultaneous_95_ci=[max(support[0],lo-crit*se),min(support[1],hi+crit*se)])
    return result


def _capability_blocks(index,profile):
    n=64 if profile=='full' else 32
    grid=(.2,.35,.5,.65,.8) if profile=='full' else (.5,)
    result=[]
    for b in range(n):
        rows=[]
        for p in grid:
            for s in (4,6):
                minimal=index[('minimal',b,'none','none',s,0,p)]
                full=[index[('independent' if p==.5 else 'grid_full',b,q,e,s,0,p)] for q in ('R','S') for e in ('table','prose')]
                card=[index[('payoff_card',b,q,e,s,0,p)] for q in ('R','S') for e in ('table','prose')]
                rows.append((p,s,minimal,full,card))
        result.append(rows)
    return result


def _correct(job,outcomes):
    a=_a(job,outcomes)
    return a if job['expected']=='JOIN' else (1-a[1],1-a[0])


def _prediction(capblocks,outcomes,complete):
    if not complete:return {'status':'not_computed_missing_planned_responses'}
    obs=[]
    for b,rows in enumerate(capblocks):
        for p,s,mini,full,card in rows:
            for context,items in (('minimal',[mini]),('full',full),('card',card)):
                for j in items:
                    m=j['metadata'];y=_a(j,outcomes)[0]
                    obs.append(dict(context=context,p=p,s=s,law=m['law'],encoding=m['encoding'],wording=m['wording'],block=b,y=y))
    def features(r,enriched):
        x=10*r['p']-r['s']
        if not enriched:return [1.,x]
        full=float(r['context']=='full');card=float(r['context']=='card')
        ss=float(r['law']=='S');prose=float(r['encoding']=='prose')
        return [1.,x,full,card,ss,prose,ss*prose,full*x,card*x]
    train=[r for r in obs if r['wording'] in (0,1)];test=[r for r in obs if r['wording'] in (2,3)]
    def weights(rows):
        # Equal weight to each capability context and p,s combination: the
        # minimal task has one response where receipt contexts cross four cells.
        counts=defaultdict(int)
        for r in rows:counts[(r['context'],r['p'],r['s'])]+=1
        return np.array([1/counts[(r['context'],r['p'],r['s'])] for r in rows])
    result=dict(status='fixed_heldout_wording_prediction',train_wordings=[0,1],test_wordings=[2,3],
                training_n=len(train),test_n=len(test),penalty='L2 coefficient=1 on nonintercept; weighted objective scaled to training observation count',
                feature_sets={'payoff_only':['intercept','10p-safe'],
                              'payoff_and_context':['intercept','10p-safe','full','card','S','prose','S*prose','full*(10p-safe)','card*(10p-safe)']},models={})
    for label,enriched in (('payoff_only',False),('payoff_and_context',True)):
        X=np.array([features(r,enriched) for r in train]);Y=np.array([r['y'] for r in train]);W=weights(train);W=W/W.sum()*len(train)
        def objective(beta):
            z=X@beta
            loss=np.sum(W*(np.logaddexp(0,z)-Y*z))+.5*np.sum(beta[1:]**2)
            pr=1/(1+np.exp(-np.clip(z,-50,50)))
            grad=X.T@(W*(pr-Y));grad[1:]+=beta[1:]
            return float(loss),grad
        fit=minimize(objective,np.zeros(X.shape[1]),method='L-BFGS-B',jac=True,options={'maxiter':2000,'ftol':1e-12,'gtol':1e-8})
        if not fit.success:
            result['models'][label]={'status':'optimization_failed','message':str(fit.message)};continue
        XT=np.array([features(r,enriched) for r in test]);YT=np.array([r['y'] for r in test]);WT=weights(test);WT/=WT.sum()
        pp=1/(1+np.exp(-np.clip(XT@fit.x,-35,35)))
        ll=-(YT*np.log(pp)+(1-YT)*np.log1p(-pp));bb=(pp-YT)**2
        cellmetrics=[]
        for context in ('minimal','full','card'):
            mask=np.array([r['context']==context for r in test]);wc=WT[mask]/WT[mask].sum()
            cellmetrics.append(dict(context=context,log_loss=float(wc@ll[mask]),brier=float(wc@bb[mask]),n=int(mask.sum())))
        result['models'][label]=dict(status='fit',coefficients=fit.x.tolist(),test_log_loss=float(WT@ll),test_brier=float(WT@bb),by_context=cellmetrics)
    result['interpretation']='Predictive reduced-form comparison on two fixed heldout wordings, not a latent cognitive model or an estimate over all possible language.'
    return result


def analyze(jobs,outcomes,plan=None):
    plan=plan or {};profile=plan.get('allocationprofile',plan.get('allocation_profile','full'))
    ids={j['id'] for j in jobs}
    if len(ids)!=len(jobs) or not set(outcomes)<=ids:raise ValueError('duplicate or unknown logical outcome id')
    complete=all(_a(j,outcomes)[0]==_a(j,outcomes)[1] for j in jobs)
    index={};groups=defaultdict(list)
    for j in jobs:
        m=j['metadata'];actor=m['actor'] if j['module']=='free' else 0
        key=(j['module'],m['block_index'],m['law'],m['encoding'],m['safe'],actor,m['p'])
        if key in index:raise ValueError('duplicate condition')
        index[key]=j;groups[j['module'],m['block_index']].append(j)
    primary={k:[] for k in PRIMARY_NAMES};value={'responsive_safe6':[],'complement_safe4':[]}
    for (module,b),rows in groups.items():
        m=rows[0]['metadata']
        if module=='free':
            s=m['safe'];cell=_stratum(m,True);d={}
            for e in ('table','prose'):
                js={q:_joint(_a(index[('free',b,q,e,s,0,None)],outcomes),_a(index[('free',b,q,e,s,1,None)],outcomes)) for q in ('R','S')}
                d[e]=_lin([(1,js['S']),(-1,js['R'])]);primary['tau_'+e].append((cell,*d[e]))
            primary['phi'].append((cell,*_lin([(1,d['table']),(-1,d['prose'])])))
        elif module=='independent':
            cell=_stratum(m)
            for e,s in ((e,s) for e in ('table','prose') for s in (4,6)):
                delta=_lin([(1,_a(index[(module,b,'S',e,s,0,.5)],outcomes)),(-1,_a(index[(module,b,'R',e,s,0,.5)],outcomes))])
                primary[f'delta_{e}_safe{s}'].append((cell,*delta))
        elif module in ('responsive','complement'):
            s=6 if module=='responsive' else 4;cell=_stratum(m);terms=[]
            for q in ('R','S'):
                p=.5 if q=='R' else (1. if module=='responsive' else 0.)
                for e in ('table','prose'):
                    terms.append(((.5 if q=='S' else -.5),_a(index[(module,b,q,e,s,0,p)],outcomes)))
            value[module+f'_safe{s}'].append((cell,*_lin(terms)))
    primary_rows=primary
    primary={k:estimate(v,(-2,2) if k=='phi' else (-1,1),7,complete) for k,v in primary.items()}
    value={k:estimate(v,(-1,1),2,complete) for k,v in value.items()}
    equivalence={'margin':EQUIVALENCE_MARGIN,'alpha':.05,'normal_branch_alpha':TOST_ALPHA,'zero_discordance_branch_alpha':ZERO_DISCORDANCE_ALPHA,'global_all_four_equivalent':None,'per_contrast_tost':{},
                 'rule':'Intersection-union global claim: all four contrasts must pass. Per contrast, alpha=.049 approximate TOST plus alpha=.001 exact zero-discordance fallback reserve total alpha=.05. No individual equivalence claim from a lone pass. Full profile only.'}
    if complete and profile=='full':
        flags=[]
        for name,r in primary.items():
            if not name.startswith('delta_'):continue
            if r['se'] is None:
                if all(lo==hi==0. for _,lo,hi in primary_rows[name]):
                    upper=-math.expm1(math.log(ZERO_DISCORDANCE_ALPHA)/r['n_blocks'])
                    passed=upper<.05
                    equivalence['per_contrast_tost'][name]={'method':'independent-block zero-discordance conservative exact bound','conservative_99_9_equivalence_bound':[-upper,upper],'passed':passed}
                    flags.append(passed);continue
                equivalence['per_contrast_tost'][name]={'passed':False,'reason':'variance_estimate_unavailable'};flags.append(False);continue
            point,se,df=r['point'],r['se'],r['df'];c=float(t.ppf(1-TOST_ALPHA,df));ci=[point-c*se,point+c*se]
            passed=ci[0]>-.05 and ci[1]<.05
            pval=max(float(t.sf((point+.05)/se,df)),float(t.cdf((point-.05)/se,df)))
            equivalence['per_contrast_tost'][name]=dict(approximate_tost_ci=ci,interval_coverage=1-2*TOST_ALPHA,tost_p=pval,passed=passed);flags.append(passed)
        equivalence['global_all_four_equivalent']=all(flags)
    capblocks=_capability_blocks(index,profile);cap={'minimal_minus_full_accuracy':[],'card_minus_full_accuracy':[],'card_minus_full_payoff_sensitivity_at_half':[]}
    for rows in capblocks:
        meta=rows[0][2]['metadata'];cell=_stratum(meta);terms1=[];terms2=[];terms3=[];n=len(rows)
        for p,s,mini,full,card in rows:
            terms1.append((1/n,_correct(mini,outcomes)))
            for f,c in zip(full,card):
                terms1.append((-1/(4*n),_correct(f,outcomes)))
                terms2.extend([(1/(4*n),_correct(c,outcomes)),(-1/(4*n),_correct(f,outcomes))])
                if p==.5:
                    sign=1 if s==4 else -1
                    terms3.extend([(sign/4,_a(c,outcomes)),(-sign/4,_a(f,outcomes))])
        for k,terms in zip(cap,(terms1,terms2,terms3)):cap[k].append((cell,*_lin(terms)))
    # Capability panels have 64/32 blocks. For stable interval estimation we
    # condition on four fixed wording strata, not 32 nuisance combinations.
    cap={k:estimate([((cell[0],),lo,hi) for cell,lo,hi in rows],(-2,2) if 'sensitivity' in k else (-1,1),3,complete) for k,rows in cap.items()}
    summary=defaultdict(list);free=defaultdict(list)
    for j in jobs:
        m=j['metadata'];key=(j['module'],m['wording'],m['law'],m['encoding'],m['safe'],m['p'])
        summary[key].append(j)
        if j['module']=='free':free[(m['block_index'],m['wording'],m['law'],m['encoding'],m['safe'])].append(j)
    cells=[]
    for key,rows in sorted(summary.items(),key=lambda x:str(x[0])):
        aa=[_a(j,outcomes) for j in rows];n=len(rows)
        r=dict(zip(('module','wording','law','encoding','safe','p'),key));r.update(n=n,valid=sum(a==b for a,b in aa),join_range=[sum(a[i] for a in aa)/n for i in (0,1)])
        if key[0]!='free':
            cc=[_correct(j,outcomes) for j in rows];r['accuracy_range']=[sum(c[i] for c in cc)/n for i in (0,1)]
            scores=[_lin([(10*j['metadata']['p']-j['metadata']['safe'],_a(j,outcomes)),(j['metadata']['safe'],(1.,1.))]) for j in rows]
            r['expected_score_range']=[sum(c[i] for c in scores)/n for i in (0,1)]
            opt=max(key[4],10*key[5]);r['expected_regret_range']=[opt-r['expected_score_range'][1],opt-r['expected_score_range'][0]]
        cells.append(r)
    dyads=[]
    for key,rows in sorted(free.items()):
        if len(rows)!=2:raise ValueError('free dyad not pair')
        aa=[_a(j,outcomes) for j in rows];jj=_joint(*aa);ii=_lin([(.5,x) for x in aa]);dd=(float(aa[0][0]!=aa[1][0]),)*2 if all(a==b for a,b in aa) else (0.,1.)
        score=_lin([(key[4],(1.,1.)),(-key[4],ii),(10,jj)])
        dyads.append(dict(block=key[0],wording=key[1],law=key[2],encoding=key[3],safe=key[4],joint_join_range=list(jj),individual_join_range=list(ii),mismatch_range=list(dd),pair_mean_score_range=list(score)))
    freegroups=defaultdict(list)
    for d in dyads:
        for wording in (d['wording'],'all'):
            freegroups[(wording,d['law'],d['encoding'],d['safe'])].append(d)
    freecells=[]
    for key,ds in sorted(freegroups.items(),key=lambda x:str(x[0])):
        row=dict(zip(('wording','law','encoding','safe'),key));row['n_dyads']=len(ds)
        for field in ('joint_join_range','individual_join_range','mismatch_range','pair_mean_score_range'):
            row[field]=[sum(d[field][i] for d in ds)/len(ds) for i in (0,1)]
        freecells.append(row)
    return dict(status='complete' if complete else 'incomplete_keep_all_planned_bounds',scientific_planned=len(jobs),scientific_valid=sum(_a(j,outcomes)[0]==_a(j,outcomes)[1] for j in jobs),
                primary_family_7=primary,value_family_2=value,capability_family_3=cap,equivalence=equivalence,
                summaries=cells,free_dyads=dyads,free_cells=freecells,prediction=_prediction(capblocks,outcomes,complete),
                inference_assumptions=['Fixed predeclared prompt mixture and first-valid response within at most three unchanged physical attempts.',
                  'Independent block response vectors and stable response policy across execution time and operational pauses; these assumptions are not proved by balanced failure rates.',
                  'Stratified Welch intervals are approximate. Bounded Hoeffding enclosures are a separate conservative sensitivity under independent blocks.',
                  'Transport-only pauses with unchanged identity and prompt do not by themselves cancel the prospectively specified inference.',
                  'All missing responses retain binary completion bounds; no complete-case reweighting or retries of valid wrong answers.',
                  'Provider/model identity changes and material execution drift require explicit reporting and prevent unqualified pooling.',
                  'Inference concerns the four fixed wordings, not all possible language or human coordination.'])



