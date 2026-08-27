---
name: ultralyticspro
description: "Routes UltralyticsPro workflows for YOLO and RT-DETR training,
  prediction, and preset selection from the repository's wrapper scripts and
  model notes."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NO_LICENSE
---

# UltralyticsPro

Use this repo skill when a user asks to train, predict, or adapt the wrapper
scripts in this repository for Ultralytics YOLO or RT-DETR workflows.

This repository is a script collection, not an installable Python package. The
runtime skill therefore centers on the public `ultralytics` package and the
repo-maintained wrappers in `scripts/` and `sub-skills/`.

## Start here

1. Install the public dependency set:
   - `python -m pip install ultralytics`
   - If you plan to execute GPU training, install a PyTorch build that matches
     your platform and CUDA driver.
2. Run the smoke helper:
   - `python scripts/check_ultralytics_env.py --show-presets`
3. Read `references/interface-reference.md` when you need verified Ultralytics
   API signatures or CLI syntax.
4. Read `references/model-family-map.md` when you need to translate one of the
   source scripts into the bundled training or prediction presets.
5. Read `references/troubleshooting.md` for cross-cutting import, config, weight,
   data, and device failures.

## Minimal import check

```bash
python -c "from ultralytics import YOLO, RTDETR; print(YOLO, RTDETR)"
```

## Route map

### `sub-skills/training`
Use this route for any task that sounds like:
- train, finetune, or resume a YOLO or RT-DETR model
- reproduce `train_v8.py`, `train_yolo11.py`, `train_yolov10.py`,
  `train_yolo12.py`, `train_cls.py`, `train_obb.py`, `train_pose.py`,
  `train_seg01.py`, or `train_rtdetr.py`
- choose a model-family preset, dataset YAML, image size, batch size, or device
  for a training run

Read the sub-skill's workflow and troubleshooting references before launching
an actual run, because some presets require packaged config paths or a custom
local YAML file.

### `sub-skills/prediction`
Use this route for any task that sounds like:
- predict, infer, or run a single-image YOLO detection example
- reproduce `predict_v8.py`, `predict_yolo11.py`, or `predict_yolov10.py`
- choose a model weight file, source image, confidence threshold, or output
  directory for a prediction run

Read the sub-skill's workflow reference before executing a real inference,
because the first run may download pretrained weights if they are not already
cached.

## Shared runtime helper

- `scripts/check_ultralytics_env.py` — run this first when you need to confirm
  the installed Ultralytics version, packaged config paths, sample assets, or
  the preset index.

## What this skill does not cover

- Modifying the upstream `ultralytics` source code.
- Exporting this repo into another agent's skill library.
- Large training studies, benchmark sweeps, or long-running evaluation jobs.
- Native dataset preparation beyond the dataset names and YAMLs already used by
  the wrappers.

For provenance, see `references/repo-provenance.md` when you need to check
whether this skill still matches the current checkout or before refreshing it.
