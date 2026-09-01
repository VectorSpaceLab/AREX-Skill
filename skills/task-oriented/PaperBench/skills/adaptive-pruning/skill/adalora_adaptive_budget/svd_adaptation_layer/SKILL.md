---
name: svd_adaptation_layer
description: Implement AdaLoRA SVD-style low-rank linear updates with frozen base weights and active-rank scaling.
---

# SVD Adaptation Layer

Use this skill when reconstructing or testing AdaLoRA-style parameter-efficient adaptation for a linear layer without depending on the original paper repository.

## Inputs

- Base weight as a row-major matrix `[out_features][in_features]` and optional bias.
- Trainable low-rank state: `A` with shape `[rank][in_features]`, `E` singular values, and `B` with shape `[out_features][rank]`.
- Batch input vectors `[batch][in_features]`, scaling alpha, and active-rank denominator.

## Outputs

- Adapted linear outputs.
- Active rank and update matrix metadata.

## Workflow

1. Treat the base weight as immutable.
2. Count nonzero singular values to determine active rank unless an explicit rank denominator is supplied.
3. Compute the base linear output.
4. Compute the SVD-like update `B @ (diag(E) @ A)` and add `x @ update.T * alpha / active_rank`.
5. If rank is zero or all singular values are zero, return exactly the base linear output.

## Validation

Run `python scripts/svd_layer.py --self-test` or validate the skill tree with `validate_skill_tree.py --run-tests`.

## Limitations

The bundled script uses standard-library arithmetic for deterministic recovery tests. Production model integrations should map this contract to tensor libraries while preserving the same parameter semantics.
