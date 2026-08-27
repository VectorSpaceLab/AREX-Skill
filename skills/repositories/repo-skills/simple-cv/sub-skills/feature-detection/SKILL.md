---
name: feature-detection
description: "Guides SimpleCV blob, line, corner, template, Haar, keypoint,
  barcode, OCR, and feature-set workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: BSD 3-Clause
---

# Feature Detection

Use this sub-skill when a task needs SimpleCV to find, measure, sort, filter, draw, or interpret features in an image.

## Read first

Read `references/workflows.md` for detector recipes and feature object handling.
Read `references/troubleshooting.md` for empty detections, threshold tuning, optional detectors, and OpenCV feature availability.
Read the root `../../references/api-reference.md` for verified method signatures.
Run `scripts/feature_recipe.py --help` for finite sample-image detection recipes.

## Use this for

- `FeatureSet`, `Feature`, `Blob`, `Corner`, `Line`, `TemplateMatch`, `Circle`, `KeyPoint`, `HaarFeature`, `Barcode`, `Chessboard`, and `ROI` objects.
- `Image.findBlobs`, `findLines`, `findCorners`, `findTemplate`, `findTemplateOnce`, `findCircle`, `findKeypoints`, `findKeypointMatch`, `findHaarFeatures`, `findBarcode`, and `readText`.
- Blob measurements such as area, radius, contour, hull, min rectangle, shape tests, and masks.
- Template matching and keypoint matching decisions.
- Optional barcode/OCR/Haar/keypoint dependencies and limitations.

## Route elsewhere

- Static transforms before or after detection → `../image-processing-basics/SKILL.md`.
- Live camera/display loops that supply frames → `../acquisition-display-shell/SKILL.md`.
- Stateful segmentation masks and trackers → `../segmentation-tracking/SKILL.md`.
- Classifier training from extracted features → `../machine-learning-legacy/SKILL.md`.

## Core workflow

1. Load or create a non-empty `Image`.
2. Choose the detector method and make thresholds explicit.
3. Handle `None` or empty `FeatureSet` before indexing or drawing.
4. Draw or measure features, then call `applyLayers()` before saving an annotated image.
5. If the detector relies on optional dependencies or nonfree OpenCV features, prove those before treating an empty result as an algorithm problem.

Example pattern:

```python
from SimpleCV import Image, Color
img = Image('coins.jpg', sample=True)
features = img.invert().findBlobs(minsize=200)
if features:
    biggest = features[-1]
    img.drawText('radius=%s' % biggest.radius(), biggest.x, biggest.y, color=Color.RED)
    img.applyLayers().save('coins_annotated.png')
```

## Important decisions

- `findBlobs` threshold/minsize defaults are convenient, not universal.
- Template matching methods have different score semantics; document the chosen method.
- `findKeypoints` defaults to `SURF`, which may be unavailable in many OpenCV builds.
- Barcode and OCR are optional integrations; missing ZXing or tesseract is not a core SimpleCV failure.
- Feature coordinates are image coordinates; verify image resize/scale before reusing a bounding box.

## Bundled helper

```bash
python sub-skills/feature-detection/scripts/feature_recipe.py --recipe blobs --output-dir /tmp/simplecv-features
python sub-skills/feature-detection/scripts/feature_recipe.py --recipe template --output-dir /tmp/simplecv-features
```

The helper adapts safe parts of source examples and writes finite outputs instead of opening windows.

## Verification hooks

Good final native candidates include `test_detection_findCorners`, `test_detection_blobs`, `test_template_match_once`, `test_detection_lines`, `test_findKeypoints_all`, `test_keypoint_match`, and `test_findHaarFeatures`. Run them only after integration and environment readiness.
