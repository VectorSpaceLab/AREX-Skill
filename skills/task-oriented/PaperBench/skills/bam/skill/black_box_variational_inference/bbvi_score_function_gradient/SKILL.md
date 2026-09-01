---
name: bbvi_score_function_gradient
description: Compute black-box variational inference score-function ELBO gradient estimates from samples, log-density values, and variational score functions.
---

# BBVI Score-Function Gradient

## When To Use

Use this skill when implementing or auditing the core Black Box Variational Inference estimator from Ranganath, Gerrish, and Blei. It applies when you can sample from `q(z | lambda)`, evaluate `log p(x,z)`, evaluate `log q(z | lambda)`, and compute `grad_lambda log q(z | lambda)`.

Do not use it for pathwise/reparameterization gradients or for optimizer updates.

## Inputs

- `logp`: list of scalar log-joint values, one per sample.
- `logq`: list of scalar variational log-density values, one per sample.
- `score`: list of score values. A one-dimensional list represents one scalar parameter; a two-dimensional list represents sample-by-parameter scores.

## Outputs

- `learning_signal`: `logp - logq` for each sample.
- `gradient_terms`: per-sample score-function gradient terms.
- `gradient_estimate`: Monte Carlo average over samples.
- `diagnostics`: sample count, parameter dimension, and finite-value status.

## Workflow

1. Normalize score arrays to sample-by-parameter shape.
2. Validate matching sample counts and finite numeric values.
3. Compute per-sample learning signals.
4. Multiply each score row by its learning signal.
5. Average across samples to estimate the ELBO gradient.

## Validation

Run:

```bash
python tests/test_score_gradient.py
```

## Limitations

This skill does not reduce estimator variance and does not know model structure. Use a variance-reduction skill for Rao-Blackwellization and control variates.
