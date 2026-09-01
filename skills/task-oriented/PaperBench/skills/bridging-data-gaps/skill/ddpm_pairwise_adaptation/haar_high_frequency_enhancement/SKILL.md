---
name: haar_high_frequency_enhancement
description: Extract Haar high-frequency components and compute DDPM-PA high-frequency preservation and detail losses.
---

# Haar High-Frequency Enhancement

Use this skill when implementing the DDPM-PA high-frequency branch. It decomposes images with a Haar transform, forms the paper's high-frequency representation `LH + HL + HH`, computes high-frequency pairwise preservation, and computes high-frequency MSE against target training images.

Do not substitute ordinary pixel MSE for this module. DDPM-PA separates image-level relative-distance preservation from high-frequency detail preservation.

## Inputs

- Source predicted clean images, adapted predicted clean images, and target clean images.
- Images represented as nested lists shaped `[batch, channels, height, width]` with even height and width.
- A callable or script for pairwise KL loss, or the included fallback implementation.

## Outputs

- High-frequency component tensors for each input batch.
- `Lhf`: pairwise KL preservation loss over high-frequency components.
- `Lhfmse`: mean squared error between adapted and target high-frequency components.

## Workflow

1. Validate even spatial dimensions and matching tensor shapes.
2. For each 2x2 block, compute Haar components equivalent to LL, LH, HL, and HH filters.
3. Return `hf = LH + HL + HH` for each block/channel/sample.
4. Compute pairwise KL between source and adapted high-frequency tensors.
5. Compute MSE between adapted and target high-frequency tensors.
6. Record component energies for mechanism checks.

## Validation

Run:

```bash
python scripts/haar_hf.py --smoke
python -m pytest tests
```

Tests confirm constant images have zero high-frequency response, checkerboards have positive response, and losses are finite.

## Limitations

This portable script implements a one-level Haar transform for small recovery tensors. Full training code may use framework convolutions, but should preserve the same component definitions and loss separation.
