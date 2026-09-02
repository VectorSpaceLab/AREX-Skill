---
name: rectified_ode_reflow
description: Simulate rectified-flow Euler transport and compute straightness, reflow, and convex transport diagnostics.
---

# Rectified ODE Reflow

Use this skill when a learned rectified-flow velocity field must be integrated or audited for straightness. Do not use it to fit the velocity field.

## Inputs
- Initial samples `z0`.
- Affine velocity parameters compatible with `rectified_velocity_regression`.
- Euler step count.

## Outputs
- Final transported samples.
- Path length and direct endpoint distance.
- Straightness ratio and squared transport cost.

## Workflow
1. Integrate `z <- z + dt * v(z,t)` using Euler steps.
2. Accumulate segment lengths for each sample.
3. Compare accumulated path length with direct endpoint distance.
4. Report one-step and multi-step diagnostics for reduced recovery.

## Validation
Run `python tests/test_ode.py` or the Distiller validator with tests enabled.

## Limitations
The script checks the ODE/reflow mechanism on numeric vectors. Full image quality metrics require a separate heavy runtime that is outside this bounded reduced recovery.
