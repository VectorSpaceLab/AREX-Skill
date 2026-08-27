# Tiled VAE Workflows

## Purpose

Use this reference to configure Tiled VAE and explain how its options affect memory, speed, and quality.

## What Tiled VAE changes

Tiled VAE decomposes VAE encoder/decoder execution into tile task queues. It estimates or aggregates GroupNorm statistics across tiles, processes tiles in a memory-aware order, and writes cropped valid regions into the final tensor. This targets VAE memory pressure, not UNet/sampler tile denoising.

## Basic workflow

1. Enable **Tiled VAE** in txt2img or img2img.
2. Leave **Move VAE to GPU** enabled when GPU memory allows; if the VAE is on CPU and a CUDA device is available, the extension warns that checking this can help.
3. Start from the recommended encoder/decoder tile sizes.
4. Keep **Fast Encoder** and **Fast Decoder** enabled for speed unless quality/color or NaN issues suggest otherwise.
5. Use **Fast Encoder Color Fix** when fast encoder color drift is more important than maximum speed.
6. If VAE OOM persists, lower decoder tile size first for decode failures and encoder tile size for img2img encode failures.

## Recommended tile-size defaults

The extension chooses defaults from detected CUDA memory when CUDA is available. These are source-level defaults, not universal optima.

### Encoder tile size

| Device memory signal | Default encoder tile size |
| --- | --- |
| CPU or non-CUDA path | 512 |
| CUDA, <= 8 GB | 960 |
| CUDA, > 8 GB | 1536 |
| CUDA, > 12 GB | 2048 |
| CUDA, > 16 GB | 3072 |

### Decoder tile size

| Device memory signal | Default decoder tile size |
| --- | --- |
| CPU or non-CUDA path | 64 |
| CUDA, <= 8 GB | 64 |
| CUDA, > 8 GB | 96 |
| CUDA, > 12 GB | 128 |
| CUDA, > 16 GB | 192 |
| CUDA, > 30 GB | 256 |

## Fast mode behavior

Fast mode estimates GroupNorm parameters from a downsampled representation, then uses those estimates across tiles. This avoids heavier CPU/RAM/GPU transfers.

- **Fast Decoder**: faster VAE decode when quality is acceptable.
- **Fast Encoder**: faster VAE encode for img2img/input images.
- **Fast Encoder Color Fix**: a semi-fast path that estimates GroupNorm before downsampling to reduce color shifts.

Disable fast mode when output artifacts, color shift, or NaNs appear and a slower but more conservative path is acceptable.

## Attention optimization compatibility

Tiled VAE delegates VAE attention blocks to a helper that mirrors WebUI attention optimization methods. Recognized method names include:

- `none`
- `sdp-no-mem`
- `sdp`
- `xformers`
- `sub-quadratic`
- `v1`
- `invokeai`
- `doggettx`

Unknown methods print a warning and fall back to the basic attention path. For attention-related failures, confirm WebUI's selected optimization and optional packages such as xFormers.

## Validation signals

A healthy Tiled VAE run should print messages such as:

- input size, tile size, and padding;
- split grid count and optimal tile size;
- task queue execution progress;
- completion time and peak VRAM allocation when CUDA stats are available.

If the input is small, the extension may correctly print that it is tiny and unnecessary to tile.
