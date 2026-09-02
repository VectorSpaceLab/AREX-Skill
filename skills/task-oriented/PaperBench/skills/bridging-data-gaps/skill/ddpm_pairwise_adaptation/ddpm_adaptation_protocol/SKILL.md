---
name: ddpm_adaptation_protocol
description: Build shared noised DDPM adaptation batches and reconstruct clean-image predictions for source and adapted denoisers.
---

# DDPM Adaptation Protocol

Use this skill when implementing or auditing DDPM-PA style few-shot adaptation. It prepares the shared noised inputs used by a frozen source denoiser and a trainable adapted denoiser, then reconstructs predicted clean images with the paper's Equation 15.

Do not use this skill to compute pairwise KL or high-frequency losses directly; those are separate module contracts. This skill owns only the noising, denoiser-call alignment, reconstruction formula, and metadata needed by downstream losses.

## Inputs

- Clean images as nested Python lists or numeric arrays shaped `[batch, channels, height, width]`.
- `alpha_bar_t` with `0 < alpha_bar_t <= 1`.
- A deterministic noise tensor with the same shape as the image batch, or a caller-controlled seed in higher-level code.
- Source and adapted predicted-noise tensors/callable outputs with the same shape as `x_t`.

## Outputs

- Noised batch `x_t`.
- Reconstructed `source_x0_hat` and `adapted_x0_hat`.
- Metadata including shape and `alpha_bar_t`.

## Workflow

1. Validate that image, noise, and predicted-noise tensors share shape.
2. Compute `x_t = sqrt(alpha_bar_t) * x0 + sqrt(1 - alpha_bar_t) * epsilon`.
3. Reconstruct `x0_hat = (x_t - sqrt(1 - alpha_bar_t) * predicted_epsilon) / sqrt(alpha_bar_t)` for each branch.
4. Pass only tensors and metadata downstream; never update source parameters here.

## Validation

Run:

```bash
python scripts/ddpm_protocol.py --smoke
python -m pytest tests
```

The tests verify deterministic noising and exact reconstruction when predicted noise equals the injected noise.

## Limitations

The script uses standard-library nested-list math for portability. Full diffusion training code may wrap the same formulas in NumPy, PyTorch, or JAX, but must preserve shared `x_t` and branch-aligned reconstruction semantics.
