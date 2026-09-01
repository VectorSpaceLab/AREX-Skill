---
name: conditioning_dropout_training
description: Prepare classifier-free diffusion conditioning-dropout batches and tiny denoising training traces for reduced recovery.
---

# Conditioning Dropout Training

Use this skill when implementing classifier-free guidance training logic from Ho and Salimans: a conditional denoiser is also trained unconditionally by replacing labels with a null condition with probability `p_uncond`. Do not use it for classifier-guided methods that require external classifier gradients.

## Inputs
- Labeled examples or synthetic class means.
- `p_uncond` in `[0, 1]`.
- Random seed for deterministic recovery.

## Outputs
- Records containing original label, effective condition, and null/drop counts.
- Optional tiny trainable denoiser parameters and loss trace.

## Workflow
1. Validate `p_uncond` and seed.
2. Replace each condition with `null` independently with probability `p_uncond`.
3. Train or update conditional and unconditional statistics using the effective condition.
4. Record enough counts to prove the joint conditional/unconditional objective ran.

## Validation
Run `python tests/test_conditioning_dropout_training.py` or validate the skill tree with `--run-tests`.

## Limitations
This skill provides mechanism-faithful small-scale utilities. It does not claim full ImageNet diffusion training.
