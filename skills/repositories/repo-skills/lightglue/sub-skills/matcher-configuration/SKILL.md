---
name: matcher-configuration
description: "Configure and call LightGlue directly on feature dictionaries and
  precomputed descriptors."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# LightGlue matcher configuration

Use this sub-skill when the task is about the direct matcher API rather than image loading, extractor selection, or plotting: `LightGlue(features='...')`, `LightGlue(features=None, **conf)`, precomputed feature dictionaries, `depth_confidence`, `width_confidence`, `filter_threshold`, `flash`, `mp`, `compile()`, or interpreting `matches0`, `matches`, `scores`, `stop`, and `prune*`.

## Route first

- For extractor defaults, extractor output schemas, SIFT/DoGHardNet scale-orientation details, or pretrained extractor behavior, use [extractors-and-features](../extractors-and-features/SKILL.md).
- For real image pair loading, `match_pair`, batch-dimension removal, or coordinate indexing on images, use [image-pair-matching](../image-pair-matching/SKILL.md).
- For benchmark commands, visualization helpers, throughput tables, or match display, use [performance-and-visualization](../performance-and-visualization/SKILL.md).

## Operating references

- [Direct matcher API reference](references/api-reference.md) covers signatures, valid feature presets, input/output dictionary schemas, result interpretation, and a synthetic `features=None` example.
- [Configuration decisions](references/configuration.md) covers default values, speed/accuracy trade-offs, adaptive depth/width, filtering, FlashAttention, mixed precision, `torch.compile`, and pruning thresholds.
- [Troubleshooting](references/troubleshooting.md) covers common assertions, unsupported feature names, missing `image_size`, descriptor dimension mismatches, optional acceleration warnings, compile/pruning interactions, and no-keypoint behavior.
- Planned synthetic API check: [root smoke script](../../scripts/lightglue_smoke.py) when present in the root LightGlue skill. It should use `LightGlue(features=None, ...)` to avoid pretrained weight downloads.

## Default operating stance

1. Use a feature preset (`features='superpoint'`, `'disk'`, `'aliked'`, `'sift'`, or `'doghardnet'`) when descriptors come from a supported extractor and pretrained LightGlue matching quality is required. Preset matcher weights can download on first use.
2. Use `features=None` only when the caller supplies fully precomputed descriptors and intentionally controls `input_dim`, `descriptor_dim`, `n_layers`, and `num_heads`; without compatible weights this is an untrained matcher configuration, useful for API smoke tests or custom-trained deployments.
3. For maximum accuracy, keep all desired keypoints and disable adaptivity with `depth_confidence=-1` and `width_confidence=-1`.
4. For speed, keep `flash=True`, consider CUDA `mp=True`, lower adaptive thresholds carefully, and consider `compile()` only after understanding the pruning interaction documented in [configuration](references/configuration.md).
