# Object-Detection-Metrics Python API reference

This reference covers direct programmatic use of the legacy source-style API. It is intended for a user-provided checkout or copy of the repository's `lib/` directory; the generated skill itself does not vendor the upstream source classes.

## Import model

The source files import each other with unqualified names such as `from utils import *` and `from BoundingBox import *`. Add the `lib` directory itself to `sys.path` before importing:

```python
import os
import sys
from pathlib import Path

os.environ.setdefault("MPLBACKEND", "Agg")  # useful before importing Evaluator in headless runs
lib_dir = Path("/path/to/lib")
sys.path.insert(0, str(lib_dir))

from BoundingBox import BoundingBox
from BoundingBoxes import BoundingBoxes
from Evaluator import Evaluator
from utils import BBFormat, BBType, CoordinatesType, MethodAveragePrecision
```

`utils.py` imports `cv2` at module import time, so even non-drawing API code needs `opencv-python` or `opencv-python-headless` installed.

## Enums

| Enum | Values | Use |
|---|---|---|
| `MethodAveragePrecision` | `EveryPointInterpolation = 1`, `ElevenPointInterpolation = 2` | Select AP interpolation in `Evaluator.GetPascalVOCMetrics` and `PlotPrecisionRecallCurve`. |
| `CoordinatesType` | `Relative = 1`, `Absolute = 2` | Tell `BoundingBox` whether input coordinates are normalized relative values or absolute pixel values. |
| `BBType` | `GroundTruth = 1`, `Detected = 2` | Mark boxes as ground truth or detections. Detection boxes require `classConfidence`. |
| `BBFormat` | `XYWH = 1`, `XYX2Y2 = 2` | Interpret box arguments as `(left, top, width, height)` or `(left, top, right, bottom)`. `XYX2Y2` corresponds to the README/CLI `xyrb` wording. |

## `BoundingBox`

Verified constructor signature:

```python
BoundingBox(imageName, classId, x, y, w, h,
            typeCoordinates=CoordinatesType.Absolute,
            imgSize=None,
            bbType=BBType.GroundTruth,
            classConfidence=None,
            format=BBFormat.XYWH)
```

Responsibilities:

- Store one ground-truth or detected object box.
- Preserve `imageName` and `classId` for matching; detections and ground truths for the same image must use exactly the same `imageName` string.
- Convert relative normalized boxes into absolute coordinates at construction time.
- Provide both absolute and relative getters.

Important constructor rules:

- `bbType=BBType.Detected` requires `classConfidence`; omission raises an `IOError`.
- `typeCoordinates=CoordinatesType.Relative` requires `imgSize=(width, height)` and must use `format=BBFormat.XYWH`.
- Relative `XYWH` means `(center_x / image_width, center_y / image_height, box_width / image_width, box_height / image_height)`, not top-left normalized coordinates.
- Absolute `BBFormat.XYWH` stores width and height; absolute `BBFormat.XYX2Y2` treats the `w` and `h` arguments as right and bottom coordinates.

Useful methods:

| Method | Output / behavior |
|---|---|
| `getAbsoluteBoundingBox(format=BBFormat.XYWH)` | Returns `(x, y, w, h)` or `(x1, y1, x2, y2)`. |
| `getRelativeBoundingBox(imgSize=None)` | Returns normalized `(center_x, center_y, width, height)`; requires an image size if the box was not constructed with one. |
| `getImageName()`, `getClassId()`, `getConfidence()` | Return matching and confidence fields. |
| `getImageSize()`, `getCoordinatesType()`, `getBBType()`, `getFormat()` | Return stored metadata. |
| `BoundingBox.clone(box)` | Create a copied `BoundingBox` using absolute `XYWH` values. |

Example: absolute `XYX2Y2` ground truth and detection.

```python
gt = BoundingBox("img-1", "person", 10, 10, 50, 50,
                 CoordinatesType.Absolute,
                 bbType=BBType.GroundTruth,
                 format=BBFormat.XYX2Y2)
det = BoundingBox("img-1", "person", 10, 10, 50, 50,
                  CoordinatesType.Absolute,
                  bbType=BBType.Detected,
                  classConfidence=0.99,
                  format=BBFormat.XYX2Y2)
```

Example: relative normalized center box over a `200 x 200` image.

```python
rel = BoundingBox("img-1", "person", 0.5, 0.5, 0.5, 0.5,
                  CoordinatesType.Relative,
                  imgSize=(200, 200),
                  bbType=BBType.GroundTruth,
                  format=BBFormat.XYWH)
assert rel.getAbsoluteBoundingBox(BBFormat.XYX2Y2) == (50, 50, 150, 150)
```

The conversion rounds endpoints and clamps them into the image extent.

## `BoundingBoxes`

`BoundingBoxes` is a mutable collection consumed by `Evaluator`.

| Method | Use |
|---|---|
| `addBoundingBox(bb)` | Append a `BoundingBox`. |
| `removeBoundingBox(bb)` | Remove a matching box using the class comparison helper. Prefer rebuilding the collection if exact removal matters. |
| `removeAllBoundingBoxes()` | Clear the collection. |
| `getBoundingBoxes()` | Return the underlying list. |
| `getBoundingBoxByClass(classId)` | Return boxes for one class. |
| `getClasses()` | Return class ids in first-seen order. |
| `getBoundingBoxesByType(bbType)` | Return all ground-truth or detected boxes. |
| `getBoundingBoxesByImageName(imageName)` | Return boxes attached to one image name. |
| `count(bbType=None)` | Count all boxes, or only one `BBType`. |
| `clone()` | Copy the collection. |
| `drawAllBoundingBoxes(image, imageName)` | Draw boxes for one image into an OpenCV image array; returns the modified image. |

Drawing caveats:

- `drawAllBoundingBoxes(image, imageName)` does not read or write images by itself; the caller owns `cv2.imread` / `cv2.imwrite` and must check that the image array is not `None`.
- It uses `utils.add_bb_into_image`, so OpenCV must be importable.
- Ground truths are drawn green and detections red in the source convention.

## `Evaluator`

Verified metric signature:

```python
Evaluator().GetPascalVOCMetrics(
    boundingboxes,
    IOUThreshold=0.5,
    method=MethodAveragePrecision.EveryPointInterpolation,
)
```

Returns a list of dictionaries, one per class, with these keys:

- `class`
- `precision`
- `recall`
- `AP`
- `interpolated precision`
- `interpolated recall`
- `total positives`
- `total TP`
- `total FP`

`precision`, `recall`, and interpolation fields are NumPy arrays or lists depending on the method path. Convert them with `list(...)` or `.tolist()` before JSON serialization.

`PlotPrecisionRecallCurve` signature:

```python
Evaluator().PlotPrecisionRecallCurve(
    boundingBoxes,
    IOUThreshold=0.5,
    method=MethodAveragePrecision.EveryPointInterpolation,
    showAP=False,
    showInterpolatedPrecision=False,
    savePath=None,
    showGraphic=True,
)
```

For automation, prefer `GetPascalVOCMetrics`. If plotting is required, set a headless backend before import, pass `showGraphic=False`, and ensure `savePath` exists if you want image files.

Static helpers:

| Helper | Use |
|---|---|
| `Evaluator.CalculateAveragePrecision(rec, prec)` | Every-point interpolated AP from recall/precision arrays. |
| `Evaluator.ElevenPointInterpolatedAP(rec, prec)` | VOC 11-point AP from recall/precision arrays. |
| `Evaluator.iou(boxA, boxB)` | IoU for `(x1, y1, x2, y2)` boxes using inclusive pixel-area arithmetic. |

## Complete in-memory metric example

```python
boxes = BoundingBoxes()
boxes.addBoundingBox(BoundingBox("img-1", "person", 10, 10, 50, 50,
                                 CoordinatesType.Absolute,
                                 bbType=BBType.GroundTruth,
                                 format=BBFormat.XYX2Y2))
boxes.addBoundingBox(BoundingBox("img-1", "person", 10, 10, 50, 50,
                                 CoordinatesType.Absolute,
                                 bbType=BBType.Detected,
                                 classConfidence=0.99,
                                 format=BBFormat.XYX2Y2))

method = MethodAveragePrecision.EveryPointInterpolation
result = Evaluator().GetPascalVOCMetrics(boxes, IOUThreshold=0.5, method=method)[0]
assert result["class"] == "person"
assert float(result["AP"]) == 1.0
assert int(result["total TP"]) == 1
assert int(result["total FP"]) == 0
```

## Source evidence

Distilled from `lib/BoundingBox.py`, `lib/BoundingBoxes.py`, `lib/Evaluator.py`, `lib/utils.py`, and the programmatic samples under `samples/sample_1/` and `samples/sample_2/`.
