---
name: parameter_transform_adapter
description: Apply scalar Stan-style constrained and unconstrained transforms with support checks and log-Jacobian values for bounded real parameters.
---

# Parameter Transform Adapter

Use this skill when a Stan parameter contract must be converted between constrained model coordinates and unconstrained inference coordinates. Do not use it to evaluate likelihoods or gradients.

## Inputs
- Parameter contract containing `name`, `lower`, and `upper`.
- Numeric value in constrained or unconstrained coordinates.

## Outputs
- JSON-compatible result with mapped value, validity, diagnostic message, and log absolute Jacobian.

## Workflow
1. Load or define the scalar parameter contract.
2. Use `scripts/parameter_transforms.py` for `constrain`, `unconstrain`, and `roundtrip` operations.
3. Reject constrained values outside support instead of silently clipping.
4. Pass only valid transformed values to score-model evaluators.

## Validation
Run `python tests/test_parameter_transforms.py` from this skill directory.

## Limitations
This skill supports univariate finite-interval real parameters, which is sufficient for the Bernoulli recovery proxy. Extend it before applying to vectors, simplexes, ordered vectors, or covariance matrices.
