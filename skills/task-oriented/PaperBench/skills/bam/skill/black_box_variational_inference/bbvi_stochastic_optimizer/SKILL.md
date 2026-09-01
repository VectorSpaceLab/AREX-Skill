---
name: bbvi_stochastic_optimizer
description: Apply stochastic ascent and AdaGrad updates to black-box variational inference gradient estimates while recording parameter-change evidence.
---

# BBVI Stochastic Optimizer

## When To Use

Use this skill to update variational parameters with BBVI gradient estimates. It supports fixed Robbins-Monro-style scalar ascent and diagonal AdaGrad updates from the paper.

Do not use it to compute BBVI gradients or to evaluate predictive likelihood.

## Inputs

- `params`: current variational parameters as a numeric list.
- `gradient`: gradient estimate with the same shape.
- `method`: `scalar` or `adagrad`.
- `learning_rate`: scalar base learning rate.
- `state`: optional AdaGrad accumulator.

## Outputs

- `params_before` and `params_after`.
- `gradient` and `step`.
- `state_before` and `state_after`.
- `optimizer_step_executed` boolean.

## Workflow

1. Validate finite parameters and gradients.
2. For `scalar`, apply `params + learning_rate * gradient`.
3. For `adagrad`, update the squared-gradient accumulator and apply `learning_rate / sqrt(accumulator + epsilon)` per parameter.
4. Return a trace suitable for recovery validation.

## Validation

Run:

```bash
python tests/test_optimizer.py
```

## Limitations

This skill performs ascent. If minimizing a loss, negate the gradient before calling it.
