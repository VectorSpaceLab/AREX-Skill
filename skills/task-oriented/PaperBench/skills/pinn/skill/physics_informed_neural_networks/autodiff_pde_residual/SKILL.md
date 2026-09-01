---
name: autodiff_pde_residual
description: Compute Burgers-style PINN residual values and derivative diagnostics from differentiable or analytic surrogate predictions.
---

# Automatic Differentiation PDE Residual

Use this skill when a recovery harness needs the physics residual that turns a neural surrogate into a PINN. It is designed for Burgers-equation reduced recovery and can also serve as a template for other PDE residual builders. Do not use it to create data items or perform optimizer steps.

## Inputs
- A surrogate with analytic derivative methods or a differentiable backend wrapper.
- Collocation coordinates with `t` and `x` values.
- PDE coefficients, especially Burgers viscosity `nu`.

## Outputs
- Residual values for each collocation point.
- Diagnostic derivatives `u`, `u_t`, `u_x`, and `u_xx`.
- Mean-squared residual loss helper for training objectives.

## Workflow
1. Evaluate the surrogate at each collocation point.
2. Compute time and spatial derivatives using the available differentiable interface.
3. Assemble `u_t + u * u_x - nu * u_xx`.
4. Return residuals and diagnostics separately so recovery can log mechanism evidence.

## Validation
Run `python tests/test_residual.py` or validate the tree with `validate_skill_tree.py --run-tests`.

## Limitations
The included script uses an analytic tiny surrogate for deterministic reduced recovery. Full automatic differentiation backends can wrap the same residual contract when available.
