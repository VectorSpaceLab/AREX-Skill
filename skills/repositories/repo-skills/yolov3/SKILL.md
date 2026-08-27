---
name: yolov3
description: "Operate Ultralytics YOLOv3 detection workflows: inference,
  training, validation, architecture, export, and maintenance."
disable-model-invocation: true
metadata:
  disco-role: operating
license: AGPL 3.0
---

# Ultralytics YOLOv3 Repo Skill

Use this skill for the Ultralytics YOLOv3 repository: detection-only YOLOv3, YOLOv3-SPP, and YOLOv3-tiny workflows.

## Route by task

- Inference, `detect.py`, PyTorch Hub, `DetectMultiBackend`, labels, crops, or input sources: read `sub-skills/inference/SKILL.md`.
- Training, custom dataset YAMLs, hyperparameters, checkpoints, resume, DDP, or smoke training: read `sub-skills/training/SKILL.md`.
- Validation, mAP, `val.py`, COCO JSON, speed/study, or saved validation artifacts: read `sub-skills/validation-evaluation/SKILL.md`.
- Model YAMLs, anchors, `Detect`, `Model`, `parse_model`, or output-shape debugging: read `sub-skills/model-architecture/SKILL.md`.
- Export formats, deployment suffixes, `export.py`, ONNX, OpenVINO, TensorRT, CoreML, TorchScript, or Paddle: read `sub-skills/export-deployment/SKILL.md`.
- Repository changes, CI smokes, dependency floors, docs, PR policy, or packaging metadata: read `sub-skills/repo-maintenance/SKILL.md`.

## Public setup

YOLOv3 is normally used from a source checkout:

```bash
python -m pip install -r requirements.txt
python - <<'PY'
import torch
from models.yolo import Model
m = Model('models/yolov3-tiny.yaml').eval()
y = m(torch.zeros(1, 3, 64, 64))[0]
print(tuple(y.shape))
PY
```

Expected tiny-model shape for 80 classes is `(1, 60, 85)`. Official weights such as `yolov3-tiny.pt` may download on first use, so ask before running network-dependent native commands.

## Shared references

- `references/repo-provenance.md` records the source snapshot and evidence basis.
- `references/package-and-environment.md` summarizes install, dependency, and backend facts.
- `references/troubleshooting.md` covers cross-cutting failures.
- `scripts/yolov3_repo_smoke_plan.py` prints safe native smoke-test commands and safety notes without running them.

