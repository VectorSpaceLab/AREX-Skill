---
name: masked_sparse_optimizer
description: Apply masked Adam-style sparse updates so only selected per-example unlabeled weights and their optimizer moments change during SSL hyperparameter optimization.
---

# Masked Sparse Optimizer

Use this skill when per-example unlabeled weights are stored globally but only a minibatch subset receives hypergradients. It preserves the paper contract that untouched examples should not have their Adam moments decayed or otherwise modified.

Do not use this skill for dense parameter vectors where every coordinate receives a gradient at every step.

## Inputs
- Weight dictionary keyed by unlabeled example id.
- Gradient dictionary for the selected ids only.
- Optimizer moment state keyed by id.
- Adam hyperparameters and projection bounds.

## Outputs
- Updated weights with selected ids changed and unselected ids untouched.
- Updated moment state only for selected ids.
- Step diagnostics for audit logs.

## Workflow
1. Copy the current weight and optimizer state dictionaries.
2. For each selected id, update first and second moments using Adam recurrences.
3. Apply bias correction, step the selected scalar weight, and project to non-negative values.
4. Leave all unselected ids and moments byte-for-byte unchanged.

## Validation
Run `python tests/test_masked_adam.py` or validate through `validate_skill_tree.py --run-tests`.

## Limitations
This is a scalar per-example optimizer for recovery and skill reuse. It does not replace framework optimizers for dense neural-network parameters.
