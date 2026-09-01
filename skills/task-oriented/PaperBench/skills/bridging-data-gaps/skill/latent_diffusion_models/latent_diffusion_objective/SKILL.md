---
name: latent_diffusion_objective
description: Execute and validate a reduced LDM latent noising, epsilon prediction loss, and optimizer-step training primitive.
---

# Latent Diffusion Objective

Use this skill when a recovery or experiment must exercise the core Latent Diffusion Model objective. It is appropriate for full training traces and for declared reduced proxies. Do not use it to claim full checkpoint-based training unless the caller separately proves that the full model and dataset ran.

## Inputs

- A latent value or latent vector.
- Matching Gaussian noise value or vector.
- Timestep and noise schedule metadata.
- A denoiser prediction function or reduced trainable scalar parameter.
- Learning rate for a bounded optimizer step.

## Outputs

- Epsilon-prediction mean-squared error.
- Noised latent metadata.
- Training trace containing `loss_before`, `loss_after`, `params_before`, and `params_after`.
- Mechanism booleans for latent noising, loss computation, reduced training, and optimizer execution.

## Workflow

1. Build `z_t` from latent, noise, and schedule coefficients.
2. Predict epsilon with the supplied denoiser or the deterministic reduced linear denoiser.
3. Compute MSE against the sampled noise.
4. If requested, take a gradient step that changes trainable parameters.
5. Save a validator-compatible trace and never mark full-model training true for a reduced proxy.

## Validation

Run `python scripts/reduced_ldm_step.py --output /tmp/trace.json` and confirm the trace shows parameter movement and loss reduction. The included tests exercise the deterministic update and schema fields.

## Limitations

The reduced script is a mechanism-faithful proxy only. It is not a substitute for large-scale FID reproduction, pretrained autoencoder loading, or multi-step sampler evaluation.
