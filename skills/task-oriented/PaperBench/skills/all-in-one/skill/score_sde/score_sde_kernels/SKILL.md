---
name: score_sde_kernels
description: Define Score SDE VE, VP, and sub-VP kernels with reverse and probability-flow drift checks.
---

# Score SDE Kernels

Use this skill when you need the forward perturbation kernels from "Score-Based Generative Modeling through Stochastic Differential Equations" or when a recovery experiment needs reverse-time SDE or probability-flow drift algebra without the original repository.

Do not use this skill as a replacement for a trained score network, FID evaluation, or a full image-generation pipeline. It supplies the deterministic SDE math that other skills can consume.

## Inputs

- `family`: one of `ve`, `vp`, or `subvp`.
- Schedule parameters: `sigma_min` and `sigma_max` for VE; `beta_min` and `beta_max` for VP and sub-VP.
- State values as scalars or lists of floats.
- Time `t` in `[0, 1]`.
- Optional score callback `score_fn(x, t)` for reverse-time or probability-flow drifts.

## Outputs

- Forward drift and diffusion.
- Gaussian marginal mean and standard deviation.
- Prior samples and prior log densities.
- Reverse-time SDE drift `f - g^2 score`.
- Probability-flow ODE drift `f - 0.5 g^2 score`.

## Workflow

1. Instantiate `SDEKernel` from `scripts/sde_kernels.py` with the required family and schedule.
2. Use `sde(x, t)` for forward drift and diffusion.
3. Use `marginal_prob(x0, t)` to perturb data and construct score-matching targets.
4. Use `reverse_drift(x, t, score_fn, probability_flow=False)` for reverse SDE drift.
5. Use `reverse_drift(..., probability_flow=True)` for the probability-flow ODE drift.
6. Save numerical checks in recovery logs when accepting a proxy experiment.

## Validation

Run:

```bash
python scripts/sde_kernels.py --self-test
python tests/test_sde_kernels.py
```

The tests verify VP/sub-VP marginal bounds, VE prior log probability, and the half-correction identity for probability flow.

## Limitations

This skill intentionally uses standard-library math and one-dimensional or vector fixtures. It preserves the paper's SDE contracts, but it does not implement neural architectures, dataset pipelines, or high-resolution image sampling.
