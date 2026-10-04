"""Prespecified block analysis. No network or paid requests."""
from pathlib import Path
from collections import defaultdict, Counter
import json, math, argparse
import numpy as np
from scipy.stats import t
import protocol
FAMILY=8

def comparison_specs(jobs):
    specs=[]
    def add(name,study,width,fn,metric):
        groups=defaultdict(list)
        for j in jobs:
            if j['metadata']['study']!=study:continue
            weight=fn(j['metadata'])
            if weight:groups[j['block_id']].append((j['id'],weight,j['metadata']['wording']))
        specs.append((name,width,metric,dict(groups)))
    for safe in (4,6):
        for enc in ('table','prose'):
            add(f'core_s{safe}_{enc}','framing',2,lambda m,s=safe,e=enc: (1 if m['law']=='S' else -1) if m['frame']=='original' and m['safe']==s and m['encoding']==e else 0,'join')
    add('partner_minus_device_protocol_effect','framing',4,lambda m: (1 if m['law']=='S' else -1)*(1 if m['frame']=='partner' else -1)/4 if m['frame']!='original' else 0,'join')
    add('explicit_own_minus_original_protocol_effect','referent',4,lambda m:(1 if m['law']=='S' else -1)*(1 if m['edit']=='explicit_own' else -1)/4,'join')
    add('lottery_minus_full_payoff_accuracy','payoff_transfer',2,lambda m: (1 if m['context']=='lottery' else -.5)/8 if m['response_task']=='payoffs' else 0,'correct')
    add('full_S_minus_R_payoff_accuracy','payoff_transfer',2,lambda m: (1 if m['context']=='full_S' else -1)/8 if m['response_task']=='payoffs' and m['context']!='lottery' else 0,'correct')
    assert len(specs)==FAMILY
    return specs

def estimate(spec,scores):
    name,width,metric,blocks=spec;complete=defaultdict(list);bounds=defaultdict(list)
    for ident,terms in blocks.items():
        known=[];lo=hi=0.;wording=terms[0][2]
        for jid,w,_ in terms:
            value=scores.get(jid,{}).get(metric)
            if value is None:lo+=min(0,w);hi+=max(0,w)
            else:lo+=w*value;hi+=w*value;known.append(w*value)
        bounds[wording].append((lo,hi))
        if len(known)==len(terms):complete[wording].append(sum(known))
    strata=sorted(bounds);H=len(strata)
    low=sum(np.mean([v[0] for v in bounds[h]]) for h in strata)/H
    high=sum(np.mean([v[1] for v in bounds[h]]) for h in strata)/H
    result={'name':name,'planned_blocks':len(blocks),'complete_blocks':sum(map(len,complete.values())),
            'missing_point_bounds':[float(low),float(high)],'support_width':width}
    if any(len(complete[h])<2 for h in strata):return result
    mean=sum(np.mean(complete[h]) for h in strata)/H
    pieces=[float(np.var(complete[h],ddof=1))/(H*H*len(complete[h])) for h in strata]
    variance=sum(pieces);denom=sum(v*v/(len(complete[h])-1) for h,v in zip(strata,pieces))
    df=variance*variance/denom if denom else None
    margin=t.ppf(1-.05/(2*FAMILY),df)*math.sqrt(variance) if df else 0.
    rad=math.sqrt(.5*math.log(2*FAMILY/.05)*sum(width*width/(H*H*len(complete[h])) for h in strata))
    fullrad=math.sqrt(.5*math.log(2*FAMILY/.05)*sum(width*width/(H*H*len(bounds[h])) for h in strata))
    result.update(estimate=float(mean),approx_ci=[max(-width/2,float(mean-margin)),min(width/2,float(mean+margin))],
                  hoeffding_ci=[max(-width/2,float(mean-rad)),min(width/2,float(mean+rad))],
                  adversarial_hoeffding_ci=[max(-width/2,float(low-fullrad)),min(width/2,float(high+fullrad))],
                  df=df,conditional_on_complete_blocks=result['complete_blocks']<len(blocks))
    return result

def analyze(jobs,answers):
    scores={j['id']:protocol.score(j,answers[j['id']]) for j in jobs if j['id'] in answers}
    groups=defaultdict(list);wordgroups=defaultdict(list);patterns=Counter()
    for j in jobs:
        m=j['metadata'];s=scores.get(j['id'],{})
        if m['study']=='framing':keys=(m['study'],m['frame'],m['law'],m['safe'],m['encoding'])
        elif m['study']=='referent':keys=(m['study'],m['edit'],m['law'],m['safe'],m['encoding'])
        else:keys=(m['study'],m['recipe'],m['context'],m['response_task'])
        groups[keys].append(s);wordgroups[keys+(m['wording'],)].append(s)
        if m['study']=='payoff_transfer' and m['response_task']=='payoffs' and s.get('valid'):
            a=answers[j['id']]['join_expected_score'];ev=j['truth']['join_expected_score'];p,h,l=m['p'],m['high'],m['low']
            if abs(a)<=1e6 and abs(a-ev)>1e-8:
                patterns[(m['context'],m['recipe'],'reported:'+str(a))]+=1
                if m['context']!='lottery':
                    q=.5 if m['law']=='R' else 1.
                    for name,value in {'receipt_times_EV':q*ev,'receipt_times_success':q*p*h+(1-q*p)*l,'prior_times_EV':.2*ev,'prior_times_success':.2*p*h+(1-.2*p)*l}.items():
                        if abs(a-value)<=1e-8:patterns[(m['context'],m['recipe'],name)]+=1
    def summarize(groups):
        rows=[]
        for keys,ss in sorted(groups.items(),key=lambda x:str(x[0])):
            row={'cell':list(keys),'planned':len(ss),'valid':sum(bool(s.get('valid')) for s in ss)}
            for key in ('join','correct','regret'):
                values=[s[key] for s in ss if s.get(key) is not None];row[key]=float(np.mean(values)) if values else None
            rows.append(row)
        return rows
    return {'planned':len(jobs),'valid':len(scores),'primary':[estimate(s,scores) for s in comparison_specs(jobs)],
            'cells':summarize(groups),'wording_cells':summarize(wordgroups),
            'numeric_error_patterns':[{'context':k[0],'recipe':k[1],'pattern':k[2],'count':v} for k,v in sorted(patterns.items())]}

def export(run,out):
    import runtime as r
    m,jobs=r.validate(run);status=r.read(run/'status.json')
    r.require(status['state'] in r.TERMINAL,'collection_not_terminal')
    attempts=r.lines(run/'attempts.jsonl');starts=r.lines(run/'started.jsonl');ledger=r.read(run/'final_ledger.json')
    r.require(r.sha(run/'attempts.jsonl')==ledger['settled_sha256'] and r.sha(run/'started.jsonl')==ledger['started_sha256'],'terminal_journal_changed')
    r.require(str(r.accounting(starts,attempts))==ledger['cumulative_occupied_usd'],'cost_reconciliation')
    profile=m['profiles'][0];byid={j['id']:j for j in jobs+[r.compatibility(profile)]};final={};first={}
    for a in attempts:
        j=byid[a['id']]
        if a['reason']!='interrupted_unknown':
            checked=r.classify(a,profile,j,r.D(a['reserve_usd']))
            r.require(checked==(a['valid'],a['action'],a['reason'],a['fatal']),'classification_changed')
        if a['valid'] and a['id'] in {j['id'] for j in jobs}:
            r.require(a['id'] not in final,'multiple_valid_answers');final[a['id']]=a['action']
            if a['attempt']==1:first[a['id']]=a['action']
    out.mkdir(parents=True,exist_ok=True)
    for name,answer in [('final',final),('first_attempt',first)]:
        data=analyze(jobs,answer);data['manifest_sha256']=m['manifest_sha256'];data['answer_selection']=name
        (out/(name+'.json')).write_text(json.dumps(data,indent=2,allow_nan=False),encoding='utf-8')
    (out/'ledger.json').write_text(json.dumps(ledger,indent=2),encoding='utf-8')
    print(json.dumps({'state':status['state'],'planned':len(jobs),'first_valid':len(first),'final_valid':len(final),'cost':ledger}))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--run',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();export(a.run,a.output)
