---
name: activation_calibration
description: Estimate per-channel activation norms for Wanda outlier-aware pruning from calibration tensors.
---

# Activation Calibration

Use this skill when implementing Wanda-style pruning and you need input-channel activation scales before computing weight importance. Do not use it for methods that compare weights only by magnitude.

## Inputs
- A JSON file containing `batches`, a list of 2D numeric arrays shaped samples/tokens by input channels, or one 2D array.
- Optional norm type: `l2` is the Wanda default.

## Outputs
- `activation_norms`: one non-negative scale per input channel.
- Metadata with channel count, row count, norm type, and outlier-channel ranking.

## Workflow
1. Flatten calibration examples across batch/token rows while preserving the final feature dimension.
2. Compute the selected norm independently for every input channel; Wanda uses L2 because it smoothly captures high-magnitude outlier features.
3. Keep zero-norm channels as zero, not NaN or epsilon-inflated values.
4. Save norms and metadata for the row-pruning skill.

## Validation
Run `python tests/test_activation_calibration.py` or validate the skill tree with `--run-tests`.

## Limitations
This skill estimates scales only; it does not choose prune masks or evaluate perplexity.
