---
name: stochastic_interpolant_objectives
description: Compute stochastic-interpolant velocity, denoiser, and score objective diagnostics from sampled tuples without evaluating densities.
---

# Stochastic Interpolant Objectives

Use this skill when a recovery needs the paper's quadratic learning signals for velocity, denoiser, or score fields. Do not use it to define endpoint interpolation or to integrate a sampler.

## Inputs

- Velocity targets `dot_x_t` from the interpolant protocol.
- Latent noise `z` and positive interior `gamma` values.
- Predictions for velocity `b_hat` and denoiser `eta_hat`.

## Outputs

- Mean velocity objective from Eq. (2.13).
- Mean denoiser objective from Eq. (2.19).
- Denoiser-derived score values `-eta/gamma` for safe interior times.
- Loss-comparison diagnostics for recovery traces.

## Workflow

1. Compute per-sample velocity terms `0.5*b_hat^2 - dot_x_t*b_hat`.
2. Compute per-sample denoiser terms `0.5*eta_hat^2 - z*eta_hat`.
3. Convert denoiser to score only when `gamma >= min_gamma`.
4. In reduced recovery, compare before/after losses and log parameter updates.

## Validation

Run:

```bash
python scripts/objectives.py --demo
python tests/test_objectives.py
```

## Limitations

The included implementation is scalar/list based for deterministic recovery checks. Neural parameterizations can reuse the same objective formulas with tensor libraries in an isolated environment.
