---
name: lpips_feature_distance
description: Compute LPIPS-style perceptual patch distances from normalized multi-layer feature differences with optional non-negative calibration weights.
---

# LPIPS Feature Distance

Use this skill when you need a lightweight, auditable implementation of the LPIPS distance mechanism from Zhang et al. 2018, especially for bounded recovery experiments where full pretrained networks may be unavailable.

Do not use it to claim full official LPIPS reproduction unless the feature extractor and learned weights are the real pretrained LPIPS assets. A deterministic proxy extractor must be labeled as proxy.

## Inputs

- Two RGB images or batches as Python lists with shape `N x C x H x W`, `C x H x W`, or `H x W x C`.
- Input range: `minus_one_to_one` or `zero_to_one`.
- Optional non-negative layer weights.
- Optional feature records produced externally; otherwise use the deterministic proxy extractor in `scripts/lpips_distance.py`.

## Outputs

- Scalar distance per image pair.
- Per-layer contribution details for mechanism checks.

## Workflow

1. Normalize image values to the declared `[-1,1]` scale.
2. Build multi-scale proxy features or consume supplied layer features.
3. L2-normalize features across channels per spatial location.
4. Square feature differences for each layer.
5. Apply non-negative calibration weights.
6. Spatially average and sum layer contributions.
7. Record whether the run used proxy or real features.

## Validation

Run:

```bash
python scripts/lpips_distance.py --self-test
python tests/test_lpips_distance.py
```

## Limitations

The bundled script uses standard-library deterministic proxy features. It is mechanism-faithful for reduced recovery but not a replacement for official pretrained AlexNet/VGG/SqueezeNet LPIPS scores.
