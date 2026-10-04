"""Prospectively resumable, append-only OpenRouter runner; no scientific repair.
Only --execute sends paid requests. Hidden TTY credentials are never persisted.
A valid wrong answer is valid. First valid response wins; <=3 unchanged attempts.
"""
from pathlib import Path
from decimal import Decimal
from collections import Counter,deque
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime,timezone
from contextlib import contextmanager
from email.utils import parsedate_to_datetime
import argparse,hashlib,json,os,sys,time,getpass,warnings,urllib.request,urllib.error,math
from http.client import HTTPException
HERE=Path(__file__).resolve().parent
D=Decimal
BASE='https://openrouter.ai/api/v1/'
PRIOR=D('43.68265773418')
CAP=D('50')
TERMINAL={'complete','halted_fatal','halted_budget','halted_service','attempts_exhausted'}
class FatalRun(ValueError): pass
class PreflightUnavailable(RuntimeError): pass
def compact(x): return json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False)
def digest(x): return hashlib.sha256(x).hexdigest()
def sha(p): return digest(Path(p).read_bytes())
def now(): return datetime.now(timezone.utc).isoformat()
def read(p): return json.loads(Path(p).read_text(encoding='utf-8'))
def lines(p):
    return [json.loads(x) for x in Path(p).read_text(encoding='utf-8').splitlines()] if Path(p).exists() else []
def save(p,x):
    p=Path(p);t=p.with_suffix(p.suffix+'.writing')
    with t.open('w',encoding='utf-8',newline='\n') as f: f.write(compact(x)+'\n');f.flush();os.fsync(f.fileno())
    for attempt in range(30):
        try:
            os.replace(t,p);break
        except PermissionError:
            if attempt==29:raise
            time.sleep(.2)
def append(p,x):
    with Path(p).open('a',encoding='utf-8',newline='\n') as f: f.write(compact(x)+'\n');f.flush();os.fsync(f.fileno())
def require(x,why):
    if not x: raise FatalRun(why)
def finite_nonnegative(x):
    return type(x) in (int,float) and math.isfinite(x) and x>=0
def object_or_empty(x): return x if isinstance(x,dict) else {}
class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,*args,**kwargs): return None

@contextmanager
def execution_lock(path):
    """OS lock releases on crash. Persistent lock-file existence is not liveness."""
    fd=os.open(path,os.O_CREAT|os.O_RDWR)
    locked=False
    try:
        if os.name=='nt':
            import msvcrt
            if os.fstat(fd).st_size==0:os.write(fd,b' ')
            os.lseek(fd,0,os.SEEK_SET);msvcrt.locking(fd,msvcrt.LK_NBLCK,1)
        else:
            import fcntl
            fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB)
        locked=True
        os.lseek(fd,0,os.SEEK_SET);os.write(fd,str(os.getpid()).encode());os.ftruncate(fd,os.lseek(fd,0,os.SEEK_CUR));os.fsync(fd)
        yield
    finally:
        if locked:
            if os.name=='nt':
                import msvcrt
                os.lseek(fd,0,os.SEEK_SET);msvcrt.locking(fd,msvcrt.LK_UNLCK,1)
            else:
                import fcntl
                fcntl.flock(fd,fcntl.LOCK_UN)
        os.close(fd)

def http(path,key=None,payload=None):
    headers={'Content-Type':'application/json','User-Agent':'ReceiptDecisionValueResearch/1'}
    if key: headers['Authorization']='Bearer '+key
    req=urllib.request.Request(BASE+path,data=None if payload is None else compact(payload).encode(),headers=headers)
    opener=urllib.request.build_opener(NoRedirect())
    start=time.monotonic()
    try:
        try:
            with opener.open(req,timeout=60) as response:
                status=response.status;raw=response.read();retry=response.headers.get('Retry-After')
        except urllib.error.HTTPError as exc:
            status=exc.code;raw=exc.read();retry=exc.headers.get('Retry-After')
    except (urllib.error.URLError,TimeoutError,OSError,HTTPException) as exc:
        return {'http_status':None,'response':None,'transport_error':type(exc).__name__,
                'elapsed_seconds':time.monotonic()-start,'retry_after_seconds':0}
    try:
        obj=json.loads(raw,parse_constant=lambda value: (_ for _ in ()).throw(ValueError('nonfinite_json')))
        encoded=compact(obj)
        if key:encoded=encoded.replace(key,'[REDACTED]')
        obj=json.loads(encoded)
    except (ValueError,UnicodeError,TypeError):
        obj={'unparsed_body_sha256':digest(raw)}
    try: retry_seconds=float(retry or 0)
    except (ValueError,TypeError):
        try:retry_seconds=parsedate_to_datetime(retry).timestamp()-time.time()
        except (ValueError,TypeError,OverflowError):retry_seconds=0
    retry_seconds=max(0,retry_seconds) if math.isfinite(retry_seconds) else 0
    return {'http_status':status,'response':obj,'elapsed_seconds':time.monotonic()-start,
            'retry_after_seconds':retry_seconds}

def normalize_profiles(source):
    rows=source['profiles'] if isinstance(source,dict) else source
    require(isinstance(rows,list) and rows,'profiles_list_required')
    profiles=[]
    for original in rows:
        p=json.loads(compact(original))
        p.setdefault('model',p.get('model_id'))
        p.setdefault('allowed_models',p.get('returned_model_allowlist'))
        p.setdefault('input_bound',p.get('reservation_usd_per_token',{}).get('input'))
        p.setdefault('output_bound',p.get('reservation_usd_per_token',{}).get('output'))
        require(isinstance(p.get('key'),str) and isinstance(p.get('model'),str),'invalid_profile')
        require(p.get('request_reasoning') in ({'effort':'none'},{'enabled':False}),'thinking_not_disabled')
        provider=p.get('provider_request',{})
        require(provider.get('only')==[p['provider_tag']] and provider.get('allow_fallbacks') is False and provider.get('require_parameters') is True,
                'exact_provider_contract_required')
        require(isinstance(p.get('allowed_models'),list) and p['allowed_models'],'returned_model_allowlist_required')
        for field in ('input_bound','output_bound'):
            price=D(str(p[field]));require(price.is_finite() and price>=0,'invalid_price_bound')
        profiles.append(p)
    require(len({p['key'] for p in profiles})==len(profiles),'duplicate_model_key')
    return profiles

def payload(profile,job):
    return {'model':profile['model'],'messages':job['messages'],'max_tokens':512,
            'reasoning':profile['request_reasoning'],'provider':profile['provider_request']}
def prompt_bound(body): return len(compact(body).encode())+2048
def reserve(profile,body):
    return D(prompt_bound(body))*D(profile['input_bound'])+D(512)*D(profile['output_bound'])
def endpoint(profile,key=None):
    result=http('models/'+profile['model']+'/endpoints')
    if result['http_status']!=200:raise PreflightUnavailable('endpoint_metadata_unavailable')
    rows=object_or_empty(object_or_empty(result.get('response')).get('data')).get('endpoints',[])
    require(isinstance(rows,list),'invalid_endpoint_metadata')
    matches=[x for x in rows if isinstance(x,dict) and x.get('tag')==profile['provider_tag']]
    require(len(matches)==1,'endpoint_not_unique')
    e=matches[0]
    require(e.get('name')==profile['endpoint_name'] and e.get('provider_name')==profile['provider_name'],'endpoint_identity_changed')
    supported=e.get('supported_parameters',[])
    require('reasoning' in supported and 'max_tokens' in supported,'request_parameter_unsupported')
    pricing=e.get('pricing',{})
    for field,bound in (('prompt','input_bound'),('completion','output_bound'),
                        ('input_cache_read','input_bound'),('input_cache_write','input_bound')):
        if field not in pricing:continue
        price=D(str(pricing[field]));require(price.is_finite() and 0<=price<=D(profile[bound]),'price_bound_changed:'+field)
    require('prompt' in pricing and 'completion' in pricing,'missing_endpoint_price')
    max_tokens=profile.get('max_prompt_bound',0)
    for tier in pricing.get('overrides',[]):
        if tier.get('min_prompt_tokens',math.inf)>max_tokens:continue
        for field,bound in (('prompt','input_bound'),('completion','output_bound'),
                            ('input_cache_read','input_bound'),('input_cache_write','input_bound')):
            if field in tier:
                price=D(str(tier[field]));require(price.is_finite() and 0<=price<=D(profile[bound]),'tier_price_bound_changed:'+field)
    return e

class ObjectPairs(list): pass
def nested_error(obj):
    if isinstance(obj,dict):
        return any((k=='error' and bool(v)) or nested_error(v) for k,v in obj.items())
    return isinstance(obj,list) and any(nested_error(v) for v in obj)
def classify(result,profile,job,bound):
    obj=result.get('response'); status=result.get('http_status')
    try:text=compact(obj).lower()
    except (ValueError,TypeError):return False,None,'fatal_response',True
    if any(t in text for t in ('content_filter','content_policy','policy_violation','policy rejection','moderation','safety policy')):
        return False,None,'fatal_policy',True
    if status in (401,402,403) or (type(status) is int and 400<=status<500 and status not in (408,429)):
        return False,None,'fatal_http_'+str(status),True
    if status is None or status in (408,429) or (type(status) is int and status>=500):
        return False,None,'transport',False
    if status!=200 or not isinstance(obj,dict) or nested_error(obj):
        return False,None,'fatal_response',True
    if obj.get('model') not in profile['allowed_models'] or obj.get('provider')!=profile['provider_name']:
        return False,None,'fatal_identity',True
    usage=obj.get('usage')
    if not isinstance(usage,dict):return False,None,'fatal_token_accounting',True
    details=usage.get('completion_tokens_details')
    if not isinstance(details,dict) or type(details.get('reasoning_tokens')) is not int or details['reasoning_tokens']!=0:
        return False,None,'fatal_reasoning_contract',True
    if any(type(usage.get(k)) is not int or usage[k]<0 for k in ('prompt_tokens','completion_tokens')):
        return False,None,'fatal_token_accounting',True
    if usage['completion_tokens']>512 or usage['prompt_tokens']>prompt_bound(payload(profile,job)):
        return False,None,'fatal_token_bound',True
    cost=usage.get('cost')
    if cost is not None and (not finite_nonnegative(cost) or D(str(cost))>bound):
        return False,None,'fatal_cost_bound',True
    choices=obj.get('choices')
    if not isinstance(choices,list) or len(choices)!=1 or not isinstance(choices[0],dict): return False,None,'fatal_choices',True
    c=choices[0];message=c.get('message')
    if not isinstance(message,dict):return False,None,'fatal_message',True
    if message.get('refusal') or c.get('finish_reason')=='content_filter': return False,None,'fatal_policy',True
    if any(message.get(k) for k in ('reasoning','reasoning_content','reasoning_details','tool_calls')) or any(obj.get(k) for k in ('reasoning','reasoning_content','reasoning_details')):
        return False,None,'fatal_unexpected_reasoning_or_tools',True
    if c.get('finish_reason')=='error':return False,None,'fatal_response',True
    if c.get('finish_reason')!='stop': return False,None,'invalid_finish',False
    try:
        import re, protocol
        content=message.get('content')
        if not isinstance(content,str):raise ValueError()
        content=content.strip()
        fence=re.fullmatch(r"```(?:json)?\s*(.*?)\s*```",content,re.S|re.I)
        if fence:content=fence.group(1).strip()
        def unique(pairs):
            obj={}
            for k,v in pairs:
                if k in obj:raise ValueError('duplicate_key')
                obj[k]=v
            return obj
        answer=json.loads(content,object_pairs_hook=unique,
                          parse_constant=lambda x: (_ for _ in ()).throw(ValueError('nonfinite')))
        if job.get('module')=='compatibility':
            okay=isinstance(answer,dict) and set(answer)=={'action'} and answer['action']=='X'
        else:okay=protocol.valid_answer(job,answer)
        if not okay:raise ValueError()
    except (ValueError,TypeError,KeyError):return False,None,'invalid_schema',False
    return True,answer,'valid',False

def cost_value(result,bound):
    cost=object_or_empty(object_or_empty(result.get('response')).get('usage')).get('cost')
    known=finite_nonnegative(cost)
    return (D(str(cost)) if known else bound),not known
def compatibility(profile):
    return {'id':profile['key']+'|compatibility','model_key':profile['key'],'block_id':'compatibility','module':'compatibility',
            'metadata':{},'messages':[{'role':'user','content':'Return exactly the JSON object {"action":"X"}.'}],
            'answer_map':{'X':'JOIN'},'expected':'JOIN'}

class Ledger:
    """Incremental cost accounting and journal integrity; rebuild once per resume."""
    def __init__(self,started=(),settled=()):
        self.starts={};self.settled={};self.tries=Counter();self.accepted=set();self.occupied=PRIOR
        for row in started:self.start(row)
        for row in settled:self.settle(row)
    def start(self,row):
        ident=row['attempt_id'];cost=D(row['reserve_usd'])
        require(ident not in self.starts,'duplicate_start')
        require(row['id'] not in self.accepted,'retry_after_valid')
        require(row['attempt']==self.tries[row['id']]+1 and row['attempt']<=3,'attempt_count')
        require(ident==row['id']+'|try'+str(row['attempt']),'attempt_identifier')
        require(cost.is_finite() and cost>=0,'invalid_start_reserve')
        self.starts[ident]=row;self.tries[row['id']]+=1;self.occupied+=cost
    def settle(self,row):
        ident=row['attempt_id'];require(ident in self.starts and ident not in self.settled,'orphan_or_duplicate_settlement')
        start=self.starts[ident]
        require(all(row[k]==start[k] for k in ('id','model_key','attempt','request_sha256','reserve_usd')),'settlement_start_mismatch')
        cost=D(row['charged_or_reserved_usd']);require(cost.is_finite() and cost>=0,'invalid_settlement_cost')
        if row['cost_is_reserve']:require(cost==D(start['reserve_usd']),'unknown_cost_reserve_changed')
        if row.get('valid'):
            require(row['id'] not in self.accepted and self.tries[row['id']]==row['attempt'],'retry_after_valid')
            self.accepted.add(row['id'])
        self.settled[ident]=row;self.occupied+=cost-D(start['reserve_usd'])
def accounting(started,settled):
    # Independent full-journal sum, used only for terminal reconciliation.
    starts={row["attempt_id"]:row for row in started}
    costs={row["attempt_id"]:D(row["charged_or_reserved_usd"]) for row in settled}
    require(len(starts)==len(started) and len(costs)==len(settled) and set(costs)<=set(starts),"terminal_accounting_ids")
    return PRIOR+sum((costs.get(ident,D(row["reserve_usd"])) for ident,row in starts.items()),D(0))

class PauseTracker:
    """Latch any threshold crossed in issued order, even if later wave results succeed."""
    def __init__(self):self.recent=deque(maxlen=50);self.consecutive=0;self.trigger=None;self.retry_after=0
    def observe(self,row):
        failure=row.get('reason') in ('transport','interrupted_unknown')
        self.recent.append(failure);self.consecutive=self.consecutive+1 if failure else 0
        delay=row.get('retry_after_seconds',0)
        if finite_nonnegative(delay):self.retry_after=max(self.retry_after,delay)
        if self.trigger is None and (self.consecutive>=5 or (len(self.recent)==50 and sum(self.recent)>=10) or self.retry_after>60):
            self.trigger={'attempt_id':row['attempt_id'],'consecutive':self.consecutive,'window_size':len(self.recent),'window_failures':sum(self.recent)}
    def reset(self):self.__init__()
def pause_state(settled,events):
    begins=[x for x in events if x['event']=='operational_pause']
    completions=[x for x in events if x['event']=='operational_pause_completed']
    require(len({x['pause'] for x in begins})==len(begins),'duplicate_pause')
    require(len({x['pause'] for x in completions})==len(completions),'duplicate_pause_completion')
    require(all(any(b['pause']==c['pause'] for b in begins) for c in completions),'orphan_pause_completion')
    completed={x['pause'] for x in completions}
    pending=[x for x in begins if x['pause'] not in completed]
    require(len(pending)<=1,'multiple_pending_pauses')
    reset=max([x['settled_count'] for x in completions],default=0)
    require(reset<=len(settled),'pause_journal_ahead')
    tracker=PauseTracker()
    for row in settled[reset:]:tracker.observe(row)
    return tracker,len(begins),(pending[0] if pending else None)

def freeze(profiles_path,run):
    import protocol
    require(not run.exists(),'run_directory_exists')
    profile=normalize_profiles(read(profiles_path))[0]
    jobs=protocol.generate()
    require(len(jobs)==5632,'scientific_allocation_mismatch')
    for j in jobs:
        j['model_key']='luna'
        j.setdefault('module','diagnostic_aid')
        j['request_sha256']=digest(compact(payload(profile,j)).encode())
    require(len({j['id'] for j in jobs})==len(jobs),'duplicate_ids')
    profile['max_prompt_bound']=max(prompt_bound(payload(profile,j)) for j in jobs+[compatibility(profile)])
    names=('runtime.py','protocol.py','analysis.py','profiles.json','PLAN.md','original_protocol.py','verify.py')
    for n in names:require((HERE/n).exists(),'missing_frozen_source:'+n)
    run.mkdir(parents=True)
    with (run/'planned.jsonl').open('x',encoding='utf-8',newline='\n') as f:
        for j in jobs:f.write(compact(j)+'\n')
    total=sum((reserve(profile,payload(profile,j)) for j in jobs+[compatibility(profile)]),D(0))
    require(PRIOR+total<=CAP,'first_pass_unfunded')
    m={'version':3,'kind':'TARGETED_REFERENT_FRAMING_AND_PAYOFF_TESTS','profiles':[profile],
       'sources':{n:sha(HERE/n) for n in names},'planned_sha256':sha(run/'planned.jsonl'),
       'scientific_count':len(jobs),'prior_occupied_usd':str(PRIOR),'cumulative_cap_usd':str(CAP),
       'first_pass_max_reservation_usd':str(total),'max_attempts_per_id':3,'concurrency':16,
       'acquisition':'Three unchanged attempts for operational/schema failures only; first valid answer retained. Strict JSON or a single JSON code fence. Finite wrong numeric values retained. Fixed sample, independent calls, no diagnostic filtering.',
       'operational_pause':'Five consecutive transport failures or ten in fifty issued attempts: cooldown 60/120/240/300 seconds, maximum twelve pauses; revalidate endpoint before resume. First policy/fatal contract failure stops new issues, drains issued wave.',
       'frozen_utc':now()}
    m['manifest_sha256']=digest(compact(m).encode());save(run/'manifest.json',m)
    print(compact({'status':'frozen','manifest_sha256':m['manifest_sha256'],'science':len(jobs),
                   'first_pass_reserve':str(total),'occupied_including_first_pass':str(PRIOR+total)}))

def validate(run):
    m=read(run/'manifest.json');body=dict(m);h=body.pop('manifest_sha256')
    require(digest(compact(body).encode())==h,'manifest_modified')
    require(sha(run/'planned.jsonl')==m['planned_sha256'],'schedule_modified')
    for n,h in m['sources'].items():require(sha(HERE/n)==h,'source_changed:'+n)
    require(m['prior_occupied_usd']==str(PRIOR) and m['cumulative_cap_usd']==str(CAP),'budget_changed')
    require(m['version']==3 and m['max_attempts_per_id']==3 and m['concurrency']==16,'runtime_policy_changed')
    jobs=lines(run/'planned.jsonl');profile=m['profiles'][0]
    require(len(jobs)==5632 and len({j['id'] for j in jobs})==5632,'job_count')
    for j in jobs:require(digest(compact(payload(profile,j)).encode())==j['request_sha256'],'request_changed')
    return m,jobs

def execute(run,compat_only=False):
    m,jobs=validate(run)
    with execution_lock(run/'execution.lock'):
        return _execute_locked(run,m,jobs,compat_only)

def _execute_locked(run,m,jobs,compat_only=False):
    prior_state=read(run/'status.json') if (run/'status.json').exists() else {}
    require(prior_state.get('state') not in TERMINAL,'terminal_run_cannot_resume')
    if prior_state:require(prior_state.get('manifest_sha256')==m['manifest_sha256'],'status_manifest_mismatch')
    started=lines(run/'started.jsonl');settled=lines(run/'attempts.jsonl')
    ledger=Ledger(started,settled);events=lines(run/'operations.jsonl')
    profiles={p['key']:p for p in m['profiles']}
    compjobs=[compatibility(p) for p in m['profiles']]
    byid={j['id']:j for j in jobs+compjobs}
    for row in started:
        require(row['id'] in byid and row['model_key']==byid[row['id']]['model_key'],'unknown_started_job')
        prof=profiles[row['model_key']];body=payload(prof,byid[row['id']])
        require(row['request_sha256']==digest(compact(body).encode()) and D(row['reserve_usd'])==reserve(prof,body),'started_request_changed')
    for row in settled:
        if row.get('reason')=='interrupted_unknown':require(not row.get('valid') and row.get('cost_is_reserve'),'invalid_crash_settlement');continue
        checked=classify(row,profiles[row['model_key']],byid[row['id']],D(row['reserve_usd']))
        if row.get('reason') not in ('fatal_fingerprint_drift','fatal_worker_exception'):
            require(checked==(row['valid'],row['action'],row['reason'],row['fatal']),'settlement_classification_changed')
        charged,reserved=cost_value(row,D(row['reserve_usd']))
        require(D(row['charged_or_reserved_usd'])==charged and row['cost_is_reserve']==reserved,'settlement_cost_changed')
    state='interrupted';reason=None
    accepted=ledger.accepted
    science_accepted=sum(not ident.endswith('|compatibility') for ident in accepted)
    def snapshot():
        save(run/'status.json',{'state':state,'reason':reason,'utc':now(),'pid':os.getpid(),'manifest_sha256':m['manifest_sha256'],
                               'scientific_planned':len(jobs),'science_accepted':science_accepted,'physical_started':len(started),
                               'physical_settled':len(settled),'inflight':len(ledger.starts)-len(ledger.settled),
                               'cumulative_occupied_usd':str(ledger.occupied),'lock_kind':'os_advisory_persistent_file'})
        if state in TERMINAL:
            # Re-read disk, independently sum costs, and bind terminal ledger to journals.
            disk_started=lines(run/'started.jsonl');disk_settled=lines(run/'attempts.jsonl')
            independent=accounting(disk_started,disk_settled)
            require(disk_started==started and disk_settled==settled and independent==ledger.occupied,"terminal_ledger_reconciliation")
            known=sum((D(row["charged_or_reserved_usd"]) for row in disk_settled if not row["cost_is_reserve"]),D(0))
            reserved=independent-PRIOR-known
            save(run/'final_ledger.json',{'status':'independently_reconciled','prior_occupied_usd':str(PRIOR),
                 'known_new_cost_usd':str(known),'unknown_new_reserved_usd':str(reserved),
                 'cumulative_occupied_usd':str(independent),'cumulative_cap_usd':str(CAP),
                 'started_sha256':sha(run/'started.jsonl') if (run/'started.jsonl').exists() else None,
                 'settled_sha256':sha(run/'attempts.jsonl') if (run/'attempts.jsonl').exists() else None,
                 'manifest_sha256':m['manifest_sha256']})

    def settle(row):
        append(run/'attempts.jsonl',row);ledger.settle(row);settled.append(row)
    try:
        if ledger.occupied>CAP:state='halted_budget';reason='cumulative_budget_exceeded';snapshot();return
        # Crash-unknown starts consume both their attempt and full reserve.
        for start in started:
            if start['attempt_id'] not in ledger.settled:
                settle({**start,'valid':False,'action':None,'reason':'interrupted_unknown','fatal':False,
                        'charged_or_reserved_usd':start['reserve_usd'],'cost_is_reserve':True,'settled_utc':now()})
        if any(row.get('fatal') for row in settled):
            state='halted_fatal';reason='fatal_journal_prevents_resume';snapshot();return
        tracker,pauses,pending_pause=pause_state(settled,events)
        if not sys.stdin.isatty():raise PreflightUnavailable('hidden_tty_required')
        with warnings.catch_warnings():
            warnings.simplefilter('error',getpass.GetPassWarning)
            key=getpass.getpass('OpenRouter key (hidden): ')
        if not key.strip():raise PreflightUnavailable('empty_key')
        account=http('key',key)
        if account['http_status']!=200:raise PreflightUnavailable('account_preflight_failed')
        details=object_or_empty(object_or_empty(account.get('response')).get('data'))
        clean={k:details.get(k) for k in ('usage','limit','limit_remaining')}
        append(run/'preflight.jsonl',{'utc':now(),'manifest_sha256':m['manifest_sha256'],'account':clean})
        state='running';snapshot()
        def do_pause(profile):
            nonlocal pending_pause,pauses,state,reason
            if pending_pause is None:
                pauses+=1
                if pauses>12:
                    state='halted_service';reason='maximum_operational_pauses';snapshot();return False
                delay=max(tracker.retry_after,[60,120,240,300][min(pauses-1,3)])
                pending_pause={'event':'operational_pause','utc':now(),'pause':pauses,'model_key':profile['key'],
                               'seconds':delay,'until_unix':time.time()+delay,'settled_count':len(settled),'trigger':tracker.trigger}
                append(run/'operations.jsonl',pending_pause)
            state='paused';snapshot()
            # No new request is issued until the original pause deadline has elapsed.
            time.sleep(max(0,pending_pause['until_unix']-time.time()))
            p=profiles[pending_pause['model_key']]
            ep=endpoint(p)
            append(run/'preflight.jsonl',{'utc':now(),'model_key':p['key'],'endpoint':ep,'after_pause':pauses,'manifest_sha256':m['manifest_sha256']})
            append(run/'operations.jsonl',{'event':'operational_pause_completed','utc':now(),'pause':pending_pause['pause'],'settled_count':len(settled)})
            pending_pause=None;tracker.reset();state='running';snapshot();return True
        if pending_pause is not None or tracker.trigger is not None:
            pause_profile=profiles[pending_pause['model_key']] if pending_pause else profiles[settled[-1]['model_key']]
            if not do_pause(pause_profile):return
        for profile in m['profiles']:
            ep=endpoint(profile)
            append(run/'preflight.jsonl',{'utc':now(),'model_key':profile['key'],'endpoint':ep,'manifest_sha256':m['manifest_sha256']})
            comp=compatibility(profile)
            subset=[comp]+([] if compat_only else [j for j in jobs if j['model_key']==profile['key']])
            fingerprint=None
            for row in settled:
                obj=object_or_empty(row.get('response'))
                if row.get('model_key')==profile['key'] and obj.get('model') in profile['allowed_models'] and obj.get('provider')==profile['provider_name']:
                    fp=obj.get('system_fingerprint')
                    if fp is not None:
                        require(fingerprint is None or fingerprint==fp,'historical_fingerprint_drift')
                        fingerprint=fp
            with ThreadPoolExecutor(max_workers=m['concurrency']) as pool:
                index=0
                while index<len(subset):
                    size=1 if index==0 else m['concurrency']
                    block=subset[index:index+size];index+=size
                    pending=[j for j in block if j['id'] not in accepted and ledger.tries[j['id']]<3]
                    while pending:
                        bodies=[payload(profile,j) for j in pending]
                        bounds=[reserve(profile,body) for body in bodies]
                        if ledger.occupied+sum(bounds,D(0))>CAP:
                            state='halted_budget';reason='cumulative_budget_reservation';snapshot();return
                        starts=[]
                        for j,body,bound in zip(pending,bodies,bounds):
                            attempt=ledger.tries[j['id']]+1
                            start={'id':j['id'],'model_key':profile['key'],'attempt':attempt,
                                   'attempt_id':j['id']+'|try'+str(attempt),'utc':now(),
                                   'request_sha256':digest(compact(body).encode()),'reserve_usd':str(bound)}
                            append(run/'started.jsonl',start);ledger.start(start);started.append(start);starts.append(start)
                        snapshot()
                        futures=[pool.submit(http,'chat/completions',key,body) for body in bodies]
                        failed_transport=False;fatal=None;delay=.25
                        for j,start,future in zip(pending,starts,futures):
                            try:result=future.result()
                            except Exception as exc:
                                # Settle every already-issued call before stopping; no exception text can contain a key.
                                result={'http_status':None,'response':None,'worker_error':type(exc).__name__,'retry_after_seconds':0}
                            bound=D(start['reserve_usd'])
                            valid,action,why,is_fatal=classify(result,profile,j,bound)
                            if 'worker_error' in result:valid=False;action=None;why='fatal_worker_exception';is_fatal=True
                            obj=object_or_empty(result.get('response'));fp=obj.get('system_fingerprint')
                            if obj.get('model') in profile['allowed_models'] and obj.get('provider')==profile['provider_name'] and fp is not None:
                                if fingerprint is None:fingerprint=fp
                                elif fp!=fingerprint:valid=False;action=None;why='fatal_fingerprint_drift';is_fatal=True
                            charged,reserved=cost_value(result,bound)
                            row={**start,**result,'valid':valid,'action':action,'reason':why,'fatal':is_fatal,
                                 'charged_or_reserved_usd':str(charged),'cost_is_reserve':reserved,'settled_utc':now()}
                            settle(row)
                            if valid and not j['id'].endswith('|compatibility'):science_accepted+=1
                            if is_fatal and fatal is None:fatal=why
                            tracker.observe(row)
                            failed_transport|=why=='transport'
                            if finite_nonnegative(result.get('retry_after_seconds')):delay=max(delay,result['retry_after_seconds'])
                        snapshot()
                        if fatal:
                            state='halted_fatal';reason=fatal;snapshot();return
                        if tracker.trigger is not None:
                            if not do_pause(profile):return
                        else:time.sleep(max(delay,2 if failed_transport else .25))
                        pending=[j for j in block if j['id'] not in accepted and ledger.tries[j['id']]<3]
                    if block[0]['module']=='compatibility' and comp['id'] not in accepted:
                        state='halted_fatal';reason='compatibility_failed';snapshot();return
                    if len(started)%128<8:
                        print(compact({'model':profile['key'],'settled':len(settled),'accepted':len(accepted),
                                       'occupied_usd':str(ledger.occupied)}),flush=True)
        state='compatibility_complete' if compat_only else ('complete' if science_accepted==len(jobs) else 'attempts_exhausted');reason=None;snapshot()
    except (KeyboardInterrupt,PreflightUnavailable) as exc:
        state='interrupted';reason=str(exc) if isinstance(exc,PreflightUnavailable) else type(exc).__name__;snapshot()
        print(compact({'status':state,'reason':reason}),flush=True);raise SystemExit(1)
    except BaseException as exc:
        state='halted_fatal';reason=str(exc) if isinstance(exc,FatalRun) else type(exc).__name__
        if 'key' in locals():reason=reason.replace(key,'[REDACTED]')
        # Only static contract-failure labels are serialized; arbitrary exception messages are omitted.
        snapshot();print(compact({'status':state,'reason':reason}),flush=True);raise SystemExit(1)
    finally:
        if 'key' in locals():key=None
    print(compact({'status':state,'science_planned':len(jobs),'occupied_usd':str(ledger.occupied)}),flush=True)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--freeze',action='store_true');p.add_argument('--execute',action='store_true')
    p.add_argument('--compat-only',action='store_true');p.add_argument('--profiles',type=Path,default=HERE/'profiles.json')
    p.add_argument('--run',type=Path,default=HERE/'validation');a=p.parse_args()
    if a.freeze:freeze(a.profiles,a.run)
    elif a.execute:execute(a.run,a.compat_only)
    else:p.print_help()

