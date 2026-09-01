---
name: periodic_pde_benchmark
description: Build deterministic periodic PDE benchmarks for PINN failure-mode recovery experiments.
---

# Periodic PDE Benchmark

Use this skill when a recovery or evaluation task needs a small synthetic PDE benchmark matching the PINN failure-mode paper. Do not use it for unrelated PDE families or as evidence of full paper-scale reproduction.

## Inputs
- PDE system and coefficients, currently convection for deterministic reduced recovery.
- Grid sizes, collocation count, and random seed.
- Periodic spatial domain and time horizon assumptions.

## Outputs
- A JSON-compatible benchmark with evaluation grid, exact target values, collocation points, boundary pairs, and initial-condition samples.
- Metadata identifying coefficient values and exact/proxy target type.

## Workflow
1. Choose the smallest system that tests the paper mechanism, usually periodic convection.
2. Build `x` and `t` grids on `[0, 2π] × [0, 1]`.
3. Compute `u(x,t)=sin(x-beta*t)` for exact convection targets.
4. Generate seeded collocation points and periodic boundary pairs.
5. Save the benchmark or pass it directly to residual-objective and diagnostics skills.

## Validation
Run `python scripts/benchmark.py --beta 30 --x-points 8 --t-points 4 --collocation-count 5` and run the tests in `tests/`.

## Limitations
This skill provides a reduced exact convection benchmark. Full reaction-diffusion data generation should extend the same contract and declare numerical target provenance.
