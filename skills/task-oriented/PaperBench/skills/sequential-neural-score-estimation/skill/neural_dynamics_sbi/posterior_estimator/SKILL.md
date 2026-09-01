---
name: posterior_estimator
description: Fit a conditional Gaussian posterior surrogate from simulated summary/parameter pairs without likelihood evaluations.
---

# Conditional Posterior Estimator

Use this skill when simulated pairs `(summary, theta)` are available and the task is to approximate `p(theta | observed_summary)` for an SNPE-style recovery. Do not use it when exact likelihood evaluation is required.

## Inputs
- `summaries`: list of summary vectors.
- `parameters`: list of parameter vectors paired with summaries.
- `observed_summary`: summary vector for the observation.
- Optional ridge regularization and posterior sample count.

## Outputs
- Posterior mean vector.
- Residual variance uncertainty proxy.
- Deterministic posterior samples.
- Diagnostics showing simulation count and no likelihood use.

## Workflow
1. Fit ridge-regularized linear maps from summary features to parameter dimensions.
2. Estimate residual variance from simulated pairs.
3. Predict the posterior mean for the observed summary.
4. Draw deterministic Gaussian samples for downstream posterior predictive checks.

## Validation
Run `python tests/test_posterior_estimator.py` from this skill directory.

## Limitations
This is a transparent reduced surrogate for recovery validation, not a full neural density estimator such as an MDN or normalizing flow.
