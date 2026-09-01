---
name: bar_zeroth_order_optimizer
description: Train BAR universal-program parameters with query-only one-sided zeroth-order gradient estimates and SGD updates.
---

# BAR Zeroth-order Optimizer

Use this skill when recovery must optimize adversarial-program parameters against a black-box classifier that exposes only prediction outputs. It is the core BAR training loop from the paper.

Do not use it when white-box gradients are available and the goal is ordinary fine-tuning.

## Inputs

- Black-box prediction callable that accepts programmed samples and returns source probabilities.
- Embedded target samples, labels, mask, and initial program parameters.
- Label mapping from source to target classes.
- Focal-loss parameters, smoothing `beta`, random-vector count `q`, learning rate, iterations, and seed.

## Outputs

- Updated parameters `W`.
- Loss before and after optimization.
- Prediction/accuracy trace.
- Query count and evidence that an optimizer step changed parameters.

## Workflow

1. Evaluate focal loss at current parameters.
2. Draw `q` normalized random directions with a fixed seed when reproducibility matters.
3. Evaluate perturbed losses at `W + beta*U_j` using black-box calls only.
4. Average one-sided gradient estimates and update `W` by SGD.
5. Log losses, query counts, and parameters before/after.

## Validation

Run `python tests/test_bar_optimizer.py` or `validate_skill_tree.py --run-tests`.

## Limitations

This skill can run a reduced deterministic proxy. Full paper-scale results require real source models and target datasets supplied by the caller.
