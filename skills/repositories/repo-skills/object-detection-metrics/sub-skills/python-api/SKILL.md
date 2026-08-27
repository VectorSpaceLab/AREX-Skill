---
name: python-api
description: "Programmatic Object-Detection-Metrics API guidance for
  BoundingBox, BoundingBoxes, Evaluator, enums, coordinate conversion, AP/mAP
  semantics, and source-style import diagnostics."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Python API sub-skill

Use this sub-skill when the task needs direct, in-memory use of the legacy Object-Detection-Metrics classes instead of a text-folder CLI workflow.

## Best-fit triggers

- Construct `BoundingBox` / `BoundingBoxes` objects directly from Python data.
- Compute AP or mAP from in-memory detections and ground truths with `Evaluator.GetPascalVOCMetrics`.
- Select `EveryPointInterpolation` versus `ElevenPointInterpolation`.
- Convert relative YOLO-style center coordinates into the repository's absolute box representation.
- Diagnose source-style imports, OpenCV import failures, or headless plotting/drawing caveats.

## Route away

- For end-to-end evaluation from ground-truth and detection text folders, use `../file-evaluation/SKILL.md`; that path owns safe folder parsing and the self-contained CLI helper.
- For COCO metrics, the newer successor toolkit, model training, inference, or benchmark-paper analysis, do not use this legacy PASCAL VOC API skill.

## Operating checklist

1. Prepare a Python process that can import from a user-provided checkout or copied `lib/` directory. The repo is source-style, so add the `lib` directory itself to `sys.path`; do not expect a pip package import.
2. Read `references/api-reference.md` for verified signatures, enums, class responsibilities, and in-memory usage patterns.
3. Read `references/metric-behavior.md` before interpreting AP, TP/FP, duplicate detections, relative coordinates, or IoU edge cases.
4. Use `scripts/api_metric_smoke.py --repo-root PATH` or `--lib-dir PATH` to verify a user-provided checkout/copy before relying on it.
5. If import, plotting, drawing, or coordinate errors occur, use `references/troubleshooting.md`.

## Minimal in-memory pattern

```python
import sys
from pathlib import Path

lib_dir = Path("/path/to/copied-or-checked-out/lib")
sys.path.insert(0, str(lib_dir))

from BoundingBox import BoundingBox
from BoundingBoxes import BoundingBoxes
from Evaluator import Evaluator
from utils import BBFormat, BBType, CoordinatesType, MethodAveragePrecision

boxes = BoundingBoxes()
boxes.addBoundingBox(BoundingBox("img-1", "person", 10, 10, 50, 50,
                                 CoordinatesType.Absolute, bbType=BBType.GroundTruth,
                                 format=BBFormat.XYX2Y2))
boxes.addBoundingBox(BoundingBox("img-1", "person", 10, 10, 50, 50,
                                 CoordinatesType.Absolute, bbType=BBType.Detected,
                                 classConfidence=0.99, format=BBFormat.XYX2Y2))
metrics = Evaluator().GetPascalVOCMetrics(
    boxes,
    IOUThreshold=0.5,
    method=MethodAveragePrecision.EveryPointInterpolation,
)
```

This should produce one `person` result with AP `1.0`, total positives `1`, total TP `1`, and total FP `0`.

## Distilled evidence

This sub-skill distills the repository's `lib/BoundingBox.py`, `lib/BoundingBoxes.py`, `lib/Evaluator.py`, `lib/utils.py`, and the programmatic examples under `samples/sample_1/` and `samples/sample_2/`. Those paths are evidence for the guidance here; runtime use should rely on the bundled references and script above.
