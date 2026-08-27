---
name: training-and-cli
description: "Train, evaluate, configure, and validate RF-DETR datasets with the
  Python API or Lightning CLI."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# RF-DETR training and CLI

Use this sub-skill when the task is to fine-tune, evaluate, configure, or debug RF-DETR training runs. It covers the high-level Python API, the Lightning CLI, dataset layout validation, `TrainConfig` variants, augmentation backends, loggers, resume behavior, and distributed training.

## Route by task

| If the user needs... | Open this |
| --- | --- |
| COCO, YOLO, segmentation, or keypoint dataset layout checks | [references/data-formats.md](references/data-formats.md) and [scripts/validate_dataset_layout.py](scripts/validate_dataset_layout.py) |
| `model.train(...)`, `model.evaluate(...)`, checkpoints, EMA, early stopping, auto batch, augmentation, loggers, or multi-GPU advice | [references/training-workflows.md](references/training-workflows.md) |
| `rfdetr fit/validate/test/predict`, Lightning YAML configs, or config overrides | [references/cli-and-configs.md](references/cli-and-configs.md) and [scripts/inspect_training_config.py](scripts/inspect_training_config.py) |
| Training failures, missing extras, bad schemas, resume surprises, DDP, logger credentials, or resolution errors | [references/troubleshooting.md](references/troubleshooting.md) |

## First actions

1. Identify the model family: detection (`RFDETRSmall` / `rfdetr-small`), segmentation (`RFDETRSegSmall` / `rfdetr-seg-small`), or keypoint preview (`RFDETRKeypointPreview` / `rfdetr-keypoint-preview`).
2. Confirm the extras. Training needs `pip install "rfdetr[train]"`; the Lightning CLI also needs `pip install "rfdetr[train,cli]"`. Add `augment` for Albumentations/Kornia and `loggers` for TensorBoard/W&B/MLflow.
3. Validate the dataset layout before long runs:

   ```bash
   python scripts/validate_dataset_layout.py data/my_dataset --task auto
   python scripts/validate_dataset_layout.py data/my_pose_dataset --task keypoint --infer-keypoint-schema
   ```

4. Inspect the installed config surface or a bundled Lightning YAML before editing it:

   ```bash
   python scripts/inspect_training_config.py
   python scripts/inspect_training_config.py --config references/configs/rfdetr_small.yaml
   ```

## Quick decision rules

- Use the high-level `RFDETR.train(**kwargs)` path for ordinary fine-tuning and `RFDETR.evaluate(split="test"|"val", **kwargs)` for one-shot COCO metrics.
- Use the Lightning CLI or custom PTL API when a task needs YAML-driven runs, trainer strategies, callbacks/loggers, or framework integration.
- For multi-GPU launches, set `devices="auto"` or an explicit count; the default Trainer device count is one.
- Use `resume=".../last.ckpt"` for full optimizer/scheduler continuity. Use lightweight `.pth` best checkpoints as weights or cold-continuation inputs.
- Keypoint preview can infer COCO/YOLO pose schemas, but YOLO pose must declare `kpt_shape`; keypoint training supports DDP but not Kornia GPU augmentation, FSDP, or DeepSpeed.

## Boundaries

- Prediction-only outputs and label interpretation belong to `../inference-and-models/SKILL.md`.
- ONNX, TensorRT, TFLite, ExecuTorch, CoreML, and deployment artifacts belong to `../export-and-deployment/SKILL.md`.
- Contributor test policy, pre-commit, and source-repository maintenance belong to `../repository-development/SKILL.md`.
