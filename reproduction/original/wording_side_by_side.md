# Wording differences

All entries below are exact source text. The four alternatives change the whole task (domain nouns, syntax, payoff wording, objective wording and delivery presentation), not only the partner-policy sentence. They do not isolate a single causal linguistic feature.

## introduction

| wording 0 | wording 1 | wording 2 | wording 3 |
|---|---|---|---|
| You choose for module A in a pair of modules A and B. Their actions are collected in separate requests and then executed together. Neither action is observed before the other is chosen. | There are two control stations, A and B. Select the action of station A. Decisions are simultaneous: each is requested separately, and no station is shown the other decision in advance. | A job is assigned to processing units A and B. You act for unit A. Each unit submits one action without seeing the other submission; the two submissions are executed together. | Deployment services A and B each submit an action. Make the submission for service A. The submissions are requested independently and applied simultaneously, with no advance disclosure of either one. |

## world

| wording 0 | wording 1 | wording 2 | wording 3 |
|---|---|---|---|
| The job is READY with prior probability 1/5. A truthful base certificate states whether it is READY. Each module receives its own certificate independently with probability 1/2, independent of readiness. A monitor issues two receipts if and only if both certificates were delivered; each receipt truthfully confirms delivery of both certificates. | Before any observations, READY has probability 1/5. A station can receive a truthful readiness certificate. The two certificate deliveries are independent fair-coin events and independent of READY. Exactly when both certificates arrive, a monitor issues a receipt for each station, certifying that both readiness certificates arrived. | Readiness initially has probability 1/5. For each unit, a base certificate reporting the true readiness state is delivered with probability 1/2; these deliveries are mutually independent and do not depend on readiness. Two receipts are issued exactly when both base certificates arrive. A receipt confirms this joint certificate delivery. | Initially the probability of READY is 1/5. Each service independently has probability 1/2 of obtaining a truthful readiness certificate, regardless of the readiness state. The monitor creates one receipt for each service exactly when both certificates have been delivered. Each receipt verifies delivery of the two certificates. |

## distribution introduction

| wording 0 | wording 1 | wording 2 | wording 3 |
|---|---|---|---|
| Conditional on receipt issuance, delivery of the receipts follows the distribution below, independently of readiness and base-certificate deliveries. | Once the monitor has issued receipts, the following rule determines their delivery. This rule is independent of readiness and of the preceding certificate deliveries. | Given that receipts have been issued, their joint delivery distribution is the following. Readiness and the certificate-delivery events do not otherwise influence this distribution. | For issued receipts, delivery is governed by this distribution. The delivery draw is independent of readiness and of the base-certificate draws. |

## distribution

| wording 0 | wording 1 | wording 2 | wording 3 |
|---|---|---|---|
| Receipt delivery \| Probability<br>(0,0) \| 1/4<br>(0,1) \| 1/4<br>(1,0) \| 1/4<br>(1,1) \| 1/4<br>Here 1 means a receipt arrives and 0 means it does not. The first entry refers to A and the second to B. | A receipt \| B receipt \| Probability<br>0 \| 0 \| 1/4<br>0 \| 1 \| 1/4<br>1 \| 0 \| 1/4<br>1 \| 1 \| 1/4<br>Here 1 means a receipt arrives and 0 means it does not. The first entry refers to A and the second to B. | (A receives, B receives) \| Probability<br>(0,0) \| 1/4<br>(0,1) \| 1/4<br>(1,0) \| 1/4<br>(1,1) \| 1/4<br>Here 1 means a receipt arrives and 0 means it does not. The first entry refers to A and the second to B. | Receipt pair (A,B) \| Probability<br>(0,0) \| 1/4<br>(0,1) \| 1/4<br>(1,0) \| 1/4<br>(1,1) \| 1/4<br>Here 1 means a receipt arrives and 0 means it does not. The first entry refers to A and the second to B. |

## observation

| wording 0 | wording 1 | wording 2 | wording 3 |
|---|---|---|---|
| A shared panel displays the true readiness state to both modules, and it currently displays READY. Your own base certificate says READY and your own receipt has arrived. You do not observe whether the other receipt arrived. | Both stations see the same panel, which truthfully reports READY now. Your station has its READY certificate and its receipt. Delivery of the other station's receipt is not shown to you. | The true readiness state is displayed on a panel visible to both units; its current value is READY. Locally, your unit sees its READY certificate and its receipt. You cannot inspect receipt delivery at the other unit. | A panel visible to both services truthfully says READY. You have received your own READY certificate and your own receipt. No observation reveals to you whether the other service has its receipt. |

## common rules

| wording 0 | wording 1 | wording 2 | wording 3 |
|---|---|---|---|
| The full rules, payoffs, and panel display rule are public common knowledge. Each module knows them, knows that the other knows them, and so on. Under the receipt rule, each individual receipt has delivery probability 1/2; conditional on your own receipt, the other receipt arrives with probability 1/2. A probability of receiving a receipt is not a declaration of an action probability. | The full rules, payoffs, and panel display rule are public common knowledge. Each module knows them, knows that the other knows them, and so on. Under the receipt rule, each individual receipt has delivery probability 1/2; conditional on your own receipt, the other receipt arrives with probability 1/2. A probability of receiving a receipt is not a declaration of an action probability. | The full rules, payoffs, and panel display rule are public common knowledge. Each module knows them, knows that the other knows them, and so on. Under the receipt rule, each individual receipt has delivery probability 1/2; conditional on your own receipt, the other receipt arrives with probability 1/2. A probability of receiving a receipt is not a declaration of an action probability. | The full rules, payoffs, and panel display rule are public common knowledge. Each module knows them, knows that the other knows them, and so on. Under the receipt rule, each individual receipt has delivery probability 1/2; conditional on your own receipt, the other receipt arrives with probability 1/2. A probability of receiving a receipt is not a declaration of an action probability. |

## complement policy

| wording 0 | wording 1 | wording 2 | wording 3 |
|---|---|---|---|
| The partner is a host-implemented program, not a free-choice decision maker. It chooses JOIN if and only if its own receipt did not arrive; otherwise it chooses SAFE. Its realized action is not disclosed before you choose. | The host fixes the other station's actions by a program. Its action is SAFE when it has its receipt and JOIN when it does not. Its realized action is not disclosed before you choose. | For this decision, the other unit follows a program implemented by the host. Receipt absent means JOIN; receipt present means SAFE. Its realized action is not disclosed before you choose. | A host-controlled program selects the counterpart's action. The program uses SAFE on receipt delivery and JOIN otherwise. Its realized action is not disclosed before you choose. |

## responsive policy

| wording 0 | wording 1 | wording 2 | wording 3 |
|---|---|---|---|
| The partner is a host-implemented program, not a free-choice decision maker. It chooses JOIN if and only if its own receipt arrived; otherwise it chooses SAFE. Its realized action is not disclosed before you choose. | The host fixes the other station's actions by a program. Its action is JOIN when it has its receipt and SAFE when it does not. Its realized action is not disclosed before you choose. | For this decision, the other unit follows a program implemented by the host. Receipt present means JOIN; receipt absent means SAFE. Its realized action is not disclosed before you choose. | A host-controlled program selects the counterpart's action. The program uses JOIN exactly on receipt delivery and SAFE otherwise. Its realized action is not disclosed before you choose. |

## independent policy

| wording 0 | wording 1 | wording 2 | wording 3 |
|---|---|---|---|
| The partner is a host-implemented program, not a free-choice decision maker. It chooses JOIN with probability 0.5 and SAFE with probability 0.5. The draw is independent of readiness, all deliveries, all observations, and your action; these probabilities apply at every information state. Its realized action is not disclosed before you choose. | The host fixes the other station's actions by a program. Its JOIN probability is 0.5 and its SAFE probability is 0.5. Neither readiness, any certificate or receipt delivery, any observation, nor your action affects this draw. It uses these same probabilities everywhere. Its realized action is not disclosed before you choose. | For this decision, the other unit follows a program implemented by the host. A fresh random draw gives JOIN with probability 0.5, otherwise SAFE with probability 0.5. The draw is independent of readiness, certificate and receipt deliveries, observations, and your choice. The rule is constant across information states. Its realized action is not disclosed before you choose. | A host-controlled program selects the counterpart's action. The program randomizes between JOIN with probability 0.5 and SAFE with probability 0.5. This randomization is independent of the readiness state, all deliveries and observations, and your submitted action, at every information state. Its realized action is not disclosed before you choose. |

## payoff and objective

| wording 0 | wording 1 | wording 2 | wording 3 |
|---|---|---|---|
| SAFE gives you 4 points regardless of the other action. JOIN gives you 10 points if the job is READY and the partner also chooses JOIN, and 0 otherwise.<br><br>Choose the action that maximizes your expected score.<br>Output labels: X means JOIN; Y means SAFE. Return exactly one JSON object with key "action" and value "X" or "Y". Do not include any other text. | Your score from SAFE is always 4. Your score from JOIN is 10 when READY and the partner chooses JOIN; in all other cases it is 0.<br><br>Your objective is to maximize expected points.<br>Output labels: X means JOIN; Y means SAFE. Return exactly one JSON object with key "action" and value "X" or "Y". Do not include any other text. | The scoring rule awards 4 for SAFE. JOIN receives 10 if readiness is READY and the partner also selects JOIN, and receives zero in every other case.<br><br>Select an action to obtain the highest expected score.<br>Output labels: X means JOIN; Y means SAFE. Return exactly one JSON object with key "action" and value "X" or "Y". Do not include any other text. | Scoring: SAFE pays 4 unconditionally. JOIN pays 10 exactly when READY holds and the counterpart submits JOIN; otherwise JOIN pays 0.<br><br>Maximize the expected number of points from this decision.<br>Output labels: X means JOIN; Y means SAFE. Return exactly one JSON object with key "action" and value "X" or "Y". Do not include any other text. |

## Literal complement program difference (wording 0 versus wording 3)
```diff
--- wording_0
+++ wording_3
@@ -1 +1 @@
-The partner is a host-implemented program, not a free-choice decision maker. It chooses JOIN if and only if its own receipt did not arrive; otherwise it chooses SAFE. Its realized action is not disclosed before you choose.+A host-controlled program selects the counterpart's action. The program uses SAFE on receipt delivery and JOIN otherwise. Its realized action is not disclosed before you choose.
```
