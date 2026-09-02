---
name: deep_ritz_stochastic_quadrature_sampling
description: Generate stochastic interior and boundary quadrature samples for Deep Ritz variational PDE training.
---

# Deep Ritz Stochastic Quadrature Sampling

## When To Use

Use this skill when implementing a Deep Ritz or variational neural PDE experiment that needs Monte Carlo estimates of domain and boundary integrals. Do not use it for fixed-grid finite differences or finite elements.

## Inputs

- `dimension`: positive integer spatial dimension.
- `lower`, `upper`: scalar hypercube bounds.
- `interior_count`: number of interior samples.
- `boundary_count`: number of boundary samples.
- `seed`: optional deterministic seed.

## Outputs

- Interior points inside `[lower, upper]^dimension`.
- Boundary points with at least one coordinate fixed to a lower or upper face.
- Face metadata for each boundary point.

## Workflow

1. Use fresh random interior points for each training iteration.
2. Sample boundary faces uniformly across dimensions and low/high sides.
3. Use simple batch means as equal-weight Monte Carlo quadrature estimates.
4. Use fixed seeds only for validation, tests, and reproducible reduced recovery.

## Validation

Run:

```bash
python tests/test_sampler.py
```

## Limitations

The helper targets hypercube domains, matching the paper's high-dimensional Poisson recovery. L-shaped domains require a custom rejection sampler.
