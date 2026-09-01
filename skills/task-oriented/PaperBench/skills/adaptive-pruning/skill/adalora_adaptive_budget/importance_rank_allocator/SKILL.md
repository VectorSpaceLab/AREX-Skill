---
name: importance_rank_allocator
description: Compute AdaLoRA sensitivity-uncertainty triplet scores and globally mask singular values to a target rank budget.
---

# Importance-Aware Rank Allocator

Use this skill when a recovery or implementation needs AdaLoRA's adaptive rank allocation rather than fixed LoRA ranks.

## Inputs

- A list of adapted matrices with `A`, `E`, `B` parameters and matching gradients.
- Previous EMA state for sensitivity and uncertainty, or empty state for the first step.
- Hyperparameters `beta1`, `beta2`, and target global rank.

## Outputs

- Updated EMA state.
- Per-triplet importance scores.
- Mask threshold and masked singular values.
- Rank pattern for every adapted matrix.

## Workflow

1. Compute instantaneous sensitivity `abs(parameter * gradient)` for every AdaLoRA parameter.
2. Update smoothed sensitivity and uncertainty EMAs.
3. Score each entry with `smoothed_sensitivity * uncertainty`.
4. Combine each triplet as singular-value score plus mean scores from the corresponding `A` row and `B` column.
5. Retain the top target-rank triplets across all matrices and set other singular values to zero.
6. Log rank pattern and threshold so downstream recovery can verify budget compliance.

## Validation

Run `python scripts/rank_allocator.py --self-test` or the provided tests.

## Limitations

This script is deterministic and standard-library only. It is intended as executable mechanism evidence and a reference contract for tensor implementations.
