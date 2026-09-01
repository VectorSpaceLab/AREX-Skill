---
name: imagenet_c_corruption_protocol
description: Apply ImageNet-C-style common image corruptions with five severity levels and reproducible metadata for robustness experiments.
---

# ImageNet-C Corruption Protocol

Use this skill when a task needs a bounded, reproducible version of the ImageNet-C corruption protocol for arrays or lightweight image fixtures. Do not use it for adversarial perturbations, training-time augmentation claims, or full ImageNet-C scoring unless the real ImageNet-C assets are available.

## Inputs

- Image-like numeric arrays shaped as height x width x channels with values in `[0, 1]`.
- `corruption`: one of `gaussian_noise`, `shot_noise`, `defocus_blur`, `brightness`, `contrast`, `pixelate`, or `jpeg_compression_proxy`.
- `severity`: integer from 1 to 5.
- Optional integer `seed` for stochastic corruptions.

## Outputs

- Corrupted image with the same shape and value range.
- Metadata containing corruption name, severity, seed, and distortion summaries.

## Workflow

1. Validate shape, severity, and corruption name.
2. Map the severity to a fixed distortion strength.
3. Apply the corruption without changing labels.
4. Clip the result into `[0, 1]` and preserve shape.
5. Record distortion metadata for downstream mechanism checks.

## Validation

Run:

```bash
python tests/test_corruption_protocol.py
```

## Limitations

This skill is mechanism-faithful for reduced recovery but is not a byte-identical implementation of every ImageNet-C corruption. Full benchmark claims require the official ImageNet-C data or exact generation pipeline.
