---
name: scaled_lbfgs_solver
description: Run bounded scaled L-BFGS optimization with two-loop directions, memory updates, and backtracking safeguards.
---

# Scaled L-BFGS Solver

Use this skill to recover a small, executable instance of the Liu-Nocedal L-BFGS mechanism. It is appropriate for smooth unconstrained objectives where gradients are available. It is not a replacement for full historical benchmark reproduction.

## Inputs
- Objective function and gradient function.
- Initial vector, memory limit, iteration count, and tolerance.
- Optional line-search constants.

## Outputs
- Final parameter vector.
- Trace containing objective values, gradient norms, step sizes, memory lengths, and scaling values.
- Mechanism evidence that two-loop recursion, bounded memory, scalar scaling, and optimizer steps ran.

## Workflow
1. Start with empty limited-memory state.
2. Compute the two-loop direction; fall back to steepest descent if needed.
3. Backtrack until Armijo decrease holds.
4. Update parameters and curvature memory.
5. Log loss, gradient norm, scale, and memory length at each iteration.

## Validation
Run `python tests/test_scaled_lbfgs_solver.py`; the deterministic quadratic test must reduce objective and gradient norm.

## Limitations
This skill is a bounded recovery harness component. Full paper-level numerical comparisons require original benchmark definitions that are not available from the resolved page.
