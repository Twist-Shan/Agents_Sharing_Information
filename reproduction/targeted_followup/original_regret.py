"""Descriptive expected regret from archived original selections; no new tests."""
from pathlib import Path
from collections import defaultdict
import csv,json,argparse

def main(source,output):
    groups=defaultdict(list)
    for row in csv.DictReader(source.open(encoding='utf-8-sig')):
        if row['model_key']!='luna' or row['module'] not in ('independent','responsive','complement'):continue
        assert row['valid']=='True' and row['action'] in ('JOIN','SAFE')
        p=float(row['p']);safe=int(row['safe']);chosen=10*p if row['action']=='JOIN' else safe
        regret=max(10*p,safe)-chosen
        assert abs(regret-(0 if row['correct']=='True' else abs(10*p-safe)))<1e-12
        groups[(row['policy'],row['encoding'],safe,row['law'])].append(regret)
    result=[{'policy':k[0],'encoding':k[1],'safe':k[2],'law':k[3],'n':len(v),'mean_regret':sum(v)/len(v)} for k,v in sorted(groups.items())]
    output.parent.mkdir(parents=True,exist_ok=True);output.write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps({'descriptive_cells':len(result),'selected_choices':sum(x['n'] for x in result),'new_tests':0}))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--input',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();main(a.input,a.output)
