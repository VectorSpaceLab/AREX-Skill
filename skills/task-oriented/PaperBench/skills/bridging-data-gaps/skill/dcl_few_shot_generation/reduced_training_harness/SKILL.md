---
name: reduced_training_harness
description: Execute a bounded finite-difference optimizer step for DCL proxy recovery and emit validator-compatible training traces.
---

# Reduced DCL Training Harness

Use this skill only when full GAN training is blocked and soft-mode reduced recovery is allowed. It runs a tiny optimizer step over target feature parameters using the generated DCL loss implementation. Do not mark this as full model training.

## Inputs
- Latent-paired feature batch.
- DCL loss function.
- Learning rate and finite-difference epsilon.

## Outputs
- `loss_before`, `loss_after`, `params_before`, and `params_after`.
- Optimizer-state change evidence.
- Reduced-mode mechanism checks.

## Workflow
1. Flatten target generated features as trainable parameters.
2. Estimate finite-difference gradients of DCL proxy loss.
3. Apply one gradient descent step.
4. Write a trace proving parameters changed and loss decreased.

## Validation
Run `python tests/test_reduced_training_harness.py` from this skill directory.

## Limitations
This skill is a proxy for objective mechanics, not a StyleGAN or discriminator implementation.
