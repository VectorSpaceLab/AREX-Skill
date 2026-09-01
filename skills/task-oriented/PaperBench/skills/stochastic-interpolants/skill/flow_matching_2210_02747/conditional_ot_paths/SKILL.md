---
name: conditional_ot_paths
description: Construct and validate Flow Matching conditional optimal-transport paths and target vector fields for paired noise/data samples.
---

# Conditional OT Paths

Use this skill when a recovery or implementation needs the paper's conditional optimal-transport path from a base sample `x0` to a data sample `x1` and the corresponding regression target for Conditional Flow Matching. Do not use it to train a neural network or integrate a CNF; those are separate contracts.

## Inputs

- Equal-length numeric vectors `x0` and `x1`.
- A time `t` in `[0, 1]`.
- `sigma_min` in `(0, 1]` for the OT variance schedule.

## Outputs

- `x_t = (1 - (1 - sigma_min)t) x0 + t x1`.
- `u_t = x1 - (1 - sigma_min) x0`.
- Diagnostics for endpoint consistency, finite values, and target invariance.

## Workflow

1. Validate vector dimensions and scalar ranges before computing path values.
2. Use `scripts/ot_paths.py` to compute `x_t`, `u_t`, and diagnostics.
3. Treat `u_t` as the target for a vector-field regressor; do not modify it with downstream loss weighting.
4. Preserve the distinction between the conditional path sample and the marginal CNF trajectory.

## Validation

Run:

```bash
python tests/test_ot_paths.py
python scripts/ot_paths.py --x0 '[0, 1]' --x1 '[2, 3]' --t 0.5
```

## Limitations

This skill implements the deterministic Gaussian OT-path formulas used for fast proxy validation. It does not estimate marginal vector fields or train image-scale models.

Cycle refinement: invalid times must fail before any recovery harness consumes the path sample.
