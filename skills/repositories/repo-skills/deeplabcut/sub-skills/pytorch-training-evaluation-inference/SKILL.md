---
name: pytorch-training-evaluation-inference
description: "PyTorch DeepLabCut train, evaluate, image/video inference,
  labeled-video handoff, and export routing."
disable-model-invocation: true
metadata:
  disco-role: operating
license: LGPL 3.0
---

# PyTorch Training, Evaluation, Inference

Use this sub-skill when the task is inside the DeepLabCut 3.x PyTorch engine and you need to:

- train or resume a shuffle
- evaluate one or more snapshots
- run image or video inference
- choose device, snapshot, batch-size, and config overrides
- hand off analyzed outputs for labeled-video rendering
- export a relocatable PyTorch model bundle

This sub-skill owns the PyTorch-specific choices for `device`, snapshot selection, detector handling, `batch_size`, `pytorch_cfg_updates`, `inference_cfg`, and export packaging.

## Stay here when

- the project or shuffle is already built and you only need training, evaluation, analysis, or export
- you are choosing between `cpu`, `cuda`, `mps`, or `auto`
- you need to resume from a pose snapshot or detector snapshot
- you want to inspect or override a PyTorch config without editing the full file by hand

## Route away when

- upstream label extraction or training-dataset creation is needed → [data-labeling-and-training-datasets](../data-labeling-and-training-datasets/SKILL.md)
- multi-animal tracklet stitching or identity recovery is needed after analysis → [multi-animal-tracking](../multi-animal-tracking/SKILL.md)
- SuperAnimal pretrained, adaptation, or model-zoo workflows are needed → [model-zoo-superanimal](../model-zoo-superanimal/SKILL.md)
- filtered predictions, labeled-video rendering details, or 3D export are needed → [postprocessing-3d-video-exports](../postprocessing-3d-video-exports/SKILL.md)
- TensorFlow engine details are needed → route to the root compatibility layer

## Bundled guidance

- [API reference](references/api-reference.md)
- [PyTorch configuration guide](references/pytorch-configuration.md)
- [Workflow guide](references/workflows.md)
- [Troubleshooting guide](references/troubleshooting.md)
- [Config inspector](scripts/inspect_pytorch_config.py)

When you only need to inspect a `pytorch_config` file, use the bundled script. It summarizes the key sections and never trains.
