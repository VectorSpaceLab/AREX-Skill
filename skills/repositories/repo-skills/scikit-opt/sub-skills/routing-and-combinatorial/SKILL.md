---
name: routing-and-combinatorial
description: "Use scikit-opt route and permutation optimizers for TSP-style problems."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# routing-and-combinatorial

Use this sub-skill when a task is about permutation search, TSP-style routing, fixed-endpoint route construction, or other combinatorial route objectives in `scikit-opt` / `sko`.

## Read these bundled files
- `references/api-reference.md` — exact signatures and route-representation notes for `GA_TSP`, `SA_TSP`, `ACA_TSP`, and `IA_TSP`, plus the `function_for_TSP` helper. Read this when you need parameter names or route-state details.
- `references/workflows.md` — how to build a distance matrix, define a route-cost function, handle fixed endpoints, and choose a route optimizer. Read this before solving a routing task.
- `references/troubleshooting.md` — fixes for non-permutation outputs, invalid distance matrices, endpoint handling, plotting extras, and the `PSO_TSP` version-specific failure. Read this when route behavior is confusing.
- `scripts/smoke_routing_algorithms.py` — tiny deterministic CLI smoke for route optimizers using an in-script coordinate fixture. Run this after changes or before handoff.

## Route elsewhere when needed
- Route continuous vectors and constrained real-valued optimization to `continuous-optimizers`.
- Route GA integer/mixed-precision search and custom operators to `genetic-algorithms`.
- Route objective run modes, benchmark functions, and optional GPU acceleration to `objective-functions-and-speedups`.

## Core guidance
- Use a permutation objective that returns the total route cost.
- Build a square distance matrix from coordinates before optimizing.
- Validate that every best route contains each city exactly once.
- Treat `PSO_TSP` as a known version-specific caveat in this release, not as a reliable default route solver.

This sub-skill stays focused on route representation and permutation workflows; the bundled references carry the exact recipes and caveats.
