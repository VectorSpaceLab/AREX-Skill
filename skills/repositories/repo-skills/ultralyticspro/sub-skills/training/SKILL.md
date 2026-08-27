---
name: training
description: "Routes UltralyticsPro training workflows for YOLO and RT-DETR
  presets, including detection, classification, segmentation, pose, and oriented
  bounding-box examples."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NO_LICENSE
---

# Training

Use this sub-skill when the user wants to train, finetune, or resume a model
using one of the repository's training wrappers.

## Typical triggers

- "train YOLOv11 on coco128"
- "run the classification example"
- "use the RT-DETR training script"
- "switch the model preset or device"
- "why does `train_yolo12.py` fail on this machine?"

## What belongs here

- The training wrappers that mirror `train_v8.py`, `train_v8_linux.py`,
  `train_yolo11.py`, `train_yolov10.py`, `train_yolo12.py`, `train_cls.py`,
  `train_obb.py`, `train_pose.py`, `train_seg01.py`, and `train_rtdetr.py`.
- Preset selection, model-config path selection, dataset YAML selection, and
  device overrides for those training examples.
- Safe dry-run planning before a real training job starts.
- Troubleshooting for missing packaged configs, missing dataset YAMLs, device
  selection, and first-run downloads.

## What stays out

- Single-image prediction workflows. Use `sub-skills/prediction` instead.
- Upstream library source changes. This repo skill only wraps the public
  `ultralytics` package.
- Long benchmark or large-scale training sweeps.

## First reads

1. `references/workflows.md` for the preset-to-script map and the canonical
   command forms.
2. `references/presets.md` when you need to translate a source script name into
   the bundled training preset name.
3. `references/troubleshooting.md` for data, config, device, and download
   failures.
4. `../../references/interface-reference.md` when you need verified Ultralytics
   API or CLI details.
5. `../../references/model-family-map.md` when you need the broader source
   script inventory.

## Bundled helper

- `scripts/run_train.py` — preferred wrapper for all training presets. It is
  safe by default and performs a dry run unless `--execute` is supplied.

## How to use the helper

- Start with `--list-presets` when you are mapping a source script to the
  bundled preset.
- Use `--preset train-yolo11` or another preset when you want the same model
  and dataset pair as a source example.
- Override `--model`, `--data`, `--imgsz`, `--batch`, `--workers`, `--device`,
  `--project`, or `--name` when a user asks for a variation.
- Pass `--execute` only after confirming that the model config and dataset are
  available and that the user is willing to start a real training job.

## Common decisions

- If the path is `cfg_yolov12/yolo12.yaml`, the preset is a custom local config
  case. The verified public Ultralytics install used for authoring does not ship
  that file, so the user must supply it or choose a different preset.
- If the user only needs to inspect the parameters, stay in dry-run mode and
  read the printed plan instead of launching training.
- If the requested run is meant for CPU, choose the preset or override that sets
  `device=cpu` explicitly.

## When to escalate to the root skill

Go back to `SKILL.md` if the task turns into general package inspection,
installation, or route selection across training and prediction.
