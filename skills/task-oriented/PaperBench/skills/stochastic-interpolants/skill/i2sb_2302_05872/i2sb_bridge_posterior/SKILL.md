---
name: i2sb_bridge_posterior
description: Compute the analytic Gaussian bridge posterior q(Xt | X0, X1) for I2SB paired clean/degraded endpoints.
---

# I2SB Bridge Posterior

Use this skill when implementing or checking I2SB training data construction from paired clean and degraded samples. Do not use it for ordinary diffusion noising to Gaussian noise; the terminal endpoint is the degraded paired sample `X1`.

## Inputs

- Clean endpoint `x0` as a scalar or vector.
- Degraded endpoint `x1` with the same shape.
- Time `t` in `[0, 1]`.
- Positive constant beta, or precomputed accumulated variances.
- Optional seed or explicit standard-normal noise for reproducible sampling.

## Outputs

- `sigma2_t`, `barsigma2_t`, posterior mean, posterior variance.
- Optional posterior sample `xt`.

## Workflow

1. Validate endpoint shapes and time bounds.
2. Compute accumulated variances: for constant beta, `sigma2_t = beta * t` and `barsigma2_t = beta * (1 - t)`.
3. Compute the posterior mean using variance weights from I2SB Equation (11).
4. Compute covariance `sigma2_t * barsigma2_t / (sigma2_t + barsigma2_t)`.
5. Add seeded Gaussian noise only when a sample is requested.

## Validation

Run:

```bash
python scripts/bridge_posterior.py --demo
python tests/test_bridge_posterior.py
```

## Limitations

This skill implements the scalar/vector contract for recovery and validation. Image tensors use the same broadcasted formulas but require external array/tensor containers.
