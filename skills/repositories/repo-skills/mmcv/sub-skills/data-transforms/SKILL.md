---
name: data-transforms
description: "Compose, customize, inspect, and troubleshoot MMCV dict-style data
  transform pipelines with mmcv.transforms and MMEngine registries."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# MMCV Data Transforms

Use this sub-skill when a task involves `mmcv.transforms`, `TRANSFORMS`, dict-style data pipelines, custom transform registration, transform wrappers, or transform failures involving image/annotation keys.

## Read When

- Building a `pipeline = [dict(type=...)]` list for an OpenMMLab dataset or standalone MMCV preprocessing flow.
- Debugging missing `img`, `img_path`, `img_shape`, `ori_shape`, `pad_shape`, `scale_factor`, `flip`, `gt_bboxes`, `gt_seg_map`, or `gt_keypoints` keys.
- Writing a custom `BaseTransform` registered into `TRANSFORMS` for config-based construction.
- Using `Compose`, `KeyMapper`, `RandomChoice`, `RandomApply`, `TransformBroadcaster`, or cached randomness.
- Validating tensor conversion through `ToTensor`, `ImageToTensor`, or `to_tensor`.

## Quick Workflow

1. Identify the contract for each transform in `references/data-contracts.md` before reordering the pipeline.
2. Check constructor defaults and side effects in `references/api-reference.md`.
3. Start from a recipe in `references/workflows.md` and adapt keys, shapes, and registry imports deliberately.
4. For failures, match the symptom in `references/troubleshooting.md` before changing source code.
5. Run `scripts/transform_pipeline_check.py --help`, then run the checker against a tiny generated fixture to verify key, shape, and type expectations.

## Shape Convention Warning

Initialization sizes such as `Resize(scale=(width, height))`, `RandomResize(scale=...)`, `RandomChoiceResize(scales=...)`, `Pad(size=(width, height))`, and crop sizes follow width-height argument conventions where documented by MMCV image APIs. Returned metadata keys such as `img_shape`, `ori_shape`, and `pad_shape` are height-width tuples from NumPy image shape.

## Boundaries

- Low-level image IO, resizing, padding, normalization, color conversion, and geometric image functions are covered by `../media-processing/`.
- CNN layers, model builders, and network initialization are covered by `../cnn-model-building/`.
- Compiled ops, CUDA extensions, and full-MMCV build issues are covered by `../ops-and-builds/`.

## References

- `references/api-reference.md` for signatures, defaults, registry behavior, and transform side effects.
- `references/data-contracts.md` for read/write keys, bbox/seg/keypoint shapes, metadata conventions, and tensor assumptions.
- `references/workflows.md` for pipeline config recipes, custom transform registration, wrappers, and test-time augmentation.
- `references/troubleshooting.md` for actionable fixes for common transform failures.
- `scripts/transform_pipeline_check.py` for a self-contained tiny pipeline smoke check.
