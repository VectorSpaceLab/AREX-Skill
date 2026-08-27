---
name: image-processing-basics
description: "Guides SimpleCV Image, ImageSet, color, drawing, transform, DFT,
  and scanline workflows on static images."
disable-model-invocation: true
metadata:
  disco-role: operating
license: BSD 3-Clause
---

# Image Processing Basics

Use this sub-skill when the task is about static SimpleCV images rather than live cameras, detectors, trackers, or classifiers.

## Read first

Read `references/workflows.md` for detailed image recipes, parameter notes, and source-example replacements.
Read `references/troubleshooting.md` when loading, saving, showing, sample-image, color-space, or filter steps fail.
Read the root `../../references/api-reference.md` for verified constructor and method signatures.
Run `scripts/image_recipe.py --help` when you need a finite sample-image smoke helper.

## Use this for

- `Image(...)` construction from sample names, files, numpy arrays, or existing matrices.
- `ImageSet(...)` directory/sample loading and list-style processing.
- Cropping, resizing, scaling, rotating, shearing, warping, flipping, blitting, side-by-side composition, and drawing.
- Thresholding, binarization, masks, morphology, gradients, edges, histograms, palettes, and color models.
- DFT filters, line scans, pixel access, and arithmetic/logical image operations.
- Headless conversions where `Image.save(...)` is safer than `Image.show(...)`.

## Route elsewhere

- Camera, `Display`, shell, stream, calibration, or physical device questions → `../acquisition-display-shell/SKILL.md`.
- Blobs, lines, corners, templates, Haar, keypoints, barcode, or OCR → `../feature-detection/SKILL.md`.
- Segmentation masks over frames or trackers → `../segmentation-tracking/SKILL.md`.
- Classifier training/testing wrappers → `../machine-learning-legacy/SKILL.md`.

## Core workflow

1. Confirm the package imports with the root `../../scripts/check_env.py` if the environment is unknown.
2. Load sample images with package data instead of source-checkout paths:
   ```python
   from SimpleCV import Image
   img = Image('simplecv')
   coins = Image('coins.jpg', sample=True)
   ```
3. Use finite operations and save outputs:
   ```python
   crop = img.crop(0, 0, 100, 100).scale(64, 64)
   crop.save('crop.png')
   ```
4. Only use `show()` when a display is available; otherwise use `save()` and `applyLayers()`.
5. Validate non-empty images and dimensions before chaining expensive or feature-dependent operations.

## Important decisions

- If an image path is user-supplied, check file existence and whether SimpleCV is interpreting it as a package sample.
- If the task needs color thresholds, clarify whether colors are RGB tuples in SimpleCV's public API or BGR/OpenCV internals.
- If a transform changes image size, choose whether fixed-size output or full extents are needed.
- If drawing layers are used, call `applyLayers()` or `save()` through the rendered image when comparing outputs.
- If a filter depends on old OpenCV symbols, fix the root OpenCV compatibility issue before changing the algorithm.

## Bundled helper

Run a finite image smoke recipe:

```bash
python sub-skills/image-processing-basics/scripts/image_recipe.py --recipe all --output-dir /tmp/simplecv-image
```

Use `--repo-root` only when SimpleCV is not installed and you intentionally want to inspect a separate checkout.

## Verification hooks

Good native-backed checks for this sub-skill include `test_image_loadsave`, `test_image_numpy_constructor`, `test_color_meancolor`, `test_image_scale`, DFT tests, and line-scan tests from SimpleCV's native suite. Use them only after the full skill has been integrated and the runtime environment is ready.
