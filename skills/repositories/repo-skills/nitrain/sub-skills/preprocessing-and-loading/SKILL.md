---
name: preprocessing-and-loading
description: "Apply Nitrain transforms, random augmentation, samplers, and
  loader batching workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: AGPL 3.0
---

# Preprocessing and loading

Use this sub-skill when a user needs to transform images, apply random
augmentation, sample slices or patches, or batch a dataset with `Loader` or
`Loader.to_keras()`.

## What belongs here

- Deterministic transforms for image, intensity, math, shape, spatial, and
  label workflows.
- Random transforms that wrap those deterministic transforms.
- `BaseSampler`, `SliceSampler`, `PatchSampler`, `BlockSampler`, and
  `SlicePatchSampler`.
- `Loader`, `Loader.copy()`, `Loader.to_keras()`, and the batch-shaping logic
  that sits between a `Dataset` and a model.

## What does not belong here

- Building datasets from source files or cloud storage: use
  `sub-skills/datasets-readers/`.
- Model discovery, trainers, or pretrained weights: use
  `sub-skills/models-training/`.
- Prediction and explanation post-processing: use
  `sub-skills/prediction-and-explanation/`.

## Typical user requests

- "Normalize and resample the images before training"
- "Apply the same transform to inputs and outputs"
- "Sample 2D slices from 3D volumes"
- "Batch the dataset for Keras"
- "Why did my transform or sampler fail on this image shape?"

## Working pattern

1. Decide whether the task is deterministic preprocessing, random augmentation,
   or sampling.
2. Route paired transforms with tuple keys such as `('inputs', 'outputs')` when
   the same operation must stay aligned.
3. Use `Loader` after the dataset is already shaped the way the model expects.
4. Pick the sampler based on the data geometry: slices for 3D-to-2D, patches
   for 2D crops, blocks for 3D crops, and slice-patch for slice-wise patching.

## Read these references

- [references/api-reference.md](references/api-reference.md) for the
  transform and sampler constructors.
- [references/workflows.md](references/workflows.md) for canonical
  preprocessing and batching examples.
- [references/troubleshooting.md](references/troubleshooting.md) for shape
  mismatches, transform key errors, and loader warnings.

## Smoke check

After installing dependencies, run the bundled helper [scripts/check_install.py](../../scripts/check_install.py):

```bash
python scripts/check_install.py --mode preprocess
```

Use this when you want to confirm the transformation, sampler, and loader stack
before model construction or prediction.

## Decision notes

- `channels_first=True` adds a channel axis in the loader; `channels_first=None`
  disables the extra expansion.
- `Loader.transforms` applies after the dataset records are collected and before
  the sampler emits batches.
- A transform value may be a single transform or a list/tuple of transforms that
  are applied in order.
- A tuple transform key means the transform should see all named values together
  so paired inputs and outputs stay aligned.

## Key categories

### Deterministic image transforms

- `Astype`, `Smooth`, `Crop`, `Resample`, `Slice`, `Pad`
- `ImageMath`, `BiasCorrection`, `StandardNormalize`, `RangeNormalize`, `Clip`,
  `QuantileClip`, `Threshold`
- `Abs`, `Ceil`, `Floor`, `Log`, `Exp`, `Sqrt`, `Power`
- `AddChannel`, `Reorient`
- `ApplyAntsTransform`, `AffineTransform`, `Shear`, `Rotate`, `Zoom`, `Flip`,
  `Translate`
- `LabelsToChannels`
- `CustomFunction`, `NumpyFunction`

### Random transforms

- `RandomCrop`
- `RandomShear`, `RandomRotate`, `RandomZoom`, `RandomFlip`, `RandomTranslate`

### Samplers

- `BaseSampler` for plain batching
- `SliceSampler` for 2D slices from 3D volumes
- `PatchSampler` for 2D patches
- `BlockSampler` for 3D blocks
- `SlicePatchSampler` for slice-then-patch workflows

## Common outcomes

- `Loader.__iter__()` returns numpy batches with the expected channel layout.
- `Loader.to_keras()` returns a `tf.data.Dataset`-style object that Keras can
  consume.
- Samplers keep batch length and crop geometry consistent with the chosen mode.

## Watch for these signals

- `Some names in your transform were not found` means the transform key labels do
  not match the dataset keys.
- `images_per_batch` larger than the dataset triggers a warning and is clipped
  down to the dataset size.
- Slice, patch, and block samplers only work when the images are large enough to
  support the requested geometry.

## Before handing off

If the user actually needs architecture discovery, trainers, or prediction,
hand off to the relevant sibling sub-skill instead of adding that logic here.
