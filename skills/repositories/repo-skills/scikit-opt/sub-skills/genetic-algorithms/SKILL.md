---
name: genetic-algorithms
description: "Use scikit-opt GA-family APIs for Gray-coded, elitist, and
  real-coded optimization."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# genetic-algorithms

Use this sub-skill for bounded optimization with `GA`, `EGA`, and `RCGA`, including integer or mixed-precision search, continuation with repeated `run(max_iter)` calls, history extraction, and safe `register()`-based operator swaps.

## Read these bundled files
- `references/api-reference.md` — exact constructor signatures, parameter meanings, result/history fields, and the `GA_TSP` handoff note. Read this when you need precise argument names or return values.
- `references/workflows.md` — which GA-family class to choose, how to continue a run, how to set integer or mixed precision, and when to route problem workflows elsewhere. Read this before planning a solution.
- `references/custom-operators.md` — `SkoBase.register`, operator signatures, built-in `ranking`/`selection`/`crossover`/`mutation` helpers, and a safe custom selection pattern. Read this when replacing defaults.
- `references/troubleshooting.md` — fixes for even-population assertions, objective shape issues, bound/precision mismatches, penalty surprises, custom operator errors, and stochastic convergence. Read this when a run fails or behaves oddly.
- `scripts/smoke_genetic_algorithms.py` — tiny deterministic import-and-run smoke for GA, EGA, RCGA, and `register()` behavior. Run this after changes or before handoff.

## Route elsewhere when needed
- Route DE, PSO, SA, and AFSA continuous optimizers to `continuous-optimizers`.
- Route full TSP or routing workflows to `routing-and-combinatorial`; treat `GA_TSP` only as a handoff marker here.
- Route run-mode, vectorization, cache, multiprocessing, and `GA.to(device)` details to `objective-functions-and-speedups`.

This sub-skill stays small on purpose: the bundled references carry the exact API and workflow detail, while the runtime tree remains self-contained.
