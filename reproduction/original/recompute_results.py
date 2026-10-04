"""Portable offline reanalysis of all 36 prespecified contrasts from selected choices.

Run: python recompute_results.py
Requires scipy (only its Student-t quantile function); no network or API access.
Reconstructs every paired block contribution independently of frozen_analysis.py.
"""
from pathlib import Path
import collections,csv,hashlib,json,math,statistics
from scipy.stats import t
from reconstruct_requests import records

BASE=Path(__file__).resolve().parent
MODELS=('luna','qwen','deepseek')
def compact(x):return json.dumps(x,sort_keys=True,separators=(',',':'),allow_nan=False)
def savecsv(path,rows):
    with path.open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
def hashfile(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for x in iter(lambda:f.read(2**20),b''):h.update(x)
    return h.hexdigest()
def close(a,b,tol=2e-10):
    if a is None or b is None:return a is b
    if isinstance(a,list):return isinstance(b,list) and len(a)==len(b) and all(close(x,y,tol) for x,y in zip(a,b))
    return math.isclose(float(a),float(b),rel_tol=tol,abs_tol=tol)

def main():
    manifest=json.loads((BASE/'package_manifest.json').read_text(encoding='utf-8'))
    for name,h in manifest['files_sha256'].items():assert hashfile(BASE/name)==h,('hash_mismatch',name)
    assert sum(1 for _ in records())==44800
    rows=list(csv.DictReader((BASE/'request_block_map.csv').open(encoding='utf-8',newline='')))
    index={};meta={}
    for r in rows:
        assert r['valid']=='True' and r['action'] in ('JOIN','SAFE')
        model=r['model_key'];mod=r['module'];b=int(r['block_id'].rsplit('-',1)[1])
        actor=int(r['actor']) if mod=='free' else 0
        p=float(r['p']) if r['p'] else None
        key=(model,mod,b,r['law'],r['encoding'],int(r['safe']),actor,p)
        assert key not in index,key
        index[key]=float(r['action']=='JOIN');meta[(model,mod,b)]=r
    blocks=[]
    def value(model,mod,b,q,e,s,p,actor=0):return index[(model,mod,b,q,e,s,actor,p)]
    def emit(model,fam,name,bid,stratum,v):
        blocks.append(dict(model_key=model,family=fam,contrast=name,block_id=bid,stratum=compact(stratum),value=v))
    for model in MODELS:
        nfree,nind,ndir,ncap=(1024,2048,512,64) if model=='luna' else (128,128,64,32)
        for b in range(nfree):
            m=meta[model,'free',b];s=int(m['safe']);stratum=(int(m['wording']),int(m['mapping']),int(m['display_order']),s)
            delta={}
            for enc in ('table','prose'):
                joint={q:value(model,'free',b,q,enc,s,None,0)*value(model,'free',b,q,enc,s,None,1) for q in ('R','S')}
                delta[enc]=joint['S']-joint['R']
                emit(model,'primary_family_7','tau_'+enc,'free-'+str(b).zfill(4),stratum,delta[enc])
            emit(model,'primary_family_7','phi','free-'+str(b).zfill(4),stratum,delta['table']-delta['prose'])
        for b in range(nind):
            m=meta[model,'independent',b];stratum=tuple(int(m[k]) for k in ('wording','mapping','display_order','actor'))
            for enc in ('table','prose'):
                for s in (4,6):
                    d=value(model,'independent',b,'S',enc,s,.5)-value(model,'independent',b,'R',enc,s,.5)
                    emit(model,'primary_family_7',f'delta_{enc}_safe{s}','independent-'+str(b).zfill(4),stratum,d)
        for mod,s,pS in (('responsive',6,1.),('complement',4,0.)):
            for b in range(ndir):
                m=meta[model,mod,b];stratum=tuple(int(m[k]) for k in ('wording','mapping','display_order','actor'))
                d=sum(value(model,mod,b,'S',enc,s,pS)-value(model,mod,b,'R',enc,s,.5) for enc in ('table','prose'))/2
                emit(model,'value_family_2',mod+'_safe'+str(s),mod+'-'+str(b).zfill(4),stratum,d)
        grid=(.2,.35,.5,.65,.8) if model=='luna' else (.5,)
        for b in range(ncap):
            m=meta[model,'minimal',b];stratum=(int(m['wording']),);acc={x:[] for x in ('minimal','full','card')};sens={'full':0.,'card':0.}
            for p in grid:
                for s in (4,6):
                    right_join=10*p>s
                    correct=lambda y:y if right_join else 1-y
                    acc['minimal'].append(correct(value(model,'minimal',b,'none','none',s,p)))
                    for ctx,mod in (('full','independent' if p==.5 else 'grid_full'),('card','payoff_card')):
                        ys=[value(model,mod,b,q,e,s,p) for q in ('R','S') for e in ('table','prose')]
                        acc[ctx].append(sum(map(correct,ys))/4)
                        if p==.5:sens[ctx]+=(1 if s==4 else -1)*sum(ys)/4
            av={ctx:sum(xs)/len(xs) for ctx,xs in acc.items()}
            for name,d in (('minimal_minus_full_accuracy',av['minimal']-av['full']),('card_minus_full_accuracy',av['card']-av['full']),('card_minus_full_payoff_sensitivity_at_half',sens['card']-sens['full'])):
                emit(model,'capability_family_3',name,'independent-'+str(b).zfill(4),stratum,d)
    grouped=collections.defaultdict(list)
    for r in blocks:grouped[r['model_key'],r['family'],r['contrast']].append(r)
    stored={ (r['model_key'],r['family'],r['contrast']):r for r in csv.DictReader((BASE/'stored_contrasts.csv').open(encoding='utf-8',newline=''))}
    assert len(grouped)==len(stored)==36
    estimates=[];checks=[]
    for key,rs in sorted(grouped.items()):
        model,fam,name=key;n=len(rs);family_size=int(fam.rsplit('_',1)[1]);support=(-2.,2.) if name=='phi' or 'sensitivity' in name else (-1.,1.)
        point=sum(r['value'] for r in rs)/n;cells=collections.defaultdict(list)
        for r in rs:cells[r['stratum']].append(r['value'])
        variance=0.;den=0.
        for xs in cells.values():
            assert len(xs)>=2
            part=(len(xs)/n)**2*statistics.variance(xs)/len(xs)
            variance+=part;den+=part*part/(len(xs)-1)
        se=df=approx=None
        if variance>0:
            se=math.sqrt(variance);df=variance*variance/den;crit=float(t.ppf(1-.05/(2*family_size),df))
            approx=[max(support[0],point-crit*se),min(support[1],point+crit*se)]
        radius=(support[1]-support[0])*math.sqrt(math.log(2*family_size/.05)/(2*n))
        bound=[max(support[0],point-radius),min(support[1],point+radius)]
        result=dict(model_key=model,family=fam,contrast=name,n_blocks=n,point=point,se=se,df=df,approximate_simultaneous_95_ci=approx,conservative_hoeffding_95_ci=bound)
        expected=stored[key]
        for field in ('n_blocks','point','se','df','approximate_simultaneous_95_ci','conservative_hoeffding_95_ci'):
            old=json.loads(expected[field]) if expected[field] else None
            assert close(result[field],old),(key,field,result[field],old)
        checks.append(dict(model_key=model,contrast=name,matched_stored_point_and_paired_variance_and_both_intervals=True))
        estimates.append({k:compact(v) if isinstance(v,list) else v for k,v in result.items()})
    target=BASE/'recomputed';target.mkdir(exist_ok=True)
    savecsv(target/'block_contributions.csv',blocks);savecsv(target/'contrasts.csv',estimates)
    report={'status':'passed','logical_choices':len(rows),'paired_block_contributions':len(blocks),'contrasts_checked':len(checks),'all_36_points_standard_errors_degrees_of_freedom_and_intervals_match':True,'floating_point_tolerance':2e-10,'inferential_scope':'The original four fixed wordings and accepted-response acquisition policies; this check verifies arithmetic, not those assumptions.','api_calls':0,'checks':checks}
    (target/'checks.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in report.items() if k!='checks'},indent=2))
if __name__=='__main__':main()
