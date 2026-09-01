---
name: reduced_recovery_evaluation
description: Run bounded reduced Helmholtz PINN recovery with optimizer updates, lambda traces, relative L2 metrics, and validator-compatible evidence.
---

# Reduced Recovery Evaluation

Use this skill for soft-mode recovery when full legacy TensorFlow PINN training is blocked but a mechanism-faithful reduced experiment is allowed. It must execute real parameter updates and record gradient-statistic annealing evidence.

## Inputs

- Problem builder and loss modules.
- Trainable model implementation.
- Annealing policy.
- Step count, learning rate, and random seed.
- Output directory for recovery artifacts.

## Outputs

- Training trace with `params_before`, `params_after`, losses, lambdas, and metrics.
- Recovery result containing numeric relative-L2 metrics.
- Mechanism checks for residual loss, boundary loss, adaptive lambda, and optimizer execution.

## Workflow

1. Build a deterministic Helmholtz problem.
2. Initialize a small trainable model.
3. Evaluate relative L2 before training.
4. Compute separated losses and finite-difference gradients.
5. Update lambda from gradient statistics and perform optimizer steps.
6. Evaluate relative L2 after training and write JSON artifacts.

## Validation

Run a recovery harness that imports this skill and then run the Distiller recovery experiment validator.
