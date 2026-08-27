---
name: extractors-and-features
description: "Choose LightGlue-supported feature extractors and validate feature
  dictionaries before matching."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Extractors and feature dictionaries

Use this sub-skill when the task is to choose, configure, or sanity-check LightGlue-compatible local feature extractors, or when a user brings precomputed keypoints/descriptors and needs to format them for matching.

## Start here

1. Pick the feature family and matcher pairing from [references/extractor-reference.md](references/extractor-reference.md).
2. Confirm the feature dictionary keys, shapes, descriptor dimensions, and `scales`/`oris` rules in [references/feature-schema.md](references/feature-schema.md).
3. For a supplied image, run [scripts/inspect_feature_schema.py](scripts/inspect_feature_schema.py) to print the extractor output keys, shapes, dtypes, and validation notes. It defaults to OpenCV SIFT to avoid pretrained model downloads.
4. If something fails, use [references/troubleshooting.md](references/troubleshooting.md) before changing model families or SIFT backends.

## Router boundaries

- Complete image-pair matching, `match_pair`, visualization of matches, and extracting matched coordinates route to [../image-pair-matching/SKILL.md](../image-pair-matching/SKILL.md).
- `LightGlue` thresholds, adaptivity, `filter_threshold`, `depth_confidence`, `width_confidence`, FlashAttention, `torch.compile`, and raw matcher output interpretation route to [../matcher-configuration/SKILL.md](../matcher-configuration/SKILL.md).
- Benchmarking, latency plots, pruning plots, and visualization helper details route to [../performance-and-visualization/SKILL.md](../performance-and-visualization/SKILL.md).

## Critical operating facts

- The package exports `SuperPoint`, `DISK`, `ALIKED`, `SIFT`, `DoGHardNet`, `LightGlue`, and `match_pair`.
- Supported pretrained matcher presets are feature-specific: `superpoint`, `disk`, `aliked`, `sift`, `doghardnet`, plus `raco-aliked` for compatible 128-D precomputed features.
- `SuperPoint`, `DISK`, `ALIKED`, `DoGHardNet`, and feature-specific `LightGlue` matchers may download pretrained weights on first use. The default SIFT extractor path is the offline-safe choice when OpenCV exposes SIFT.
- `SIFT` and `DoGHardNet` features require `scales` and `oris` in addition to `keypoints`, `descriptors`, and `image_size` when used with their pretrained matcher presets.

## Minimal feature workflow

```python
from lightglue import SIFT
from lightglue.utils import load_image

image = load_image("image.jpg")
extractor = SIFT(max_num_keypoints=1024).eval()
features = extractor.extract(image, resize=1024)
print(features.keys())  # keypoints, descriptors, image_size, scales, oris, usually keypoint_scores
```

For precomputed descriptors, validate the exact schema in [references/feature-schema.md](references/feature-schema.md) before calling any matcher.
