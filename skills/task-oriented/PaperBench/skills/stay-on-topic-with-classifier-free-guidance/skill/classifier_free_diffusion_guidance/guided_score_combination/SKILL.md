---
name: guided_score_combination
description: Compute classifier-free guided diffusion score estimates from conditional and unconditional predictions.
---

# Guided Score Combination

Use this skill when a sampler needs Ho and Salimans classifier-free guidance: `guided = (1+w)*conditional - w*unconditional`. It is not a classifier-gradient implementation.

## Inputs
- Scalar or equal-length vector conditional epsilon estimate.
- Scalar or equal-length vector unconditional epsilon estimate.
- Guidance strength `w`, usually non-negative for fidelity-increasing guidance.

## Outputs
- Guided epsilon estimate with matching shape.
- Audit metadata preserving `w` and formula.

## Workflow
1. Validate shapes and numeric values.
2. Apply `(1+w) * eps_cond - w * eps_uncond`.
3. For `w=0`, confirm the output equals the conditional prediction.
4. Log formula usage for recovery source evidence.

## Validation
Run the included tests or the Distiller skill validator.

## Limitations
The formula depends on a denoiser that was trained with conditioning dropout; by itself it does not train a model.
