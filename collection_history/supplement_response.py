"""Separate fixed-512 request/response contract. Frozen runtime stays unchanged."""
import json
import runtime
import answer_extraction

MAX_TOKENS=512


def payload(profile,job):
    return {'model':profile['model'],'messages':job['messages'],'max_tokens':MAX_TOKENS,
            'reasoning':profile['request_reasoning'],'provider':profile['provider_request']}


def reserve(profile,body):
    return runtime.D(runtime.prompt_bound(body))*runtime.D(profile['input_bound'])+runtime.D(MAX_TOKENS)*runtime.D(profile['output_bound'])


def strict_classify(result,profile,job,bound):
    """Same identity/safety/usage checks, with actual 512 payload bounds, no spoofing."""
    obj=result.get('response');status=result.get('http_status')
    try:text=runtime.compact(obj).lower()
    except (ValueError,TypeError):return False,None,'fatal_response',True
    if any(t in text for t in ('content_filter','content_policy','policy_violation','policy rejection','moderation','safety policy')):
        return False,None,'fatal_policy',True
    if status in (401,402,403) or (type(status) is int and 400<=status<500 and status not in (408,429)):
        return False,None,'fatal_http_'+str(status),True
    if status is None or status in (408,429) or (type(status) is int and status>=500):return False,None,'transport',False
    if status!=200 or not isinstance(obj,dict) or runtime.nested_error(obj):return False,None,'fatal_response',True
    if obj.get('model') not in profile['allowed_models'] or obj.get('provider')!=profile['provider_name']:
        return False,None,'fatal_identity',True
    usage=obj.get('usage')
    if not isinstance(usage,dict):return False,None,'fatal_token_accounting',True
    details=usage.get('completion_tokens_details')
    if not isinstance(details,dict) or type(details.get('reasoning_tokens')) is not int or details['reasoning_tokens']!=0:
        return False,None,'fatal_reasoning_contract',True
    if any(type(usage.get(k)) is not int or usage[k]<0 for k in ('prompt_tokens','completion_tokens')):
        return False,None,'fatal_token_accounting',True
    if usage['completion_tokens']>MAX_TOKENS or usage['prompt_tokens']>runtime.prompt_bound(payload(profile,job)):
        return False,None,'fatal_token_bound',True
    cost=usage.get('cost')
    if cost is not None and (not runtime.finite_nonnegative(cost) or runtime.D(str(cost))>bound):
        return False,None,'fatal_cost_bound',True
    choices=obj.get('choices')
    if not isinstance(choices,list) or len(choices)!=1 or not isinstance(choices[0],dict):return False,None,'fatal_choices',True
    choice=choices[0];message=choice.get('message')
    if not isinstance(message,dict):return False,None,'fatal_message',True
    if message.get('refusal') or choice.get('finish_reason')=='content_filter':return False,None,'fatal_policy',True
    if any(message.get(k) for k in ('reasoning','reasoning_content','reasoning_details','tool_calls')) or any(obj.get(k) for k in ('reasoning','reasoning_content','reasoning_details')):
        return False,None,'fatal_unexpected_reasoning_or_tools',True
    if choice.get('finish_reason')=='error':return False,None,'fatal_response',True
    if choice.get('finish_reason')!='stop':return False,None,'invalid_finish',False
    try:
        pairs=json.loads(message.get('content'),object_pairs_hook=runtime.ObjectPairs)
        if not isinstance(pairs,runtime.ObjectPairs) or len(pairs)!=1 or pairs[0][0]!='action':raise ValueError()
        code=pairs[0][1]
        if not isinstance(code,str) or code not in job['answer_map']:raise ValueError()
    except (ValueError,TypeError,KeyError):return False,None,'invalid_schema',False
    return True,job['answer_map'][code],'valid',False


def classify(result,profile,job,bound):
    """Raw strict result and effective acceptance remain separate fields."""
    strict=strict_classify(result,profile,job,bound)
    decision=None
    valid,action,reason,fatal=strict
    if not valid and not fatal and reason=='invalid_schema':
        choice=result['response']['choices'][0]
        decision=answer_extraction.extract_content(choice['message'].get('content'),job['answer_map'],choice['finish_reason'])
    accepted=valid or bool(decision and decision['accepted'])
    return {'strict':strict,'accepted':accepted,
            'accepted_action':action if valid else decision['action'] if accepted else None,
            'acceptance_rule':'strict' if valid else decision['rule'] if accepted else None,
            'extraction':decision}
