# Feature Detection Workflows

## When to read this

Read this when a task asks SimpleCV to find objects, edges, corners, blobs, templates, keypoints, or text/barcodes in an image.

## Feature object model

- Detector methods usually return a `FeatureSet`, which is list-like and offers helper arrays such as coordinates, areas, widths, heights, and sorting/filtering methods.
- A feature can usually draw itself on its source image.
- Always guard empty results before indexing: `if features:`.
- Rendering annotations normally requires `applyLayers()` before saving or comparing.

## Blob detection recipe

Adapted from the coin detector example but finite and headless:

```python
from SimpleCV import Image, Color
img = Image('coins.jpg', sample=True)
blobs = img.invert().findBlobs(minsize=200)
if blobs:
    largest = blobs[-1]
    diameter = largest.radius() * 2
    largest.draw(color=Color.RED)
    img.drawText('diameter=%0.1f px' % diameter, largest.x, largest.y)
    img.applyLayers().save('coins_blobs.png')
```

Useful blob methods include `area()`, `radius()`, `contour()`, `hull()`, `minRect()`, `draw()`, `drawOutline()`, `drawHull()`, `blobImage()`, and `blobMask()`.

## Line and corner recipe

```python
img = Image('aerospace.jpg', sample=True)
corners = img.findCorners(maxnum=25)
if corners:
    corners.draw()
    img.applyLayers().save('corners.png')
```

For lines, tune `threshold`, `minlinelength`, `maxlinegap`, and Canny thresholds. `useStandard=True` switches the Hough path exposed by the old implementation.

## Template matching recipe

```python
source = Image('templatetest.png', sample=True)
template = Image('template.png', sample=True)
matches = source.findTemplate(template, threshold=5, method='SQR_DIFF_NORM')
if matches:
    matches.draw()
source.applyLayers().save('template_matches.png')
```

Template matching is sensitive to scale and rotation. Use keypoints instead when the object may change scale or rotate.

## Keypoint workflow

`findKeypoints(min_quality=300.0, flavor='SURF', highQuality=False)` and `findKeypointMatch(template, quality=500.0, minDist=0.2, minMatch=0.4)` use OpenCV feature APIs. Many modern builds omit SURF/nonfree features; check available flavors before promising a workflow.

Fallback plan:

1. Try the requested flavor.
2. If OpenCV reports the detector is unavailable, document the build limitation.
3. Use templates, corners, or blobs if they solve the task without nonfree features.

## Haar, barcode, and OCR

- `HaarCascade(fname=None, name=None)` and `Image.findHaarFeatures(...)` use built-in cascade data or a cascade file.
- `findBarcode(doZLib=True, zxing_path='')` requires ZXing.
- `readText()` requires tesseract.

Treat barcode and OCR as optional workflows. Missing optional dependencies should produce an actionable setup note, not a generic detection failure.

## Source example replacement map

| Source repo artifact | Runtime replacement |
|---|---|
| `examples/detection/CoinDetector.py` | `scripts/feature_recipe.py --recipe blobs` and the blob recipe above. |
| `examples/detection/TemplateMatching.py` | `scripts/feature_recipe.py --recipe template`; finite output, no display sleeps. |
| `examples/detection/FeatureDetection.py` | Reference-only; interactive camera/mouse training workflow. |
| `examples/detection/barcode_reader.py` | Optional ZXing guidance; do not verify unless ZXing is installed. |
| `tests/tests.py` detection cases | Final native verification candidates after integration. |

## Validation checklist

- Is the input image non-empty?
- Are thresholds and minimum sizes explicit?
- Did the code check for empty `FeatureSet` before indexing?
- Are optional detector dependencies available?
- Are annotations rendered with `applyLayers()` before saving?
- If a detector returns no features, did you try a sample image with known expected features before changing the user's algorithm?
