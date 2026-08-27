# Troubleshooting

## Purpose

Use this page for cross-cutting installation, import, backend, and optional-dependency failures that can affect more than one sub-skill.

## Common failures

### `TypeError: Descriptors cannot not be created directly`

**Symptom**: Importing `vis` or `tensorflow` fails with a protobuf descriptor error.

**Likely cause**: TensorFlow 1.15 is using a protobuf release that is too new.

**Recovery**:
- Pin `protobuf` to `3.20.3` or another compatible 3.20.x release.
- Re-run the minimal import check from [installation-and-compatibility.md](installation-and-compatibility.md).
- If the environment was shared, create a new private prefix instead of mutating someone else's install.

### `ImportError` for `keras` or `tensorflow`

**Symptom**: The package imports fail before any visualization helper runs.

**Likely cause**: The environment has only `tensorflow.keras`, a modern TensorFlow wheel, or no standalone Keras install.

**Recovery**:
- Install the pinned legacy stack from [installation-and-compatibility.md](installation-and-compatibility.md).
- Confirm the import path is `keras`, not `tensorflow.keras`.
- Use Python 3.7 when possible; newer runtimes are not a good fit for this release.

### `ImportError: Failed to import PIL` or missing `imageio`

**Symptom**: `draw_text`, `GifGenerator`, or image annotation helpers fail.

**Likely cause**: Optional image packages were skipped.

**Recovery**:
- Install `Pillow` for text drawing and `imageio` for GIF writing.
- Re-run [scripts/check_keras_vis_env.py](../scripts/check_keras_vis_env.py) or the relevant sub-skill smoke script.
- If the task does not need annotated GIFs, keep those packages optional and use the core numeric workflows instead.

### `ValueError: Unable to determine penultimate Conv or Pooling layer`

**Symptom**: Grad-CAM cannot infer a penultimate spatial layer.

**Likely cause**: The model is dense-only, the spatial layer is too far away, or the requested layer index is unsuitable.

**Recovery**:
- Use saliency instead of CAM when no close convolutional or pooling layer exists.
- Pass `penultimate_layer_idx` explicitly when you know the right layer.
- Confirm `layer_idx` points to the output you actually want to explain.

### Poor activation-maximization images or flat losses

**Symptom**: Activation maximization produces garbage, noise, or little movement.

**Likely cause**: Loss weights are unbalanced, a softmax layer is being maximized directly, or `Jitter` is missing.

**Recovery**:
- Use the activation-maximization sub-skill's workflows to linearize softmax outputs when needed.
- Reduce or disable regularization weights temporarily, then tune them back upward.
- Add `Jitter` and inspect verbose loss output.

### Guided/rectified backprop does not behave as expected

**Symptom**: Guided saliency or guided backprop changes the graph unexpectedly or fails to build.

**Likely cause**: TensorFlow graph mode is required and advanced activations are not fully supported in the model-rewrite path.

**Recovery**:
- Stay on the legacy TensorFlow graph-mode path.
- Prefer the built-in guided/rectified modifier helpers from the optimization or saliency sub-skill.
- Fall back to plain saliency if the model uses unsupported advanced activations.

### Shape confusion between channels-first and channels-last

**Symptom**: Heatmaps, overlays, or seeds appear transposed or mismatched.

**Likely cause**: The model backend data format differs from the display image format.

**Recovery**:
- Check [sub-skills/image-utilities/SKILL.md](../sub-skills/image-utilities/SKILL.md) and its data-format guide.
- Use the bundled diagnostic script to confirm `get_img_shape()` and `slicer` behavior.
- Keep the array contract consistent before calling visualization helpers.

## When to stop and escalate

Stop at a model/data/hardware limit when:

- the task requires a missing proprietary model or dataset;
- a required GPU/backend is unavailable for a user-requested accelerator path;
- the request depends on a package fork or unsupported TensorFlow 2.x-only behavior.

In those cases, route the task to the narrowest supported sub-skill and state the limitation plainly.
