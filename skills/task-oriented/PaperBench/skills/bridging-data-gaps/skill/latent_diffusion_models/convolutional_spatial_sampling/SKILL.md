---
name: convolutional_spatial_sampling
description: Compute and validate LDM spatial latent-grid sampling plans for high-resolution and dense conditional tasks.
---

# Convolutional Spatial Sampling

Use this skill when an LDM task needs image-to-latent spatial sizing, dense-conditioning alignment, or bounded sampler metadata. It is useful for text-to-image, inpainting, super-resolution, and recovery planning. Do not use it to compute denoising loss or claim image quality.

## Inputs

- Requested image height and width.
- Autoencoder downsampling factor.
- Optional dense conditioning shape such as mask or low-resolution image dimensions.
- Sampler step count and stochasticity setting.

## Outputs

- Latent grid dimensions.
- Validity status and errors for non-divisible dimensions.
- Conditioning alignment status.
- Bounded sampler plan metadata and warnings.

## Workflow

1. Validate positive image dimensions and downsampling factor.
2. Compute the latent grid only when dimensions divide cleanly by the factor.
3. Check dense conditioning shapes against image-space or latent-space alignment.
4. Bound sampler step counts for recovery experiments.
5. Return a plan that downstream recovery can cite without reading the original repo.

## Validation

Run `python scripts/spatial_plan.py --height 256 --width 512 --factor 8 --steps 20 --output /tmp/spatial.json`. Tests cover valid grids, divisibility errors, mask alignment, and bounded-step warnings.

## Limitations

This skill validates spatial contracts only. It does not run DDIM/PLMS sampling, load UNet weights, or evaluate generated images.
