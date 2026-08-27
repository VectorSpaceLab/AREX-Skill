# Python API troubleshooting

## `ModuleNotFoundError: BoundingBox`, `BoundingBoxes`, `Evaluator`, or `utils`

This repository is source-style, not a pip-installable distribution. Add the `lib` directory itself to `sys.path`:

```python
from pathlib import Path
import sys
sys.path.insert(0, str(Path("/path/to/lib")))
```

Do not add the repository root and expect `import lib.BoundingBox`; the source modules use unqualified intra-module imports.

## `ModuleNotFoundError: cv2`

`utils.py` imports OpenCV at import time. This can fail even if you only need metric computation and never draw images. Install an OpenCV wheel appropriate for the environment, usually `opencv-python-headless` for non-GUI servers.

## Matplotlib or display errors

`Evaluator.py` imports `matplotlib.pyplot`. In headless automation:

```python
import os
os.environ.setdefault("MPLBACKEND", "Agg")
```

Set that before importing `Evaluator`. Prefer `GetPascalVOCMetrics` for metrics. If plotting is required, call `PlotPrecisionRecallCurve(..., showGraphic=False, savePath="existing-directory")`.

## `imgSize` is required for relative coordinates

Relative boxes need the image size:

```python
BoundingBox("img", "person", 0.5, 0.5, 0.25, 0.25,
            CoordinatesType.Relative,
            imgSize=(640, 480),
            bbType=BBType.GroundTruth,
            format=BBFormat.XYWH)
```

Relative values are center coordinates plus width/height. They are not normalized top-left/right-bottom coordinates. Relative coordinates only support `BBFormat.XYWH` in this implementation.

## Detection boxes require `classConfidence`

A detection must include a confidence:

```python
BoundingBox("img", "person", 10, 10, 50, 50,
            CoordinatesType.Absolute,
            bbType=BBType.Detected,
            classConfidence=0.9,
            format=BBFormat.XYX2Y2)
```

The enum is `BBType.Detected`. Some text in the original error message says `Detection`, but the actual enum member is `Detected`.

## `BBFormat.XYX2Y2` versus `xyrb`

The API enum `BBFormat.XYX2Y2` means `(left, top, right, bottom)`. This is the same coordinate idea that the README/CLI calls `xyrb`. For `(left, top, width, height)`, use `BBFormat.XYWH`.

## Duplicate detections look like a perfect AP

If one correct high-confidence detection reaches full recall before duplicate detections, AP can remain `1.0` even though duplicate detections are counted as FP. Check `total TP`, `total FP`, and precision arrays when debugging duplicate detector output.

## All detections become FP

Check these first:

- `imageName` strings match exactly between ground truth and detections.
- `classId` strings match exactly.
- The coordinate format matches the numbers you supplied (`XYWH` versus `XYX2Y2`).
- The IoU threshold is appropriate.
- Relative boxes used the correct `imgSize=(width, height)`.

## NaN, inf, or divide-by-zero behavior

The evaluator builds classes from both detections and ground truths. If a class appears only in detections, `total positives` is zero and recall/AP calculations may emit invalid values. Filter those detections, add corresponding ground truths, or handle zero-positive classes before averaging mAP.

## Drawing failures

`drawAllBoundingBoxes(image, imageName)` expects a valid OpenCV image array and a matching image name. If `cv2.imread` returned `None`, fix the caller's image loading before drawing. The method returns the modified image; it does not save files by itself.

## Quick diagnostic

Use the bundled helper with a user-provided checkout or copied `lib` directory:

```bash
python scripts/api_metric_smoke.py --repo-root PATH --ap-method every-point
python scripts/api_metric_smoke.py --lib-dir PATH_TO_LIB --ap-method eleven-point --case duplicate
```

The helper imports the source modules, creates tiny in-memory boxes, routes the selected AP enum, and prints expected AP/TP/FP values without opening windows, writing images, or using network access.
