---
name: image-hypermodels
description: "Routes KerasTuner's built-in HyperResNet, HyperXception,
  HyperEfficientNet, and HyperImageAugment workflows, including shape contracts,
  search-space overrides, augmentation composition, backend layout, and safe
  build gating."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Image Hypermodels

Use this sub-skill when a task names `HyperResNet`, `HyperXception`,
`HyperEfficientNet`, or `HyperImageAugment`, or asks for a KerasTuner image
architecture/augmentation search space. Route generic tuner and
`HyperParameters` questions to the parent skill's generic tuning route.

## Route by intent

- **ResNet classifier or feature extractor** → read
  `references/api-reference.md` for `HyperResNet`, then follow the staged
  architecture workflow in `references/workflows.md`.
- **Xception classifier or feature extractor** → use the same API reference
  and workflow, checking the Xception-specific hyperparameters before building.
- **EfficientNet classifier** → read the EfficientNet and composition sections
  first. Its Keras Applications call uses the default ImageNet weights and may
  download files; do not build it implicitly or in an offline smoke check.
- **Searchable image augmentation** → use `HyperImageAugment`. Choose fixed
  sequential mode with `augment_layers=0`/`None`, or RandAugment-like mode with
  a positive integer or two-integer range.
- **Augmentation plus EfficientNet** → pass a Keras `Model` or `HyperModel` as
  `augmentation_model`; the latter is built with the same `HyperParameters`
  object. Use the explicit expensive-build gate described in the workflow.

## Before calling `build(hp)`

1. Check `keras_tuner.__version__` and the active
   `keras.backend.image_data_format()`. `input_shape` excludes the batch axis
   and must use the active channel layout.
2. Supply at least one of `input_shape` and `input_tensor`. If both are
   supplied, the implementation uses `input_tensor` and obtains its source
   inputs; do not rely on `input_shape` to override a tensor's shape.
3. For ResNet/Xception, set `include_top=True` only when `classes` is supplied.
   With `include_top=False`, `classes` is not required and the returned model
   is a feature extractor without the classifier compile step.
4. For EfficientNet, always supply a truthy `classes` value. It has no
   `include_top` argument: the built-in hypermodel always constructs and
   compiles its classifier head.
5. Decide whether a build is safe before starting it. ResNet/Xception can be
   slow, and EfficientNet also resizes to a variant-specific image size and
   can fetch ImageNet weights.

## Progressive disclosure

- Read `references/api-reference.md` for exact 1.4.8 signatures, validation,
  model outputs, hyperparameter names/defaults, transform ranges, and backend
  layout rules.
- Read `references/workflows.md` for safe construction, deterministic
  hyperparameter overrides, input-tensor composition, augmentation modes, and
  staged EfficientNet use.
- Read `references/troubleshooting.md` for validation errors, backend shape
  failures, stale test expectations, slow/OOM builds, and weight-cache/offline
  recovery.
- From the skill root, run `sub-skills/image-hypermodels/scripts/smoke_build.py` for a flag-gated augmentation-only check. It uses the installed package by default; pass `--repo-root <CHECKOUT>` to select a source checkout explicitly. Opt into
  architecture builds explicitly; opt into EfficientNet only when a possible
  network/weight-cache access is acceptable and an external timeout is set.

## Operating guardrails

- Treat the installed signatures and the current implementation's search-space
  names as the contract. In particular, current augmentation names are
  `augment_layers` and `factor_<transform>`; do not substitute older
  `randaug_count`/`randaug_mag` names.
- Prefer an existing `HyperParameters` object with `Fixed`, `Choice`, or
  compatible values to make a smoke build deterministic. A pre-existing name
  whose domain conflicts with the hypermodel can fail during build.
- Assert the model input(s), output shape, selected `hp.values`, and compiled
  state appropriate to `include_top` before starting a search.
- Keep heavyweight or weight-fetching builds behind a user-visible flag or a
  bounded subprocess/time limit. Never put an EfficientNet build in an import
  check or an automatic default smoke path.
