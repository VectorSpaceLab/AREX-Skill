---
name: two_loop_direction
description: Compute L-BFGS search directions with the two-loop inverse-Hessian recursion and scalar scaling.
---

# Two-Loop Direction

Use this skill when an optimizer has L-BFGS curvature memory and needs a quasi-Newton descent direction without materializing a Hessian matrix. Do not use it when curvature pairs fail the positive-curvature condition.

## Inputs
- Current gradient vector.
- Ordered correction memory `(s_i, y_i)` from oldest to newest.
- Optional scalar initial inverse-Hessian scale.

## Outputs
- Search direction `p = -H g`.
- Diagnostics with pair count, effective scale, and descent dot product.

## Workflow
1. Run the first loop from newest pair to oldest and store alpha values.
2. Apply scalar initial scaling; use the newest pair scale `(s^T y)/(y^T y)` when none is supplied.
3. Run the second loop from oldest pair to newest.
4. Negate the resulting inverse-Hessian product.
5. Verify the result is a descent direction on convex positive-curvature tests.

## Validation
Run `python tests/test_two_loop_direction.py` or use the generated skill tree validator with tests enabled.

## Limitations
The skill computes directions only; it does not update memory or perform line search.
