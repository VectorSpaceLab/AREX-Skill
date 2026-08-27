---
name: inference-demo
description: "Guides FCOS image inference, installed CLI use, public FCOS API
  calls, image preprocessing, visualization, and demo troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# FCOS Inference and Demo

Use this sub-skill when the user wants to run FCOS on images, inspect `fcos.FCOS`, use the installed `fcos` command, choose a pretrained model, format detection outputs, or debug demo/inference failures.

## Start here

1. Read [`references/api-reference.md`](references/api-reference.md) for the public `FCOS` constructor and method contracts.
2. Read [`references/model-overview.md`](references/model-overview.md) before selecting a pretrained high-level API model or a config/weight pair.
3. Read [`references/workflows.md`](references/workflows.md) for CLI, Python API, no-display, and webcam/display workflows.
4. Use [`scripts/prepare_image_for_fcos.py`](scripts/prepare_image_for_fcos.py) to validate a local image and produce a resized BGR NumPy array for API tests.
5. Use [`scripts/fcos_cli_safe_wrapper.py`](scripts/fcos_cli_safe_wrapper.py) to construct or run a no-display FCOS inference path without relying on GUI behavior.
6. Read [`references/troubleshooting.md`](references/troubleshooting.md) for `_C`, downloads, color-channel, display, and OOM failures.

## Boundaries

- Route config selection, dataset registration, and YAML errors to [`../data-configs/SKILL.md`](../data-configs/SKILL.md).
- Route COCO/VOC/Cityscapes evaluation and training commands to [`../training-evaluation/SKILL.md`](../training-evaluation/SKILL.md).
- Route ONNX export or ONNX post-processing to [`../onnx-export/SKILL.md`](../onnx-export/SKILL.md).
- Route source edits, compiled layer tests, or modern PyTorch porting to [`../internals-maintenance/SKILL.md`](../internals-maintenance/SKILL.md).

## Minimal safe response pattern

When a user asks for image inference:

1. Ask whether model weights may be downloaded if they did not provide a local weight file.
2. Prefer no-display output in automated contexts; only call visualization when a display is available.
3. Verify the package and extension before model construction because `FCOS(...)` loads weights and builds a detector.
4. Ensure the input is a 3-channel image. The installed CLI reads RGB via image I/O, flips to BGR, and resizes the shorter side to 800.
5. Set `cpu_only=True` only for CPU runs; expect it to be slow.

## Output contract reminder

`FCOS.detect(im)` returns a list of dictionaries with `box`, `score`, `label_name`, and `label_id`. Boxes are `[x1, y1, x2, y2]` floats in the image coordinate system used for inference.
