"""Portable offline audit reproduction. Python standard library only.

Default layout: ../original/{request_block_map.csv,protocol_frozen.py,...}.
No API access, raw acquisition journals, repository checkout, or new study data.
"""
from pathlib import Path
from collections import Counter,defaultdict
from fractions import Fraction as F
import argparse,csv,hashlib,importlib.util,json,math

MODELS=('luna','qwen','deepseek')
ROOT=Path(__file__).resolve().parent
KEYS={
 'acquisition_models.csv':('model_key',),
 'acquisition_modules.csv':('model_key','module'),
 'acquisition_condition_summary.csv':('model_key','module','law','encoding','safe'),
 'acquisition_conditions.csv':('model_key','module','law','encoding','safe','p','wording'),
 'independent_pairing_strata.csv':('model_key','law','encoding','safe','wording','mapping','display_order'),
 'independent_pairing_baseline.csv':('model_key','law','encoding','safe'),
 'independent_pairing_changes.csv':('model_key','encoding','safe'),
 'all_programmed_policy_rates.csv':('model_key','policy','safe','law'),
 'capability_by_probability.csv':('model_key','context','p'),
 'first_attempt_bounds.csv':('model_key','family','contrast')}

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def readcsv(path):
 with Path(path).open(encoding='utf-8',newline='') as f:return list(csv.DictReader(f))
def savecsv(path,rows):
 with Path(path).open('w',encoding='utf-8',newline='') as f:
  writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
def groups(rows,keys):
 out=defaultdict(list)
 for row in rows:out[tuple(row[k] for k in keys)].append(row)
 return out
def rate(rows):return F(sum(r['action']=='JOIN' for r in rows),len(rows))
def close(a,b,tol=2e-10):
 if isinstance(a,dict) or isinstance(b,dict):
  return isinstance(a,dict) and isinstance(b,dict) and set(a)==set(b) and all(close(a[k],b[k],tol) for k in a)
 if isinstance(a,list) or isinstance(b,list):
  return isinstance(a,list) and isinstance(b,list) and len(a)==len(b) and all(close(x,y,tol) for x,y in zip(a,b))
 if a==b:return True
 try:return math.isclose(float(a),float(b),rel_tol=tol,abs_tol=tol)
 except (TypeError,ValueError):return False
def cell_value(value):
 if isinstance(value,str) and value.startswith(('{','[')):
  try:return json.loads(value)
  except ValueError:pass
 return value

def acquisition(records,attempts,ids):
 byid={r['runtime_id']:r for r in records};given={r['runtime_id']:r for r in ids}
 grouped=groups(attempts,('runtime_id',));logical=[]
 assert set(byid)==set(given)=={key[0] for key in grouped}
 for rid,record in byid.items():
  aa=sorted(grouped[rid,],key=lambda x:int(x['attempt']));first=aa[0]
  assert [int(a['attempt']) for a in aa]==list(range(1,len(aa)+1))
  assert len(aa)==int(record['physical_attempts'])
  selected=[a for a in aa if a['is_final_selected']=='True'];assert len(selected)==1
  assert selected[0]['attempt_id']==record['selected_attempt_id']
  if first['operationally_accepted']=='True':assert first['is_final_selected']=='True'
  failures=Counter(a['reason'] for a in aa if a['operationally_accepted']!='True')
  # This separately audited flag reports retrospective extractability. It is
  # not derivable from format-only lineage; the raw prose is intentionally not
  # needed to reproduce the published numeric aggregation.
  retro=given[rid]['first_retrospectively_extractable']=='True'
  logical.append({k:record[k] for k in ('model_key','module','law','encoding','safe','wording','p')}
   |dict(first_strict_valid=first['strict_valid']=='True',first_operationally_accepted=first['operationally_accepted']=='True',
         first_retrospectively_extractable=retro,first_reason=first['reason'],physical_attempts=len(aa),retries=len(aa)-1,
         selected_layer=record['selected_source_layer'],unsettled=sum(a['reason']=='unsettled_no_response' for a in aa),
         failed_attempts=sum(failures.values()),failure_reasons=failures))
 results={}
 for name in [n for n in KEYS if n.startswith('acquisition_')]:
  keys=KEYS[name];output=[]
  for kk,rr in sorted(groups(logical,keys).items(),key=lambda x:repr(x[0])):
   n=len(rr);failures=Counter()
   for row in rr:failures.update(row['failure_reasons'])
   result=dict(zip(keys,kk))|dict(planned=n,
    first_strict_valid=sum(r['first_strict_valid'] for r in rr),
    first_operationally_accepted=sum(r['first_operationally_accepted'] for r in rr),
    first_retrospectively_extractable=sum(r['first_retrospectively_extractable'] for r in rr),
    first_strict_valid_rate=sum(r['first_strict_valid'] for r in rr)/n,
    first_operational_acceptance_rate=sum(r['first_operationally_accepted'] for r in rr)/n,
    first_retrospective_extraction_rate=sum(r['first_retrospectively_extractable'] for r in rr)/n,
    ids_retried=sum(r['retries']>0 for r in rr),retries=sum(r['retries'] for r in rr),
    physical_attempts=sum(r['physical_attempts'] for r in rr),mean_attempts=sum(r['physical_attempts'] for r in rr)/n,
    max_attempts=max(r['physical_attempts'] for r in rr),failed_attempts=sum(r['failed_attempts'] for r in rr),
    unsettled=sum(r['unsettled'] for r in rr),accepted_final=n,
    original128_strict=sum(r['selected_layer']=='strict' for r in rr),
    original128_extracted=sum(r['selected_layer']=='parsed_recovery' for r in rr),
    supplement512_strict=sum(r['selected_layer']=='supplement_strict' for r in rr),
    supplement512_extracted=sum(r['selected_layer']=='supplement_parsed' for r in rr),
    completion2048_strict=sum(r['selected_layer']=='ceiling2048_strict' for r in rr),
    completion2048_extracted=sum(r['selected_layer']=='ceiling2048_parsed' for r in rr),
    first_reasons=json.dumps(dict(sorted(Counter(r['first_reason'] for r in rr).items())),sort_keys=True),
    all_failure_reasons=json.dumps(dict(sorted(failures.items())),sort_keys=True),
    retry_distribution=json.dumps(dict(sorted(Counter(r['retries'] for r in rr).items())),sort_keys=True))
   output.append(result)
  results[name]=output
 return results

def pair_baseline(records):
 keys=KEYS['independent_pairing_strata.csv'];strata=[]
 for kk,rr in sorted(groups([r for r in records if r['module']=='free'],keys).items()):
  actors={a:{r['block_id']:int(r['action']=='JOIN') for r in rr if r['actor']==a} for a in (0,1)}
  assert actors[0].keys()==actors[1].keys();n=len(actors[0]);assert n>1
  a=sum(actors[0].values());b=sum(actors[1].values());ab=sum(v*actors[1][i] for i,v in actors[0].items())
  pa,pb=F(a,n),F(b,n);j=F(ab,n);s=kk[3];ind=pa*pb;cross=F(a*b-ab,n*(n-1))
  def mismatch(x):return pa+pb-2*x
  def score(x):return s+(10-s)*x-F(s,2)*mismatch(x)
  strata.append(dict(zip(keys,kk))|dict(n_pairs=n,A_join_count=a,B_join_count=b,A_join_rate=float(pa),B_join_rate=float(pb),
   observed_joint=float(j),observed_mismatch=float(mismatch(j)),observed_mean_score=float(score(j)),
   independent_joint=float(ind),independent_mismatch=float(mismatch(ind)),independent_mean_score=float(score(ind)),
   crossblock_joint=float(cross),crossblock_mismatch=float(mismatch(cross)),crossblock_mean_score=float(score(cross)),
   observed_minus_independent_joint=float(j-ind)))
 metrics=('A_join_rate','B_join_rate','observed_joint','observed_mismatch','observed_mean_score','independent_joint',
          'independent_mismatch','independent_mean_score','crossblock_joint','crossblock_mismatch','crossblock_mean_score',
          'observed_minus_independent_joint')
 keys=KEYS['independent_pairing_baseline.csv'];cells=[]
 for kk,ss in sorted(groups(strata,keys).items()):
  n=sum(s['n_pairs'] for s in ss)
  r=dict(zip(keys,kk))|dict(n_pairs=n,n_strata=len(ss),min_pairs_per_stratum=min(s['n_pairs'] for s in ss))
  r.update({m:sum(s['n_pairs']*s[m] for s in ss)/n for m in metrics})
  r['pooled_actor_product_not_used']=r['A_join_rate']*r['B_join_rate']
  r['pooling_error_in_joint_baseline']=r['pooled_actor_product_not_used']-r['independent_joint'];cells.append(r)
 keys=KEYS['independent_pairing_changes.csv'];deltas=[]
 for kk,rr in sorted(groups(cells,keys).items()):
  q={r['law']:r for r in rr};assert set(q)=={'R','S'}
  deltas.append(dict(zip(keys,kk))|{m+'_S_minus_R':q['S'][m]-q['R'][m] for m in metrics})
 return dict(zip(('independent_pairing_strata.csv','independent_pairing_baseline.csv','independent_pairing_changes.csv'),(strata,cells,deltas)))

def policy_and_capability(records):
 rates=[];keys=KEYS['all_programmed_policy_rates.csv']
 for kk,rr in sorted(groups([r for r in records if r['module'] in ('responsive','complement')],('model_key','module','safe','law')).items()):
  rates.append(dict(zip(keys,kk))|dict(n=len(rr),join_count=sum(r['action']=='JOIN' for r in rr),join_rate=float(rate(rr)),
   correct_count=sum(r['correct']=='True' for r in rr),accuracy=sum(r['correct']=='True' for r in rr)/len(rr)))
 capability=[]
 for model in MODELS:
  n=64 if model=='luna' else 32
  rr=[r|{'context':('full' if r['module'] in ('independent','grid_full') else ('card' if r['module']=='payoff_card' else 'minimal'))}
      for r in records if r['model_key']==model and r['module'] in ('independent','grid_full','minimal','payoff_card') and r['block_index']<n]
  for kk,ss in sorted(groups(rr,('context','p')).items()):
   bysafe={s:[r for r in ss if r['safe']==s] for s in (4,6)};a,b=rate(bysafe[4]),rate(bysafe[6])
   capability.append(dict(model_key=model,context=kk[0],p=kk[1],linked_blocks=n,n_per_safe=len(bysafe[4]),
    JOIN_safe4_count=sum(r['action']=='JOIN' for r in bysafe[4]),JOIN_safe6_count=sum(r['action']=='JOIN' for r in bysafe[6]),
    JOIN_safe4=float(a),JOIN_safe6=float(b),SAFE_sensitivity=float(a-b),accuracy=sum(r['correct']=='True' for r in ss)/len(ss),
    descriptive_SAFE_sensitivity_reversal=a<b))
 return {'all_programmed_policy_rates.csv':rates,'capability_by_probability.csv':capability}

def first_bounds(records,attempts):
 first={r['runtime_id']:r for r in attempts if int(r['attempt'])==1};index={}
 for r in records:
  key=(r['model_key'],r['module'],r['block_index'],r['law'],r['encoding'],r['safe'],r['actor'] if r['module']=='free' else 0,r['p'])
  assert key not in index;index[key]=r
 def lin(terms):
  return tuple(sum((weight*interval[i if weight>=0 else 1-i] for weight,interval in terms),F(0)) for i in (0,1))
 def mean(values):return lin([(F(1,len(values)),value) for value in values])
 def joint(a,b):return (a[0]*b[0],a[1]*b[1])
 blocksets={}
 for use_first in (True,False):
  blocks=[]
  def value(model,mod,b,q,e,s,p,actor=0):
   r=index[model,mod,b,q,e,s,actor,p];a=first[r['runtime_id']]
   if use_first and a['operationally_accepted']!='True':return (F(0),F(1))
   assert not use_first or a['is_final_selected']=='True'
   v=F(int(r['action']=='JOIN'));return v,v
  def emit(model,fam,name,b,interval):
   blocks.append(dict(model_key=model,family=fam,contrast=name,block_id=b,lower=interval[0],upper=interval[1]))
  for model in MODELS:
   nf,ni,nd,nc=(1024,2048,512,64) if model=='luna' else (128,128,64,32)
   for b in range(nf):
    s=4 if (b//16)%2==0 else 6;delta={}
    for e in ('table','prose'):
     jj={q:joint(value(model,'free',b,q,e,s,None,0),value(model,'free',b,q,e,s,None,1)) for q in ('R','S')}
     delta[e]=lin([(1,jj['S']),(-1,jj['R'])]);emit(model,'primary_family_7','tau_'+e,f'free-{b:04d}',delta[e])
    emit(model,'primary_family_7','phi',f'free-{b:04d}',lin([(1,delta['table']),(-1,delta['prose'])]))
   for b in range(ni):
    for e in ('table','prose'):
     for s in (4,6):
      d=lin([(1,value(model,'independent',b,'S',e,s,.5)),(-1,value(model,'independent',b,'R',e,s,.5))])
      emit(model,'primary_family_7',f'delta_{e}_safe{s}',f'independent-{b:04d}',d)
   for mod,s,pS in (('responsive',6,1.),('complement',4,0.)):
    for b in range(nd):
     differences=[lin([(1,value(model,mod,b,'S',e,s,pS)),(-1,value(model,mod,b,'R',e,s,.5))]) for e in ('table','prose')]
     emit(model,'value_family_2',mod+'_safe'+str(s),f'{mod}-{b:04d}',mean(differences))
   for b in range(nc):
    accuracies={'minimal':[],'full':[],'card':[]};sens={'full':[],'card':[]}
    for p in ((.2,.35,.5,.65,.8) if model=='luna' else (.5,)):
     for s in (4,6):
      def correct(interval):return interval if 10*p>s else (1-interval[1],1-interval[0])
      accuracies['minimal'].append(correct(value(model,'minimal',b,'none','none',s,p)))
      for context,mod in (('full','independent' if p==.5 else 'grid_full'),('card','payoff_card')):
       vals=[value(model,mod,b,q,e,s,p) for q in ('R','S') for e in ('table','prose')]
       accuracies[context].append(mean([correct(v) for v in vals]))
       if p==.5:sens[context].append((1 if s==4 else -1,mean(vals)))
    acc={k:mean(v) for k,v in accuracies.items()};sensitivity={k:lin(v) for k,v in sens.items()}
    for name,interval in [('minimal_minus_full_accuracy',lin([(1,acc['minimal']),(-1,acc['full'])])),
       ('card_minus_full_accuracy',lin([(1,acc['card']),(-1,acc['full'])])),
       ('card_minus_full_payoff_sensitivity_at_half',lin([(1,sensitivity['card']),(-1,sensitivity['full'])]))]:
     emit(model,'capability_family_3',name,f'independent-{b:04d}',interval)
  blocksets[use_first]=blocks
 keys=('model_key','family','contrast');full=groups(blocksets[False],keys);output=[]
 for kk,bb in sorted(groups(blocksets[True],keys).items()):
  model,family,name=kk;n=len(bb);k=int(family.rsplit('_',1)[1]);a,b=(-2,2) if name=='phi' or 'sensitivity' in name else (-1,1)
  lo=float(sum((r['lower'] for r in bb),F(0))/n);hi=float(sum((r['upper'] for r in bb),F(0))/n)
  radius=(b-a)*math.sqrt(math.log(2*k/.05)/(2*n));lower=max(a,lo-radius);upper=min(b,hi+radius)
  point=float(sum((r['lower'] for r in full[kk]),F(0))/n);assert lo-2e-10<=point<=hi+2e-10
  output.append(dict(zip(keys,kk))|dict(n_planned_blocks=n,unresolved_blocks=sum(r['lower']!=r['upper'] for r in bb),
   original_family_size=k,block_support_lower=a,block_support_upper=b,first_attempt_completion_lower=lo,
   first_attempt_completion_upper=hi,original_hoeffding_radius=radius,completion_hoeffding95_lower=lower,
   completion_hoeffding95_upper=upper,original_selected_point=point,original_selected_point_inside_completion_bounds=True,
   conservative_lower_above_zero=lower>0,conservative_upper_below_zero=upper<0,post_review_sensitivity=True))
 assert len(output)==36
 return output,[{k:(float(v) if isinstance(v,F) else v) for k,v in row.items()} for row in blocksets[True]]

def main(original,output):
 original=Path(original).resolve();output=Path(output).resolve()
 own_manifest=json.loads((ROOT/'package_manifest.json').read_text(encoding='utf-8'))
 for name,digest in own_manifest['files_sha256'].items():assert sha(ROOT/name)==digest,('audit_package_changed',name)
 orig_manifest=json.loads((original/'package_manifest.json').read_text(encoding='utf-8'))
 for name in ('request_block_map.csv','protocol_frozen.py','frozen_analysis.py'):
  assert sha(original/name)==orig_manifest['files_sha256'][name],('original_package_changed',name)
 raw=readcsv(original/'request_block_map.csv');records=[]
 assert len(raw)==44800 and len({r['runtime_id'] for r in raw})==44800
 for row in raw:
  r=dict(row)
  for key in ('safe','wording','actor','mapping','display_order'):r[key]=int(r[key])
  r['p']=float(r['p']) if r['p'] not in ('','None') else None;r['block_index']=int(r['block_id'].rsplit('-',1)[1]);records.append(r)
 spec=importlib.util.spec_from_file_location('portable_original_protocol',original/'protocol_frozen.py');protocol=importlib.util.module_from_spec(spec);spec.loader.exec_module(protocol)
 byid={r['runtime_id']:r for r in records}
 for model in MODELS:
  jobs=protocol.generate({'allocationprofile':'full' if model=='luna' else 'cross'})
  for job in jobs:
   rr=byid[model+'|'+job['id']]
   assert all(rr[k]==job['metadata'][k] for k in ('module','safe','wording','actor','mapping','display_order','p','law','encoding','block_index'))
 attempts=readcsv(ROOT/'acquisition_by_attempt.csv');ids=readcsv(ROOT/'acquisition_by_id.csv')
 data=acquisition(records,attempts,ids);data.update(pair_baseline(records));data.update(policy_and_capability(records))
 bounds,blocks=first_bounds(records,attempts);data['first_attempt_bounds.csv']=bounds
 output.mkdir(parents=True,exist_ok=True);checks=[]
 for name,rr in data.items():
  savecsv(output/name,rr);actual=readcsv(output/name);reference=readcsv(ROOT/'reference'/name);keys=KEYS[name]
  a={tuple(r[k] for k in keys):r for r in actual};b={tuple(r[k] for k in keys):r for r in reference}
  assert len(a)==len(actual) and len(b)==len(reference) and a.keys()==b.keys(),('row_keys',name)
  for key,row in a.items():
   assert row.keys()==b[key].keys(),('columns',name)
   for field,value in row.items():assert close(cell_value(value),cell_value(b[key][field])),(name,key,field,value,b[key][field])
  checks.append(dict(file=name,rows=len(rr),all_values_match=True))
 savecsv(output/'first_attempt_block_bounds.csv',blocks)
 spec=importlib.util.spec_from_file_location('portable_answer_extraction',ROOT/'answer_extraction_frozen.py')
 extractor=importlib.util.module_from_spec(spec);spec.loader.exec_module(extractor)
 parsed_count=0
 with (ROOT/'all_parser_selected_responses.jsonl').open(encoding='utf-8') as f:
  for line in f:
   record=json.loads(line);content=record['raw_content']
   assert hashlib.sha256(content.encode()).hexdigest()==record['content_sha256']
   parsed=extractor.extract_content(content,record['answer_map'],record['finish_reason'])
   assert parsed['accepted'] and parsed['action']==record['selected_action']
   assert byid[record['runtime_id']]['action']==record['selected_action']
   parsed_count+=1
 assert parsed_count==1012
 summary={'status':'passed','logical_ids':44800,'physical_attempt_rows':len(attempts),'csvs_checked':len(checks),
  'first_attempt_contrasts':36,'block_bounds_reconstructed':len(blocks),'floating_point_tolerance':2e-10,'api_calls':0,
  'selected_parser_responses_replayed':parsed_count,'parser_replay_disagreements':0,
  'requirements':'Python standard library only','original_request_map_sha256':sha(original/'request_block_map.csv'),
  'checks':checks,'scope':'Numerical reproduction from selected records and complete operational lineage; not an independent audit of provider responses or parser fidelity.',
  'limitations':['Retrospective first-response extractability is an audited input flag in acquisition_by_id.csv; raw first-response text is not reinterpreted here.',
   'All 36 first-response contrast bounds are reconstructed independently of frozen_analysis.py using exact rational block arithmetic.',
   'Confidence enclosures retain original block supports/family sizes and require independent, well-defined latent first-attempt block outcomes; no MAR assumption.',
   'The paired baseline retains actor-specific marginals within every model/law/format/SAFE/wording/mapping/display-order stratum.']}
 (output/'reproduction_checks.json').write_text(json.dumps(summary,indent=2)+'\n',encoding='utf-8')
 print(json.dumps(summary,indent=2))

if __name__=='__main__':
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--original',type=Path,default=ROOT.parent/'original')
 parser.add_argument('--output',type=Path,default=ROOT/'recomputed');args=parser.parse_args();main(args.original,args.output)
