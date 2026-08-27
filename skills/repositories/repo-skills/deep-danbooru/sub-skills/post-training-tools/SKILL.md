---
name: post-training-tools
description: "Use after DeepDanbooru training to convert a saved Keras model to
  TensorFlow Lite or generate experimental Grad-CAM visualizations, with
  explicit artifact, dependency, and CPU-backend checks."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Post-training tools

Use this sub-skill after a DeepDanbooru project has a loadable trained Keras
model. It routes two post-training workflows:

- **TFLite conversion**: emit and inspect a non-empty `.tflite` artifact.
- **Grad-CAM**: generate experimental, qualitative maps for tags selected by a
  prediction threshold.

Do not use this skill to train, repair a dataset, or judge model quality. Route
ordinary predictions, thresholds, and tag alignment to
[Inference and evaluation](../inference-evaluation/SKILL.md). Route missing or
stale models and retraining to [Model training](../model-training/SKILL.md).
For exact details, read the focused references before running a command.

## Choose the route

| Goal | Entry point | Read first |
|---|---|---|
| Convert a saved Keras model | `deepdanbooru conv2tflite` | [TFLite conversion](references/tflite-conversion.md) |
| Visualize input gradients | `deepdanbooru grad-cam` | [Grad-CAM workflow](references/grad-cam-workflow.md) |
| Check paths without loading a model | `post_training_preflight.py` | [Troubleshooting](references/troubleshooting.md) |
| Verify conversion in isolation | `tflite_conversion_smoke.py` | [TFLite conversion](references/tflite-conversion.md) |

## Shared preflight

1. Use the verified CPU TensorFlow backend first. GPU may be faster, but GPU
   support and speed are optional and unverified; a GPU option is not proof of
   GPU readiness.
2. Keep the model/project and output paths explicit. For TFLite output,
   `--allow-existing-output` only permits replacing an existing regular file;
   an existing directory at `--save-path` is always rejected. Use a disposable
   output directory for Grad-CAM because files can be overwritten.
3. A project-based operation expects `project.json`, `tags.txt`, and the model
   selected by `project.json`. The project loader searches
   `model-{model}.keras`, then `model-{model}.h5`.
4. Check that the model has an NHWC image input and that the tag count matches
   the output width before interpreting results. DeepDanbooru preprocessing
   resizes with aspect-ratio preservation, edge-pads, and normalizes to `[0,1]`.
5. Run the bundled preflight before an expensive conversion or visualization.
   It performs no downloads, network access, credential use, or model loading.

## TFLite decision rules

The CLI requires `--save-path`, a project or direct model path, and at least one
optimization method. The exact flags are `--project-path`, `--model-path`,
`--save-path`, `--optimize-default`, `--optimize-experimental-sparsity`, and
`--verbose`; do not substitute similarly named flags. A direct `--model-path`
takes precedence over a project. The converter API and artifact checks are in
[references/tflite-conversion.md](references/tflite-conversion.md).

After conversion, require `test -s OUTPUT.tflite`; then, when possible, load it
with a CPU TFLite interpreter and call `allocate_tensors()`. A non-empty file
alone does not prove compatible preprocessing, tag metadata, delegates, or
model quality. If sparsity or a layer is incompatible, retry without sparsity
before changing the original model.

## Grad-CAM decision rules

`grad-cam` is explicitly experimental. It requires a project and target path,
accepts an optional output directory (default `.`), and uses `--threshold`
default `0.5`; selection is inclusive (`score >= threshold`). It creates an
input image and per-selected-tag maps under a folder named for each input
basename. No selected tags means no result maps, not necessarily a failed
inference. Read the output contract and limitations in
[references/grad-cam-workflow.md](references/grad-cam-workflow.md).

## Failure handling and handoff

Use [references/troubleshooting.md](references/troubleshooting.md) for missing
model/save/optimization inputs, incompatible conversion operators, absent
SciPy or Pillow imports, malformed projects, and threshold cases with no maps.
Do not import the old `deepdanbooru.gradcam` module as a generic helper: its
source-level experimental test runs at import time. After any artifact or map
run, compare predictions and prerequisites through
[Inference and evaluation](../inference-evaluation/SKILL.md); if the model is
missing, use [Model training](../model-training/SKILL.md).
