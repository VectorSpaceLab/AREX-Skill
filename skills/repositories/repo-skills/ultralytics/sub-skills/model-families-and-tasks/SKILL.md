---
name: model-families-and-tasks
description: "Choose the correct Ultralytics model class, family, task, model
  naming pattern, and expected result fields before using train, val, predict,
  track, or export workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: AGPL 3.0
---

# Model Families and Tasks

Use this sub-skill when the user needs to decide which Ultralytics model class or model filename fits a vision task, output shape, prompt style, or model family. It covers `YOLO`, `YOLOWorld`, `YOLOE`, `NAS`, `SAM`, `FastSAM`, and `RTDETR`; tasks `detect`, `segment`, `semantic`, `classify`, `pose`, and `obb`; and YAML/weight naming cues.

## Quick Routing

- Need ordinary boxes, masks, classes, poses, OBB, or dense semantic maps from YOLO model names? Use `references/workflows.md#yolo-task-routing`.
- Need open-vocabulary boxes from text class names? Use `YOLOWorld` or `YOLOE` and see `references/workflows.md#open-vocabulary-models`.
- Need promptable segmentation with points, boxes, masks, text concepts, or exemplars? Use `SAM`/SAM2/SAM3 or `FastSAM` and see `references/workflows.md#promptable-segmentation`.
- Need RT-DETR or YOLO-NAS detection instead of YOLO? See `references/workflows.md#specialized-detection-families`.
- Need a safe local hint without importing Ultralytics or downloading weights? Run `python scripts/model_family_lookup.py --cue "semantic segmentation"`.

## Core Decisions

1. Choose the task from desired result fields, not from a visual buzzword:
   - `detect` returns `result.boxes` for axis-aligned boxes, classes, and confidences.
   - `segment` returns object-level `result.masks` plus usually boxes; this is instance segmentation.
   - `semantic` returns one dense `result.semantic_mask`; it is not a tracking/box workflow.
   - `classify` returns image-level `result.probs` and no object locations.
   - `pose` returns `result.keypoints` plus boxes for detected instances.
   - `obb` returns rotated boxes in `result.obb`, not ordinary `result.boxes`.
2. Choose the public class from model family constraints:
   - `YOLO(...)` handles standard YOLO tasks and auto-switches for `-world`, `yoloe`, and RT-DETR-headed models.
   - `YOLOWorld(...)` is detection-only open-vocabulary YOLO-World with `set_classes([...])`.
   - `YOLOE(...)` supports open-vocabulary detection and instance segmentation with text/visual prompting.
   - `SAM(...)` is promptable segmentation for SAM, SAM2, and SAM3 `.pt`/`.pth` weights.
   - `FastSAM(...)` is faster CNN-based promptable instance segmentation and requires weights, not YAML.
   - `NAS(...)` and `RTDETR(...)` are detection-only families.
3. Pick filenames by suffix when possible:
   - No suffix or family default, such as `yolo26n.pt`: `detect`.
   - `-seg`: instance segmentation.
   - `-sem`: semantic segmentation.
   - `-cls`: classification.
   - `-pose`: pose estimation.
   - `-obb`: oriented bounding boxes.
   - `-world`/`-worldv2`: YOLO-World detection.
   - `yoloe-...` and often `-seg`/`-pf`: YOLOE promptable open-vocabulary model.
   - `rtdetr-...`: RT-DETR detection.

## Safe Command Patterns

Prefer examples that do not accidentally start training, export, webcam, or network-heavy work while choosing a model:

```bash
python scripts/model_family_lookup.py --cue "SAM3 text prompt segmentation"
python scripts/model_family_lookup.py --cue "dense semantic mask no boxes"
yolo detect predict model=yolo26n.pt source=path/to/image.jpg device=cpu save=False
```

```python
from ultralytics import YOLO, YOLOWorld, YOLOE, SAM, FastSAM, NAS, RTDETR

model = YOLO("yolo26n-sem.pt", task="semantic")  # dense class-map output
world = YOLOWorld("yolov8s-worldv2.pt")
world.set_classes(["bus", "person"])
```

## Boundaries and Cross-Links

- For dataset YAMLs, label formats, config precedence, and bad `data=` paths, use `../data-and-configuration/`.
- For `train` and `val` procedures after model selection, use `../training-and-validation/`.
- For reading `Results`, streaming, prompt execution, and save behavior after selection, use `../inference-and-results/`.
- For export formats, backend limits, TensorRT/ONNX/CoreML, and deployment, use `../export-and-deployment/`.
- For object tracking and application solutions, use `../tracking-and-solutions/`.
- For repository maintenance, tests, contribution, or source edits, use `../repo-development/`.

## Troubleshooting First

If the task/model combination does not load or outputs do not match expectations, check `references/troubleshooting.md` before changing code. Common root causes are wrong task suffix, CLI ordering (`yolo TASK MODE arg=value`), missing optional dependencies, bad data/source paths, automatic weight download failures, and using semantic segmentation where downstream tracking expects boxes.
