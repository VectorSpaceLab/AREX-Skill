---
name: checkpoint-inference
description: "Guides Tencent ML-Images checkpoint-backed classification and
  feature extraction workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Checkpoint Inference

Use this sub-skill when the task is about running Tencent ML-Images checkpoint
inference: top-k single-label classification or feature extraction from a
pretrained ResNet checkpoint.

## Read first

- Read [references/workflows.md](references/workflows.md) for classification and
  feature-extraction recipes.
- Read [references/input-output-formats.md](references/input-output-formats.md)
  for dictionary, image-list, prediction, and feature result layouts.
- Read [references/troubleshooting.md](references/troubleshooting.md) when a
  checkpoint, dictionary, image, or OpenCV preprocessing step fails.

## Bundled helpers

- `scripts/inspect_inference_inputs.py` validates the image list, dictionary,
  checkpoint path/prefix, and compatibility settings before printing a safe
  classification command.
- `scripts/inspect_feature_inputs.py` validates the image list, checkpoint,
  and output path before printing a safe feature-extraction command.

## Route by task

- **Need the model graph or checkpoint compatibility**: cross-link to
  [../resnet-training/SKILL.md](../resnet-training/SKILL.md).
- **Need classification results**: use the classification inspector to check the
  image list, dictionary, and checkpoint. Only then run the printed command in a
  prepared TensorFlow 1.x/OpenCV runtime.
- **Need features**: use the feature inspector to confirm the checkpoint and
  output path, then run the printed command.
- **Need training or finetuning**: route to the training sub-skill.

## Safety notes

- The public example scripts restore checkpoints at top level. Do not import or
  execute them blindly in a generic Python session; use the bundled inspectors
  to validate inputs first.
- Checkpoint files are external artifacts. This skill documents the expected
  prefix/path structure and compatibility checks but does not bundle weights.
- OpenCV is required for preprocessing. If `cv2` is missing, install it in the
  inspection environment or report the missing optional dependency clearly.
