---
name: inference-and-results
description: "Use this sub-skill for Ultralytics YOLO predict workflows, source
  handling, streaming and batching, Results extraction,
  saving/plotting/cropping, and thread-safe inference."
disable-model-invocation: true
metadata:
  disco-role: operating
license: AGPL 3.0
---

# Inference and Results

Use this sub-skill when a task asks an agent to run Ultralytics inference or consume prediction outputs. It covers Python `YOLO(...)(source)`, `model.predict(source=...)`, CLI `yolo predict`, memory-safe streaming, batch/source choices, task-specific `Results` extraction, plotting/saving/cropping, and concurrent inference safety.

## Route elsewhere

- Dataset YAMLs, label formats, config overrides, and path validation belong in `../data-and-configuration/`.
- Training, validation metrics, callbacks for train/val, and checkpoint selection belong in `../training-and-validation/`.
- Model family/task selection across YOLO, YOLOWorld, YOLOE, SAM, FastSAM, NAS, and RTDETR belongs in `../model-families-and-tasks/`.
- Exported model formats, ONNX/OpenCV Runtime deployment, and benchmark/deploy tradeoffs belong in `../export-and-deployment/`.
- Tracking IDs, tracker configs, and solution apps belong in `../tracking-and-solutions/`.
- Repository contribution, testing, and maintenance workflows belong in `../repo-development/`.

## Start Here

1. Pick the entry point: Python `from ultralytics import YOLO` for application code, or CLI `yolo predict model=... source=...` for one-off prediction runs.
2. Use an explicit local model path when possible. Names such as `yolo26n.pt`, `yolo26n-seg.pt`, or `yolo26n-cls.pt` may trigger downloads if the weights are not present.
3. Pass predictor overrides as keyword arguments in Python or `arg=value` pairs in CLI, for example `imgsz=640`, `conf=0.25`, `device=cpu`, `save=True`, `save_txt=True`, `project=runs/predict`, `name=exp`.
4. Use `stream=True` for videos, webcams, RTSP/RTMP/TCP streams, screenshots, very large directories, and long source lists; iterate the generator immediately.
5. Branch on task-specific `Results` fields before access. Classification has `probs` and no boxes; semantic segmentation has `semantic_mask` and no instance boxes/masks.
6. Use `result.cpu()`, `result.numpy()`, or `result.to(...)` before handing tensors to non-Torch post-processing or JSON/CSV/dataframe conversion.

## Common Entry Points

```python
from ultralytics import YOLO

model = YOLO("weights.pt")
results = model.predict(source="image.jpg", imgsz=640, conf=0.25, device="cpu")
for result in results:
    print(result.path, result.speed, result.summary(normalize=True))
```

```python
from ultralytics import YOLO

model = YOLO("weights.pt")
for result in model("video.mp4", stream=True, imgsz=640):
    if result.boxes is not None:
        boxes = result.boxes.xyxy.cpu().tolist()
```

```bash
yolo predict model=weights.pt source=image.jpg imgsz=640 conf=0.25 save=True
```

The CLI syntax is `yolo TASK MODE arg=value`; `TASK` is optional for many models, but `MODE` is required. Prefer `yolo predict model=... source=...` unless a task-specific prefix is needed, such as `yolo segment predict model=... source=...`.

## Result Routing Checklist

- Detect: read `result.boxes` only after `if result.boxes is not None`.
- Segment: read both `result.boxes` and `result.masks`; `retina_masks=True` requests masks scaled to the original image shape.
- Semantic: read `result.semantic_mask.data`; do not expect `result.boxes`, `result.masks.xy`, or per-instance polygons.
- Classify: read `result.probs.top1`, `top1conf`, `top5`, and `top5conf`; do not call crop/box code.
- Pose: read `result.boxes` plus `result.keypoints.xy`, `xyn`, and optional `conf`.
- OBB: read `result.obb.xywhr` or `xyxyxyxy`; `result.obb.xyxy` is the enclosing axis-aligned rectangle, not the rotated box.

## Save and Visualization Rules

- `result.plot()` returns an annotated image array; by default it is suitable for OpenCV-style BGR handling, while `plot(pil=True)` returns a PIL image.
- `result.save(filename="out.jpg")` writes the annotated image and creates missing parent directories.
- `result.save_txt(path, save_conf=True)` supports detection, segmentation, pose, OBB, and classification text outputs, but not semantic segmentation.
- `result.save_crop(save_dir=...)` supports box-based detection/segmentation/pose, but not classification, OBB, or semantic segmentation.
- CLI `save=True`, `save_txt=True`, `save_conf=True`, and `save_crop=True` create output files under the predictor save directory; set `project`, `name`, and `exist_ok=True` when deterministic output paths matter.
- Avoid `show=True` on headless systems; use `save=True` or `result.plot()` and encode/display with a terminal or notebook-aware tool instead.

## Thread-Safe Inference

Ultralytics predictors use an internal lock during `stream_inference`, but application-level threading should still avoid sharing mutable model state across threads unless access is serialized. The safest pattern is one `YOLO` instance per worker thread or process. If memory forces shared-model use, wrap the shared inference function with `ultralytics.utils.ThreadingLocked` and expect serialized throughput.

## References

- Prediction workflows and source handling: `references/workflows.md`
- Results extraction contract: `references/api-reference.md`
- Failure diagnosis and fixes: `references/troubleshooting.md`
- Download-free result schema helper: `scripts/inspect_results_contract.py`
