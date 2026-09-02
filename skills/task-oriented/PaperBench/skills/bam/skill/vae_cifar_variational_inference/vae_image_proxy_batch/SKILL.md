---
name: vae_image_proxy_batch
description: Create deterministic tiny image batches for bounded VAE/AEVB recovery experiments when full image datasets are unavailable or too expensive.
---

# VAE Image Proxy Batch

Use this skill when a VAE recovery needs image-shaped unsupervised observations but must remain bounded. Do not use it to claim full MNIST or CIFAR reproduction; it produces a declared synthetic proxy batch.

## Inputs
- `batch_size`: number of examples, default `8`.
- `height`, `width`: image size, default `8x8`.
- `seed`: deterministic ordering seed.
- Optional output path for JSON.

## Outputs
- JSON with `dataset`, `split`, `seed`, `shape`, `value_range`, `synthetic_proxy`, and `images`; no labels are emitted because the VAE objective is unsupervised.
- Images are nested lists with shape `[batch, 1, height, width]` and values in `[0, 1]`.

## Workflow
1. Select structured binary patterns: bars, diagonals, checkerboards, and squares.
2. Stack examples as single-channel images.
3. Record metadata declaring synthetic reduced-proxy status.
4. Pass the JSON to an AEVB/VAE core step.

## Validation
Run:

```bash
python scripts/create_proxy_batch.py --output /tmp/vae_proxy_batch.json
python tests/test_proxy_batch.py
```

## Limitations
This skill supplies mechanism-faithful image-like data only. It does not download MNIST/CIFAR and does not provide labels.
