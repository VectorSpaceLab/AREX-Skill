---
name: visual_projection_training_step
description: Execute a deterministic tiny projection update that mirrors LLaVA's visual-token to language-token alignment step.
---

# Visual Projection Training Step

Use this skill when a recovery needs executable evidence that the trainable projection matrix mechanism ran. It is appropriate for reduced/proxy experiments when full CLIP/Vicuna training is blocked.

## Inputs
- Numeric visual feature vector.
- Numeric target language embedding vector.
- Initial scalar or matrix parameters.
- Learning rate and number of steps.

## Outputs
A training trace with `loss_before`, `loss_after`, `params_before`, `params_after`, and `optimizer_state_changed`.

## Workflow
1. Compute projected visual features with a linear map.
2. Compute mean squared error against the target language vector.
3. Apply deterministic gradient descent to trainable parameters.
4. Report parameter and loss changes for recovery validation.

## Validation
Run the standard-library tests or the Distiller skill-tree validator.

## Limitations
This script is a tiny mathematical proxy. It does not load CLIP, Vicuna, LLaMA, or real image tensors.
