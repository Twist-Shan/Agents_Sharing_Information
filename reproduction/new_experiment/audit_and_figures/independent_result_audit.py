"""Recompute completed diagnostic results from CSV without importing analysis.py."""
from collections import Counter,defaultdict
from decimal import Decimal
from pathlib import Path
import argparse,csv,json,math,re,statistics
from scipy.stats import t

HERE=Path(__file__).resolve().parent
DEFAULT_EXPERIMENT=(HERE/'new_experiment' if (HERE/'new_experiment').is_dir() else HERE.parent)


def read_csv(root,name):
    with (root/name).open(encoding='utf-8-sig',newline='') as f:
        return list(csv.DictReader(f))


def numeric(row,key):
    return Decimal(row['normalized.'+key])


def independently_score(row):
    policy,law=row['metadata.policy'],row['metadata.law']
    p=Decimal('.5') if law=='R' or policy=='independent' else Decimal(1 if policy=='responsive' else 0)
    safe=Decimal(row['metadata.safe'])
    mode=row['mode']
    if mode in ('U','A1','A2','A3'):
        join_code='X' if row['metadata.mapping']=='0' else 'Y'
        selected_join=row['normalized.action']==join_code
        return selected_join==(10*p>safe)
    if mode=='D1':
        a,b={'responsive':(1,0),'independent':('.5','.5'),'complement':(0,1)}[policy]
        targets={'join_if_present':Decimal(a),'join_if_absent':Decimal(b)}
    elif mode=='D2':
        targets={'partner_join_probability':p}
    else:
        targets={'join_expected_score':10*p,'safe_expected_score':safe}
    return all(abs(numeric(row,k)-v)<=Decimal('0.00000001') for k,v in targets.items())


def run(experiment=DEFAULT_EXPERIMENT, output=HERE/'independent_result_audit.json'):
    EXP=Path(experiment).resolve()
    OUT=EXP/'exports'
    output=Path(output).resolve()
    status=json.loads((EXP/'run_v2'/'status.json').read_text(encoding='utf-8'))
    assert status['state']=='complete'
    rows=read_csv(OUT,'final_scored_requests.csv')
    assert len(rows)==5376 and len({r['id'] for r in rows})==5376
    assert all(r['valid']=='True' for r in rows)
    for row in rows:
        row['recomputed_correct']=independently_score(row)
        assert row['recomputed_correct']==(row['correct']=='True')
    modes={}
    for mode in ('U','D1','D2','D3','A1','A2','A3'):
        these=[r for r in rows if r['mode']==mode]
        assert len(these)==768
        correct=sum(r['recomputed_correct'] for r in these)
        modes[mode]={'correct':correct,'n':len(these),'accuracy':correct/len(these)}
    bycell=defaultdict(dict)
    for row in rows:
        bycell[row['metadata.cell_id']][row['mode']]=row
    contrasts={}
    expected_export={r['contrast']:r for r in read_csv(OUT,'aid_contrasts.csv') if r['response_policy']=='final'}
    for plus,minus in (('A1','U'),('A2','A1'),('A3','A2')):
        block=defaultdict(list)
        for values in bycell.values():
            a,b=values[plus],values[minus]
            block[int(a['metadata.block_index'])].append(int(a['recomputed_correct'])-int(b['recomputed_correct']))
        assert len(block)==32 and all(len(x)==24 for x in block.values())
        blockmeans={b:sum(values)/24 for b,values in block.items()}
        mean=sum(blockmeans.values())/32
        variances=[]
        word_means={}
        for w in range(4):
            x=[blockmeans[b] for b in sorted(blockmeans) if b%4==w]
            assert len(x)==8
            mu=sum(x)/8
            var=sum((z-mu)**2 for z in x)/7
            variances.append(var/8/16)
            word_means[str(w)]=mu
        v=sum(variances);se=math.sqrt(v)
        df=v*v/sum(vv*vv/7 for vv in variances)
        critical=float(t.ppf(1-.05/6,df))
        ci=[max(-1,mean-critical*se),min(1,mean+critical*se)]
        radius=math.sqrt(2*math.log(120)/32)
        hoeffding=[max(-1,mean-radius),min(1,mean+radius)]
        name=plus+'_minus_'+minus
        e=expected_export[name]
        assert math.isclose(mean,float(e['estimate']),abs_tol=1e-13)
        assert math.isclose(se,float(e['standard_error']),abs_tol=1e-13)
        assert math.isclose(df,float(e['degrees_of_freedom']),abs_tol=1e-11)
        assert all(math.isclose(a,b,abs_tol=1e-13) for a,b in zip(ci,json.loads(e['approximate_simultaneous_95_ci'])))
        assert all(math.isclose(a,b,abs_tol=1e-13) for a,b in zip(hoeffding,json.loads(e['hoeffding_simultaneous_95_ci'])))
        contrasts[name]={'estimate':mean,'approximate_family95':ci,'hoeffding_family95':hoeffding,
                         'standard_error':se,'degrees_of_freedom':df,'wording_means':word_means}
    first=read_csv(OUT,'first_scored_requests.csv')
    assert len(first)==5376
    assert sum(r['valid']=='True' for r in first)==5357
    lineages=read_csv(OUT,'request_lineage.csv')
    missing=Counter(r['first_attempt_reason'] for r in lineages if r['first_attempt_valid']=='False')
    assert missing==Counter({'interrupted_unknown':16,'transport':3})
    assert Counter(r['accepted_attempt'] for r in lineages)==Counter({'1':5357,'2':19})
    # Recalculate money directly from raw journal decimal amounts and starts.
    starts=[json.loads(x) for x in (EXP/'run_v2'/'started.jsonl').read_text(encoding='utf-8').splitlines()]
    attempts=[json.loads(x) for x in (EXP/'run_v2'/'attempts.jsonl').read_text(encoding='utf-8').splitlines()]
    assert len(starts)==len(attempts)==5396
    assert {x['attempt_id'] for x in starts}=={x['attempt_id'] for x in attempts}
    known=sum((Decimal(a['charged_or_reserved_usd']) for a in attempts if not a['cost_is_reserve']),Decimal(0))
    reserved=sum((Decimal(a['charged_or_reserved_usd']) for a in attempts if a['cost_is_reserve']),Decimal(0))
    occupied=Decimal('43.36383745918')+known+reserved
    assert occupied==Decimal('43.68265773418')==Decimal(status['cumulative_occupied_usd'])
    assert known==Decimal('0.3028449') and reserved==Decimal('0.01597537500')
    # All accepted raw responses are parseable as one direct JSON or one fence.
    format_counts=Counter()
    for a in attempts:
        if not a['valid']:continue
        content=a['response']['choices'][0]['message']['content'].strip()
        fence=re.fullmatch(r'```(?:json)?\s*(.*?)\s*```',content,re.S|re.I)
        if fence:
            content=fence.group(1).strip();format_counts['single_fence']+=1
        else:format_counts['direct_json']+=1
        parsed=json.loads(content)
        assert parsed==a['action']
    failures=Counter(a['reason'] for a in attempts if not a['valid'])
    assert failures==Counter({'interrupted_unknown':16,'transport':3})
    domain_violations=[]
    for row in rows:
        if row['mode'] not in ('D1','D2','D3'):continue
        hi=Decimal(10) if row['mode']=='D3' else Decimal(1)
        for key,value in row.items():
            if key.startswith('normalized.') and value:
                x=Decimal(value)
                if not x.is_finite() or not 0<=x<=hi:
                    domain_violations.append({'id':row['id'],'field':key,'value':value})
    # Descriptive subgroup tables and repeated numeric errors; no extra tests.
    complement_s={}
    for mode in modes:
        complement_s[mode]={}
        for w in range(4):
            g=[x for x in rows if x['mode']==mode and x['metadata.policy']=='complement' and x['metadata.law']=='S' and x['metadata.wording']==str(w)]
            assert len(g)==32
            complement_s[mode][str(w)]={'correct':sum(x['recomputed_correct'] for x in g),'n':32}
    policy_law={}
    for policy in ('responsive','independent','complement'):
        for law in ('R','S'):
            policy_law[policy+'_'+law]={}
            for mode in modes:
                g=[x for x in rows if x['mode']==mode and x['metadata.policy']==policy and x['metadata.law']==law]
                assert len(g)==128
                policy_law[policy+'_'+law][mode]={'correct':sum(x['recomputed_correct'] for x in g),'n':128}
    d3=[x for x in rows if x['mode']=='D3']
    safe_correct=sum(numeric(x,'safe_expected_score')==Decimal(x['metadata.safe']) for x in d3)
    wrong_join=Counter((x['metadata.p'],str(numeric(x,'join_expected_score').normalize())) for x in d3 if not x['recomputed_correct'])
    detailed_wrong_join=Counter((x['metadata.wording'],x['metadata.policy'],x['metadata.law'],x['metadata.p'],
                                str(numeric(x,'join_expected_score').normalize()))
                               for x in d3 if not x['recomputed_correct'])
    d2wrong=Counter((x['metadata.policy'],x['metadata.law'],x['metadata.wording'],str(numeric(x,'partner_join_probability').normalize())) for x in rows if x['mode']=='D2' and not x['recomputed_correct'])
    result=dict(passed=True,mode_rates=modes,adjacent_contrasts=contrasts,
                first_valid=5357,first_missing=19,missing_causes=dict(missing),
                known_cost_usd=str(known),reserved_cost_usd=str(reserved),occupied_usd=str(occupied),
                raw_accepted_format_counts=dict(format_counts),schema_failure_count=0,
                numeric_domain_violations=domain_violations,D3_safe_score_correct=safe_correct,
                complement_S_by_wording=complement_s,policy_law_rates=policy_law,
                D3_wrong_join_patterns=[{'true_p':k[0],'reported_join_EV':k[1],'n':n} for k,n in wrong_join.most_common()],
                D2_wrong_patterns=[{'policy':k[0],'law':k[1],'wording':k[2],'reported_p':k[3],'n':n} for k,n in d2wrong.most_common()],
                A3_errors=[x['id'] for x in rows if x['mode']=='A3' and not x['recomputed_correct']],
                independence_note='This file imports neither the protocol nor analysis implementation. CSV answers were rescored from the analytic partner rules; every primary CI was independently recomputed.',
                paid_calls=0)
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    simple=[dict(true_partner_join_probability=k[0],true_join_expected_score=str(Decimal(k[0])*10),
                 reported_join_expected_score=k[1],count=n,
                 reporting_status='Post hoc descriptive frequency; no additional significance test or mechanism inference.')
            for k,n in wrong_join.most_common()]
    detailed=[dict(wording=k[0],policy=k[1],law=k[2],true_partner_join_probability=k[3],
                   true_join_expected_score=str(Decimal(k[3])*10),reported_join_expected_score=k[4],count=n,
                   reporting_status='Post hoc descriptive frequency; pooled over SAFE, encoding, and other balanced factors; no mechanism inference.')
              for k,n in sorted(detailed_wrong_join.items())]
    for name,data in [('diagnostic_join_ev_errors.csv',simple),('diagnostic_join_ev_errors_by_wording_policy_law.csv',detailed)]:
        with (output.parent/name).open('w',encoding='utf-8-sig',newline='') as f:
            writer=csv.DictWriter(f,fieldnames=list(data[0]) if data else ['count','reporting_status'])
            writer.writeheader();writer.writerows(data)
    appendix=('All numerical diagnostic responses were well formed, all 768 reported SAFE scores were correct, '
              'and the most frequent JOIN-score error was 2.5 instead of the correct expected score of 5 (161 responses). '
              'These post hoc error frequencies are descriptive and do not identify whether the discrepancies arose from '
              'conditioning, arithmetic, or another aspect of the task representation.\n')
    (output.parent/'diagnostic_error_appendix_sentences.txt').write_text(appendix,encoding='utf-8')
    print(json.dumps({k:result[k] for k in ('passed','mode_rates','adjacent_contrasts','first_valid','first_missing','occupied_usd','raw_accepted_format_counts','schema_failure_count','numeric_domain_violations','D3_safe_score_correct','policy_law_rates')},indent=2))
    return result


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--experiment',type=Path,default=DEFAULT_EXPERIMENT,
                        help='Portable new_experiment directory containing exports and run_v2.')
    parser.add_argument('--output',type=Path,default=HERE/'independent_result_audit.json',
                        help='Audit JSON destination; descriptive CSVs are saved beside it.')
    args=parser.parse_args()
    run(args.experiment,args.output)
