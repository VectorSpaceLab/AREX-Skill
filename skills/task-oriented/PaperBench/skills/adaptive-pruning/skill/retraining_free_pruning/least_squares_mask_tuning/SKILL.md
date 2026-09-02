---
name: least_squares_mask_tuning
description: Tune surviving pruning mask coefficients with damped least squares for activation reconstruction.
---

# Least Squares Mask Tuning

Use this skill for the paper's final post-training pruning stage, after a binary structured mask has been selected and rearranged. It tunes only surviving mask entries to reconstruct original layer activations. Do not use it as model-weight retraining, and never revive pruned entries.

## Inputs

- Matrix `A` of per-unit activation contributions.
- Target vector `b` for reconstruction.
- Binary keep mask.
- Damping and acceptable coefficient range.

## Outputs

A real-valued mask, baseline/tuned reconstruction errors, and an accepted flag. Pruned entries remain zero.

## Workflow

Restrict `A` to kept columns, solve damped normal equations, insert the coefficients into the full mask, and reject coefficients outside the range. Report whether reconstruction error improved.

## Validation

Run the included deterministic synthetic tests.
