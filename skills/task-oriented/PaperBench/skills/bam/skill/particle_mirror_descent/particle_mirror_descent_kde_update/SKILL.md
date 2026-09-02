---
name: particle_mirror_descent_kde_update
description: Use this skill to run the weighted kernel-density Particle Mirror Descent prox update loop with stochastic likelihood factors, normalized weights, Gaussian kernels, and trace logging.
---

# KDE Particle Mirror Descent Update

## When To Use

Use this skill when a Bayesian target has log prior and log likelihood callbacks and the experiment needs a reduced PMD density approximation. Do not use it to define the data protocol or final acceptance metric.

## Inputs

- Prior sampler or prior standard deviation for two-dimensional particles.
- Single-datum log likelihood callback and log prior callback.
- Observations, particle count, iteration count, step size, bandwidth, and seed.

## Outputs

- Final particle locations and normalized weights.
- Gaussian KDE density evaluator on arbitrary points or grids.
- Training trace with stochastic datum indices, ESS, bandwidth, and parameter snapshots.

## Workflow

1. Initialize particles from the prior and equal weights.
2. At each iteration, choose one observation uniformly.
3. Resample from the current KDE by weighted ancestor choice plus Gaussian kernel jitter.
4. Apply exponentiated PMD-style log weights using likelihood, prior, and current-density correction terms.
5. Normalize weights with log-sum-exp and retain trace statistics.
6. Return a density evaluator for downstream total variation and mode metrics.

## Validation

Run:

```bash
python tests/test_kde_update.py
```

## Limitations

This reduced implementation is designed for bounded recovery and mechanism checks. It is not an optimized full-scale PMD implementation for million-sample datasets.
