# Model Family and Task Workflows

This reference helps future agents choose a public Ultralytics class, task string, model naming pattern, and expected output field before handing off to data, training, inference, export, or tracking sub-skills.

## Public Class Surface

The verified public package exports these model classes from `ultralytics`: `YOLO`, `YOLOWorld`, `YOLOE`, `NAS`, `SAM`, `FastSAM`, and `RTDETR`. The installed version used for extraction was `8.4.72`, with CLI entry points `yolo` and `ultralytics` and CLI shape `yolo TASK MODE arg=value`.

| Family | Public class | Main task(s) | Use when | Avoid when |
| --- | --- | --- | --- | --- |
| YOLO | `YOLO` | `detect`, `segment`, `semantic`, `classify`, `pose`, `obb` | Standard YOLO model YAMLs or `.pt` weights, including YOLOv3/v5/v8/v9/v10/11/12/26 style names | Need SAM-style promptable segmentation or a detector-only non-YOLO family |
| YOLO-World | `YOLOWorld` or `YOLO("...-world.pt")` | `detect` | Open-vocabulary detection with a class list set by text labels | Need masks, dense class maps, keypoints, OBB, or classification |
| YOLOE | `YOLOE` or `YOLO("yoloe-...")` | `detect`, `segment` | Open-vocabulary/promptable detection or instance segmentation with text/visual/internal vocabulary prompts | Need semantic class-map output or ordinary fixed-label YOLO simplicity |
| SAM/SAM2/SAM3 | `SAM` plus SAM predictor classes | `segment` | Promptable segmentation with points, boxes, masks, SAM2/SAM3 weights, or SAM3 concept prompts | Need YOLO trainable detector/classifier/pose/OBB workflows |
| FastSAM | `FastSAM` | `segment` | Faster CNN-based promptable instance segmentation using `FastSAM-s.pt` or `FastSAM-x.pt` | Need YAML training from scratch or SAM3 concept segmentation |
| YOLO-NAS | `NAS` | `detect` | YOLO-NAS pretrained detection and validation/export workflows | Need training through Ultralytics or YAML architecture construction |
| RT-DETR | `RTDETR` | `detect` | Transformer-based real-time object detection, especially RT-DETR L/X weights | Need non-detection task outputs |

## YOLO Task Routing

Choose the task from the output contract. This avoids a frequent error: routing all segmentation requests to `segment` even when the user asks for dense semantic segmentation.

| Desired output | Task | Model naming cue | Python class | Primary result field | CLI task |
| --- | --- | --- | --- | --- | --- |
| Axis-aligned boxes with classes/confidence | `detect` | default names such as `yolo26n.pt` | `YOLO` | `result.boxes` | `yolo detect predict ...` or often `yolo predict ...` |
| One mask per object instance plus labels/confidence | `segment` | `-seg`, such as `yolo26n-seg.pt` | `YOLO` | `result.masks` and usually `result.boxes` | `yolo segment predict ...` |
| One dense class ID map per image | `semantic` | `-sem`, such as `yolo26n-sem.pt` | `YOLO` | `result.semantic_mask` | `yolo semantic predict ...` |
| Whole-image class probabilities | `classify` | `-cls`, such as `yolo26n-cls.pt` | `YOLO` | `result.probs` | `yolo classify predict ...` |
| Keypoints for detected instances | `pose` | `-pose`, such as `yolo26n-pose.pt` | `YOLO` | `result.keypoints` and `result.boxes` | `yolo pose predict ...` |
| Rotated boxes | `obb` | `-obb`, such as `yolo26n-obb.pt` | `YOLO` | `result.obb` | `yolo obb predict ...` |

Minimal examples:

```python
from ultralytics import YOLO

box_model = YOLO("yolo26n.pt")
mask_model = YOLO("yolo26n-seg.pt")
dense_model = YOLO("yolo26n-sem.pt", task="semantic")
pose_model = YOLO("yolo26n-pose.pt")
obb_model = YOLO("yolo26n-obb.pt")
```

```bash
yolo detect predict model=yolo26n.pt source=path/to/image.jpg save=False
yolo segment predict model=yolo26n-seg.pt source=path/to/image.jpg save=False
yolo semantic predict model=yolo26n-sem.pt source=path/to/image.jpg save=False
yolo classify predict model=yolo26n-cls.pt source=path/to/image.jpg save=False
yolo pose predict model=yolo26n-pose.pt source=path/to/image.jpg save=False
yolo obb predict model=yolo26n-obb.pt source=path/to/image.jpg save=False
```

### Instance vs Semantic Segmentation

Use `segment` for object-level masks. It returns one mask per detected instance, along with class IDs and confidences. This fits object counting, cropping, object-level measurement, and some tracking pipelines.

Use `semantic` for pixel-level class maps. It returns one image-sized class map in `result.semantic_mask`, where same-class regions are merged and there are no per-instance boxes or polygon lists by default. Do not route semantic segmentation to tracking unless another workflow explicitly derives objects from the dense map.

## Model YAML and Weight Naming

Official config evidence includes standard YOLO generations and task suffixes under model config directories. Use these naming cues when creating a model from YAML, loading pretrained weights, or debugging task auto-detection.

- Current standard YOLO26 names include `yolo26.yaml`, `yolo26-seg.yaml`, `yolo26-sem.yaml`, `yolo26-cls.yaml`, `yolo26-pose.yaml`, `yolo26-obb.yaml`, plus `p2`/`p6` variants.
- YOLO11 and YOLO12 follow similar task suffixes for detect, segment, classify, pose, and OBB; YOLO26 adds semantic configs.
- YOLOv8 includes `yolov8-world.yaml`, `yolov8-worldv2.yaml`, RT-DETR compatibility YAML, segmentation, OBB, pose, classify, and detect variants.
- RT-DETR config names include `rtdetr-l.yaml`, `rtdetr-x.yaml`, `rtdetr-resnet50.yaml`, and `rtdetr-resnet101.yaml`; pretrained weights are primarily `rtdetr-l.pt` and `rtdetr-x.pt`.
- YOLOE config/weight cues include `yoloe-11...`, `yoloe-26...`, `yoloe-v8...`, optional `-seg`, and prompt-free `-pf` weights in docs.
- `FastSAM` and `NAS` do not accept YAML configs in their public constructors; use supported pretrained names or local weights.

When the task cannot be inferred reliably from a custom filename, pass `task=` explicitly for `YOLO`, for example `YOLO("custom-semantic-best.pt", task="semantic")`.

## Open-Vocabulary Models

### YOLO-World

Use `YOLOWorld` for open-vocabulary object detection when the desired output is still boxes/classes/confidences. It maps only the `detect` task.

```python
from ultralytics import YOLOWorld

model = YOLOWorld("yolov8s-worldv2.pt")
model.set_classes(["bus", "traffic light", "construction cone"])
results = model.predict("path/to/image.jpg", imgsz=640)
boxes = results[0].boxes
```

`YOLO("yolov8s-world.pt")` also auto-switches to `YOLOWorld` because the YOLO constructor checks for `-world` in supported `.pt`/YAML names.

### YOLOE

Use `YOLOE` when the user needs open-vocabulary detection or instance segmentation with text, visual prompts, or prompt-free vocabulary behavior. The public task map supports `detect` and `segment`.

```python
from ultralytics import YOLOE

model = YOLOE("yoloe-26s-seg.pt")
model.set_classes(["safety vest", "hard hat"])
results = model.predict("path/to/image.jpg")
```

For visual prompts, pass matching `bboxes` and `cls` lists in `visual_prompts`; the API asserts both keys exist and have equal lengths.

```python
prompts = {"bboxes": [[10, 20, 100, 200]], "cls": ["hard hat"]}
results = model.predict("path/to/image.jpg", visual_prompts=prompts)
```

If training YOLOE, use the training sub-skill because YOLOE docs require task-specific trainers for detection vs segmentation fine-tuning.

## Promptable Segmentation

### SAM, SAM2, and SAM3

`SAM("sam_b.pt")`, `SAM("sam2_....pt")`, and `SAM("sam3.pt")` are all routed through the `SAM` class with task `segment`. The constructor requires `.pt` or `.pth` weights. Standard SAM/SAM2 visual prompts include bounding boxes, points, labels, and masks.

```python
from ultralytics import SAM

sam = SAM("sam_b.pt")
results = sam.predict("path/to/image.jpg", points=[[500, 375]], labels=[1])
```

SAM3 has two important modes:

- Visual prompt segmentation through `SAM("sam3.pt")`/SAM3 predictor behavior for points, boxes, and masks.
- Concept segmentation through SAM3 semantic predictor classes for text prompts and image exemplars, where output is all matching instances for a concept.

For SAM3 concept segmentation, the docs use `SAM3SemanticPredictor` directly rather than plain `SAM(...).predict(text=...)`:

```python
from ultralytics.models.sam import SAM3SemanticPredictor

overrides = dict(conf=0.25, task="segment", mode="predict", model="sam3.pt", save=False)
predictor = SAM3SemanticPredictor(overrides=overrides)
predictor.set_image("path/to/image.jpg")
results = predictor(text=["yellow school bus", "person wearing helmet"])
```

SAM3 weights are not automatically downloaded in the docs. Users must obtain approved weights separately. This is a selection constraint, not a code bug.

### FastSAM

Use `FastSAM` for efficient promptable instance segmentation when supported weights are available. It supports `bboxes`, `points`, `labels`, and `texts` in `predict`, but it is not SAM3 concept segmentation and does not accept YAML models.

```python
from ultralytics import FastSAM

model = FastSAM("FastSAM-s.pt")
results = model.predict("path/to/image.jpg", bboxes=[[100, 100, 200, 200]], imgsz=1024)
```

## Specialized Detection Families

### RT-DETR

Use `RTDETR` for RT-DETR detection. It requires `torch>=1.11`, supports `.pt` and YAML-style model names, and exposes detector trainer/validator/predictor classes.

```python
from ultralytics import RTDETR

model = RTDETR("rtdetr-l.pt")
results = model.predict("path/to/image.jpg")
```

RT-DETR is detection-only. For speed/accuracy trade-offs, the docs describe `head.decoder.eval_idx` and `head.num_queries`; hand that to export/deployment after model selection.

### YOLO-NAS

Use `NAS` for YOLO-NAS pretrained detection. It is detection-only, does not support training through Ultralytics, and does not accept YAML configs. It imports `super_gradients` when loading non-`.pt` model names.

```python
from ultralytics import NAS

model = NAS("yolo_nas_s.pt")
results = model.predict("path/to/image.jpg")
```

## CLI Ordering and Handoff

Ultralytics CLI accepts `yolo TASK MODE arg=value`. If a user writes positional flags or shell-style `--model`, convert to key-value form:

```bash
yolo detect predict model=yolo26n.pt source=path/to/image.jpg imgsz=640 device=cpu save=False
```

After selecting family/task, hand off to sibling sub-skills:

- Dataset or config details: `../data-and-configuration/`.
- Training/validation invocation: `../training-and-validation/`.
- Predicting and reading `Results`: `../inference-and-results/`.
- Export/deployment: `../export-and-deployment/`.
- Tracking: `../tracking-and-solutions/`, but only when the selected task emits object detections or masks compatible with tracking.
