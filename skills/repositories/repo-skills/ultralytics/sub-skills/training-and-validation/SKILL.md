---
name: training-and-validation
description: "Plan and troubleshoot Ultralytics YOLO training, validation,
  resume, tuning, device selection, trainer/validator ownership, and metrics
  workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: AGPL 3.0
---

# Training and Validation

Use this sub-skill when the user needs to train or validate Ultralytics models through `model.train()`, `model.val()`, `model.tune()`, `yolo train`, or `yolo val`, including resume behavior, CPU/GPU/MPS device choices, and metric interpretation.

## Route Here For

- Creating safe train or validation commands with `yolo TASK MODE arg=value` or Python `YOLO(...).train()/val()/tune()`.
- Resuming interrupted training from `last.pt`, diagnosing missing or non-resumable checkpoint state, or choosing between resume and a fresh fine-tune.
- Selecting `device`, `batch`, `workers`, `amp`, `compile`, `cache`, `fraction`, `patience`, `optimizer`, and tuning options for constrained hardware.
- Reading validation outputs such as `metrics.box.map`, `metrics.box.map50`, `metrics.confusion_matrix`, `to_df()`, `to_csv()`, and `to_json()`.
- Explaining trainer/validator ownership, callbacks, result directories, checkpoints, and where side effects are written.

## Do Not Handle Here

- Dataset YAML layout, class names, custom data paths, and config-file authoring; route to `../data-and-configuration/SKILL.md`.
- Choosing model families, task names, or checkpoint variants; route to `../model-families-and-tasks/SKILL.md`.
- Prediction result objects, streaming inference, saving inference media, or post-processing; route to `../inference-and-results/SKILL.md`.
- Export, deployment, benchmark formats, TensorRT/ONNX conversion, or serving; route to `../export-and-deployment/SKILL.md`.
- Tracking and solutions workflows; route to `../tracking-and-solutions/SKILL.md`.
- Repository development, source tests, or maintainer workflows; route to `../repo-development/SKILL.md`.

## Start With These References

- `references/workflows.md` for train, validation, resume, tuning, device, and metrics patterns.
- `references/api-reference.md` for Python API/CLI argument shape and trainer/validator ownership.
- `references/troubleshooting.md` for install/import, CLI syntax, data/config, backend/device, network/download, checkpoint, and side-effect failures.
- `scripts/plan_training_run.py` to generate safe CPU/tiny-fixture train/val/tune command plans without executing training.

## Safe Planning Defaults

Prefer a dry plan before running any training. For smoke tests or examples, default to `device=cpu`, `imgsz=32`, `epochs=1`, `batch=1`, `workers=0`, `plots=False`, and a tiny dataset such as `coco8.yaml` only when a download is acceptable. If the user wants to avoid downloads, require a local dataset YAML or prepared fixture and route data-layout checks to `data-and-configuration`.

## Common Command Shapes

```bash
yolo detect train model=yolo26n.pt data=coco8.yaml epochs=1 imgsz=32 device=cpu batch=1 workers=0 plots=False
yolo detect val model=yolo26n.pt data=coco8.yaml imgsz=32 device=cpu batch=1 plots=False
python scripts/plan_training_run.py --mode train --task detect --model yolo26n.pt --data coco8.yaml --cpu-tiny
```

```python
from ultralytics import YOLO

model = YOLO("yolo26n.pt")
metrics = model.train(data="coco8.yaml", epochs=1, imgsz=32, device="cpu", batch=1, workers=0, plots=False)
metrics = model.val(data="coco8.yaml", imgsz=32, device="cpu", batch=1, plots=False)
```

## Handoff Notes

Training and validation create run directories and may download model weights or datasets when names such as `yolo26n.pt` or `coco8.yaml` are not already available. Always surface those side effects before execution, and use the bundled planner script when the user asks for a safe plan rather than an actual run.
