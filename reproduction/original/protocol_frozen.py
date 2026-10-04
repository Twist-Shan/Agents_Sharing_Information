"""Fixed scientific design for independent receipt decision-value validation.
No network; no data-dependent sampling. Scientific jobs contain no model options.
"""
from __future__ import annotations
from collections import Counter
from itertools import product
import hashlib
import json
import random

SEEDS = {'labels': 16411, 'allocation': 8879, 'analysis': 4273, 'prediction': 7321}
GRID = (.2, .35, .5, .65, .8)
ALLOCATIONS = {
    'full': dict(free=1024, independent=2048, responsive=512, complement=512, capability=64),
    'cross': dict(free=128, independent=128, responsive=64, complement=64, capability=32),
}
SCENARIOS = ('paired modules', 'two control stations', 'paired processing units', 'two deployment services')


def compact(obj):
    return json.dumps(obj, sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False)


def _base(block, module, rng):
    # Every consecutive group of 32 balances wording, mapping, display order,
    # and the between-block free-player safe payoff. The core independent task
    # crosses both payoffs within block, so its extra bit is a harmless replicate.
    c = block % 32
    return dict(block_index=block, wording=c % 4, mapping=(c // 4) % 2,
                display_order=(c // 8) % 2, free_safe=(4, 6)[(c // 16) % 2],
                operation=f'case-{rng.getrandbits(48):012x}',
                analysis_split='train' if c % 4 < 2 else 'test')


def _law(law, encoding, wording):
    values = ('1/4', '1/4', '1/4', '1/4') if law == 'R' else ('1/2', '0', '0', '1/2')
    if encoding == 'table':
        heads = ('Receipt delivery | Probability', 'A receipt | B receipt | Probability',
                 '(A receives, B receives) | Probability', 'Receipt pair (A,B) | Probability')
        if wording == 1:
            rows = [f'{a} | {b} | {p}' for (a, b), p in zip(product((0, 1), repeat=2), values)]
        else:
            rows = [f'({a},{b}) | {p}' for (a, b), p in zip(product((0, 1), repeat=2), values)]
        text = heads[wording] + '\n' + '\n'.join(rows)
    else:
        sentences = [f'the pair ({a},{b}) has probability {p}' for (a, b), p in zip(product((0, 1), repeat=2), values)]
        if wording == 0:
            text = 'The distribution is: ' + '; '.join(sentences) + '.'
        elif wording == 1:
            text = 'For the four possible deliveries, ' + ', while '.join(sentences) + '.'
        elif wording == 2:
            text = 'The delivery probabilities are specified as follows. ' + '. '.join(s[0].upper()+s[1:] for s in sentences) + '.'
        else:
            text = 'The rule assigns these probabilities: ' + '; and '.join(sentences) + '.'
    return text + '\nHere 1 means a receipt arrives and 0 means it does not. The first entry refers to A and the second to B.'


def _environment(m):
    w = m['wording']
    name = ('A', 'B')[m['actor']]
    intro = (
      'You choose for module {name} in a pair of modules A and B. Their actions are collected in separate requests and then executed together. Neither action is observed before the other is chosen.',
      'There are two control stations, A and B. Select the action of station {name}. Decisions are simultaneous: each is requested separately, and no station is shown the other decision in advance.',
      'A job is assigned to processing units A and B. You act for unit {name}. Each unit submits one action without seeing the other submission; the two submissions are executed together.',
      'Deployment services A and B each submit an action. Make the submission for service {name}. The submissions are requested independently and applied simultaneously, with no advance disclosure of either one.'
    )[w].format(name=name)
    world = (
      'The job is READY with prior probability 1/5. A truthful base certificate states whether it is READY. Each module receives its own certificate independently with probability 1/2, independent of readiness. A monitor issues two receipts if and only if both certificates were delivered; each receipt truthfully confirms delivery of both certificates.',
      'Before any observations, READY has probability 1/5. A station can receive a truthful readiness certificate. The two certificate deliveries are independent fair-coin events and independent of READY. Exactly when both certificates arrive, a monitor issues a receipt for each station, certifying that both readiness certificates arrived.',
      'Readiness initially has probability 1/5. For each unit, a base certificate reporting the true readiness state is delivered with probability 1/2; these deliveries are mutually independent and do not depend on readiness. Two receipts are issued exactly when both base certificates arrive. A receipt confirms this joint certificate delivery.',
      'Initially the probability of READY is 1/5. Each service independently has probability 1/2 of obtaining a truthful readiness certificate, regardless of the readiness state. The monitor creates one receipt for each service exactly when both certificates have been delivered. Each receipt verifies delivery of the two certificates.'
    )[w]
    distribution = (
      'Conditional on receipt issuance, delivery of the receipts follows the distribution below, independently of readiness and base-certificate deliveries.',
      'Once the monitor has issued receipts, the following rule determines their delivery. This rule is independent of readiness and of the preceding certificate deliveries.',
      'Given that receipts have been issued, their joint delivery distribution is the following. Readiness and the certificate-delivery events do not otherwise influence this distribution.',
      'For issued receipts, delivery is governed by this distribution. The delivery draw is independent of readiness and of the base-certificate draws.'
    )[w]
    observation = (
      'A shared panel displays the true readiness state to both modules, and it currently displays READY. Your own base certificate says READY and your own receipt has arrived. You do not observe whether the other receipt arrived.',
      'Both stations see the same panel, which truthfully reports READY now. Your station has its READY certificate and its receipt. Delivery of the other station\'s receipt is not shown to you.',
      'The true readiness state is displayed on a panel visible to both units; its current value is READY. Locally, your unit sees its READY certificate and its receipt. You cannot inspect receipt delivery at the other unit.',
      'A panel visible to both services truthfully says READY. You have received your own READY certificate and your own receipt. No observation reveals to you whether the other service has its receipt.'
    )[w]
    assurance = '1/2' if m['law'] == 'R' else '1'
    common = ('The full rules, payoffs, and panel display rule are public common knowledge. '
              'Each module knows them, knows that the other knows them, and so on. '
              f'Under the receipt rule, each individual receipt has delivery probability 1/2; conditional on your own receipt, the other receipt arrives with probability {assurance}. '
              'A probability of receiving a receipt is not a declaration of an action probability.')
    return '\n\n'.join((intro, world, distribution, _law(m['law'],m['encoding'],w), observation,common))


def _program(m):
    w = m['wording']; pol=m['policy']
    if pol == 'free':
        return ('The partner is another independently prompted decision maker with the same payoff rule. Its action is not prescribed.',
                'The other station selects its own action under the same payoffs; no fixed action rule is imposed on it.',
                'The other unit also makes a choice under these payoffs. It is not a programmed partner with a specified strategy.',
                'Your counterpart chooses an action under the same scoring rule, without a prescribed strategy.')[w]
    head = ('The partner is a host-implemented program, not a free-choice decision maker. ',
            'The host fixes the other station\'s actions by a program. ',
            'For this decision, the other unit follows a program implemented by the host. ',
            'A host-controlled program selects the counterpart\'s action. ')[w]
    if pol == 'responsive':
        rule = ('It chooses JOIN if and only if its own receipt arrived; otherwise it chooses SAFE.',
                'Its action is JOIN when it has its receipt and SAFE when it does not.',
                'Receipt present means JOIN; receipt absent means SAFE.',
                'The program uses JOIN exactly on receipt delivery and SAFE otherwise.')[w]
    elif pol == 'complement':
        rule = ('It chooses JOIN if and only if its own receipt did not arrive; otherwise it chooses SAFE.',
                'Its action is SAFE when it has its receipt and JOIN when it does not.',
                'Receipt absent means JOIN; receipt present means SAFE.',
                'The program uses SAFE on receipt delivery and JOIN otherwise.')[w]
    elif pol == 'independent':
        p = f'{m["p"]:g}'; r = f'{1-m["p"]:g}'
        rule = (f'It chooses JOIN with probability {p} and SAFE with probability {r}. The draw is independent of readiness, all deliveries, all observations, and your action; these probabilities apply at every information state.',
                f'Its JOIN probability is {p} and its SAFE probability is {r}. Neither readiness, any certificate or receipt delivery, any observation, nor your action affects this draw. It uses these same probabilities everywhere.',
                f'A fresh random draw gives JOIN with probability {p}, otherwise SAFE with probability {r}. The draw is independent of readiness, certificate and receipt deliveries, observations, and your choice. The rule is constant across information states.',
                f'The program randomizes between JOIN with probability {p} and SAFE with probability {r}. This randomization is independent of the readiness state, all deliveries and observations, and your submitted action, at every information state.')[w]
    else:
        raise ValueError('unknown policy')
    return head + rule + ' Its realized action is not disclosed before you choose.'


def render(m):
    w = m['wording']; s=m['safe']; p=m['p']
    if m['module']=='minimal':
        texts=(
          f'Choose one of two actions. SAFE gives {s} points for certain. JOIN gives 10 points with probability {p:g} and 0 otherwise.',
          f'Two options are available: a certain {s} points from SAFE, or a lottery from JOIN that pays 10 with probability {p:g} and 0 with probability {1-p:g}.',
          f'Your decision is between SAFE, paying {s} with certainty, and JOIN, paying 10 with probability {p:g} and zero otherwise.',
          f'Select SAFE for a guaranteed {s} points, or select JOIN for 10 points with probability {p:g} and 0 points with probability {1-p:g}.')
        body=texts[w]
    else:
        body=_environment(m)+'\n\n'+_program(m)
        payoff=(f'SAFE gives you {s} points regardless of the other action. JOIN gives you 10 points if the job is READY and the partner also chooses JOIN, and 0 otherwise.',
                f'Your score from SAFE is always {s}. Your score from JOIN is 10 when READY and the partner chooses JOIN; in all other cases it is 0.',
                f'The scoring rule awards {s} for SAFE. JOIN receives 10 if readiness is READY and the partner also selects JOIN, and receives zero in every other case.',
                f'Scoring: SAFE pays {s} unconditionally. JOIN pays 10 exactly when READY holds and the counterpart submits JOIN; otherwise JOIN pays 0.')[w]
        body+='\n\n'+payoff
        if m['module']=='payoff_card':
            body+=('\n\nDecision payoff card for your current information: '
                   f'JOIN pays 10 with probability {p:g} and 0 with probability {1-p:g}; its expected score is {10*p:g}. '
                   f'SAFE pays {s} for certain, with expected score {s}. These quantities follow from the stated program and observed READY state.')
    aim=('Choose the action that maximizes your expected score.',
         'Your objective is to maximize expected points.',
         'Select an action to obtain the highest expected score.',
         'Maximize the expected number of points from this decision.')[w]
    amap={'X':'JOIN','Y':'SAFE'} if m['mapping']==0 else {'X':'SAFE','Y':'JOIN'}
    labels=('X','Y') if m['display_order']==0 else ('Y','X')
    mapping='; '.join(f'{x} means {amap[x]}' for x in labels)
    return [{'role':'user','content':f'Instance: {m["operation"]}\n\n{body}\n\n{aim}\nOutput labels: {mapping}. Return exactly one JSON object with key "action" and value "X" or "Y". Do not include any other text.'}]


def generate(plan):
    profile=plan.get('allocationprofile',plan.get('allocation_profile','full'))
    if profile not in ALLOCATIONS: raise ValueError('allocationprofile must be full or cross')
    ns=ALLOCATIONS[profile]; rng=random.Random(SEEDS['labels']); jobs=[]; bases={}
    def add(module, policy, b, base, law, enc, safe, actor=0,p=None):
        if policy=='responsive': p=.5 if law=='R' else 1.
        if policy=='complement': p=.5 if law=='R' else 0.
        block_id=('independent' if module in ('minimal','grid_full','payoff_card') else module)+f'-{b:04d}'
        m={**base,'module':module,'policy':policy,'law':law,'encoding':enc,'safe':safe,'actor':actor,'p':p,'block_id':block_id}
        token='na' if p is None else f'{p:g}'
        ident=f'{module}-b{b:04d}-q{law}-e{enc}-s{safe}-a{actor}-p{token}'
        amap={'X':'JOIN','Y':'SAFE'} if m['mapping']==0 else {'X':'SAFE','Y':'JOIN'}
        jobs.append(dict(id=ident,block_id=block_id,module=module,metadata=m,messages=render(m),answer_map=amap,
                         expected=None if policy=='free' else ('JOIN' if 10*p>safe else 'SAFE')))
    for module in ('free','independent','responsive','complement'):
        for b in range(ns[module]):
            base=_base(b,module,rng)
            if module=='independent':bases[b]=base
            for law,enc in product(('R','S'),('table','prose')):
                if module=='free':
                    for actor in (0,1):add(module,module,b,base,law,enc,base['free_safe'],actor)
                else:
                    for safe in (4,6):add(module,module,b,base,law,enc,safe,(b//16)%2,.5)
    for b in range(ns['capability']):
        base=bases[b]; grid=GRID if profile=='full' else (.5,)
        for p,safe in product(grid,(4,6)):
            add('minimal','independent',b,base,'none','none',safe,(b//16)%2,p)
            for law,enc in product(('R','S'),('table','prose')):
                if p!=.5:add('grid_full','independent',b,base,law,enc,safe,(b//16)%2,p)
                add('payoff_card','independent',b,base,law,enc,safe,(b//16)%2,p)
    # Interleave all conditions before execution. A block is an analysis cluster,
    # never a run-long consecutive condition batch. Randomization is frozen.
    random.Random(SEEDS['allocation']).shuffle(jobs)
    expected_count=38016 if profile=='full' else 3392
    assert len(jobs)==expected_count and len({j['id'] for j in jobs})==expected_count
    assert all(j['expected'] in (None,'JOIN','SAFE') for j in jobs)
    assert all(j['messages']==render(j['metadata']) for j in jobs)
    return jobs


def audit(plan):
    jobs=generate(plan)
    counts=Counter(j['module'] for j in jobs)
    wording=Counter(j['metadata']['wording'] for j in jobs)
    assert len(set(wording.values()))==1
    assert all(j['metadata']['p'] is None or 10*j['metadata']['p']!=j['metadata']['safe'] for j in jobs)
    return dict(passed=True,scientific_calls=len(jobs),counts=dict(counts),wording_counts=dict(wording),
                scientific_plan_sha256=hashlib.sha256(compact(jobs).encode()).hexdigest(),seeds=SEEDS,
                prediction_train_wordings=[0,1],prediction_test_wordings=[2,3],model_calls=0)

if __name__=='__main__':
    print(json.dumps({p:audit({'allocationprofile':p}) for p in ALLOCATIONS},indent=2))

