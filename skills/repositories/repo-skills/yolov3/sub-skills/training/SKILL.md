---
name: training
description: "Plan and debug YOLOv3 training, custom dataset YAMLs, checkpoints,
  hyperparameters, resume, DDP, and CPU smoke commands."
disable-model-invocation: true
metadata:
  disco-role: operating
license: AGPL 3.0
---

# Training Sub-skill

Read this for `train.py`, custom object-detection datasets, `data/*.yaml`, `data/hyps/*.yaml`, pretrained versus scratch training, resume/evolve/freeze/DDP flags, and training smoke plans.

## Use

- Read `references/workflows.md` for training command patterns and dataset layout.
- Use `scripts/yolov3_command_builder.py` to build reproducible train commands without running them.
- Use `scripts/yolov3_dataset_yaml_check.py` before training when dataset paths or class names are uncertain.
- Read `references/troubleshooting.md` for dataset, checkpoint, logging, and DDP issues.

## Important facts

- Main entry point: `python train.py`.
- Defaults: `--weights yolov3-tiny.pt`, `--data data/coco128.yaml`, `--hyp data/hyps/hyp.scratch-low.yaml`, `--epochs 100`, `--batch-size 16`, `--imgsz 640`.
- CPU smoke used by repo guidance: tiny model, image size 64, one epoch, `--device cpu`, `--name smoke`, `--exist-ok`.
- Dataset YAML needs `train`, `val`, and `names`; if `nc` is present it must match the number of names. Optional `download` commands can have network side effects.
