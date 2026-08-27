---
name: conversion
description: "Guides TensorFlow YOLOv3 checkpoint conversion, COCO
  initialization, Darknet weight pitfalls, and graph freezing to PB inference
  models."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# TensorFlow YOLOv3 conversion operating guide

Use this sub-skill when a user asks to convert pretrained YOLOv3 weights, initialize training from COCO, freeze a TensorFlow checkpoint, diagnose `convert_weight.py` / `freeze_graph.py`, or decide whether the bundled Darknet conversion scripts are safe to run.

## Boundaries

- Owns checkpoint and weight conversion plus freezing a TensorFlow 1.x graph to a `.pb` file.
- Routes running image/video inference with the final `.pb` to the inference sub-skill.
- Routes training after COCO initialization to the training sub-skill.
- Routes dataset, class-name, and anchor-file preparation to the data-preparation sub-skill.
- Does not claim that direct Darknet `.weights` conversion works unmodified; the bundled direct-conversion scripts have known source bugs.

## Required working assumptions

- Run repository scripts from the repository root so relative config paths such as `./data/classes/coco.names`, `./data/anchors/basline_anchors.txt`, and `./checkpoint/...` resolve correctly.
- Use a TensorFlow 1.x-compatible environment. TensorFlow 1.15.x CPU is sufficient for conversion/freezing if the checkpoint and graph are compatible; legacy `tensorflow-gpu==1.11.0` is optional and difficult on modern CUDA hardware.
- Default conversion inputs and outputs are:
  - original release checkpoint prefix: `./checkpoint/yolov3_coco.ckpt` (`cfg.YOLO.ORIGINAL_WEIGHT`)
  - converted/demo checkpoint prefix: `./checkpoint/yolov3_coco_demo.ckpt` (`cfg.YOLO.DEMO_WEIGHT`)
  - frozen graph output: `./yolov3_coco.pb`
  - freeze output nodes: `input/input_data`, `pred_sbbox/concat_2`, `pred_mbbox/concat_2`, `pred_lbbox/concat_2`

## Fast operating path

1. Read [conversion workflows](references/workflows.md) for the exact COCO release checkpoint, `--train_from_coco`, and freeze flows.
2. Run the safe preflight checker before expensive or destructive commands:

   ```bash
   python sub-skills/conversion/scripts/check_conversion_inputs.py --repo-root .
   ```

3. If creating custom-class training initialization from COCO, update the class-name config first, then use:

   ```bash
   python convert_weight.py --train_from_coco
   ```

   This intentionally skips the output head variables (`conv_sbbox`, `conv_mbbox`, `conv_lbbox`) and saves randomly initialized heads into `cfg.YOLO.DEMO_WEIGHT`.

4. If creating a COCO demo PB, use the release checkpoint flow, run `python convert_weight.py`, then run `python freeze_graph.py`.
5. If the user supplies Darknet `.weights`, consult [conversion troubleshooting](references/troubleshooting.md) before running anything; prefer the release checkpoint flow or patch a copy of the direct conversion scripts first.

## Safety checklist

- Confirm checkpoint prefixes have `.meta`, `.index`, and at least one `.data-*` shard before restore.
- Confirm class-name and anchor files are present and match the graph/class-count intent.
- For `freeze_graph.py`, use output node names without `:0`; inference code fetches the same tensors with `:0` suffix.
- Keep generated checkpoints and PB files in user-selected working paths; do not copy large model artifacts into this skill directory.
