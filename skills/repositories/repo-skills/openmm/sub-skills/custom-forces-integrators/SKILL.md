---
name: custom-forces-integrators
description: "Implement and debug OpenMM custom expression forces,
  CustomIntegrator algorithms, force groups, runtime parameters, tabulated
  functions, and serialization-aware custom systems."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT, GPL, LGPL
---

# Custom Forces and Integrators

Use this sub-skill when the task involves OpenMM `Custom*Force` classes, `CustomIntegrator`, force groups, global/per-element parameter updates, tabulated functions, expression parsing, or smoke-testing a hand-built custom `System`.

## Route Tasks

- For selecting a custom force class, expression variables, parameters, exclusions, cutoffs, interaction groups, tabulated functions, or serialization behavior, read `references/custom-force-api.md`.
- For `CustomIntegrator` algorithms, constraints, random variables, force-group-specific `f0`/`energy0` expressions, MTS patterns, or aMD-style boosts, read `references/custom-integrator-recipes.md`.
- For parse errors, undefined variables, parameter update mistakes, unit/count mismatches, nonbonded double counting, force-group queries, stochastic reproducibility, or serialization failures, read `references/troubleshooting.md`.
- For a quick installed OpenMM sanity check, run `scripts/custom_force_smoke.py`; it builds a two-particle `CustomBondForce` on the Reference platform and asserts finite energy.

## Core Workflow

1. Choose the narrowest `Custom*Force` class that matches the interaction geometry, then write the expression in OpenMM algebra syntax with class-specific variables.
2. Add all global, per-particle, per-bond, per-angle, per-torsion, donor/acceptor, group, or computed parameters before adding interaction records.
3. Ensure every required element count matches the `System` before creating a `Context`; for `CustomNonbondedForce`, add one particle parameter record for every system particle.
4. Prefer `Context.setParameter()` for frequently tuned globals; use `set*Parameters()` plus `updateParametersInContext()` for changed per-element values; reserve `Context.reinitialize()` for topology/count/force-definition changes.
5. Assign force groups deliberately when querying energy pieces, excluding query-only forces from integration, or implementing MTS/custom algorithms.
6. Validate on the `Reference` platform with explicit positions, finite energy/force assertions, and XML serialization round trips when systems must be portable.

## Boundaries

- Use `../force-fields-modeling/` for ForceField XML authoring, template matching, residue modeling, and parameter file selection.
- Use `../platforms-performance/` for CUDA/OpenCL/HIP/CPU/Reference platform selection, precision, determinism, and performance tuning.
- Use `../development-extensions/` for implementing new platform kernels, C++ plugins, or new core OpenMM force classes.
