---
name: policy_gradient_outer_update
description: Apply the score-function outer update for probabilistic bilevel coreset selection without implicit differentiation.
---

# Policy Gradient Outer Update

Use this skill when a sampled coreset has been trained in an inner loop and an outer validation loss is available. It implements the paper's policy-gradient estimator and then delegates feasibility to capped-simplex projection.

Do not use this skill for backpropagating through the inner optimizer, Hessian inverse approximations, or greedy subset addition. Its contract is specifically the forward-loss score-function update from Equation (6).

## Inputs
- Current probabilities `s`.
- Sampled binary mask `m` from the same probabilities.
- Scalar validation or outer loss.
- Learning rate `eta`.
- Coreset budget `K`.

## Outputs
- Feasible updated probabilities.
- Raw pre-projection values.
- Score-function gradient diagnostics.

## Workflow
1. Import or otherwise use the mask-relaxation score gradient.
2. Multiply the score gradient by the observed outer loss.
3. Take a descent step on probabilities.
4. Project the result with the capped-simplex projection.
5. Log diagnostics so recovery can prove the generated skills were exercised.

## Validation
Run `python tests/test_policy_update.py` or validate the skill tree with tests enabled. The tests confirm finite gradients, probability movement, and post-update feasibility.

## Limitations
The update quality depends on the caller's inner-training and validation-loss computation. This skill intentionally does not own model training.
