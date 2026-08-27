---
name: prediction
description: "Routes UltralyticsPro prediction workflows for YOLO image
  inference presets and their shared sample-image defaults."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NO_LICENSE
---

# Prediction

Use this sub-skill when the user wants to run or adapt one of the repository's
single-image prediction wrappers.

## Typical triggers

- "predict on Zidane"
- "run the YOLOv11 inference example"
- "switch the model weight or confidence threshold"
- "why did the prediction script try to download a weight file?"
- "how do I save the output image?"

## What belongs here

- The prediction wrappers that mirror `predict_v8.py`, `predict_yolo11.py`, and
  `predict_yolov10.py`.
- Model weight selection, input source selection, image size, confidence,
  saving, and output naming for those examples.
- Dry-run planning before a real inference run.
- Troubleshooting for first-run weight downloads, missing source images, output
  paths, and device selection.

## What stays out

- Training, finetuning, or resume workflows. Use `sub-skills/training` instead.
- Upstream library source changes.
- Export, tracking, benchmark, or video-streaming workflows that the repository
  does not wrap directly.

## First reads

1. `references/workflows.md` for the preset-to-script map and the canonical
   command forms.
2. `references/troubleshooting.md` for weight, source, save-path, and device
   failures.
3. `../../references/interface-reference.md` when you need verified Ultralytics
   API or CLI details.
4. `../../references/model-family-map.md` when you need the broader source
   script inventory.

## Bundled helper

- `scripts/run_predict.py` — preferred wrapper for all prediction presets. It is
  safe by default and performs a dry run unless `--execute` is supplied.

## How to use the helper

- Start with `--list-presets` when you are mapping a source script to the
  bundled preset.
- Use `--preset predict-yolo11` or another preset when you want the same model
  and sample image pair as a source example.
- Override `--model`, `--source`, `--imgsz`, `--conf`, `--save`, `--device`,
  `--project`, or `--name` when a user asks for a variation.
- Pass `--execute` only after confirming that the model weights and source are
  available and that the user is willing to start a real inference run.

## Common decisions

- The default source is the packaged `ultralytics/assets/zidane.jpg` sample,
  which is shipped with the verified public Ultralytics install.
- If the model weight name ends in `.pt`, the first execution may download the
  pretrained weights when they are not already cached.
- If the user only needs to inspect the parameters, stay in dry-run mode and
  read the printed plan instead of launching inference.

## When to escalate to the root skill

Go back to `SKILL.md` if the task turns into general package inspection,
installation, or route selection across training and prediction.
