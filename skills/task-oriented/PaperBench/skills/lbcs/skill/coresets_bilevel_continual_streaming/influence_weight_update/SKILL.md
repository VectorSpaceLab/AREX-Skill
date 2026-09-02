---
name: influence_weight_update
description: Compute influence-style hypergradients and projected unlabeled weight updates from validation gradients, per-example unsupervised gradients, and a damped Hessian approximation.
---

# Influence Weight Update

Use this skill when implementing the outer loop of per-example SSL weighting. It turns validation gradients and per-example unsupervised gradients into influence-style hypergradients for unlabeled weights.

Do not use this skill for ordinary supervised optimization or for a single global unlabeled scalar unless the experiment explicitly ablates the paper mechanism.

## Inputs
- Validation gradient with respect to the last-layer parameter vector.
- Per-example unsupervised gradients for selected unlabeled examples.
- A positive Hessian diagonal or damped curvature approximation.
- Current non-negative weights and a learning rate.

## Outputs
- Influence hypergradients, one per selected unlabeled example.
- Projected non-negative updated weights.
- Diagnostics showing which examples were upweighted or downweighted.

## Workflow
1. Invert the damped last-layer Hessian approximation elementwise.
2. Compute `- validation_gradient^T H^{-1} unsupervised_gradient` for each selected example.
3. Apply a gradient step to each selected weight and project to zero or above.
4. Return explicit diagnostics rather than hiding sign conventions in the caller.

## Validation
Run `python tests/test_influence.py` or validate through `validate_skill_tree.py --run-tests`.

## Limitations
The script implements a deterministic last-layer/diagonal proxy. Full deep-network recovery should replace the curvature input with an exact last-layer Hessian or a validated Hessian-vector solver.
