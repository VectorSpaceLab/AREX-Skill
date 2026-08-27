---
name: inference
description: "Image, video, webcam, and stream detection workflows for ScaledYOLOv4."
metadata:
  disco-role: operating
disable-model-invocation: true
license: GPL 3.0
---

# Inference

Use this sub-skill when the user wants to run the detector on images, videos, webcams, or network streams.

## Typical requests

- How do I run detection on a folder of images?
- How do I use a webcam, RTSP stream, or source list?
- How do I save text outputs or rendered frames?
- Why does detection fail before the first frame is processed?
- How do I interpret the NMS and output-folder behavior?

## What this sub-skill owns

- The detection entry point and its options.
- Source handling for files, directories, webcams, RTSP/HTTP streams, and source lists.
- Output folder behavior, rendered image/video writes, and optional text output.
- Non-max suppression, class filtering, and augmented inference at prediction time.

## What it does not own

- Dataset preparation and label cleanup → `../data-preparation/`.
- Training or epoch-end validation → `../training/`.
- Standalone metric evaluation → `../evaluation/`.
- Export to TorchScript, ONNX, or CoreML → `../export/`.

## Read before acting

- `../../references/model-overview.md` for model-loading behavior and stride expectations.
- `../../references/runtime-bundle.md` for the bundled executable source mirror and configs used by the helper.
- `../../references/data-layout.md` for source handling and media conventions.
- `references/inference-workflows.md` for the common source and output patterns.
- `references/troubleshooting.md` for detection-specific failures and recovery steps.

## Bundled helper

- `scripts/prepare_inference_run.py` validates the source, output, and option plan against the bundled `runtime/` mirror before you start a long detection job.
- `scripts/run_detection.py` runs the concrete bundled `runtime/detect.py` entrypoint with the correct working directory and `PYTHONPATH`; use `--dry-run` before launching.

## Workflow in practice

1. Classify the source as file, folder, stream, or source list.
2. Confirm the weight file and image size are valid.
3. Decide whether you want rendered images, saved text labels, or both.
4. Be careful with the output directory because detection workflows treat it as scratch space.
5. Use the preflight helper before a webcam or network-stream run.

## Good signs

- The source type is known before the run begins.
- The checkpoint and image size fit the model stride.
- The output location is disposable.
- The detection mode matches the input type.

## Bad signs

- A webcam or RTSP source is broken but the run is configured as if it were a folder of images.
- The output folder contains files you expected to keep.
- `view_img` is enabled in a non-GUI environment.
- You are trying to debug dataset or label problems through inference instead of the data-preparation workflow.
