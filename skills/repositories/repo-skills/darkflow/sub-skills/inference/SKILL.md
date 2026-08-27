---
name: inference
description: "Guides Darkflow image, video, JSON, Python API, and protobuf
  inference/export workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: GPL 3.0
---

# Darkflow Inference and Export

Use this sub-skill when the user wants to run a trained Darkflow model, return predictions, save annotated images or JSON, demo a camera/video stream, or export/load a frozen graph.

## Inputs you should collect

- A Darkflow-compatible `.cfg` model file or a `.pb` / `.meta` pair.
- A `.weights` file, checkpoint step, or existing `.pb` / `.meta` pair.
- Image folder, video file, or `camera` demo source.
- Optional labels file for custom, non-VOC, non-COCO model names.
- Optional threshold, GPU fraction, batch size, JSON-output, or save-video choices.

## First checks

1. If the environment is not already proven, run `../../scripts/check_install.py`.
2. Use `../../references/model-overview.md` to select a model family and label source.
3. Use `../../references/cli-reference.md` when building a `flow` command.
4. Use `references/troubleshooting.md` before retrying failed inference or export runs.

## Route by task

- **Image folder inference**: Use `references/workflows.md#image-folder-prediction`.
- **JSON output**: Use `references/workflows.md#json-output`.
- **Python API predictions**: Use `references/workflows.md#python-api-prediction` and `../../references/api-reference.md`.
- **Camera or video demo**: Use `references/workflows.md#camera-or-video-demo`.
- **Frozen graph export / load**: Use `references/workflows.md#protobuf-export-and-load`.

## Outputs to expect

- Annotated images or JSON files are written under the selected image directory's `out/` folder.
- `return_predict()` returns a list of dictionaries with `label`, `confidence`, `topleft`, and `bottomright`.
- `--savepb` writes a `.pb` graph and a `.meta` JSON metadata file.
- `--saveVideo` writes `video.avi` from demo mode.

## Boundaries

This sub-skill does not own dataset annotation cleanup, custom-class config editing, or checkpoint training loops. Route those to `../training/SKILL.md`, then return here for prediction or export after a trained model exists.

## Quality checks before claiming success

- The CLI command or Python options include a valid model source and a valid weight/checkpoint/graph source.
- If JSON output is requested, the user knows to inspect the image directory's `out/` folder.
- If using `return_predict()`, the input is already a `numpy.ndarray` image array.
- If using GPU flags, the user has a GPU-enabled TensorFlow 1.x stack; otherwise prefer CPU mode.
