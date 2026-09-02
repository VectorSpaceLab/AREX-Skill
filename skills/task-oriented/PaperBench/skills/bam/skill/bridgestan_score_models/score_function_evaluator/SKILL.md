---
name: score_function_evaluator
description: Evaluate log density, gradient, Hessian, and finite-difference checks for a Bernoulli-Beta Stan score-model proxy in unconstrained coordinates.
---

# Score Function Evaluator

Use this skill to exercise BridgeStan-like score-model access on the Bernoulli recovery proxy. It consumes a Stan contract and transform adapter rather than inventing an unrelated objective.

## Inputs
- Contract JSON from `stan_model_contract`.
- Observation data JSON with binary `y` values.
- Unconstrained scalar parameter value.
- Optional path to the transform adapter script.

## Outputs
- JSON with log density, gradient, Hessian, finite-difference diagnostics, and pass/fail checks.

## Workflow
1. Confirm the contract contains a bounded scalar `theta` and Bernoulli likelihood.
2. Convert unconstrained `z` to constrained `theta` using the transform adapter.
3. Evaluate the Bernoulli likelihood with Beta(1,1) prior and the transform Jacobian.
4. Compute analytic gradient and Hessian in `z`.
5. Cross-check the derivatives with central finite differences before accepting the result.

## Validation
Run `python tests/test_score_evaluator.py` from this skill directory.

## Limitations
This is a recovery proxy for the score-model mechanism, not a replacement for full BridgeStan compilation or real Stan autodiff.
