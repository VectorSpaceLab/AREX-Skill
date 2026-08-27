---
name: annotators-and-preprocessing
description: "Use ControlNet 1.0 annotators and preprocessing safely: Canny,
  HED, MLSD, MiDaS depth/normal, OpenPose, Uniformer segmentation, HWC3
  conversion, resolution rounding, and detector checkpoint expectations."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Annotators and Preprocessing

Use this sub-skill when a task asks how to prepare or debug ControlNet conditioning maps, inspect `gradio_annotator` controls, choose an annotator for a control task, or reason about image channels, resolution multiples, and detector checkpoints.

For generation from an existing conditioning map, route to [gradio-inference-apps](../gradio-inference-apps/SKILL.md). For model/checkpoint layout, ControlNet weight files, or config questions, route to [model-and-weight-utilities](../model-and-weight-utilities/SKILL.md). For Fill50K, paired conditioning datasets, or training preprocessing, route to [training-and-datasets](../training-and-datasets/SKILL.md).

## Read Or Run

- Read [references/annotator-reference.md](references/annotator-reference.md) to choose Canny, HED, MLSD, MiDaS depth/normal, OpenPose, or Uniformer and confirm function signatures, parameters, output channels, RGB/BGR cautions, and checkpoint expectations.
- Read [references/troubleshooting.md](references/troubleshooting.md) when outputs look inverted, black/blank, wrong-colored, unexpectedly resized, or fail because Gradio, OpenCV, CUDA, optional packages, or detector checkpoints are missing.
- Run [scripts/inspect_annotator_inputs.py](scripts/inspect_annotator_inputs.py) before writing batch preprocessing code; it checks ControlNet-style `HWC3` and 64-multiple resizing on tiny generated arrays or a local input image, and can statically list `gradio_annotator.py` function signatures when given `--repo-root`.

## Safe Default Approach

1. Normalize incoming images to uint8 HWC RGB-style arrays with one, three, or four channels; ControlNet's `HWC3` behavior composites RGBA over white and expands grayscale to three channels.
2. Resize by scaling the short side to the requested resolution, then rounding height and width to multiples of 64; do not assume the result is square unless the aspect ratio already was square.
3. Prefer Canny for checkpoint-free, CPU-friendly preprocessing; treat HED, MLSD, MiDaS, OpenPose, and Uniformer as checkpoint- and dependency-dependent detectors.
4. Preserve polarity and channel order deliberately: edge maps can be white-on-black or black-on-white depending on downstream expectations, and normal/pose/segmentation visualizations are easy to misinterpret if RGB/BGR is swapped.
