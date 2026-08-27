---
name: augmentation-pipelines
description: "Use when building, combining, or debugging imgaug image
  augmentation pipelines, augmenter families, or deterministic image-only
  transforms."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Augmentation Pipelines

Use this sub-skill when the task is about **image augmentation pipelines** in imgaug: choosing augmenter families, composing them with `Sequential`/`SomeOf`/`OneOf`/`Sometimes`, applying transforms deterministically, or debugging image-only augmentation behavior.

## What this sub-skill covers

- Pipeline composition with `iaa.Sequential`, `iaa.SomeOf`, `iaa.OneOf`, `iaa.Sometimes`, and `iaa.WithChannels`.
- Image-only use of common augmenter families: affine/geometric, crop/pad/resize, blur, arithmetic/noise, color, contrast, blend/overlay, segmentation/superpixels, weather, PIL-like effects, and `imgcorruptlike` when installed.
- Deterministic pipeline reuse with `to_deterministic()`.
- Basic image input/output conventions: NHWC arrays, RGB order, `uint8` expectations, and shape preservation when `keep_size=True`.
- Safe visualization and contact-sheet generation via bundled helpers.

## What it does not cover

- Annotation object construction and batch normalization details belong to [`../augmentables-and-batches/SKILL.md`](../augmentables-and-batches/SKILL.md).
- Random seed, stochastic parameter, dtype, and sample-data details belong to [`../parameters-random-and-utilities/SKILL.md`](../parameters-random-and-utilities/SKILL.md).
- Background multiprocessing and `Pool` behavior belong to [`../multicore-and-diagnostics/SKILL.md`](../multicore-and-diagnostics/SKILL.md).

## Typical triggers

- “How do I build an imgaug pipeline with flips, affine, blur, and color jitter?”
- “Why did my augmentation change the image shape?”
- “How do I apply the same sampled transform twice?”
- “Which augmenter should I use for cropping, padding, weather, or superpixels?”

## Fast path

1. Read [`references/pipeline-workflows.md`](references/pipeline-workflows.md) for the minimal image-pipeline recipes.
2. Read [`references/augmenter-family-reference.md`](references/augmenter-family-reference.md) for family selection and parameter defaults.
3. Run [`scripts/generate_augmentation_contact_sheet.py`](scripts/generate_augmentation_contact_sheet.py) when you need a safe contact sheet or a tiny visual smoke.
4. Read [`references/troubleshooting.md`](references/troubleshooting.md) if the pipeline gives unexpected shapes, dtypes, or color results.

## Core usage pattern

Image pipelines usually take `numpy.ndarray` input of shape `(N, H, W, C)` or a list of `(H, W, C)` arrays. Most examples assume RGB `uint8` images.

```python
import numpy as np
import imgaug.augmenters as iaa

images = np.zeros((4, 64, 64, 3), dtype=np.uint8)
seq = iaa.Sequential([
    iaa.Fliplr(0.5),
    iaa.Affine(rotate=(-10, 10), translate_px={"x": (-2, 2)}),
    iaa.GaussianBlur(sigma=(0.0, 1.0)),
])
images_aug = seq(images=images)
```

Use `to_deterministic()` when you need the same sampled transform in separate calls. Prefer a single call containing all aligned data whenever the task also includes annotations.

## Common pipeline decisions

- Use `Sequential` for ordered pipelines.
- Use `SomeOf` when a bounded subset of augmenters should run.
- Use `OneOf` when exactly one branch should run.
- Use `Sometimes` for probability-gated branches.
- Use `WithChannels` when only selected channels should change.
- Use `fit_output=False` and `keep_size=True` as safe defaults until a task explicitly needs output resizing.
- Keep `uint8`/RGB in mind when the task starts from OpenCV or camera data.

## Handy families and when to reach for them

- `Affine`, `PerspectiveTransform`, `ElasticTransformation`, `Jigsaw`: geometric distortions.
- `Crop`, `Pad`, `CropAndPad`, `Resize`, `KeepSizeByResize`: size and framing.
- `GaussianBlur`, `AverageBlur`, `MedianBlur`, `MotionBlur`, `BilateralBlur`, `MeanShiftBlur`: smoothing/blur.
- `Add`, `Multiply`, `Dropout`, `CoarseDropout`, `Invert`, `Solarize`, `JpegCompression`: arithmetic/noise/compression.
- `WithHueAndSaturation`, `ChangeColorspace`, `Grayscale`, `Posterize`, `KMeansColorQuantization`, `UniformColorQuantization`: color and palette changes.
- `LinearContrast`, `GammaContrast`, `HistogramEqualization`, `CLAHE`: contrast shaping.
- `BlendAlpha`, `SimplexNoiseAlpha`, `FrequencyNoiseAlpha`: masked blending and partial effects.
- `Superpixels`, `Voronoi`, `Snowflakes`, `Rain`, `Fog`, `Clouds`, `FastSnowyLandscape`: segmentation-like and weather effects.

## Validation mindset

A good image-pipeline smoke should prove three things:

1. The output image array keeps the expected shape and dtype.
2. The pipeline actually changes pixels when it should.
3. A deterministic replay produces identical results.

Use the bundled script to check those properties with tiny arrays before moving to annotation-aware or multicore workflows.
