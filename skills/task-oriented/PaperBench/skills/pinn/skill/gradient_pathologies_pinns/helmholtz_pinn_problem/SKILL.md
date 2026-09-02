---
name: helmholtz_pinn_problem
description: Construct deterministic reduced Helmholtz PINN benchmark data with analytic solution, boundary samples, collocation samples, forcing, and relative L2 scoring.
---

# Helmholtz PINN Problem

Use this skill when a recovery experiment needs a small but mechanism-faithful 2D Helmholtz problem for physics-informed neural network training. Do not use it for generic regression tasks that lack a PDE residual and boundary/data-fit conflict.

## Inputs

- Domain bounds, usually `[-1, 1] x [-1, 1]`.
- Interior, boundary, and evaluation sample counts.
- Analytic parameters `a1`, `a2`, and Helmholtz coefficient `k`.
- A deterministic random seed.

## Outputs

- Interior collocation points.
- Boundary points and exact boundary values.
- Evaluation points and exact solution values.
- A forcing callback for `u_xx + u_yy + k^2 u = q`.
- Relative-L2 scoring helper.

## Workflow

1. Define an analytic solution such as `sin(a1*pi*x) * sin(a2*pi*y)`.
2. Derive the Helmholtz forcing from second derivatives of that solution.
3. Sample collocation points inside the square and boundary points on all sides.
4. Evaluate exact values on the boundary and evaluation grid.
5. Use relative L2 to compare predictions with exact values.

## Validation

Run `python scripts/helmholtz_problem.py --self-test` or validate the skill tree with tests enabled.
