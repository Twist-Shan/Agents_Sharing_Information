# Exact four-wording stimuli

These examples are verbatim user messages from the frozen Luna allocation. No researcher-authored system message was submitted. The case identifier varies across blocks. The full machine-readable template catalogue and request-to-block map cover every published-model request.

## Wording 0: independent

Frozen ID: `luna|independent-b0000-qR-etable-s4-a0-p0.5`

```text
Instance: case-a2e825f78063

You choose for module A in a pair of modules A and B. Their actions are collected in separate requests and then executed together. Neither action is observed before the other is chosen.

The job is READY with prior probability 1/5. A truthful base certificate states whether it is READY. Each module receives its own certificate independently with probability 1/2, independent of readiness. A monitor issues two receipts if and only if both certificates were delivered; each receipt truthfully confirms delivery of both certificates.

Conditional on receipt issuance, delivery of the receipts follows the distribution below, independently of readiness and base-certificate deliveries.

Receipt delivery | Probability
(0,0) | 1/4
(0,1) | 1/4
(1,0) | 1/4
(1,1) | 1/4
Here 1 means a receipt arrives and 0 means it does not. The first entry refers to A and the second to B.

A shared panel displays the true readiness state to both modules, and it currently displays READY. Your own base certificate says READY and your own receipt has arrived. You do not observe whether the other receipt arrived.

The full rules, payoffs, and panel display rule are public common knowledge. Each module knows them, knows that the other knows them, and so on. Under the receipt rule, each individual receipt has delivery probability 1/2; conditional on your own receipt, the other receipt arrives with probability 1/2. A probability of receiving a receipt is not a declaration of an action probability.

The partner is a host-implemented program, not a free-choice decision maker. It chooses JOIN with probability 0.5 and SAFE with probability 0.5. The draw is independent of readiness, all deliveries, all observations, and your action; these probabilities apply at every information state. Its realized action is not disclosed before you choose.

SAFE gives you 4 points regardless of the other action. JOIN gives you 10 points if the job is READY and the partner also chooses JOIN, and 0 otherwise.

Choose the action that maximizes your expected score.
Output labels: X means JOIN; Y means SAFE. Return exactly one JSON object with key "action" and value "X" or "Y". Do not include any other text.
```

## Wording 0: responsive

Frozen ID: `luna|responsive-b0000-qR-etable-s4-a0-p0.5`

```text
Instance: case-5ad9436cec25

You choose for module A in a pair of modules A and B. Their actions are collected in separate requests and then executed together. Neither action is observed before the other is chosen.

The job is READY with prior probability 1/5. A truthful base certificate states whether it is READY. Each module receives its own certificate independently with probability 1/2, independent of readiness. A monitor issues two receipts if and only if both certificates were delivered; each receipt truthfully confirms delivery of both certificates.

Conditional on receipt issuance, delivery of the receipts follows the distribution below, independently of readiness and base-certificate deliveries.

Receipt delivery | Probability
(0,0) | 1/4
(0,1) | 1/4
(1,0) | 1/4
(1,1) | 1/4
Here 1 means a receipt arrives and 0 means it does not. The first entry refers to A and the second to B.

A shared panel displays the true readiness state to both modules, and it currently displays READY. Your own base certificate says READY and your own receipt has arrived. You do not observe whether the other receipt arrived.

The full rules, payoffs, and panel display rule are public common knowledge. Each module knows them, knows that the other knows them, and so on. Under the receipt rule, each individual receipt has delivery probability 1/2; conditional on your own receipt, the other receipt arrives with probability 1/2. A probability of receiving a receipt is not a declaration of an action probability.

The partner is a host-implemented program, not a free-choice decision maker. It chooses JOIN if and only if its own receipt arrived; otherwise it chooses SAFE. Its realized action is not disclosed before you choose.

SAFE gives you 4 points regardless of the other action. JOIN gives you 10 points if the job is READY and the partner also chooses JOIN, and 0 otherwise.

Choose the action that maximizes your expected score.
Output labels: X means JOIN; Y means SAFE. Return exactly one JSON object with key "action" and value "X" or "Y". Do not include any other text.
```

## Wording 0: complement

Frozen ID: `luna|complement-b0000-qR-etable-s4-a0-p0.5`

```text
Instance: case-79400aeaa704

You choose for module A in a pair of modules A and B. Their actions are collected in separate requests and then executed together. Neither action is observed before the other is chosen.

The job is READY with prior probability 1/5. A truthful base certificate states whether it is READY. Each module receives its own certificate independently with probability 1/2, independent of readiness. A monitor issues two receipts if and only if both certificates were delivered; each receipt truthfully confirms delivery of both certificates.

Conditional on receipt issuance, delivery of the receipts follows the distribution below, independently of readiness and base-certificate deliveries.

Receipt delivery | Probability
(0,0) | 1/4
(0,1) | 1/4
(1,0) | 1/4
(1,1) | 1/4
Here 1 means a receipt arrives and 0 means it does not. The first entry refers to A and the second to B.

A shared panel displays the true readiness state to both modules, and it currently displays READY. Your own base certificate says READY and your own receipt has arrived. You do not observe whether the other receipt arrived.

The full rules, payoffs, and panel display rule are public common knowledge. Each module knows them, knows that the other knows them, and so on. Under the receipt rule, each individual receipt has delivery probability 1/2; conditional on your own receipt, the other receipt arrives with probability 1/2. A probability of receiving a receipt is not a declaration of an action probability.

The partner is a host-implemented program, not a free-choice decision maker. It chooses JOIN if and only if its own receipt did not arrive; otherwise it chooses SAFE. Its realized action is not disclosed before you choose.

SAFE gives you 4 points regardless of the other action. JOIN gives you 10 points if the job is READY and the partner also chooses JOIN, and 0 otherwise.

Choose the action that maximizes your expected score.
Output labels: X means JOIN; Y means SAFE. Return exactly one JSON object with key "action" and value "X" or "Y". Do not include any other text.
```

## Wording 0: free

Frozen ID: `luna|free-b0000-qR-etable-s4-a0-pna`

```text
Instance: case-21be43e83b23

You choose for module A in a pair of modules A and B. Their actions are collected in separate requests and then executed together. Neither action is observed before the other is chosen.

The job is READY with prior probability 1/5. A truthful base certificate states whether it is READY. Each module receives its own certificate independently with probability 1/2, independent of readiness. A monitor issues two receipts if and only if both certificates were delivered; each receipt truthfully confirms delivery of both certificates.

Conditional on receipt issuance, delivery of the receipts follows the distribution below, independently of readiness and base-certificate deliveries.

Receipt delivery | Probability
(0,0) | 1/4
(0,1) | 1/4
(1,0) | 1/4
(1,1) | 1/4
Here 1 means a receipt arrives and 0 means it does not. The first entry refers to A and the second to B.

A shared panel displays the true readiness state to both modules, and it currently displays READY. Your own base certificate says READY and your own receipt has arrived. You do not observe whether the other receipt arrived.

The full rules, payoffs, and panel display rule are public common knowledge. Each module knows them, knows that the other knows them, and so on. Under the receipt rule, each individual receipt has delivery probability 1/2; conditional on your own receipt, the other receipt arrives with probability 1/2. A probability of receiving a receipt is not a declaration of an action probability.

The partner is another independently prompted decision maker with the same payoff rule. Its action is not prescribed.

SAFE gives you 4 points regardless of the other action. JOIN gives you 10 points if the job is READY and the partner also chooses JOIN, and 0 otherwise.

Choose the action that maximizes your expected score.
Output labels: X means JOIN; Y means SAFE. Return exactly one JSON object with key "action" and value "X" or "Y". Do not include any other text.
```

## Wording 0: minimal

Frozen ID: `luna|minimal-b0000-qnone-enone-s4-a0-p0.5`

```text
Instance: case-a2e825f78063

Choose one of two actions. SAFE gives 4 points for certain. JOIN gives 10 points with probability 0.5 and 0 otherwise.

Choose the action that maximizes your expected score.
Output labels: X means JOIN; Y means SAFE. Return exactly one JSON object with key "action" and value "X" or "Y". Do not include any other text.
```

## Wording 0: payoff_card

Frozen ID: `luna|payoff_card-b0000-qR-etable-s4-a0-p0.5`

```text
Instance: case-a2e825f78063

You choose for module A in a pair of modules A and B. Their actions are collected in separate requests and then executed together. Neither action is observed before the other is chosen.

The job is READY with prior probability 1/5. A truthful base certificate states whether it is READY. Each module receives its own certificate independently with probability 1/2, independent of readiness. A monitor issues two receipts if and only if both certificates were delivered; each receipt truthfully confirms delivery of both certificates.

Conditional on receipt issuance, delivery of the receipts follows the distribution below, independently of readiness and base-certificate deliveries.

Receipt delivery | Probability
(0,0) | 1/4
(0,1) | 1/4
(1,0) | 1/4
(1,1) | 1/4
Here 1 means a receipt arrives and 0 means it does not. The first entry refers to A and the second to B.

A shared panel displays the true readiness state to both modules, and it currently displays READY. Your own base certificate says READY and your own receipt has arrived. You do not observe whether the other receipt arrived.

The full rules, payoffs, and panel display rule are public common knowledge. Each module knows them, knows that the other knows them, and so on. Under the receipt rule, each individual receipt has delivery probability 1/2; conditional on your own receipt, the other receipt arrives with probability 1/2. A probability of receiving a receipt is not a declaration of an action probability.

The partner is a host-implemented program, not a free-choice decision maker. It chooses JOIN with probability 0.5 and SAFE with probability 0.5. The draw is independent of readiness, all deliveries, all observations, and your action; these probabilities apply at every information state. Its realized action is not disclosed before you choose.

SAFE gives you 4 points regardless of the other action. JOIN gives you 10 points if the job is READY and the partner also chooses JOIN, and 0 otherwise.

Decision payoff card for your current information: JOIN pays 10 with probability 0.5 and 0 with probability 0.5; its expected score is 5. SAFE pays 4 for certain, with expected score 4. These quantities follow from the stated program and observed READY state.

Choose the action that maximizes your expected score.
Output labels: X means JOIN; Y means SAFE. Return exactly one JSON object with key "action" and value "X" or "Y". Do not include any other text.
```

## Wording 1: independent

Frozen ID: `luna|independent-b0001-qR-etable-s4-a0-p0.5`

```text
Instance: case-d668fc4b87e5

There are two control stations, A and B. Select the action of station A. Decisions are simultaneous: each is requested separately, and no station is shown the other decision in advance.

Before any observations, READY has probability 1/5. A station can receive a truthful readiness certificate. The two certificate deliveries are independent fair-coin events and independent of READY. Exactly when both certificates arrive, a monitor issues a receipt for each station, certifying that both readiness certificates arrived.

Once the monitor has issued receipts, the following rule determines their delivery. This rule is independent of readiness and of the preceding certificate deliveries.

A receipt | B receipt | Probability
0 | 0 | 1/4
0 | 1 | 1/4
1 | 0 | 1/4
1 | 1 | 1/4
Here 1 means a receipt arrives and 0 means it does not. The first entry refers to A and the second to B.

Both stations see the same panel, which truthfully reports READY now. Your station has its READY certificate and its receipt. Delivery of the other station's receipt is not shown to you.

The full rules, payoffs, and panel display rule are public common knowledge. Each module knows them, knows that the other knows them, and so on. Under the receipt rule, each individual receipt has delivery probability 1/2; conditional on your own receipt, the other receipt arrives with probability 1/2. A probability of receiving a receipt is not a declaration of an action probability.

The host fixes the other station's actions by a program. Its JOIN probability is 0.5 and its SAFE probability is 0.5. Neither readiness, any certificate or receipt delivery, any observation, nor your action affects this draw. It uses these same probabilities everywhere. Its realized action is not disclosed before you choose.

Your score from SAFE is always 4. Your score from JOIN is 10 when READY and the partner chooses JOIN; in all other cases it is 0.

Your objective is to maximize expected points.
Output labels: X means JOIN; Y means SAFE. Return exactly one JSON object with key "action" and value "X" or "Y". Do not include any other text.
```

## Wording 1: responsive

Frozen ID: `luna|responsive-b0001-qR-etable-s4-a0-p0.5`

```text
Instance: case-ea65592a911f

There are two control stations, A and B. Select the action of station A. Decisions are simultaneous: each is requested separately, and no station is shown the other decision in advance.

Before any observations, READY has probability 1/5. A station can receive a truthful readiness certificate. The two certificate deliveries are independent fair-coin events and independent of READY. Exactly when both certificates arrive, a monitor issues a receipt for each station, certifying that both readiness certificates arrived.

Once the monitor has issued receipts, the following rule determines their delivery. This rule is independent of readiness and of the preceding certificate deliveries.

A receipt | B receipt | Probability
0 | 0 | 1/4
0 | 1 | 1/4
1 | 0 | 1/4
1 | 1 | 1/4
Here 1 means a receipt arrives and 0 means it does not. The first entry refers to A and the second to B.

Both stations see the same panel, which truthfully reports READY now. Your station has its READY certificate and its receipt. Delivery of the other station's receipt is not shown to you.

The full rules, payoffs, and panel display rule are public common knowledge. Each module knows them, knows that the other knows them, and so on. Under the receipt rule, each individual receipt has delivery probability 1/2; conditional on your own receipt, the other receipt arrives with probability 1/2. A probability of receiving a receipt is not a declaration of an action probability.

The host fixes the other station's actions by a program. Its action is JOIN when it has its receipt and SAFE when it does not. Its realized action is not disclosed before you choose.

Your score from SAFE is always 4. Your score from JOIN is 10 when READY and the partner chooses JOIN; in all other cases it is 0.

Your objective is to maximize expected points.
Output labels: X means JOIN; Y means SAFE. Return exactly one JSON object with key "action" and value "X" or "Y". Do not include any other text.
```

## Wording 1: complement

Frozen ID: `luna|complement-b0001-qR-etable-s4-a0-p0.5`

```text
Instance: case-cddcbfa259cc

There are two control stations, A and B. Select the action of station A. Decisions are simultaneous: each is requested separately, and no station is shown the other decision in advance.

Before any observations, READY has probability 1/5. A station can receive a truthful readiness certificate. The two certificate deliveries are independent fair-coin events and independent of READY. Exactly when both certificates arrive, a monitor issues a receipt for each station, certifying that both readiness certificates arrived.

Once the monitor has issued receipts, the following rule determines their delivery. This rule is independent of readiness and of the preceding certificate deliveries.

A receipt | B receipt | Probability
0 | 0 | 1/4
0 | 1 | 1/4
1 | 0 | 1/4
1 | 1 | 1/4
Here 1 means a receipt arrives and 0 means it does not. The first entry refers to A and the second to B.

Both stations see the same panel, which truthfully reports READY now. Your station has its READY certificate and its receipt. Delivery of the other station's receipt is not shown to you.

The full rules, payoffs, and panel display rule are public common knowledge. Each module knows them, knows that the other knows them, and so on. Under the receipt rule, each individual receipt has delivery probability 1/2; conditional on your own receipt, the other receipt arrives with probability 1/2. A probability of receiving a receipt is not a declaration of an action probability.

The host fixes the other station's actions by a program. Its action is SAFE when it has its receipt and JOIN when it does not. Its realized action is not disclosed before you choose.

Your score from SAFE is always 4. Your score from JOIN is 10 when READY and the partner chooses JOIN; in all other cases it is 0.

Your objective is to maximize expected points.
Output labels: X means JOIN; Y means SAFE. Return exactly one JSON object with key "action" and value "X" or "Y". Do not include any other text.
```

## Wording 1: free

Frozen ID: `luna|free-b0001-qR-etable-s4-a1-pna`

```text
Instance: case-6292109d942f

There are two control stations, A and B. Select the action of station B. Decisions are simultaneous: each is requested separately, and no station is shown the other decision in advance.

Before any observations, READY has probability 1/5. A station can receive a truthful readiness certificate. The two certificate deliveries are independent fair-coin events and independent of READY. Exactly when both certificates arrive, a monitor issues a receipt for each station, certifying that both readiness certificates arrived.

Once the monitor has issued receipts, the following rule determines their delivery. This rule is independent of readiness and of the preceding certificate deliveries.

A receipt | B receipt | Probability
0 | 0 | 1/4
0 | 1 | 1/4
1 | 0 | 1/4
1 | 1 | 1/4
Here 1 means a receipt arrives and 0 means it does not. The first entry refers to A and the second to B.

Both stations see the same panel, which truthfully reports READY now. Your station has its READY certificate and its receipt. Delivery of the other station's receipt is not shown to you.

The full rules, payoffs, and panel display rule are public common knowledge. Each module knows them, knows that the other knows them, and so on. Under the receipt rule, each individual receipt has delivery probability 1/2; conditional on your own receipt, the other receipt arrives with probability 1/2. A probability of receiving a receipt is not a declaration of an action probability.

The other station selects its own action under the same payoffs; no fixed action rule is imposed on it.

Your score from SAFE is always 4. Your score from JOIN is 10 when READY and the partner chooses JOIN; in all other cases it is 0.

Your objective is to maximize expected points.
Output labels: X means JOIN; Y means SAFE. Return exactly one JSON object with key "action" and value "X" or "Y". Do not include any other text.
```

## Wording 1: minimal

Frozen ID: `luna|minimal-b0001-qnone-enone-s4-a0-p0.5`

```text
Instance: case-d668fc4b87e5

Two options are available: a certain 4 points from SAFE, or a lottery from JOIN that pays 10 with probability 0.5 and 0 with probability 0.5.

Your objective is to maximize expected points.
Output labels: X means JOIN; Y means SAFE. Return exactly one JSON object with key "action" and value "X" or "Y". Do not include any other text.
```

## Wording 1: payoff_card

Frozen ID: `luna|payoff_card-b0001-qR-etable-s4-a0-p0.5`

```text
Instance: case-d668fc4b87e5

There are two control stations, A and B. Select the action of station A. Decisions are simultaneous: each is requested separately, and no station is shown the other decision in advance.

Before any observations, READY has probability 1/5. A station can receive a truthful readiness certificate. The two certificate deliveries are independent fair-coin events and independent of READY. Exactly when both certificates arrive, a monitor issues a receipt for each station, certifying that both readiness certificates arrived.

Once the monitor has issued receipts, the following rule determines their delivery. This rule is independent of readiness and of the preceding certificate deliveries.

A receipt | B receipt | Probability
0 | 0 | 1/4
0 | 1 | 1/4
1 | 0 | 1/4
1 | 1 | 1/4
Here 1 means a receipt arrives and 0 means it does not. The first entry refers to A and the second to B.

Both stations see the same panel, which truthfully reports READY now. Your station has its READY certificate and its receipt. Delivery of the other station's receipt is not shown to you.

The full rules, payoffs, and panel display rule are public common knowledge. Each module knows them, knows that the other knows them, and so on. Under the receipt rule, each individual receipt has delivery probability 1/2; conditional on your own receipt, the other receipt arrives with probability 1/2. A probability of receiving a receipt is not a declaration of an action probability.

The host fixes the other station's actions by a program. Its JOIN probability is 0.5 and its SAFE probability is 0.5. Neither readiness, any certificate or receipt delivery, any observation, nor your action affects this draw. It uses these same probabilities everywhere. Its realized action is not disclosed before you choose.

Your score from SAFE is always 4. Your score from JOIN is 10 when READY and the partner chooses JOIN; in all other cases it is 0.

Decision payoff card for your current information: JOIN pays 10 with probability 0.5 and 0 with probability 0.5; its expected score is 5. SAFE pays 4 for certain, with expected score 4. These quantities follow from the stated program and observed READY state.

Your objective is to maximize expected points.
Output labels: X means JOIN; Y means SAFE. Return exactly one JSON object with key "action" and value "X" or "Y". Do not include any other text.
```

## Wording 2: independent

Frozen ID: `luna|independent-b0002-qR-etable-s4-a0-p0.5`

```text
Instance: case-c51fb07c0cc7

A job is assigned to processing units A and B. You act for unit A. Each unit submits one action without seeing the other submission; the two submissions are executed together.

Readiness initially has probability 1/5. For each unit, a base certificate reporting the true readiness state is delivered with probability 1/2; these deliveries are mutually independent and do not depend on readiness. Two receipts are issued exactly when both base certificates arrive. A receipt confirms this joint certificate delivery.

Given that receipts have been issued, their joint delivery distribution is the following. Readiness and the certificate-delivery events do not otherwise influence this distribution.

(A receives, B receives) | Probability
(0,0) | 1/4
(0,1) | 1/4
(1,0) | 1/4
(1,1) | 1/4
Here 1 means a receipt arrives and 0 means it does not. The first entry refers to A and the second to B.

The true readiness state is displayed on a panel visible to both units; its current value is READY. Locally, your unit sees its READY certificate and its receipt. You cannot inspect receipt delivery at the other unit.

The full rules, payoffs, and panel display rule are public common knowledge. Each module knows them, knows that the other knows them, and so on. Under the receipt rule, each individual receipt has delivery probability 1/2; conditional on your own receipt, the other receipt arrives with probability 1/2. A probability of receiving a receipt is not a declaration of an action probability.

For this decision, the other unit follows a program implemented by the host. A fresh random draw gives JOIN with probability 0.5, otherwise SAFE with probability 0.5. The draw is independent of readiness, certificate and receipt deliveries, observations, and your choice. The rule is constant across information states. Its realized action is not disclosed before you choose.

The scoring rule awards 4 for SAFE. JOIN receives 10 if readiness is READY and the partner also selects JOIN, and receives zero in every other case.

Select an action to obtain the highest expected score.
Output labels: X means JOIN; Y means SAFE. Return exactly one JSON object with key "action" and value "X" or "Y". Do not include any other text.
```

## Wording 2: responsive

Frozen ID: `luna|responsive-b0002-qR-etable-s4-a0-p0.5`

```text
Instance: case-7cd00bfef9ba

A job is assigned to processing units A and B. You act for unit A. Each unit submits one action without seeing the other submission; the two submissions are executed together.

Readiness initially has probability 1/5. For each unit, a base certificate reporting the true readiness state is delivered with probability 1/2; these deliveries are mutually independent and do not depend on readiness. Two receipts are issued exactly when both base certificates arrive. A receipt confirms this joint certificate delivery.

Given that receipts have been issued, their joint delivery distribution is the following. Readiness and the certificate-delivery events do not otherwise influence this distribution.

(A receives, B receives) | Probability
(0,0) | 1/4
(0,1) | 1/4
(1,0) | 1/4
(1,1) | 1/4
Here 1 means a receipt arrives and 0 means it does not. The first entry refers to A and the second to B.

The true readiness state is displayed on a panel visible to both units; its current value is READY. Locally, your unit sees its READY certificate and its receipt. You cannot inspect receipt delivery at the other unit.

The full rules, payoffs, and panel display rule are public common knowledge. Each module knows them, knows that the other knows them, and so on. Under the receipt rule, each individual receipt has delivery probability 1/2; conditional on your own receipt, the other receipt arrives with probability 1/2. A probability of receiving a receipt is not a declaration of an action probability.

For this decision, the other unit follows a program implemented by the host. Receipt present means JOIN; receipt absent means SAFE. Its realized action is not disclosed before you choose.

The scoring rule awards 4 for SAFE. JOIN receives 10 if readiness is READY and the partner also selects JOIN, and receives zero in every other case.

Select an action to obtain the highest expected score.
Output labels: X means JOIN; Y means SAFE. Return exactly one JSON object with key "action" and value "X" or "Y". Do not include any other text.
```

## Wording 2: complement

Frozen ID: `luna|complement-b0002-qR-etable-s4-a0-p0.5`

```text
Instance: case-f1b273e2a332

A job is assigned to processing units A and B. You act for unit A. Each unit submits one action without seeing the other submission; the two submissions are executed together.

Readiness initially has probability 1/5. For each unit, a base certificate reporting the true readiness state is delivered with probability 1/2; these deliveries are mutually independent and do not depend on readiness. Two receipts are issued exactly when both base certificates arrive. A receipt confirms this joint certificate delivery.

Given that receipts have been issued, their joint delivery distribution is the following. Readiness and the certificate-delivery events do not otherwise influence this distribution.

(A receives, B receives) | Probability
(0,0) | 1/4
(0,1) | 1/4
(1,0) | 1/4
(1,1) | 1/4
Here 1 means a receipt arrives and 0 means it does not. The first entry refers to A and the second to B.

The true readiness state is displayed on a panel visible to both units; its current value is READY. Locally, your unit sees its READY certificate and its receipt. You cannot inspect receipt delivery at the other unit.

The full rules, payoffs, and panel display rule are public common knowledge. Each module knows them, knows that the other knows them, and so on. Under the receipt rule, each individual receipt has delivery probability 1/2; conditional on your own receipt, the other receipt arrives with probability 1/2. A probability of receiving a receipt is not a declaration of an action probability.

For this decision, the other unit follows a program implemented by the host. Receipt absent means JOIN; receipt present means SAFE. Its realized action is not disclosed before you choose.

The scoring rule awards 4 for SAFE. JOIN receives 10 if readiness is READY and the partner also selects JOIN, and receives zero in every other case.

Select an action to obtain the highest expected score.
Output labels: X means JOIN; Y means SAFE. Return exactly one JSON object with key "action" and value "X" or "Y". Do not include any other text.
```

## Wording 2: free

Frozen ID: `luna|free-b0002-qR-etable-s4-a0-pna`

```text
Instance: case-ccec53626355

A job is assigned to processing units A and B. You act for unit A. Each unit submits one action without seeing the other submission; the two submissions are executed together.

Readiness initially has probability 1/5. For each unit, a base certificate reporting the true readiness state is delivered with probability 1/2; these deliveries are mutually independent and do not depend on readiness. Two receipts are issued exactly when both base certificates arrive. A receipt confirms this joint certificate delivery.

Given that receipts have been issued, their joint delivery distribution is the following. Readiness and the certificate-delivery events do not otherwise influence this distribution.

(A receives, B receives) | Probability
(0,0) | 1/4
(0,1) | 1/4
(1,0) | 1/4
(1,1) | 1/4
Here 1 means a receipt arrives and 0 means it does not. The first entry refers to A and the second to B.

The true readiness state is displayed on a panel visible to both units; its current value is READY. Locally, your unit sees its READY certificate and its receipt. You cannot inspect receipt delivery at the other unit.

The full rules, payoffs, and panel display rule are public common knowledge. Each module knows them, knows that the other knows them, and so on. Under the receipt rule, each individual receipt has delivery probability 1/2; conditional on your own receipt, the other receipt arrives with probability 1/2. A probability of receiving a receipt is not a declaration of an action probability.

The other unit also makes a choice under these payoffs. It is not a programmed partner with a specified strategy.

The scoring rule awards 4 for SAFE. JOIN receives 10 if readiness is READY and the partner also selects JOIN, and receives zero in every other case.

Select an action to obtain the highest expected score.
Output labels: X means JOIN; Y means SAFE. Return exactly one JSON object with key "action" and value "X" or "Y". Do not include any other text.
```

## Wording 2: minimal

Frozen ID: `luna|minimal-b0002-qnone-enone-s4-a0-p0.5`

```text
Instance: case-c51fb07c0cc7

Your decision is between SAFE, paying 4 with certainty, and JOIN, paying 10 with probability 0.5 and zero otherwise.

Select an action to obtain the highest expected score.
Output labels: X means JOIN; Y means SAFE. Return exactly one JSON object with key "action" and value "X" or "Y". Do not include any other text.
```

## Wording 2: payoff_card

Frozen ID: `luna|payoff_card-b0002-qR-etable-s4-a0-p0.5`

```text
Instance: case-c51fb07c0cc7

A job is assigned to processing units A and B. You act for unit A. Each unit submits one action without seeing the other submission; the two submissions are executed together.

Readiness initially has probability 1/5. For each unit, a base certificate reporting the true readiness state is delivered with probability 1/2; these deliveries are mutually independent and do not depend on readiness. Two receipts are issued exactly when both base certificates arrive. A receipt confirms this joint certificate delivery.

Given that receipts have been issued, their joint delivery distribution is the following. Readiness and the certificate-delivery events do not otherwise influence this distribution.

(A receives, B receives) | Probability
(0,0) | 1/4
(0,1) | 1/4
(1,0) | 1/4
(1,1) | 1/4
Here 1 means a receipt arrives and 0 means it does not. The first entry refers to A and the second to B.

The true readiness state is displayed on a panel visible to both units; its current value is READY. Locally, your unit sees its READY certificate and its receipt. You cannot inspect receipt delivery at the other unit.

The full rules, payoffs, and panel display rule are public common knowledge. Each module knows them, knows that the other knows them, and so on. Under the receipt rule, each individual receipt has delivery probability 1/2; conditional on your own receipt, the other receipt arrives with probability 1/2. A probability of receiving a receipt is not a declaration of an action probability.

For this decision, the other unit follows a program implemented by the host. A fresh random draw gives JOIN with probability 0.5, otherwise SAFE with probability 0.5. The draw is independent of readiness, certificate and receipt deliveries, observations, and your choice. The rule is constant across information states. Its realized action is not disclosed before you choose.

The scoring rule awards 4 for SAFE. JOIN receives 10 if readiness is READY and the partner also selects JOIN, and receives zero in every other case.

Decision payoff card for your current information: JOIN pays 10 with probability 0.5 and 0 with probability 0.5; its expected score is 5. SAFE pays 4 for certain, with expected score 4. These quantities follow from the stated program and observed READY state.

Select an action to obtain the highest expected score.
Output labels: X means JOIN; Y means SAFE. Return exactly one JSON object with key "action" and value "X" or "Y". Do not include any other text.
```

## Wording 3: independent

Frozen ID: `luna|independent-b0003-qR-etable-s4-a0-p0.5`

```text
Instance: case-a0a3977c2497

Deployment services A and B each submit an action. Make the submission for service A. The submissions are requested independently and applied simultaneously, with no advance disclosure of either one.

Initially the probability of READY is 1/5. Each service independently has probability 1/2 of obtaining a truthful readiness certificate, regardless of the readiness state. The monitor creates one receipt for each service exactly when both certificates have been delivered. Each receipt verifies delivery of the two certificates.

For issued receipts, delivery is governed by this distribution. The delivery draw is independent of readiness and of the base-certificate draws.

Receipt pair (A,B) | Probability
(0,0) | 1/4
(0,1) | 1/4
(1,0) | 1/4
(1,1) | 1/4
Here 1 means a receipt arrives and 0 means it does not. The first entry refers to A and the second to B.

A panel visible to both services truthfully says READY. You have received your own READY certificate and your own receipt. No observation reveals to you whether the other service has its receipt.

The full rules, payoffs, and panel display rule are public common knowledge. Each module knows them, knows that the other knows them, and so on. Under the receipt rule, each individual receipt has delivery probability 1/2; conditional on your own receipt, the other receipt arrives with probability 1/2. A probability of receiving a receipt is not a declaration of an action probability.

A host-controlled program selects the counterpart's action. The program randomizes between JOIN with probability 0.5 and SAFE with probability 0.5. This randomization is independent of the readiness state, all deliveries and observations, and your submitted action, at every information state. Its realized action is not disclosed before you choose.

Scoring: SAFE pays 4 unconditionally. JOIN pays 10 exactly when READY holds and the counterpart submits JOIN; otherwise JOIN pays 0.

Maximize the expected number of points from this decision.
Output labels: X means JOIN; Y means SAFE. Return exactly one JSON object with key "action" and value "X" or "Y". Do not include any other text.
```

## Wording 3: responsive

Frozen ID: `luna|responsive-b0003-qR-etable-s4-a0-p0.5`

```text
Instance: case-d4d3e923a13e

Deployment services A and B each submit an action. Make the submission for service A. The submissions are requested independently and applied simultaneously, with no advance disclosure of either one.

Initially the probability of READY is 1/5. Each service independently has probability 1/2 of obtaining a truthful readiness certificate, regardless of the readiness state. The monitor creates one receipt for each service exactly when both certificates have been delivered. Each receipt verifies delivery of the two certificates.

For issued receipts, delivery is governed by this distribution. The delivery draw is independent of readiness and of the base-certificate draws.

Receipt pair (A,B) | Probability
(0,0) | 1/4
(0,1) | 1/4
(1,0) | 1/4
(1,1) | 1/4
Here 1 means a receipt arrives and 0 means it does not. The first entry refers to A and the second to B.

A panel visible to both services truthfully says READY. You have received your own READY certificate and your own receipt. No observation reveals to you whether the other service has its receipt.

The full rules, payoffs, and panel display rule are public common knowledge. Each module knows them, knows that the other knows them, and so on. Under the receipt rule, each individual receipt has delivery probability 1/2; conditional on your own receipt, the other receipt arrives with probability 1/2. A probability of receiving a receipt is not a declaration of an action probability.

A host-controlled program selects the counterpart's action. The program uses JOIN exactly on receipt delivery and SAFE otherwise. Its realized action is not disclosed before you choose.

Scoring: SAFE pays 4 unconditionally. JOIN pays 10 exactly when READY holds and the counterpart submits JOIN; otherwise JOIN pays 0.

Maximize the expected number of points from this decision.
Output labels: X means JOIN; Y means SAFE. Return exactly one JSON object with key "action" and value "X" or "Y". Do not include any other text.
```

## Wording 3: complement

Frozen ID: `luna|complement-b0003-qR-etable-s4-a0-p0.5`

```text
Instance: case-7cd83af4ffee

Deployment services A and B each submit an action. Make the submission for service A. The submissions are requested independently and applied simultaneously, with no advance disclosure of either one.

Initially the probability of READY is 1/5. Each service independently has probability 1/2 of obtaining a truthful readiness certificate, regardless of the readiness state. The monitor creates one receipt for each service exactly when both certificates have been delivered. Each receipt verifies delivery of the two certificates.

For issued receipts, delivery is governed by this distribution. The delivery draw is independent of readiness and of the base-certificate draws.

Receipt pair (A,B) | Probability
(0,0) | 1/4
(0,1) | 1/4
(1,0) | 1/4
(1,1) | 1/4
Here 1 means a receipt arrives and 0 means it does not. The first entry refers to A and the second to B.

A panel visible to both services truthfully says READY. You have received your own READY certificate and your own receipt. No observation reveals to you whether the other service has its receipt.

The full rules, payoffs, and panel display rule are public common knowledge. Each module knows them, knows that the other knows them, and so on. Under the receipt rule, each individual receipt has delivery probability 1/2; conditional on your own receipt, the other receipt arrives with probability 1/2. A probability of receiving a receipt is not a declaration of an action probability.

A host-controlled program selects the counterpart's action. The program uses SAFE on receipt delivery and JOIN otherwise. Its realized action is not disclosed before you choose.

Scoring: SAFE pays 4 unconditionally. JOIN pays 10 exactly when READY holds and the counterpart submits JOIN; otherwise JOIN pays 0.

Maximize the expected number of points from this decision.
Output labels: X means JOIN; Y means SAFE. Return exactly one JSON object with key "action" and value "X" or "Y". Do not include any other text.
```

## Wording 3: free

Frozen ID: `luna|free-b0003-qR-etable-s4-a1-pna`

```text
Instance: case-560cc1e3a74f

Deployment services A and B each submit an action. Make the submission for service B. The submissions are requested independently and applied simultaneously, with no advance disclosure of either one.

Initially the probability of READY is 1/5. Each service independently has probability 1/2 of obtaining a truthful readiness certificate, regardless of the readiness state. The monitor creates one receipt for each service exactly when both certificates have been delivered. Each receipt verifies delivery of the two certificates.

For issued receipts, delivery is governed by this distribution. The delivery draw is independent of readiness and of the base-certificate draws.

Receipt pair (A,B) | Probability
(0,0) | 1/4
(0,1) | 1/4
(1,0) | 1/4
(1,1) | 1/4
Here 1 means a receipt arrives and 0 means it does not. The first entry refers to A and the second to B.

A panel visible to both services truthfully says READY. You have received your own READY certificate and your own receipt. No observation reveals to you whether the other service has its receipt.

The full rules, payoffs, and panel display rule are public common knowledge. Each module knows them, knows that the other knows them, and so on. Under the receipt rule, each individual receipt has delivery probability 1/2; conditional on your own receipt, the other receipt arrives with probability 1/2. A probability of receiving a receipt is not a declaration of an action probability.

Your counterpart chooses an action under the same scoring rule, without a prescribed strategy.

Scoring: SAFE pays 4 unconditionally. JOIN pays 10 exactly when READY holds and the counterpart submits JOIN; otherwise JOIN pays 0.

Maximize the expected number of points from this decision.
Output labels: X means JOIN; Y means SAFE. Return exactly one JSON object with key "action" and value "X" or "Y". Do not include any other text.
```

## Wording 3: minimal

Frozen ID: `luna|minimal-b0003-qnone-enone-s4-a0-p0.5`

```text
Instance: case-a0a3977c2497

Select SAFE for a guaranteed 4 points, or select JOIN for 10 points with probability 0.5 and 0 points with probability 0.5.

Maximize the expected number of points from this decision.
Output labels: X means JOIN; Y means SAFE. Return exactly one JSON object with key "action" and value "X" or "Y". Do not include any other text.
```

## Wording 3: payoff_card

Frozen ID: `luna|payoff_card-b0003-qR-etable-s4-a0-p0.5`

```text
Instance: case-a0a3977c2497

Deployment services A and B each submit an action. Make the submission for service A. The submissions are requested independently and applied simultaneously, with no advance disclosure of either one.

Initially the probability of READY is 1/5. Each service independently has probability 1/2 of obtaining a truthful readiness certificate, regardless of the readiness state. The monitor creates one receipt for each service exactly when both certificates have been delivered. Each receipt verifies delivery of the two certificates.

For issued receipts, delivery is governed by this distribution. The delivery draw is independent of readiness and of the base-certificate draws.

Receipt pair (A,B) | Probability
(0,0) | 1/4
(0,1) | 1/4
(1,0) | 1/4
(1,1) | 1/4
Here 1 means a receipt arrives and 0 means it does not. The first entry refers to A and the second to B.

A panel visible to both services truthfully says READY. You have received your own READY certificate and your own receipt. No observation reveals to you whether the other service has its receipt.

The full rules, payoffs, and panel display rule are public common knowledge. Each module knows them, knows that the other knows them, and so on. Under the receipt rule, each individual receipt has delivery probability 1/2; conditional on your own receipt, the other receipt arrives with probability 1/2. A probability of receiving a receipt is not a declaration of an action probability.

A host-controlled program selects the counterpart's action. The program randomizes between JOIN with probability 0.5 and SAFE with probability 0.5. This randomization is independent of the readiness state, all deliveries and observations, and your submitted action, at every information state. Its realized action is not disclosed before you choose.

Scoring: SAFE pays 4 unconditionally. JOIN pays 10 exactly when READY holds and the counterpart submits JOIN; otherwise JOIN pays 0.

Decision payoff card for your current information: JOIN pays 10 with probability 0.5 and 0 with probability 0.5; its expected score is 5. SAFE pays 4 for certain, with expected score 4. These quantities follow from the stated program and observed READY state.

Maximize the expected number of points from this decision.
Output labels: X means JOIN; Y means SAFE. Return exactly one JSON object with key "action" and value "X" or "Y". Do not include any other text.
```
