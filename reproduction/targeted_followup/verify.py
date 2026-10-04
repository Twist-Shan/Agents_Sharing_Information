"""Offline scientific allocation and scoring checks, run before freezing."""
from collections import Counter,defaultdict
from decimal import Decimal
import re,json
import protocol as p,analysis as a,runtime as r

def main():
    jobs=p.generate();assert jobs==p.generate();assert len(jobs)==5632
    assert Counter(j['metadata']['study'] for j in jobs)=={'framing':3072,'referent':1024,'payoff_transfer':1536}
    byid={j['id']:j for j in jobs};blockjobs=defaultdict(list)
    lengths=[]
    for j in jobs:
        m=j['metadata'];body=j['messages'][0]['content'];blockjobs[j['block_id']].append(j)
        assert p.valid_answer(j,j['truth']) and p.score(j,j['truth'])['correct']
        if j['mode']=='action':
            wrong={'action':'Y' if j['truth']['action']=='X' else 'X'}
            assert p.valid_answer(j,wrong) and not p.score(j,wrong)['correct'] and p.score(j,wrong)['regret']>0
        else:
            assert not p.valid_answer(j,{'join_expected_score':True,'safe_expected_score':4})
            assert not p.valid_answer(j,{'join_expected_score':float('nan'),'safe_expected_score':4})
            assert p.valid_answer(j,{'join_expected_score':999,'safe_expected_score':4})
        if m['study']=='framing' and m['frame']=='original':assert body==p.original.render(m)[0]['content']
        if m['study']=='referent' and m['edit']=='explicit_own':
            other=byid[j['id'].replace('-explicit_own-','-original-')]
            assert body.replace(p.NEW_CLAUSE,p.OLD_CLAUSE)==other['messages'][0]['content']
        if m['study']=='framing' and m['frame']=='partner':
            device=byid[j['id'].replace('-partner-','-device-')]['messages'][0]['content']
            assert re.findall(r'\d+(?:\.\d+)?',body)==re.findall(r'\d+(?:\.\d+)?',device)
            assert len(body.split('\n\n'))==len(device.split('\n\n'))
            lengths.append(len(body.split())-len(device.split()))
    transfer=[j for j in jobs if j['metadata']['study']=='payoff_transfer' and j['metadata']['recipe']==0 and j['metadata']['context']=='full_R' and j['mode']=='action']
    factorial=Counter(tuple(j['metadata'][k] for k in ('wording','mapping','display_order','encoding')) for j in transfer)
    assert len(factorial)==32 and set(factorial.values())=={1}
    oracle={j['id']:j['truth'] for j in jobs};result=a.analyze(jobs,oracle)
    assert result['valid']==5632 and all(c['correct']==1 for c in result['cells'])
    assert all(c['regret'] in (0,None) for c in result['cells'])
    assert all(abs(x['estimate'])<1e-12 for x in result['primary'])
    specs=a.comparison_specs(jobs)
    for spec in specs:
        for terms in spec[3].values():
            assert abs(sum(w for _,w,_ in terms))<1e-12
            assert abs(sum(abs(w) for _,w,_ in terms)-spec[1])<1e-12
        empty=a.estimate(spec,{})
        assert empty['missing_point_bounds']==[-spec[1]/2,spec[1]/2]
    pr=r.normalize_profiles(r.read(r.HERE/'profiles.json'))[0]
    cost=sum((r.reserve(pr,r.payload(pr,j)) for j in jobs+[r.compatibility(pr)]),Decimal(0))
    assert r.PRIOR+cost<=r.CAP
    print(json.dumps({'passed':True,'science':len(jobs),'exact_template_and_minimal_edit':True,'matched_numeric_structure':True,'matched_word_count_difference_range':[min(lengths),max(lengths)],'first_pass_max_reserve_usd':str(cost),'occupied_plus_reserve':str(r.PRIOR+cost),'api_calls':0}))
if __name__=='__main__':main()
