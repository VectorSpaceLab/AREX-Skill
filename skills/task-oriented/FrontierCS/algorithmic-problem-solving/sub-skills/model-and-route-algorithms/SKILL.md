---
name: model-and-route-algorithms
description: >-
  Diagnose and repair a static algorithmic problem model, state, reduction,
  recurrence, invariant, or proof, then decide whether an exact, constructive,
  exact-hybrid, heuristic, or scored-hybrid route fits the real bounds. Use as
  an internal algorithmic-problem-solving recovery route when brute force or a
  proof premise contradicts the attempted solution, or when the model is
  trusted but the justified solution class remains unclear. Do not use for
  hidden-state query design or reward-bearing online decisions.
---

# Model and Route Algorithms

Establish a trusted static model and proof target before selecting a solution class. Enter at the earliest unresolved stage and do not reopen an upstream stage without new contradictory evidence.

```
operational contract -> sufficient model/state -> proof obligation
-> resource envelope -> admissible solution class -> concrete method family
```

## Entry modes and ownership

Use the **model-repair entry** when the failed attempt may be solving the wrong problem or relying on an incomplete state, reduction, invariant, recurrence, or proof. Use the **route-selection entry** at [the feasibility envelope](#5-establish-the-operation-and-memory-envelope) only when the operational model and correctness obligations are already trusted.

This skill owns static combinatorial modeling, correctness obligations, and exact/constructive/hybrid/heuristic route choice. Route other failure layers as follows:

- evaluator parsing, legality, or objective uncertainty that blocks the current decision, or official/local disagreement: [checker and local evaluation](../checker-and-local-evaluation/SKILL.md);
- hidden-state acquisition and query semantics: [interactive problem solving](../interactive-problem-solving/SKILL.md);
- reward-bearing sequential decisions under uncertainty: [reactive online decision problem solving](../reactive-online-decision-problem-solving/SKILL.md);
- compile, numeric, memory-layout, serialization, or measured deadline failure after the route is justified: [contest solver engineering](../contest-solver-engineering/SKILL.md);
- oracle design, counterexample minimization, and controlled comparisons: [validation and experiments](../validation-and-experiments/SKILL.md).

## 1. Normalize the operational contract

Remove story terms and write:

```
Given instance I, choose x in F(I).
Hard constraints: C_j(I, x) = true for every j.
Raw objective: minimize/maximize f(I, x).
Observed score: S(I, x) = transform(f, baseline, bound, aggregation).
```

Derive this model from the statement and every directly relevant checker, scorer, configuration, and sample. When prose and executable behavior differ, record both interpretations, their legal intersection, and any dependency on the operational evaluator. If the evaluator itself is doubtful, stop and use Checker and Local Evaluation before treating either interpretation as trusted.

Check common modeling traps:

- a fine-grained constraint was replaced with an unjustifiably stronger one;
- equality, duplicates, orientation, order, or multiplicity are semantically meaningful;
- a sequential transition was replaced by a non-equivalent aggregate formula;
- the score uses a clamp, ratio, rounding, logarithm, lexicographic priority, baseline, or whole-run failure rule;
- several cases share one time, memory, state, or score budget;
- the public statement and executable evaluator disagree;
- a stochastic generation claim is a distributional promise rather than a per-instance guarantee.

Separate legality, raw objective, and displayed score. A correct objective calculation does not prove legality, and a non-perfect score does not by itself prove invalidity.

## 2. Define sufficient, tractable state and valid reductions

A state must retain exactly what affects future feasibility and value. Derive it by asking which histories are equivalent for every possible continuation.

Among sufficient states, prefer one that is compact, canonical, and efficient to encode, compare, hash, copy, and update. Its legal transitions should be easy to generate without reconstructing the full history, and the information needed for objective updates, pruning, memoization, dominance, and reconstruction should be directly available or incrementally maintained.

Look for:

- canonicalization under interchangeable labels, rotations, reflections, or component order;
- dominance: discard state `a` only if state `b` has no worse resources/value and at least the same continuation set;
- monotone resources enabling Pareto frontiers;
- sparse reachable states enabling maps instead of dense arrays;
- a small boundary between processed and unprocessed structure;
- reversible transitions and compact reconstruction parents.

Falsify a proposed compression by constructing two histories with the same compressed state and searching for a continuation that treats them differently. Such a continuation disproves the state definition.

For every reduction, define both mappings:

```
original feasible solution -> reduced feasible solution
reduced feasible solution  -> reconstructed original solution
```

Show preservation of feasibility and objective in both directions. Check capacities, integrality, direction, indexing, duplicate handling, and reconstruction rather than relying on the name of a standard reduction.

## 3. State and falsify the proof obligation

Choose the proof shape that matches the method:

- **Greedy:** feasibility plus an exchange, cut, or stays-ahead argument. A plausible priority rule is not a proof.
- **DP:** state meaning, base cases, exhaustive and non-overlapping transitions, induction order, optimum preservation, and reconstruction.
- **Graph reduction:** both solution mappings plus objective preservation; verify capacities, integrality, and edge direction.
- **Binary search:** monotone predicate, boundary convention, termination, and constructive witness when required.
- **Invariant-based construction:** initialization, preservation by every operation, progress, termination, and output conversion.
- **Randomized exact:** distinguish Las Vegas correctness from one-sided or two-sided error; bound error probability and runtime tails.

Turn every critical premise into a tiny adversarial or exhaustive test where practical. When brute force disagrees, minimize the counterexample and identify the first violated premise before changing implementation details.

## 4. Establish constructive correctness

When many outputs are accepted but not scored, model construction as invariant-preserving decisions. Prefer representations that make duplicates, overlap, disconnectedness, or capacity violations impossible.

Useful patterns include:

- build a spanning, tree, path, or assignment backbone before optional structure;
- satisfy the most constrained object first;
- use Hall, cut, degree, parity, or conservation conditions to detect impossibility;
- reserve slack explicitly instead of consuming all capacity greedily;
- canonicalize symmetric choices to simplify proof and testing;
- validate final serialization independently from the internal structure.

A promise that the input is feasible does not prove that the chosen construction reaches a solution. Prove progress and termination under every legal input.

Do not pass the model checkpoint until the operational contract, state/reduction, and applicable proof obligation are either established or isolated as the concrete unresolved cause.

## 5. Establish the operation and memory envelope

Extract from the actual bounds:

```
number of states or objects
branching and transitions per state
number of test cases or instances
bytes per state, edge, table entry, cache, parent, and copy
I/O, initialization, clearing, reconstruction, and serialization cost
official time, memory, language, and library constraints
```

Use worst-case bounds for correctness and representative pilots for constants. Account for bitset word count, hash/map constants, allocator traffic, recursion, cache locality, repeated clearing, and total cost across all cases. A mathematically smaller Big-O method can lose on constants or memory bandwidth, but empirical speed does not rescue a method whose worst case violates the contract.

For bounded exponential methods, estimate the actual remaining exponent:

```
raw variables -> forced decisions -> components -> symmetry classes
-> kernel size -> meet-in-the-middle split -> remaining states
```

Do not infer hardness from the raw Cartesian search space. Constraints may expose flow or matching structure, total unimodularity, matroids, intervals, convexity, small parameters, separators, bounded treewidth, or independent components.

## 6. Classify admissible routes

Use contract, proof, and resource evidence to distinguish:

- **Exact:** a complete worst-case method fits with adequate time and memory margin.
- **Constructive:** an invariant-preserving legal witness is sufficient and no optimization is required for acceptance.
- **Exact hybrid:** decomposition, bounds, relaxations, or subsolvers preserve overall completeness.
- **Heuristic:** non-optimal output is permitted and no complete route fits with credible margin.
- **Scored hybrid:** heuristic global decisions are combined with bounded exact subproblems.

For exact-output tasks, an incomplete search is not converted into an exact algorithm by performing well on samples. Every pruning rule, timeout, decomposition, and subsolver must preserve completeness.

For each credible exact or exact-hybrid candidate, record:

```
state/object count and transition count
worst-case time with test-count and reconstruction factors
peak memory in bytes, including parents and allocator overhead
required reductions, structural promises, and proof obligations
implementation and validation risk
resource margin under the target toolchain
```

Reject or revise a route when completeness depends on unproved compression, unsafe dominance, unguaranteed average-case behavior, unavailable solver/library support, or a resource estimate without margin. When several exact candidates remain plausible, compare representative dominant kernels, but keep worst-case feasibility authoritative.

## 7. Select the downstream method family

After the admissible class is fixed, read [technique selection](../../references/technique-selection.md) for DP, graph, algebra, geometry, string, decomposition, bounded-exponential, general-solver, or data-structure families. Do not use that catalog to bypass an unresolved model or feasibility contradiction.

When complete exact work does not fit, do not force an incomplete method if the contract requires an exact answer. Revisit missing structure or record that no justified complete route is currently known. When non-optimal output is explicitly allowed, retain hard validity and a guaranteed-valid fallback when early termination could erase all value.

For heuristic or scored-hybrid mechanics, read the shared [heuristic search](../../references/heuristic-search.md). If a verified legal champion already meets the plateau admission gate, use [plateau escape](../plateau-escape/SKILL.md) before another tuning sequence.

## 8. Design exact and scored hybrids

"Hybrid" describes composition, not a relaxation of the output contract. Exact-hybrid examples include admissible bounds inside complete branch-and-bound, exact component decomposition with exact coupling, and relaxation bounds used only for certified pruning.

When approximation is allowed, common scored hybrids include:

```
heuristic global order + exact local scheduling
heuristic destroy set + exact DP/matching/flow repair
exact solution on small components + heuristic coupling
candidate generation + exact selection/assignment
```

For each exact subproblem, quantify its size, solve cost, call frequency, cache reuse, timeout behavior, and boundary coupling. Bound variable work so one hard subsolve cannot consume the release budget. Verify that the local objective aligns with the global true score and that splicing preserves every cross-boundary constraint.

## 9. Produce one model-and-route record

Keep a single handoff rather than separate modeling and feasibility reports:

```
entry mode and decisive failure evidence
operational contract and disputed interpretation
trusted model, state, reduction, and proof obligation
smallest counterexample or remaining unproved premise
Candidate A: O(...), ... MB; accepted/rejected because ...
Candidate B: O(...), ... MB; accepted/rejected because ...
chosen route: exact / constructive / exact hybrid / heuristic / scored hybrid
critical structural, evaluator, and resource assumptions
oracle, bound, compiler pilot, or evaluator evidence actually used
next routed document/sub-skill and its exact question
```

Proceed only from the established checkpoint. Reopen the model when new correctness evidence contradicts it; reopen route choice when a bound, environment fact, or method premise changes materially.
