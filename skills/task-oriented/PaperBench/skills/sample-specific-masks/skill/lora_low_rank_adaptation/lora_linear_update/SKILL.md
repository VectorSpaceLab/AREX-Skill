---
name: lora_linear_update
description: Build and train a LoRA linear layer with frozen base weights and low-rank trainable factors.
---

# LoRA Linear Update

Use this skill when implementing the paper's core low-rank adaptation equation for a dense layer. Do not use it to claim full Transformer fine-tuning.

## Inputs
Base matrix `W0`, rank `r`, scaling `alpha`, input/target examples, learning rate, step count.

## Outputs
Forward outputs, loss trace, LoRA factors `A` and `B`, and booleans proving `W0` stayed frozen while `A/B` changed.

## Workflow
1. Validate dimensions and rank.
2. Compute `W0 x + (alpha/r) B A x`.
3. Initialize `A` deterministically and `B` to zero for initial base equivalence.
4. Backpropagate squared-error gradients by hand and update only `A` and `B`.
5. Record loss before and after plus parameter snapshots.

## Validation
Run `python tests/test_lora_linear_update.py` or the Distiller skill validator with `--run-tests`.

## Limitations
This is a mechanism skill, not a replacement for full pretrained language-model training.
