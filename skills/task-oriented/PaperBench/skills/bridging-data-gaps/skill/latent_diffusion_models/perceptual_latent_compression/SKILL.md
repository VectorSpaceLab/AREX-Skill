---
name: perceptual_latent_compression
description: Validate LDM autoencoder latent compression contracts, spatial downsampling, regularization metadata, and reconstruction diagnostics.
---

# Perceptual Latent Compression

Use this skill when a task needs the first-stage latent representation contract from Latent Diffusion Models. It is appropriate for planning or validating LDM training, sampling, or recovery experiments. Do not use it to claim that a production perceptual autoencoder has been trained or loaded; the script validates contracts and reduced-proxy metadata only.

## Inputs

- Image height, width, and RGB channel count.
- Downsampling factor `f`, preferably one of the mild LDM factors such as 4 or 8.
- Latent channel count.
- Regularization mode: `kl`, `vq`, or `none` for declared proxies.
- Optional reconstruction diagnostics supplied by the caller.

## Outputs

- Latent grid dimensions and latent shape.
- Compression ratio and spatial reduction.
- Warnings for pixel-space operation, aggressive compression, or proxy regularization.
- Validation errors for invalid shapes or unsupported modes.

## Workflow

1. Confirm the input is an RGB image tensor contract.
2. Confirm height and width are divisible by the downsampling factor; reject or require explicit caller-side padding before claiming a latent shape.
3. Compute latent height, width, and channel dimensions only after divisibility is valid.
4. Record regularization mode without inventing training evidence.
5. Forward only the latent contract to diffusion or recovery modules.
6. Treat deterministic pooling or shape-only encoders as reduced proxies.

## Validation

Run `python scripts/latent_contract.py --height 16 --width 16 --channels 3 --factor 4 --latent-channels 3 --regularization none` and execute `python tests/test_latent_contract.py` or the Distiller skill validator with `--run-tests`.

## Limitations

This skill does not load paper checkpoints, compute real FID, or train the autoencoder. Full reconstruction quality requires real autoencoder weights and dataset metrics.
