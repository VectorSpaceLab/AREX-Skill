---
name: reactive-online-decision-problem-solving
description: >-
  Design, debug, and improve decision policies that must earn immediate or
  future reward under uncertainty, including reactive or online control,
  repeated-round learning, exploration, and risk-aware action selection. Use
  when actions occur in a live sequential process, their feedback changes later
  choices in the same run or environment, and termination is a horizon, task
  completion, or decision budget. Do not use for offline output-only AHC or
  scorer-only optimization across development runs; use heuristic search. Use
  interactive-problem-solving for pure query design or protocol mechanics.
---

# Reactive Online Decision Problem Solving

Make good decisions under uncertainty. The central question is: **What should be done now?** An action's value combines immediate reward, future opportunity, information, and risk.

```
observe -> update belief/model -> generate actions -> legal/risk filter
        -> choose and act -> receive feedback -> repeat
```

This includes online or AHC tasks only when execution contains a live reward-bearing sequence in which earlier actions change the state, observations, rewards, or later choices. It excludes offline output-only AHC and scorer-only optimization whose complete input is known and whose evaluator is called only between development runs; route those tasks to [heuristic search](../../references/heuristic-search.md) and [validation and experiments](../validation-and-experiments/SKILL.md). Repeated evaluation alone does not make a task reactive.

## Boundary with information acquisition

Use [interactive problem solving](../interactive-problem-solving/SKILL.md) when actions exist primarily to eliminate hidden hypotheses and the process stops once an answer is determined. Use this skill when live sequential actions must earn reward under current uncertainty and the process stops because the horizon, task, time, or decision budget ends.

If a reactive task contains a separable calibration or hidden-state identification stage, use the Interactive skill for that subproblem while keeping overall action choice here.

## 1. Define the decision contract

Record the operational decision process:

```
observable state/history and latent uncertainty
legal actions or candidate-output representation
state transition and feedback timing
round, time, action, or evaluator budget
raw reward/cost, direction, transform, and aggregation
risk constraints and whole-run failure conditions
reset/persistence across rounds, cases, and evaluations
terminal conditions and mandatory completion requirements
```

Separate hard legality from quality. Replay state transitions and reward calculations literally. If local and official scoring disagree, route to [checker and local evaluation](../checker-and-local-evaluation/SKILL.md) before changing the policy.

## 2. Separate estimator, planner, and explorer

Use only the layers the task needs, but keep their contracts distinct:

1. **Estimator:** infer decision-relevant latent quantities and uncertainty from feedback.
2. **Planner:** choose the best feasible action under the current model and horizon.
3. **Explorer:** trade immediate cost for information that can improve later decisions.

Test each layer independently: synthetic truth for the estimator, known parameters for the planner, and controlled horizons for the exploration rule. A strong score should not be the only evidence that all three are correct.

Choose the simplest identifiable model that supports decisions:

- per-item or per-edge estimates with shrinkage;
- feature, segment, group, or low-rank models for aggregate feedback;
- posterior distributions or confidence intervals when uncertainty changes actions;
- robust updates for heavy-tailed or corrupted observations;
- recency weighting or change detection for drift;
- censored or delayed-feedback models when outcomes are partial.

Aggregate feedback may not identify every latent parameter. Optimize prediction of decision-relevant totals instead of pretending all components are known; check rank, conditioning, calibration, and regularization.

## 3. Choose actions by utility, not uncertainty alone

Define every outcome as a higher-is-better utility `U`; for a minimization objective, negate or otherwise reorient the cost first. For a separable information-gathering action `a`, feedback outcome `y`, and later decision `d`, a conceptual value-of-information test is:

```
VOI(a) = E_y[max_d E[U(d) | y, a]]
         - max_d E[U(d)]
         - immediate_and_opportunity_cost(a)
```

Exact VOI is often too expensive. Use a justified proxy such as uncertainty along likely decisions, disagreement between plausible models, confidence-bound optimism, posterior sampling, or expected regret reduction. Do not apply the pure-information expression when the action also changes state or reward; compare full action values under the real transition model instead. Do not explore uncertain regions that cannot affect later choices.

Explore more when useful future decisions remain; exploit more near the end or in heavily weighted rounds. Base the schedule on confidence, remaining opportunity, and risk rather than only a hard-coded round number.

When an action changes future feasibility, plan with the real transition and reserve recovery slack. A myopic reward can destroy reachability or mandatory completion.

## 4. Build the planner and search policy

Use exact combinatorial optimization inside each decision when it fits: shortest path, matching, flow, scheduling, DP, or a bounded exact local solve. Useful hybrids include learned costs plus exact routing, learned skills plus matching, posterior samples plus robust optimization, and rolling-horizon construction with bounded repair.

For scored construction, neighborhoods, incremental deltas, SA, beam search, LNS, portfolios, time allocation, and other concrete optimization mechanisms, read [heuristic search](../../references/heuristic-search.md). That reference owns search-method details; this skill owns the uncertainty-aware policy wrapped around them.

Maintain:

```
legal fallback policy or output
current model/policy state
best independently validated legal champion
experimental challenger
```

Never replace the champion with a seed-sensitive or invalid challenger. If controlled structural alternatives have stopped improving a verified champion, route to [plateau escape](../plateau-escape/SKILL.md).

## 5. Evaluate repeated feedback correctly

When a concrete legality, transition, reward, protocol, or official-feedback uncertainty needs local diagnosis, route to [checker and local evaluation](../checker-and-local-evaluation/SKILL.md) to implement an independent episode replayer, scorer, interactor, or process harness. Coherent accepted online episodes do not require this route solely because the policy is reactive; local replay may be deferred while the open question is policy quality. Once routed, that sub-skill owns evaluator isolation, executable contracts, and adversarial evaluator tests; this skill owns the estimator, planner, explorer, and policy-level diagnosis. When the evaluator uses `testlib.h`, follow the concrete Testlib route linked there.

Use [validation and experiments](../validation-and-experiments/SKILL.md) for champion/challenger discipline, paired cases/seeds, holdouts, and release checks.

Separate randomness sources:

```
instance seed | transition/judge noise | solver RNG | host/runtime noise
```

Track per-round and per-instance evidence, not only one aggregate score:

- cumulative and late-horizon reward;
- prediction residuals and calibration by uncertainty bucket;
- exploration cost versus measured later benefit;
- invalid action count and fallback use;
- score and runtime by instance features;
- median, quantiles, and lower-tail failures as well as mean.

Pair policies on the same allowed inputs and noise seeds. One higher noisy score is not proof of a stronger decision rule.

## 6. Safety and completion

- Filter every proposed action through legality and risk constraints.
- Keep a conservative legal action when inference or planning fails.
- Bound variable-time replanning, repair, and exact subsolves.
- Reserve actions/time needed for coverage, return-to-start, final output, or other mandatory completion.
- Checkpoint the last-known-valid model and champion.
- Make tie-breaking and seeds reproducible while diagnosing.

Do not add flush/query machinery to an offline scorer-only workflow. If a live judge protocol actually exists, route those mechanics to Interactive and [contest solver engineering](../contest-solver-engineering/SKILL.md).

## Diagnostics

| Symptom | Test first |
|---|---|
| Good prediction error, poor score | Planner objective, feasibility, horizon, proxy alignment |
| Early reward good, late reward poor | Update bias, drift, exploration schedule |
| High uncertainty persists | Identifiability, observation design, regularization |
| Exploration costs more than it returns | Decision relevance, remaining horizon, opportunity cost |
| Seeds diverge sharply | Fragile early updates, heavy tails, missing fallback |
| Runtime spikes | Replanning complexity, allocation, unbounded repair/subsolve |
| Local score rises, official score does not | Score transform, instance shift, overfit, evaluator mismatch |

Return the decision contract, estimator/planner/explorer design, legality and fallback invariants, implementation, evaluations actually run, champion comparison, and residual uncertainty or risk.
