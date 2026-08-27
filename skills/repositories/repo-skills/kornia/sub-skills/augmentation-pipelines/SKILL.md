---
name: augmentation-pipelines
description: "Use Kornia augmentation pipelines for random or deterministic
  image, mask, box, keypoint, class, patch, and video transforms."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Kornia Augmentation Pipelines

Use this sub-skill when a task asks for Kornia `kornia.augmentation` random or
deterministic transforms, synchronized image/mask/box/keypoint/class
augmentation, deterministic replay of random parameters, augmentation transform
matrices, inverse augmentation, or augmentation containers such as
`AugmentationSequential`, `ImageSequential`, `PatchSequential`, and
`VideoSequential`.

This skill assumes Kornia 0.9.0rc1 with Python >=3.11, PyTorch >=2.0, numpy,
packaging, and `kornia-rs` available. Optional ONNX, transformers, diffusers,
and ivy integrations may be absent. Augmentation image tensors should be float
PyTorch tensors in `[0, 1]`, usually `C,H,W` or `B,C,H,W`.

## Read first

- For stable call shapes, constructor signatures, and selected classes, read
  [references/api-reference.md](references/api-reference.md).
- For task recipes, read [references/workflows.md](references/workflows.md).
- For `data_keys`, input order, masks, boxes, keypoints, class labels,
  transform matrices, and inverse behavior, read
  [references/data-keys-and-matrices.md](references/data-keys-and-matrices.md).
- For common failures and repair actions, read
  [references/troubleshooting.md](references/troubleshooting.md).
- To verify a no-download Kornia augmentation runtime, run
  [scripts/augmentation_smoke.py](scripts/augmentation_smoke.py).

## Fast routing

Choose this sub-skill for:

- `AugmentationSequential` pipelines with `data_keys` such as `"input"`,
  `"mask"`, `"bbox"`, `"bbox_xyxy"`, `"bbox_xywh"`, `"keypoints"`,
  `"class"`, or `"label"`.
- Random geometric image transforms such as `RandomAffine`,
  `RandomPerspective`, `RandomResizedCrop`, `RandomHorizontalFlip`, and
  `RandomVerticalFlip`.
- Random intensity transforms in an augmentation chain, especially
  `ColorJiggle` and related image-only color/photometric perturbations.
- Container behavior: `same_on_batch`, `keepdim`, `random_apply`,
  `random_apply_weights`, deterministic replay with cached or supplied params,
  transform matrices, and `inverse`.
- Patch and video augmentation routing through `PatchSequential` and
  `VideoSequential`.

Route away when the main problem is not augmentation orchestration:

- Low-level deterministic `resize`, affine/perspective warp construction,
  homographies, camera geometry, or coordinate-system reasoning:
  [geometry-vision](../geometry-vision/SKILL.md).
- General non-random image processing, filters, color conversions, morphology,
  enhancement, or tensor I/O conventions:
  [image-processing](../image-processing/SKILL.md).
- Feature detection/matching, learned local features, LoFTR/LightGlue/DISK, or
  model weights: [features-and-matching](../features-and-matching/SKILL.md).
- Losses or metrics for training/evaluation:
  [losses-and-metrics](../losses-and-metrics/SKILL.md).

## Operating rules

1. Keep image tensors floating point in `[0, 1]` before augmentation. Convert
   `uint8` images with division by `255.0`; do not pass raw integer images to
   random color or geometric augmentations.
2. Use `B,C,H,W` for ordinary image batches. Single `C,H,W` images are accepted
   by some modules, but `B,C,H,W` is safer for multi-target pipelines and matrix
   checks.
3. In `AugmentationSequential`, make the number and order of positional inputs
   exactly match `data_keys`; the first key must be image/input when random
   parameters are generated from the image.
4. Prefer string keys in user-facing examples: `data_keys=["input", "mask"]`.
   `"image"` and `"input"` are aliases; `"class"` and `"label"` are aliases.
5. Use `p=1.0` for deterministic smokes and required transforms; set explicit
   ranges such as `degrees=0.0`, `scale=(1.0, 1.0)`, or fixed crop sizes when a
   test must be reproducible.
6. Use `same_on_batch=True` only when every batch item must receive the same
   sampled parameters. Leave it `False` for independent per-item stochastic
   augmentation.
7. Use `keepdim=True` when downstream code expects the same rank/shape as the
   input; leave defaults only when the target API accepts Kornia's batch-form
   normalization.
8. Use `extra_args` only for per-data-key overrides. Masks default to nearest
   interpolation semantics in `AugmentationSequential`, which is usually what
   segmentation masks need.
9. Treat `.transform_matrix` and cached params as per-call eager state. They are
   useful for diagnostics, replay, and inverse, but not a stable serialization
   format for deployment.
10. For export/deployment, prefer deterministic preprocessing transforms and
    single-input image pipelines. Random multi-target propagation is best kept
    in eager training or data-loading code unless the target exporter is proven
    with a focused smoke.
