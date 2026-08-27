---
name: tracking-and-solutions
description: "Use for Ultralytics track mode, tracker YAML selection, persistent
  object IDs, and YOLO Solutions such as counting, heatmaps, speed, queue,
  region, similarity search, and Streamlit inference."
disable-model-invocation: true
metadata:
  disco-role: operating
license: AGPL 3.0
---

# Tracking and Solutions

Use this sub-skill when the user asks for `model.track(...)`, `yolo track`, tracker configuration, object IDs across video frames, or Ultralytics Solutions workflows such as object counting, heatmaps, speed estimation, queue management, region counting, similarity search, and Streamlit live inference.

## Route Elsewhere

- Generic predict/result parsing without persistent IDs: `../inference-and-results/SKILL.md`
- Dataset YAMLs, config files, class names, and path validation: `../data-and-configuration/SKILL.md`
- Train/val runs, metrics, and dataset evaluation: `../training-and-validation/SKILL.md`
- Export formats, deployment runtimes, benchmarks, and engine-specific failures: `../export-and-deployment/SKILL.md`
- Model family/task selection before choosing weights: `../model-families-and-tasks/SKILL.md`
- Repository maintenance, tests, and development workflows: `../repo-development/SKILL.md`

## Fast Path

1. Confirm the model, task, and source are tracking-compatible; classification does not support `mode=track`.
2. For direct tracking, use `YOLO(...).track(source=..., tracker="botsort.yaml", stream=True, show=False)` for full videos, or `persist=True` when feeding frames manually.
3. For CLI tracking, use the Ultralytics `arg=value` form: `yolo track model=yolo26n.pt source=video.mp4 tracker=bytetrack.yaml conf=0.25`.
4. Pick a tracker using `scripts/choose_tracker.py` and then tune only copied YAML values; keep `tracker_type` unchanged in custom tracker YAMLs.
5. For counting, heatmap, speed, queue, region, trackzone, similarity search, or Streamlit inference, use `references/workflows.md` and pass `source`, `model`, `region`, `classes`, `tracker`, `device`, `conf`, and `iou` explicitly.
6. Check `references/troubleshooting.md` before advising installs, downloads, GUI display, webcam/network streams, GPU/FP16, or optional ReID/search/Streamlit dependencies.

## Safe Examples

Direct tracking API:

```python
from ultralytics import YOLO

model = YOLO("yolo26n.pt")
for result in model.track(source="video.mp4", stream=True, tracker="bytetrack.yaml", conf=0.25, show=False):
    boxes = result.obb if result.obb is not None else result.boxes
    if boxes is not None and boxes.is_track:
        print(boxes.id.cpu().tolist())
```

Manual frame loop with persistent IDs:

```python
results = model.track(frame, persist=True, tracker="botsort.yaml", verbose=False)
```

Solutions CLI with a polygon region:

```bash
yolo solutions region source="video.mp4" model=yolo26n.pt tracker=botsort.yaml region="[(20,400),(1080,400),(1080,360),(20,360)]" show=False
```

Tracker recommendation helper:

```bash
python sub-skills/tracking-and-solutions/scripts/choose_tracker.py --goal reid --moving-camera --prefer-stable-ids
```

## References

- Tracking APIs, CLI commands, tracker YAMLs, and customization: `references/api-reference.md`
- Solutions workflows, class/CLI mapping, regions, outputs, and optional apps: `references/workflows.md`
- Workflow-specific failure diagnosis and recovery: `references/troubleshooting.md`
- Safe tracker recommendation helper: `scripts/choose_tracker.py`
