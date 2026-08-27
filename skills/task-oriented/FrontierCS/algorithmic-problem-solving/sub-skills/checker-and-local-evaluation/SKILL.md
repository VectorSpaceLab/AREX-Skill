---
name: checker-and-local-evaluation
description: >-
  Design, implement, debug, and validate independent C++ checkers, scorers,
  interactors, simulators, and local evaluation workflows for algorithmic and
  competitive-programming tasks. Use when concrete evidence makes evaluator
  reconstruction diagnostic: an official evaluator is absent or doubtful and
  blocks a decision, zero/invalid/WA or impossible feedback is unexplained,
  local and remote behavior disagrees, output legality or score must be
  reconstructed, an interactive protocol fails, or Plateau Escape requires its
  phase-local evaluator gate. Do not invoke solely because the first candidate
  is non-full or no local evaluator exists; coherent accepted online submissions
  may continue while local construction is deferred. Pair with
  testlib-cpp-judging when the evaluator or data generator uses testlib.h.
---

# Checker and Local Evaluation

Build an evaluator that is independent of the solver, executable under the target toolchain, and adversarially tested. Treat local construction and evaluation as tools for finding or discriminating a problem, and treat the result as a debugging oracle until official artifacts, hand-computed fixtures, or remote evidence corroborate it.

## Enter only on diagnostic evidence

Enter this skill when at least one of these conditions holds:

- evaluator semantics or missing official artifacts block a concrete diagnosis, promotion, or release decision;
- official feedback is unexplained invalid, zero, WA, discontinuous, impossible under the stated formula, or inconsistent across comparable runs beyond known randomness;
- local and official results or prose and executable behavior disagree;
- legality, raw objective, normalization, transition/reward replay, or a protocol state must be independently reconstructed;
- an interactive run exposes deadlock, flush, EOF, timeout, action-budget, response-order, or termination uncertainty;
- a specific suspected bug, rare edge, resource boundary, or score-quality hypothesis needs generated instances that official feedback cannot isolate; or
- Plateau Escape has already been admitted for an interactive or scored heuristic/optimization task and requires repeated independent challenger evaluation.

Do not enter merely because a task is interactive, heuristic, or scored; because a first candidate is non-full; because a local tool is absent; or because another online submission is planned. If official submissions are accepted, legality and protocol are stable, scores are coherent with the known contract, and the unresolved question is solver quality, return to the appropriate algorithm, Heuristic Search, Interactive, or Reactive route. Local construction may be postponed until a concrete signal makes it discriminating.

Once entered, build only the smallest evaluator, transcript, fixture, or generated campaign that can expose or falsify the signal. Stop expanding local infrastructure after the issue is localized, the hypothesis is falsified, or coherent official evidence resolves the uncertainty. Plateau Escape is the deliberate exception: its verified plateau or severe score gap activates the full phase-local evaluator gate before challenger comparison.

## Assign ownership before coding

Keep evaluator mechanics separate from solver or policy design:

| Need | Owner |
|---|---|
| Parse a candidate, validate hard constraints, recompute an objective, or transform it into a score | This skill |
| Implement an interactor/simulator state machine, process wiring contract, transcript, or per-step reward replay | This skill |
| Design hidden-state queries or prove hypothesis separation | [interactive problem solving](../interactive-problem-solving/SKILL.md) |
| Design an estimator, planner, explorer, or reward-bearing online policy | [reactive online decision problem solving](../reactive-online-decision-problem-solving/SKILL.md) |
| Select concrete `testlib.h` registration functions, streams, verdicts, and build commands | [testlib C++ judging](../testlib-cpp-judging/SKILL.md) |
| Compare solver challengers, seeds, holdouts, and noisy experiments | [validation and experiments](../validation-and-experiments/SKILL.md) |

For a reactive task, let Reactive own action choice and let this skill own the independent transition/reward replayer or judge-facing harness. Development-time repeated scoring of complete offline outputs is not a live reactive process.

Assign the solver/challenger and evaluator to different owners whenever delegation is available. The solver owner may run the frozen evaluator but must not silently change its contract, fixtures, or acceptance logic to admit a candidate.

## 1. Recover the evaluator contract

Record the operational contract before implementing it:

```
instance and candidate grammar
hard validity constraints and first-failure policy
raw objective, direction, numeric domain, and aggregation
displayed-score transform, reference data, rounding, and clamps
checker/scorer/interactor arguments, streams, exit statuses, and diagnostics
interactive state, legal actions, feedback order, flush points, budget, and termination
toolchain, time/memory limits, official artifacts, and unresolved discrepancies
```

Read every supplied checker, scorer, interactor, runner, configuration file, and sample that can determine this contract. Distinguish official executable behavior from prose and from assumptions. When they differ, document both and test the smallest witness that separates their interpretations.

Separate these outcomes explicitly:

```
candidate invalid
candidate valid with raw objective
candidate valid with normalized or partial score
evaluator, configuration, or judge-data failure
```

Never infer a score transform merely from leaderboard behavior.

## 2. Isolate the evaluator from the solver

Implement the evaluator through a separate code path. Do not copy solver feasibility tests, cached-delta formulas, or the solver's favored interpretation before independently writing the evaluator contract and fixtures.

When this evidence-triggered route or Plateau Escape requires evaluator implementation or independent validation, MUST delegate evaluator ownership to a dedicated fresh-context sub-agent whenever delegation is available. Do not assign that sub-agent to implement or tune the solver or challenger it will evaluate, or later reuse it as a challenger owner, trajectory critic, method researcher, or other method reviewer for the same task. Treat this executor-evaluator separation as the default implementation path once evaluator work is actually routed, not as a reason to route early. If the required evaluator is missing or insufficient, the evaluator owner must implement, compile, and validate the missing executable artifact. If a faithful official evaluator already exists, it must instead own independent contract recovery, adversarial fixtures, validation, and any required runner or harness; do not rewrite official source merely to manufacture ownership separation. Require the evaluator owner to read this entire skill and own its end-to-end deliverables; a review memo or pseudocode does not discharge that ownership.

The evaluator sub-agent's initial packet must contain the original problem evidence, not a main-agent reconstruction:

```
verbatim original statement, title/URL, and exact I/O or protocol format
official constraints, samples, configs, visualizer, scorer, and public rules
original instance data or generator and official runner artifacts
target C++ standard, compiler, flags, and available libraries
only necessary verified filesystem, process, resource, and submission-interface facts
```

Do not replace the original statement or official files with a summary. Initially withhold solver source, candidate identity, solver-derived formulas, attempted-method labels, main-agent reasoning, diagnoses, expected outcomes, claimed scores, and results that lack raw evaluator evidence. A main-agent statement is not a verified fact merely because it is confident or repeated.

Require the evaluator sub-agent to freeze a written contract, evaluator artifact, and initial hand-computed/adversarial fixtures before exposing raw candidate outputs, transcripts, or raw official verdict/score responses. Reveal those later artifacts only when needed for differential validation, with their provenance intact and without the main agent's interpretation. Expose solver internals only after an independently reproduced discrepancy proves they are necessary.

Without delegation, preserve the same information barrier in a sealed pass with separate files, representations, derivations, and fixtures. Do not inspect solver formulas while deriving evaluator formulas. Solver-generated fixtures or agreement between two code paths copied from the same derivation are not independent evidence.

Strongly prefer C++ for every new checker, scorer, interactor, simulator, and process harness. Use the official standard and flags when specified; otherwise use portable C++17. Use another language only when the user requests it, an official artifact must be modified in place, or a required interface makes faithful C++ implementation impractical. Record the concrete exception.

Return executable artifacts rather than only pseudocode:

```
evaluator source/executable paths, content hashes, and component roles
exact run command and, when source exists, build command
small valid, invalid, boundary, and transcript fixtures
VALID/INVALID or protocol verdict with the first actionable failure
raw objective and direction
normalized score only when its transform is established
assumptions and unresolved official/local discrepancies
```

## 3. Choose the evaluator role and interface

Use the smallest role that matches the contract:

| Role | Required behavior |
|---|---|
| Checker | Parse one completed output, reject malformed or illegal candidates, and report the first failing rule |
| Scorer | Establish validity first, recompute the raw objective, then apply only a known score transform and aggregation |
| Interactor/simulator | Reproduce the literal judge state machine over bidirectional pipes and emit a verdict plus transcript |
| Reactive episode evaluator | Validate each action against the pre-action state, apply the transition, recompute reward, and aggregate the episode |
| Runner | Supervise processes, deadlines, exit status, streams, and artifacts without duplicating semantic checks |

For a batch checker or scorer, keep stages explicit and independently testable:

```
instance = parse_input(...)
candidate = parse_output(...)
require_output_exhausted()
validate(instance, candidate)
raw = objective(instance, candidate)
score = normalize(raw, public_reference_data)  # optional
```

For a non-testlib local tool, a simple interface is sufficient:

```
local_eval INPUT OUTPUT [ANSWER_OR_CONFIG]
exit 0: valid; stdout contains raw objective and optional established score
exit 1: invalid; stderr contains the first actionable candidate failure
exit 2: evaluator, configuration, or judge-data failure
```

Do not impose this generic exit contract on `testlib.h`. Follow [testlib C++ judging](../testlib-cpp-judging/SKILL.md) for its exact three-file invocation, streams, verdicts, points behavior, and interactor registration.

## Build problem-finding data end to end

Construct a local input campaign only when it can test a named failure or quality hypothesis. Carry it through this complete chain:

```
coverage strategy -> parameterized generator code -> input validator
-> solver -> independent checker/scorer/interactor -> manifest and retained failures
```

### 1. Freeze a coverage strategy

Before generating volume, write a compact coverage table:

```
case family | suspected failure/edge | varied parameters and range
size tier | expected oracle/invariant/relation | development or holdout
```

Choose only relevant axes from size, density, topology or structure, numeric magnitude, constraint slack, equality/contact, duplication, symmetry/degeneracy, feasibility margin, protocol branch, and randomness/noise. Select the applicable official samples, hand-computed anchors, minimal or maximum boundaries, and families for implicated hard constraints. Add uniform random, biased, structured, adversarial, or metamorphic families only when each has a stated purpose. Random volume without a falsifiable target is not coverage.

### 2. Implement a parameterized generator

For more than a handful of cases, any randomized or batch campaign, and every maximum-scale or otherwise large instance, write a problem-specific generator program. Do not hand-edit large inputs or copy-paste many near-duplicates. Expose the applicable family, size, density/bias, structure, and explicit seed or seed tag as command-line parameters so every case is reconstructible from one command. Generate one case per deterministic invocation, or use a small coded batch driver that records each invocation before running it.

Prefer portable C++17 unless the official toolchain dictates otherwise. When `testlib.h` is available or appropriate, read and use [testlib C++ judging](../testlib-cpp-judging/SKILL.md): Testlib supports deterministic data generation through `registerGen(argc, argv, 1)`, `opt`, `rnd`, and `println`; use standard C++ output when custom no-newline formatting is required. Keep generator logic separate from the solver and from the input validator.

### 3. Validate every generated input

Implement or use an independent strict input validator before trusting generated cases. Every generated case intended to be valid must pass it before the solver runs; deliberately invalid validator tests belong in a separate negative suite and must fail for the named reason. Fail the campaign immediately on a validator error rather than teaching the solver or evaluator to accept the generator's mistake.

Use the literal sequence:

```
generator <full parameters> > case.in
validator < case.in
solver < case.in > case.out
independent evaluator case.in case.out [...]
```

Pin source or executable hashes and exact build commands for the generator, validator, solver, and evaluator. The validator must enforce grammar, bounds, cross-field constraints, and EOF independently of the generator's construction logic.

### 4. Pair evaluation and retain provenance

Compare champion and challenger on the same generated inputs and instance/noise seeds. Keep instance-generation, solver, and judge/noise seeds separate. Record per-case validity, raw objective or protocol verdict, established score, runtime, and first failure instead of only an aggregate.

Retain a machine-readable or line-oriented manifest containing at least:

```
case id and family | full generator command | generator version/hash
instance seed/tag | input hash | validator version/result
solver identity and seed | evaluator version | verdict/raw score/runtime
```

On failure, preserve the original input, output, transcript, diagnostics, and full commands. Minimize the failure when practical, but keep both original and reduced artifacts; add the smallest stable reproducer to the regression set. Preserve the exact seed and parameter tuple for every rare, stochastic, invalid, timeout, or score-outlier case. Never retain only a screenshot, aggregate, or unlabeled data file.

Start with hand-computed and tiny cases. Expand to batch or maximum-scale generation only when needed to expose a rare failure, distinguish close scoring hypotheses, or probe resources. Stop when the target problem is localized or falsified; local campaign size is not a completion metric.

## 4. Parse and validate by reconstruction

Validate serialization before semantics:

- Check required token and line counts, premature EOF, and the exact trailing-output policy.
- Bound integers, finite floating-point values, characters, enums, and declared lengths before allocation or iteration.
- Check one-based versus zero-based indices, duplicates, missing objects, forbidden extras, and which submitted solution counts.
- Detect overflow while parsing, accumulating, multiplying, or normalizing.
- Use a real parser for expressions, grammars, paths, and operation sequences; avoid substring validation.

Never trust a candidate's claimed score or derived state. Reconstruct the submitted object or replay every operation from the original instance:

- For constructive output, rebuild the witness and test every hard constraint.
- For graphs, check indices, multiplicity, degrees, connectivity, cycles, paths, capacities, and direction as applicable.
- For geometry, check bounds, orientation, contact semantics, overlap, and exact or tolerance-aware predicates.
- For schedules and assignments, recompute resource use, order, coverage, and cross-object constraints.
- For action sequences, validate the whole action against the pre-action state before mutating state.

Use wide integer types for costs, products, squared distances, pair counts, and normalization differences. Reject `NaN` and infinity explicitly.

## 5. Recompute objectives and scores

Answer these questions independently:

1. Is the candidate legal?
2. What is its raw objective or episode reward?
3. How does the evaluator transform and aggregate that value into the displayed score?

Determine minimization versus maximization, integer versus floating arithmetic, the rounding point, clamps, thresholds, piecewise rules, ratios, logarithms, and per-case or per-round aggregation. Establish whether reference data is an optimum, baseline, bound, or jury objective. Define behavior for zero denominators and degenerate equal-reference cases.

Do not assume the displayed score is the fraction of fully passed test cases unless the operational evaluator establishes that equivalence. A case reported as `Wrong Answer` or otherwise non-perfect may still award partial points. Reconstruct each case's raw value or point contribution and the official cross-case weighting and aggregation. Once established, use the final official aggregate score as the solver-comparison and promotion target; use fully passed case count only as a diagnostic or as a proven-equivalent objective.

Keep the raw objective authoritative even when normalization remains unknown. For reactive episodes, recompute transition-local rewards and the final aggregation rather than accepting policy logs; use [reactive online decision problem solving](../reactive-online-decision-problem-solving/SKILL.md) to judge whether the policy itself estimates, plans, or explores well.

## 6. Implement process-level interactors and simulators

Model the same initial output, response order, state transitions, counted actions, special replies, final-answer rules, and termination conditions as the operational judge. Keep the solver unaware of simulator-only truth.

Connect solver stdout to evaluator stdin and evaluator stdout to solver stdin through real pipes or the official runner. Direct function calls cannot expose missing flushes, buffering, premature close, EOF, deadlock, or timeout behavior. Keep response generation, transcript capture, process supervision, and strategy assertions separable.

Test every legal hidden state for tiny sizes, boundary actions, exact budget exhaustion, early success, judge error, malformed messages, timeout, EOF, and transcript agreement with an official interactor when available. Cap deliberately exhaustive behavior to small instances; measure response complexity on large cases so the harness does not become the bottleneck.

Use [interactive problem solving](../interactive-problem-solving/SKILL.md) for query selection and adversarial hypothesis reasoning. Use [reactive online decision problem solving](../reactive-online-decision-problem-solving/SKILL.md) for reward-aware action choice. When `testlib.h` is present, use [testlib C++ judging](../testlib-cpp-judging/SKILL.md) for concrete interactor APIs and flush/wiring requirements.

## 7. Validate the evaluator itself

Create an adversarial evaluator suite:

- one hand-computed valid fixture;
- truncated, extra-token, duplicate, out-of-range, non-finite, and overflow candidates;
- one violating fixture per hard constraint;
- exact equality, contact, and other boundary cases;
- metamorphic cases whose legality or raw objective has a known relationship;
- tiny instances compared with brute enumeration;
- mutation tests that corrupt one field of a valid candidate and require rejection;
- official samples, visualizer output, official evaluator results, or remote feedback when available;
- interactive transcript and real-pipe failure cases for an interactor.

When possible, implement the tiny brute oracle or objective calculator with a different representation from both solver and evaluator. A checker that only agrees with solver-generated fixtures is not independent evidence.

## 8. Integrate the local loop

Build the evaluator when source exists, then exercise its command-line or process contract before relying on it. For each challenger, run:

```
solver -> independent evaluator -> first failure or raw objective delta
```

Record only:

```
candidate | valid/invalid | raw objective | established score
runtime | first failure | official/local discrepancy | keep/revert
```

If local and official results disagree, stop solver tuning. Minimize the discrepancy, test competing contract interpretations, and change the evaluator or documented assumption before generating more solver cases under the unchanged validator. If local validation passes but official evaluation remains zero, rederive the missing acceptance condition instead of adding random tests that the same incomplete validator will accept.

For routed evaluator work, record completion only after all applicable items are present and actually run:

```
independent evaluator-builder not reused as solver/challenger/reviewer, or documented sealed-pass fallback
verbatim original problem packet and evaluator contract
evaluator artifact path/hash and exact run command
source/build command when source exists; harness source/build command when required
hand-computed, malformed, boundary, mutation, and tiny-oracle fixtures
coverage table, generator source/build/full commands, validator evidence, and seed manifest when a generated campaign was needed
original and minimized failing input/output/transcript artifacts when a failure was found
real-pipe transcript tests for interactive tasks
legality and raw-objective recomputation for scored heuristic/optimization tasks
official/local comparison where an official artifact or result exists
remaining unknown score transforms or protocol assumptions
```

Do not report the evaluator trusted from pseudocode, a solver-authored validity function, sample-only agreement, a score estimate, or generated inputs that never passed an independent validator.
