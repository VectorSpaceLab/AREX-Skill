---
name: msfm_joint_cfm_loss
description: Compute Joint Conditional Flow Matching interpolation, target velocity, loss, and tiny optimizer updates for MSFM recovery.
---

# MSFM Joint CFM Loss

Use this skill when a recovery or test needs the Multisample Flow Matching objective after source-target pairs have been selected by a valid coupling.

Do not use this skill as a full neural ODE implementation; it provides deterministic small-batch objective logic and a tiny linear-vector-field optimizer for bounded recovery.

## Inputs

- Paired source vectors and target vectors with equal length and dimension.
- Time samples in `[0, 1]`, one per pair or a scalar broadcast by the caller.
- Vector-field predictions or linear model parameters.

## Outputs

- Interpolated states `x_t = (1 - t) x0 + t x1`.
- Target velocities `x1 - x0`.
- Mean squared Joint CFM loss.
- Variance proxy over target velocities.
- Optional before/after parameters from a real gradient update.

## Workflow

1. Validate equal pair counts and dimensions.
2. Compute straight-line interpolants and target velocities.
3. Compute mean squared error between predictions and target velocities.
4. For reduced recovery, fit a diagonal affine vector field with one deterministic gradient step.
5. Record loss, parameters, and optimizer-change evidence.

## Validation

Run:

```bash
python scripts/joint_cfm.py --self-test
python tests/test_joint_cfm.py
```

## Limitations

- The optimizer is intentionally tiny and deterministic.
- This skill validates the paper mechanism, not image-scale model capacity.
