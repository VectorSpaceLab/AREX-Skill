---
name: wanda_row_pruning
description: Compute row-wise Wanda pruning scores, masks, and pruned weights without any weight update.
---

# Wanda Row Pruning

Use this skill to prune a linear layer with the Wanda rule: score each weight by `abs(W_ij) * activation_norm_j`, compare scores only within the same output row, and zero the lowest-scoring weights. Do not use it when the experiment requires global layer-wise magnitude thresholds.

## Inputs
- Weight matrix shaped `[output_channels][input_channels]`.
- Activation norm vector with one entry per input channel.
- Unstructured sparsity ratio in `[0, 1)`.

## Outputs
- Boolean prune mask where `true` means the weight is removed.
- Pruned weight matrix with masked entries set to zero.
- Score matrix and exact sparsity metadata.

## Workflow
1. Validate the activation vector length against the matrix width.
2. Compute scores by multiplying every row of `abs(W)` by the activation norms.
3. For each output row, deterministically select the lowest `floor(width * sparsity_ratio)` scores.
4. Set only masked weights to zero; never alter unmasked values.

## Validation
The tests include an outlier-channel case where Wanda keeps a low-magnitude but high-activation weight that magnitude pruning removes.

## Limitations
This skill handles one dense matrix. Model traversal and calibration capture are separate modules.
