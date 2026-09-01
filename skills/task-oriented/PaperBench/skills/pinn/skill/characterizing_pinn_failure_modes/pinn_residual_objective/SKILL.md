---
name: pinn_residual_objective
description: Compute PINN data, boundary, and PDE residual losses for reduced failure-mode experiments.
---

# PINN Residual Objective

Use this skill when a recovery harness must exercise the paper's soft PDE-constraint mechanism. Do not replace it with plain supervised error; the residual term is the central object being tested.

## Inputs
- A benchmark object from `periodic_pde_benchmark`.
- A parametric prediction surrogate or model interface.
- PDE coefficient values and residual weight.

## Outputs
- Loss decomposition containing initial-condition, periodic-boundary, residual, and total losses.
- Residual metadata identifying the coefficient used for the PDE operator.

## Workflow
1. Evaluate initial-condition fit against benchmark targets.
2. Evaluate periodic boundary consistency at paired boundary points.
3. Compute convection residual `u_t + beta*u_x` for the chosen surrogate.
4. Combine losses as `initial + boundary + residual_weight * residual`.
5. Return the full decomposition for diagnostics and training traces.

## Validation
Run `python scripts/objective.py <benchmark.json> --speed 1 --beta 30` after creating a benchmark JSON, then run the tests in `tests/`.

## Limitations
The included deterministic script supports analytic sinusoidal convection surrogates. Larger neural PINN implementations should preserve the same loss-field names and residual semantics.
