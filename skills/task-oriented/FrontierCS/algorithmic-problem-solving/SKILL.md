---
name: algorithmic-problem-solving
description: >-
  Recover solutions after a focused attempt lacks a verified full pass or
  maximum score. MUST invoke and read this skill (1) after 2 non-full
  submissions, even if high-scoring; (2) after the first non-full candidate for
  any interactive or scored heuristic/optimization task, including AHC; and (3)
  before any non-full final delivery. Skip only after verified full pass/full
  score. For (2), route to an independent local interactor/checker/scorer only
  on concrete evaluator, legality, scoring, protocol, or diagnostic evidence,
  or when Plateau Escape requires its phase-local gate. Coherent accepted online
  submissions may continue, deferring local data/evaluation until it can expose
  a problem. When routed and delegation exists, assign a fresh-context evaluator
  owner and give it originals rather than solver reasoning. Also use
  for WA, TLE/MLE, crashes, invalid output, evaluator disagreement, score gaps,
  stalled heuristics, or interactive/reactive failures. Do not use before a
  fresh problem's first focused attempt.
---

# Algorithmic Problem-Solving Recovery

Diagnose the failed layer and preserve verified work. Outside Plateau Escape, make the smallest evidence-backed change that can recover a complete or materially stronger solution. Once Plateau Escape is routed, exempt structural work from the smallest-change preference and maximize evidence-weighted expected terminal official score.

## Positioning

This is a recovery router, not the default way to solve every contest problem. The focused end-to-end solve is an activation prerequisite and happens outside this skill. If no concrete failure evidence exists, leave this workflow and solve the problem directly. The post-first-candidate rule for interactive and scored heuristic/optimization tasks activates the relevant search or policy recovery guidance; it does not by itself trigger local evaluator construction. Treat local data generation and evaluation as problem-finding tools that may be deferred while accepted online submissions return coherent legality, protocol, and score evidence.

Once activated, do not restart reflexively. Reconstruct the actual contract and the failed attempt from artifacts, then reuse every verified component that is not implicated by evidence.

Use artifact terms consistently:

```
fallback   simplest guaranteed-valid emergency output
challenger experimental candidate evaluated against the champion
champion   best independently validated legal artifact
baseline   external scoring/evaluation reference, never a solver artifact
```

## Recovery snapshot

Collect only the facts needed to reproduce and localize the failure:

```
statement, bounds, and operational evaluator contract
attempted model, algorithm, proof assumptions, and complexity
source/build/run commands and target toolchain
smallest failing input, transcript, or scored instance
expected versus observed result, verdict, score, runtime, and memory
available checker, scorer, interactor, simulator, logs, and submission budget
champion/fallback/challenger paths and remaining uncertainty
```

Read every supplied artifact that is directly relevant to the failing layer. Resolve prose/config/evaluator discrepancies explicitly. Prefer their legal intersection when it has no material cost; otherwise record and test any dependency on the operational evaluator.

## Classify before changing code

| Evidence | Failing layer to test first | Route |
|---|---|---|
| Contract meaning, state, invariant, recurrence, reduction, or proof is questionable, or brute force finds a mismatch | Problem model and correctness | [model and route algorithms: model repair](sub-skills/model-and-route-algorithms/SKILL.md#1-normalize-the-operational-contract) |
| The model is trusted, but the exact/constructive/hybrid/heuristic boundary is unclear under the real bounds | Feasibility and route choice | [model and route algorithms: feasibility](sub-skills/model-and-route-algorithms/SKILL.md#5-establish-the-operation-and-memory-envelope) |
| The route is known, but its complexity class, algorithm-family premise, or abstract data-structure choice is wrong | Algorithm selection | [technique selection](references/technique-selection.md) |
| The official evaluator is absent or doubtful and that uncertainty blocks a decision; zero/invalid/WA feedback or an impossible score is unexplained; local and remote results disagree; legality, objective, score, simulator, protocol, or episode replay needs independent reconstruction; or Plateau Escape requires its phase-local evaluator gate | Evaluator contract and independent oracle | [checker and local evaluation](sub-skills/checker-and-local-evaluation/SKILL.md) |
| The evaluator is trusted, but oracle choice or counterexample search is unclear, comparisons are noisy, or a challenger needs paired, holdout, metamorphic, or other independent evidence before promotion | Experiment design and promotion evidence | [validation and experiments](sub-skills/validation-and-experiments/SKILL.md) |
| The route is justified, but compilation, crash/UB, overflow, memory layout, TLE/MLE, buffering, solver-side serialization, randomness, deadline handling, or an implemented data-structure invariant fails | Implementation and environment | [contest solver engineering](sub-skills/contest-solver-engineering/SKILL.md) |
| Any non-full AHC or other scored heuristic/optimization task has a legal candidate, whether offline or online; or its construction, representation, moves, deltas, reachability, evaluation, or optimizer behavior is weak | Mandatory scored-search baseline and search mechanics | [heuristic search](references/heuristic-search.md) |
| A verified legal scored champion has stopped improving or remains severely below the meaningful score target | Structural quality escalation | [scored-recovery escalation](#escalate-weak-scored-recovery) |
| The main value of an action is to obtain information and shrink hidden hypotheses | Protocol, query design, inference, adversarial feedback | [interactive problem solving](sub-skills/interactive-problem-solving/SKILL.md) |
| A reward-bearing decision occurs in a live sequential process and new observations or feedback can change later choices | Estimation, planning, exploration, sequential feedback | [reactive online decision problem solving](sub-skills/reactive-online-decision-problem-solving/SKILL.md); for AHC or another scored heuristic task, pair it with [heuristic search](references/heuristic-search.md) |

Choose the primary failing-layer route, but treat mandatory and paired routes as additive rather than exclusive. Read every document named by the selected route before acting. In particular, a non-full AHC always adds Heuristic Search, and a live reward-bearing AHC adds Reactive without replacing Heuristic Search. Resolve an upstream contract, evaluator, legality, or implementation contradiction before tuning through a downstream route. A symptom may move to another row after one falsifying test; update the diagnosis instead of stacking unrelated fixes.

Model and Route Algorithms has two internal entry points: begin with model repair when correctness evidence is unresolved, and enter at its feasibility envelope only when the model and proof obligations are already trusted.

Technique Selection owns whether a data structure or algorithm family matches the required operations and bounds. Contest Solver Engineering owns whether the chosen implementation maintains its invariants. Checker and Local Evaluation owns what submitted output means and independently parses legality and score; Contest Solver Engineering owns solver-side formatting, index conversion, buffering, and flush behavior.

Use the recovery loop below for a correction with a known deterministic failing test and an obvious focused regression. Route to Validation and Experiments when choosing or constructing the evidence is itself material, stochastic variance can reverse promotion, or independent promotion/release evidence is still missing.

The checker/local-evaluation sub-skill owns evaluator architecture, independent implementation, and adversarial validation of the evaluator itself. For concrete evaluator code based on `testlib.h`, pair it with [testlib C++ judging](sub-skills/testlib-cpp-judging/SKILL.md).

## Evidence-triggered local evaluation

Route to [Checker and Local Evaluation](sub-skills/checker-and-local-evaluation/SKILL.md) only when at least one concrete signal makes evaluator work useful:

- an official evaluator is absent or doubtful and its behavior now blocks diagnosis, promotion, or release;
- an accepted-looking candidate receives unexplained invalid, zero, WA, discontinuous, or impossible feedback;
- local and official results, repeated official results, or prose and executable evaluator behavior disagree beyond established randomness;
- legality, raw objective, score transformation, simulator transition, or episode replay must be independently reconstructed to distinguish the next hypotheses;
- an interactive run shows a protocol symptom such as deadlock, missing flush, premature EOF, timeout, query-budget disagreement, or unexpected termination;
- final delivery retains material evaluator, protocol, legality, or score uncertainty that coherent official evidence has not resolved; or
- an interactive or scored heuristic/optimization task enters Plateau Escape, whose repeated challenger comparison requires its own phase-local independent evaluator gate.

Do not route solely because the task is interactive, scored, heuristic, or AHC; because its first candidate is non-full; because no local evaluator exists; or because another submission is planned. If official submissions are accepted, protocol and legality remain stable, scores and diagnostics are coherent with the known contract, and the open question is algorithmic quality, continue through the model, Interactive, Reactive, Heuristic Search, or Plateau admission route as applicable. Defer local construction until it can find a suspected problem or discriminate competing explanations.

Once routed, start with the smallest artifact and data that can reproduce or falsify the signal. Build a broader generated campaign only when hand-computed cases, one failing transcript, or direct official evidence cannot localize it. Follow Checker and Local Evaluation's complete `coverage strategy -> parameterized generator -> validator -> evaluator -> seed/failure retention` workflow; when using `testlib.h`, pair it with [testlib C++ judging](sub-skills/testlib-cpp-judging/SKILL.md). Batch, randomized, or maximum-scale data must come from reproducible generator code rather than hand-authored large files.

When routed evaluator work requires implementation or independent validation and delegation is available, assign ownership to a dedicated fresh-context sub-agent that did not author the solver or challenger; do not reuse it as a challenger owner, trajectory critic, method researcher, or other method reviewer for the same task. Give it the verbatim original statement and official original artifacts first, plus only necessary verified toolchain and access facts. Withhold solver internals, solver-derived formulas, main-agent diagnoses, method preferences, estimated scores, and unverified summaries until it has frozen the evaluator contract and initial fixtures. If delegation is unavailable, perform a sealed independent pass with separate files, representations, derivations, and fixtures.

Plateau Escape retains the stricter phase-local rule: for an interactive or scored heuristic/optimization task, it must implement and validate any missing evaluator artifact before its reviewers compare structural challengers. This exception is triggered by the verified plateau or severe score gap, not by the first non-full candidate.

## Additive AHC routing

Every non-full AHC or equivalent scored heuristic/optimization task MUST read Heuristic Search before further optimization, another submission, Plateau Escape, or final delivery. This requirement does not imply a Checker and Local Evaluation route without one of the concrete signals above. If live observations or feedback can change later reward-bearing actions during the same judged execution, it MUST additionally read Reactive Online Decision Problem Solving. These requirements are additive; choosing a primary failing layer does not waive either one.

Apply the routes as follows:

```
offline, complete input, one final output -> Heuristic Search
live observations/feedback change later reward-bearing actions -> Reactive Online Decision Problem Solving -> Heuristic Search
separable query stage primarily reduces hidden hypotheses -> Interactive Problem Solving for that stage; keep the applicable Heuristic and/or Reactive route for score-bearing actions
```

Heuristic Search is the mandatory AHC baseline. It owns representation, construction, neighborhoods, rollout/search mechanics, incremental evaluation, reachability, optimizer choice, and time allocation. For a live online AHC, Reactive owns the outer observable/latent state, estimator, planner, explorer, feedback update, horizon, and risk policy; then read Heuristic Search for the concrete action-generation or inner-search machinery. Do not let either document substitute for the other.

Do not add Reactive merely because the output encodes a long action sequence or compact policy, the scorer simulates turns or randomness after receiving a fixed output, or development repeatedly calls a local/remote evaluator. If the submitted program cannot observe an outcome and adapt its next action during the same judged execution, keep the task on the offline Heuristic route. Once a non-full AHC candidate or judged result exists, its AHC label mandates Heuristic Search, but does not mandate Reactive by itself.

## Distinguish Interactive from Reactive

Use this ownership rule when a task has feedback:

```
Interactive: understand protocol -> choose query -> update hypotheses -> recover a sufficiently determined hidden answer
Reactive:    observe -> estimate -> choose a legal action -> receive reward -> update policy until the horizon/task/budget ends
```

If an action primarily eliminates candidate hidden states, route that stage to Interactive. If it must earn reward while learning from live feedback that changes later decisions in the same run or environment, route the overall policy to Reactive. For any AHC or scored heuristic task, keep Heuristic Search as the additive search-mechanics route in either case. A precommitted action sequence, an offline policy artifact, simulated turns after fixed output, stochastic execution without observable feedback, and repeated evaluation across development runs do not make a task Reactive.

## Evidence-driven recovery loop

1. Reproduce the failure with the smallest faithful command, input, transcript, or fixed seed available.
2. State one falsifiable diagnosis at the model, algorithm, implementation, evaluator, protocol, or policy layer.
3. Design the smallest discriminating test. Prefer a tiny brute oracle, hand-computed boundary, invariant assertion, transcript replay, profile, or paired champion/challenger comparison.
4. Change one implicated component. Keep the champion untouched and materialize risky work as a challenger.
5. Compile and run the targeted test, then the relevant regression set. Never claim an experiment that was not run.
6. Promote only a legal challenger that fits the resource/protocol budget and improves the required correctness or fixed scoring evidence.
7. Repeat from the new evidence; do not tune a downstream layer while an upstream contract or validity contradiction remains.

For exact work, demand a corrected proof obligation and try to falsify it on tiny exhaustive cases. For scored work, keep the true raw objective authoritative and verify cached deltas against full recomputation. For stochastic work, compare paired seeds/cases and expand the sample only when variance can reverse the decision.

## Escalate weak scored recovery

Apply this gate only after the champion is legal under trusted operational evidence and fits the resource budget. A coherent accepted official result may establish legality for admission without first constructing a local evaluator. Read [Plateau Escape](sub-skills/plateau-escape/SKILL.md) when either signal holds; for an interactive or scored heuristic/optimization task, Plateau Escape will then complete its phase-local independent evaluator gate before comparing challengers:

- **Measured plateau:** at least two materially different legal challengers, or at least 3 controlled submissions, fail to improve the champion beyond a predeclared threshold above evaluator/seed/runtime noise. Use `1%` of a normalized score scale as the default threshold when such a scale exists.
- **Severe score gap:** after the focused recovery loop, the best legal champion is still below `70%` of a meaningful official maximum or explicit target.

A controlled comparison uses the same evaluator, comparable budgets, and paired fixed cases/seeds when applicable. A materially different challenger changes the representation, objective or value model, neighborhood reachability, planning horizon, decomposition, relaxation, or algorithm family; changing only a seed, scalar parameter, tie-break, operator percentage, or runtime allocation does not count.

A single low score is not by itself a measured plateau, but the below 70% rule is an independent mandatory escalation because the remaining gap is too large to justify stopping at local tuning. After the focused recovery loop, this root-level severe-gap signal satisfies Plateau Escape's admission gate. If the score has no meaningful maximum or explicit target, do not invent a halfway point; use the measured-plateau signal instead. Route invalid or contradictory evaluation to Checker and Local Evaluation, implementation/resource failures to Contest Solver Engineering, unclear comparisons to Validation and Experiments, and ordinary search-mechanics weaknesses to Heuristic Search before escalating.

When escalation applies, preserve the champion and run Plateau Escape's two fresh-context sub-agent roles when delegation is available. Give the trajectory critic the original problem artifacts and verified facts, then the separately labeled attempt log only after it freezes an independent reconstruction. Give the method researcher the complete original problem and only verified necessary contract, budget, target, and evaluation facts; withhold the champion, attempt history, current method labels, diagnoses, risk labels, rejected-method rationales, and the other review until its independent research map is sealed. If delegation is unavailable, perform the two sealed passes and preserve the same information barrier.

Treat sub-agent work as an executable evidence track, not optional advice:

- When remote submission is authorized and budget remains, delegate an explicit quota and reserve at least one submission for the method researcher; when the budget permits, also allocate a separate multi-submission iteration quota to each selected rank-1 critic/research track. Prioritize those iterations over easier lower-ranked methods or retaining unused budget for the main agent. Both reviewers should implement, evaluate, improve, and submit their own isolated challengers instead of returning them for subjective main-agent screening. If only the main agent can access the transport, relay each exact sub-agent artifact unchanged and return the raw result for every iteration.
- Encourage both roles to explore aggressively across high-upside representations, objectives, decompositions, neighborhoods, planning horizons, relaxations, and algorithm families, including methods that require a substantial rewrite. Aggressive exploration never waives legality, evaluator fidelity, final judge limits, or submission authorization.
- Require both roles to freeze rankings by the evidence-weighted expected terminal final official aggregate score achievable under the verified remaining hard time, compute, and submission budget. Implementation difficulty, code size, rewrite scope, familiarity, prototype speed, or ability to finish within one sub-agent turn is not a ranking criterion. A turn boundary is not a hard scope limit: continue the same isolated rank-1 owner through follow-up tasks when supported. Task each role to implement its rank-1 applicable method, start with that method's smallest faithful structural prototype, and iteratively repair and improve it through the delegated evaluation/submission quota; `smallest` scopes the first experiment, not the method choice.
- Process both frozen rankings in order. Do not select a lower-ranked method until every higher-ranked method has Plateau Escape's required recorded elimination evidence. Every leading proposal must end as iteratively evaluated, queued for a named test, or rejected with a proof, primary contract citation, failing artifact, or measurement that matches Plateau Escape's rejection gate.
- The main agent may not use `risk too high`, unfamiliarity, code size, restructuring cost, or an unmeasured estimate as a veto. Under the same established final evaluator, a legal challenger with a better exact terminal final score and passing hard constraints is promoted mechanically; opinion cannot override that result.

Do not stop after collecting reports, defer all experiments back to the main agent, or resume scalar tuning before each selected rank-1 structural track reaches Plateau Escape's iteration stop condition or concrete rejection evidence.

## Guardrails

- Separate legality from quality and raw objective from displayed score.
- For scored tasks, optimize the established final official aggregate score; use passed-case count or a proxy only when proven equivalent.
- Never let a failed or weaker challenger replace the champion.
- Preserve a legal fallback when interruption, query limits, or deadlines could otherwise erase all value.
- Isolate checker/scorer/interactor logic from solver-derived formulas when evaluator fidelity is in doubt.
- Prefer the target language for solver changes. For a new checker, scorer, interactor, simulator, or evaluation harness, strongly prefer target-supported C++ and portable C++17 when unspecified; provide exact build and run commands.
- Use research when the diagnosed gap requires external facts or another method family. Treat findings as hypotheses that must pass the same contract, compile, validity, objective, and resource gates as local ideas.
- Do not submit, overwrite a champion, or spend scarce evaluation budget unless the requested workflow authorizes it. Once an explicit quota is delegated, a sub-agent may spend that quota without repeated approval but still may not mutate the champion.

## Finish

Rebuild the selected champion cleanly and rerun the focused regression, final serialization or transcript validation, and representative resource probe. If Checker and Local Evaluation was evidence-triggered or Plateau Escape completed its phase-local evaluator gate, rerun that independent evaluator and report its exact command and result. Otherwise, coherent accepted official evidence may remain the evaluation record; do not delay delivery merely to manufacture a local campaign with no unresolved problem hypothesis. Deliver the champion rather than the latest edit.

Before accepting any scored result below 70% of a meaningful official maximum or explicit target, read and execute Plateau Escape. Use its fresh-context sub-agents with role-specific evidence packets, let every selected rank-1 critic/research track complete its authorized iteration loop and stop condition, and apply the evidence-bound promotion or rejection rule; do not finish with only advice, an unevaluated recommendation, a subjective main-agent veto, or another round of minor parameter tuning.

An official score of `0`, or below `30%` of a meaningful maximum/target, is an immediate plateau: do not finish; invoke Plateau Escape and MUST run both fresh-context roles (or both sealed passes). Discard prior main-agent diagnoses, rankings, and rejections except independently verified facts. Adopt their common rank-1 route; if they disagree, execute both. The main agent may not veto; run each to its stop/rejection gate and promote only legal measured champions.

Report only:

```
root cause and decisive evidence
implemented correction or promoted challenger
commands/tests actually run and their results
sub-agent submission ids, per-iteration scores, and terminal score when applicable
remaining assumptions or material risk
```
