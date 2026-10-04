"""Independent replay of action/payoff scoring and the eight paired estimates."""
from pathlib import Path
from collections import defaultdict,Counter
import json,math,argparse,hashlib,statistics
from scipy.stats import t as student_t

def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def rows(p):return [json.loads(s) for s in p.read_text(encoding='utf-8').splitlines()]
def main(run,exports):
    manifest=read(run/'manifest.json');status=read(run/'status.json');assert status['state']=='complete'
    jobs=rows(run/'planned.jsonl');attempts=rows(run/'attempts.jsonl');final=read(exports/'final.json');first=read(exports/'first_attempt.json')
    accepted={};firsts={};byid={j['id']:j for j in jobs}
    for a in attempts:
        if not a.get('valid') or a['id'] not in byid:continue
        assert a['id'] not in accepted
        response=a['response'];assert response['model']=='openai/gpt-6-luna' and response['provider']=='OpenAI'
        assert response['usage']['completion_tokens_details']['reasoning_tokens']==0
        content=response['choices'][0]['message']['content'].strip()
        if content.startswith('```'):
            content=content.split('\n',1)[1].rsplit('```',1)[0]
        ans=json.loads(content);assert ans==a['action'];accepted[a['id']]=ans
        if a['attempt']==1:firsts[a['id']]=ans
    assert len(accepted)==len(jobs)==5632
    primitive={};groups=defaultdict(list);components=defaultdict(Counter);anchor_reports=Counter()
    for j in jobs:
        m=j['metadata'];ans=accepted[j['id']];p=m['p'];s=m['safe'];high=m.get('high',10);low=m.get('low',0);value=low+p*(high-low)
        if j['mode']=='action':
            risky=(ans['action']=='X')==(m['mapping']==0)
            correct=risky==(value>s);regret=max(value,s)-(value if risky else s)
            primitive[j['id']]={'join':int(risky),'correct':int(correct),'regret':regret}
        else:
            correct=math.isclose(ans['join_expected_score'],value,abs_tol=1e-8,rel_tol=0) and math.isclose(ans['safe_expected_score'],s,abs_tol=1e-8,rel_tol=0)
            primitive[j['id']]={'correct':int(correct)}
            cc=components[m['context']];cc['n']+=1;cc['join_correct']+=math.isclose(ans['join_expected_score'],value,abs_tol=1e-8,rel_tol=0);cc['safe_correct']+=math.isclose(ans['safe_expected_score'],s,abs_tol=1e-8,rel_tol=0)
            if m['recipe']<2 and m['context']!='lottery':anchor_reports[str(float(ans['join_expected_score']))]+=1
        groups[(m['study'],m['block_index'])].append(j)
    estimates={}
    for name in [r['name'] for r in final['primary']]:
        block_values=defaultdict(list)
        for (study,b),jj in groups.items():
            mm=jj[0]['metadata'];wording=mm['wording'];v=0.;used=False
            for j in jj:
                m=j['metadata'];w=0.;metric='join'
                if name.startswith('core_') and study=='framing':
                    _,safe,enc=name.split('_')
                    if m['frame']=='original' and m['safe']==int(safe[1:]) and m['encoding']==enc:w=1 if m['law']=='S' else -1
                elif name=='partner_minus_device_protocol_effect' and study=='framing' and m['frame'] in ('partner','device'):
                    w=(.25 if m['law']=='S' else -.25)*(1 if m['frame']=='partner' else -1)
                elif name=='explicit_own_minus_original_protocol_effect' and study=='referent':
                    w=(.25 if m['law']=='S' else -.25)*(1 if m['edit']=='explicit_own' else -1)
                elif name=='lottery_minus_full_payoff_accuracy' and study=='payoff_transfer' and j['mode']=='payoffs':
                    metric='correct';w=(1 if m['context']=='lottery' else -.5)/8
                elif name=='full_S_minus_R_payoff_accuracy' and study=='payoff_transfer' and j['mode']=='payoffs' and m['context']!='lottery':
                    metric='correct';w=(1 if m['context']=='full_S' else -1)/8
                if w:used=True;v+=w*primitive[j['id']][metric]
            if used:block_values[wording].append(v)
        estimates[name]=sum(sum(v)/len(v) for v in block_values.values())/len(block_values)
        result=next(x for x in final['primary'] if x['name']==name)
        H=len(block_values);variances=[statistics.variance(v)/(H*H*len(v)) for v in block_values.values()]
        total=sum(variances);denom=sum(x*x/(len(v)-1) for x,v in zip(variances,block_values.values()))
        df=total*total/denom if denom else None
        width=4 if name in ('partner_minus_device_protocol_effect','explicit_own_minus_original_protocol_effect') else 2
        radius=math.sqrt(math.log(320)/2*sum(width*width/(H*H*len(v)) for v in block_values.values()))
        margin=float(student_t.ppf(1-.05/16,df))*math.sqrt(total) if df else 0.
        point=estimates[name]
        expected_a=[max(-width/2,point-margin),min(width/2,point+margin)]
        expected_h=[max(-width/2,point-radius),min(width/2,point+radius)]
        assert all(abs(x-y)<1e-10 for x,y in zip(expected_a,result['approx_ci']))
        assert all(abs(x-y)<1e-10 for x,y in zip(expected_h,result['hoeffding_ci']))
        assert (df is None and result['df'] is None) or abs(df-result['df'])<1e-8

    for r in final['primary']:assert abs(estimates[r['name']]-r['estimate'])<1e-12
    for row in final['cells']:
        keys=row['cell'];selected=[]
        for j in jobs:
            m=j['metadata']
            if m['study']=='framing':k=[m['study'],m['frame'],m['law'],m['safe'],m['encoding']]
            elif m['study']=='referent':k=[m['study'],m['edit'],m['law'],m['safe'],m['encoding']]
            else:k=[m['study'],m['recipe'],m['context'],m['response_task']]
            if k==keys:selected.append(primitive[j['id']])
        assert len(selected)==row['planned']==row['valid']
        for metric in ('join','correct','regret'):
            vv=[x[metric] for x in selected if metric in x]
            if vv:assert abs(sum(vv)/len(vv)-row[metric])<1e-10
    result={'passed':True,'scientific_responses':len(accepted),'first_attempt_valid':len(firsts),'primary_estimates_verified':8,'approximate_and_conservative_intervals_verified':8,'cell_scores_verified':len(final['cells']),
            'payoff_components':dict(components),'full_context_anchor_join_reports':dict(anchor_reports),'manifest_sha256':manifest['manifest_sha256'],'analysis_sha256':hashlib.sha256((exports/'final.json').read_bytes()).hexdigest()}
    (exports/'independent_audit.json').write_text(json.dumps(result,indent=2),encoding='utf-8');print(json.dumps(result))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--run',type=Path,required=True);p.add_argument('--exports',type=Path,required=True);a=p.parse_args();main(a.run,a.exports)
