"""Pure, answer-map-only extraction. No I/O, model call, or correctness oracle."""
from __future__ import annotations
import hashlib
import json
import re

POLICY_VERSION = 'stop-only-explicit-answer-v1'
_EXAMPLE = re.compile(r'\b(?:examples?|samples?|schema|template|quoted|prompt|instructions?|output labels|if|would|could|possible|hypothetical|not|never|unless)\b|\be\.g\.', re.I)
_FINAL = re.compile(r'(?:^|(?<=[.!?\n]))\s*(?:(?:therefore|thus|hence|so)[,:]?\s*)?(?:(?:my|the)\s+)?'
                    r'(?:final\s+(?:answer|choice|action)|answer|choice|selected\s+(?:answer|action)|I\s+(?:choose|select))'
                    r'\s*(?::|=|\bis\b)?\s*["\']?\s*(?P<label>JOIN|SAFE|X|Y)\b(?P<tail>[^\n.!?]*)', re.I)
_ACTION = re.compile(r'"action"\s*:', re.I)
_AUTHORITATIVE_JSON_PREFIX = re.compile(r'(?:(?:therefore|thus|hence|so)[,:]?\s*)?'
    r'(?:(?:(?:my|the)\s+)?(?:final\s+)?(?:answer|choice|action|output)|I\s+(?:choose|select)|here\s+is\s+my\s+(?:final\s+)?answer)\s*(?::|=|is)?\s*',re.I)
_FINAL_SUFFIX = re.compile(r'\s*(?:\(\s*(?:JOIN|SAFE|X|Y)\s*\)|[-—–,:]\s*(?:JOIN|SAFE|X|Y)|(?:JOIN|SAFE))?\s*["\']?\s*[,;:]?\s*',re.I)


class _Pairs(list):
    pass


def _quote_spans(text):
    spans=[]
    for pattern in (r'"(?:\\.|[^"\\])*"', r"(?<!\w)'(?:\\.|[^'\\\n])*'", r'“[^”]*”', r'‘[^’]*’'):
        spans.extend((m.start(),m.end()) for m in re.finditer(pattern,text))
    return spans


def _ignored_spans(text):
    spans=_quote_spans(text);offset=0;example_block=False;fence=False;fence_example=False;previous=''
    for line in text.splitlines(keepends=True):
        stripped=line.strip();is_fence=stripped.startswith('```') or stripped.startswith('~~~')
        if is_fence:
            if not fence:
                fence=True;fence_example=bool(_EXAMPLE.search(previous)) or example_block
            else:
                if fence_example:spans.append((offset,offset+len(line)))
                fence=False;fence_example=False
            previous=stripped;offset+=len(line);continue
        if not stripped:
            example_block=False
        elif stripped.startswith('>') or (fence and fence_example) or example_block:
            spans.append((offset,offset+len(line)))
        elif _EXAMPLE.search(stripped) and not stripped.startswith('{'):
            # A quoted/example instruction is not the assistant's own answer.
            spans.append((offset,offset+len(line)))
            example_block=True
        if stripped:previous=stripped
        offset+=len(line)
    return spans


def extract_content(content, answer_map, finish_reason='stop'):
    """Return a decision from complete explicit JSON or final-answer syntax only.

    Interface/reasoning/fingerprint/cost verification is the caller's duty.
    The function never receives expected answers, task conditions, or payoffs.
    Only stop-terminated responses are eligible; length is always unresolved.
    """
    if not isinstance(answer_map,dict) or set(answer_map)!={'X','Y'} or set(answer_map.values())!={'JOIN','SAFE'}:
        raise ValueError('answer_extraction:invalid_answer_map')
    digest=hashlib.sha256(content.encode('utf-8')).hexdigest() if isinstance(content,str) else None
    result={'accepted':False,'label':None,'action':None,'rule':None,'reason':None,
            'content_sha256':digest,'evidence':None,'truncated':finish_reason=='length','policy_version':POLICY_VERSION}
    def reject(reason):
        return {**result,'reason':reason}
    if finish_reason!='stop':return reject('non_stop_response')
    if not isinstance(content,str) or not content.strip():return reject('missing_text')
    if len(content)>131072:return reject('text_bound')
    bare=content.strip()
    fenced=re.fullmatch(r'(?:```|~~~)(?:text|plaintext)?\s*\n(.*?)\n(?:```|~~~)',bare,re.I|re.S)
    if fenced:bare=fenced.group(1).strip()
    bare=bare.strip('`*_ ')
    direct=re.fullmatch(r'(JOIN|SAFE|X|Y)[.!;:]?',bare,re.I)
    if direct:
        token=direct.group(1).upper()
        label=token if token in answer_map else next(k for k,v in answer_map.items() if v==token)
        return {**result,'accepted':True,'label':label,'action':answer_map[label],
                'rule':'whole_response','reason':'unambiguous_explicit_answer',
                'evidence':{'start':0,'end':len(content),'matching_candidate_count':1}}
    ignored=_ignored_spans(content)
    def masked(start):return any(a<=start<b for a,b in ignored)
    decoder=json.JSONDecoder(object_pairs_hook=_Pairs)
    candidates=[];objects=[];problem=None
    for found in re.finditer(r'\{',content):
        start=found.start()
        if masked(start):continue
        if any(a<start<b for a,b in objects):continue
        try:obj,used=decoder.raw_decode(content[start:])
        except (ValueError,TypeError):
            if re.match(r'\{\s*"action"\s*:',content[start:]):problem='incomplete_action_object'
            continue
        end=start+used
        if not isinstance(obj,_Pairs):continue
        objects.append((start,end))
        line_start=content.rfind('\n',0,start)+1
        line_end=content.find('\n',end)
        if line_end<0:line_end=len(content)
        prefix=content[line_start:start].strip().strip('`* ')
        suffix=content[end:line_end].strip().strip('`* ')
        if prefix and not _AUTHORITATIVE_JSON_PREFIX.fullmatch(prefix):continue
        if suffix.strip('.;! '):continue
        actions=[value for key,value in obj if key=='action']
        if not actions:continue
        if len(actions)!=1:
            problem='duplicate_action_keys';continue
        if not isinstance(actions[0],str) or actions[0] not in answer_map:
            problem='nonunique_action_value';continue
        label=actions[0]
        candidates.append((label,'json_action',start,end))
    # Formatting markup may surround a final label; offsets stay unchanged.
    normalized=content.translate(str.maketrans({'*':' ','`':' ','_':' '}))
    for match in _FINAL.finditer(normalized):
        start=match.start();token=match.group('label').upper()
        label=token if token in answer_map else next(k for k,v in answer_map.items() if v==token)
        marker_start=start+len(match.group(0))-len(match.group(0).lstrip())
        if masked(marker_start) or any(a<=marker_start<b for a,b in objects):continue
        tail=match.group('tail')
        if not _FINAL_SUFFIX.fullmatch(tail) or content[match.end():match.end()+1]=='?':
            problem='conditional_or_uncertain_final';continue
        alternatives=set(re.findall(r'\b[XY]\b',tail,re.I))
        alternatives={x.upper() for x in alternatives}
        if alternatives-{label}:
            problem='ambiguous_final_clause';continue
        meanings={x.upper() for x in re.findall(r'\b(?:JOIN|SAFE)\b',tail,re.I)}
        if meanings and meanings!={answer_map[label]}:
            problem='conflicting_action_annotation';continue
        candidates.append((label,'explicit_final' if token in answer_map else 'explicit_final_semantic',marker_start,match.end()))
    if problem:return reject(problem)
    if not candidates:return reject('no_explicit_answer')
    if len({c[0] for c in candidates})!=1:return reject('conflicting_answers')
    label,rule,start,end=min(candidates,key=lambda c:(c[2],c[3]))
    return {**result,'accepted':True,'label':label,'action':answer_map[label],'rule':rule,'reason':'unambiguous_explicit_answer',
            'evidence':{'start':start,'end':end,'matching_candidate_count':len(candidates)}}
