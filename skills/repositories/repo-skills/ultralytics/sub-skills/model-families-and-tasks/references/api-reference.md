# Model Selection API Reference

This compact API reference lists public constructors, task compatibility, result fields, and high-risk arguments for selecting Ultralytics model families. It is intentionally limited to model/task selection; use sibling sub-skills for full train, validation, inference, tracking, and export workflows.

## Verified Public Constructors

The public package facts for version `8.4.72` expose these constructors:

```python
from ultralytics import YOLO, YOLOWorld, YOLOE, NAS, SAM, FastSAM, RTDETR
```

| Class | Constructor shape | Task map | Notes |
| --- | --- | --- | --- |
| `YOLO` | `YOLO(model="yolo26n.pt", task=None, verbose=False)` | `classify`, `detect`, `segment`, `pose`, `obb`, `semantic` | Auto-switches to `YOLOWorld` for `-world`, to `YOLOE` for `yoloe`, and to `RTDETR` for RT-DETR model heads. |
| `YOLOWorld` | `YOLOWorld(model="yolov8s-world.pt", verbose=False)` | `detect` | Use `set_classes(list[str])` for custom text labels. |
| `YOLOE` | `YOLOE(model="yoloe-11s-seg.pt", task=None, verbose=False)` | `detect`, `segment` | Supports `set_classes`, `set_vocab`, text embeddings, and visual prompts. |
| `SAM` | `SAM(model="sam_b.pt")` | `segment` predictor only | Requires `.pt` or `.pth`; detects SAM2/SAM3 from filename stem. |
| `FastSAM` | `FastSAM(model="FastSAM-x.pt")` | `segment` predictor/validator | Rejects YAML configs; `FastSAM.pt` aliases to `FastSAM-x.pt`. |
| `NAS` | `NAS(model="yolo_nas_s.pt")` | `detect` predictor/validator | Rejects YAML configs; non-`.pt` names require `super_gradients`. |
| `RTDETR` | `RTDETR(model="rtdetr-l.pt")` | `detect` trainer/validator/predictor | Requires `torch>=1.11`. |

## Result Field by Task

| Task | Expected `Results` field | Typical downstream implication |
| --- | --- | --- |
| `detect` | `result.boxes` | Suitable for box-level inference, counting, and tracking. |
| `segment` | `result.masks`, often `result.boxes` | Suitable for instance masks, object-level measurements, and some tracking. |
| `semantic` | `result.semantic_mask` | Dense pixel class map; do not assume boxes, instance IDs, confidences, or polygons. |
| `classify` | `result.probs` | Whole-image class probabilities only. |
| `pose` | `result.keypoints`, `result.boxes` | Keypoints belong to detected instances. |
| `obb` | `result.obb` | Rotated boxes; use OBB accessors rather than `boxes`. |

## Important Methods

### `YOLOWorld.set_classes`

```python
model = YOLOWorld("yolov8s-worldv2.pt")
model.set_classes(["forklift", "hard hat", "traffic cone"])
```

This sets detection class names for open-vocabulary YOLO-World. It remains a detection model; output is boxes, not masks.

### `YOLOE.set_classes` and `YOLOE.predict`

```python
model = YOLOE("yoloe-26s-seg.pt")
model.set_classes(["hard hat", "safety vest"])
results = model.predict("path/to/image.jpg")
```

For visual prompts:

```python
prompts = {"bboxes": [[10, 20, 100, 200]], "cls": ["hard hat"]}
results = model.predict("path/to/image.jpg", visual_prompts=prompts)
```

`visual_prompts` must include both `bboxes` and `cls`, and the lists must have equal lengths.

### `SAM.predict`

```python
sam = SAM("sam_b.pt")
results = sam.predict("path/to/image.jpg", bboxes=[[100, 100, 300, 300]])
results = sam.predict("path/to/image.jpg", points=[[500, 375]], labels=[1])
```

SAM uses promptable segmentation. With no prompt, the predictor may generate masks for the image depending on predictor behavior and arguments.

### `SAM3SemanticPredictor`

Use this predictor for SAM3 text concept segmentation and exemplar-style concept matching:

```python
from ultralytics.models.sam import SAM3SemanticPredictor

overrides = dict(conf=0.25, task="segment", mode="predict", model="sam3.pt", save=False)
predictor = SAM3SemanticPredictor(overrides=overrides)
predictor.set_image("path/to/image.jpg")
results = predictor(text=["red apple", "yellow bus"])
```

Plain `SAM("sam3.pt")` identifies the SAM3 model and uses SAM3 predictor routing, but concept segmentation examples use the semantic predictor class directly.

### `FastSAM.predict`

```python
model = FastSAM("FastSAM-s.pt")
results = model.predict(
    "path/to/image.jpg",
    bboxes=[[100, 100, 200, 200]],
    points=[[150, 150]],
    labels=[1],
    texts=["dog"],
)
```

FastSAM is promptable instance segmentation. It is not a dense semantic segmentation model and not a replacement for SAM3 concept segmentation when text concepts must find all matching instances.

## Naming Cheat Sheet

- `yolo26n.pt`: YOLO detection.
- `yolo26n-seg.pt`: YOLO instance segmentation.
- `yolo26n-sem.pt`: YOLO semantic segmentation.
- `yolo26n-cls.pt`: YOLO classification.
- `yolo26n-pose.pt`: YOLO pose.
- `yolo26n-obb.pt`: YOLO oriented boxes.
- `yolov8s-world.pt`, `yolov8s-worldv2.pt`: YOLO-World detection.
- `yoloe-26s-seg.pt`, `yoloe-11s-seg.pt`, `yoloe-...-pf.pt`: YOLOE promptable/open-vocabulary variants.
- `sam_b.pt`, `sam2_...pt`, `sam3.pt`: SAM family segmentation.
- `FastSAM-s.pt`, `FastSAM-x.pt`: FastSAM promptable instance segmentation.
- `rtdetr-l.pt`, `rtdetr-x.pt`: RT-DETR detection.
- `yolo_nas_s.pt`, `yolo_nas_m.pt`, `yolo_nas_l.pt`: YOLO-NAS detection.

## Side-Effect Awareness

Instantiating models with official weight names may download weights on first use, except SAM3 docs note that `sam3.pt` is not automatically downloaded and requires separate access. Running `predict`, `val`, `train`, `export`, or `track` may read media/data, write results, download assets, use GPU/CPU memory, or start long-running work. For model selection only, prefer this sub-skill's bundled `scripts/model_family_lookup.py`, source inspection, or minimal code that does not call the model.
