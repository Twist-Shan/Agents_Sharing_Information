"""Recover all original 128-token API payloads offline; never sends requests.

python reconstruct_requests.py --verify
python reconstruct_requests.py --id 'luna|independent-b0000-qR-etable-s4-a0-p0.5'
python reconstruct_requests.py --output reconstructed_original128.jsonl
"""
from pathlib import Path
import argparse,csv,json,hashlib
BASE=Path(__file__).resolve().parent
def compact(x):return json.dumps(x,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False)
def digest(x):return hashlib.sha256(compact(x).encode()).hexdigest()
def records():
    templates={r['template_sha256']:r['messages'] for r in map(json.loads,(BASE/'stimulus_templates.jsonl').read_text(encoding='utf-8').splitlines())}
    profiles=json.loads((BASE/'request_options.json').read_text(encoding='utf-8'))['profiles']
    for r in csv.DictReader((BASE/'request_block_map.csv').open(encoding='utf-8',newline='')):
        p=profiles[r['model_key']]
        messages=[{'role':m['role'],'content':m['content'].replace('{operation}',r['operation'],1)} for m in templates[r['template_sha256']]]
        assert digest(messages)==r['message_sha256'],r['runtime_id']
        body={'model':p['model'],'messages':messages,'max_tokens':128,'reasoning':p['request_reasoning'],'provider':p['provider_request']}
        assert digest(body)==r['frozen128_request_sha256']==r['request_sha256'],r['runtime_id']
        yield {'runtime_id':r['runtime_id'],'block_id':r['block_id'],'original128_request_payload':body,'original128_request_sha256':r['frozen128_request_sha256'],'accepted_action':r['action'],'selected_attempt_id':r['selected_attempt_id'],'selected_request_token_ceiling':int(r['selected_request_token_ceiling'])}
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--verify',action='store_true');p.add_argument('--id');p.add_argument('--output',type=Path);a=p.parse_args()
    if not (a.verify or a.id or a.output):p.error('choose --verify, --id or --output; no network actions exist')
    n=0;found=False;out=a.output.open('w',encoding='utf-8',newline='\n') if a.output else None
    try:
        for r in records():
            n+=1
            if r['runtime_id']==a.id:print(json.dumps(r,indent=2,ensure_ascii=False));found=True
            if out:out.write(compact(r)+'\n')
    finally:
        if out:out.close()
    assert n==44800,n
    if a.id and not found:raise ValueError('unknown runtime_id')
    if a.verify:print(json.dumps({'status':'passed','original_payloads_reconstructed_and_hashed':n,'api_calls':0}))
