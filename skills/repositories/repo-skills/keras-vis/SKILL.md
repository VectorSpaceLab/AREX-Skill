---
name: keras-vis
description: "Routes keras-vis activation maximization, saliency and Grad-CAM,
  customization, and image utility workflows for legacy Keras/TensorFlow
  graph-mode models."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# keras-vis

Use this skill for legacy keras-vis workflows that visualize or optimize what a model is doing:
activation maximization, saliency maps, Grad-CAM, custom losses, optimizer control, and image/data-format helpers.

This release was verified against keras-vis 0.5.0 with standalone Keras 2.2.4 and TensorFlow 1.15.5 on a CPU graph-mode runtime.
The package is intentionally routed through `repo-skills-router` in Researcher mode; read this file first, then jump to the sub-skill that matches the task.

## Quick install and import check

If the environment is not ready, use the legacy package stack described in
[references/installation-and-compatibility.md](references/installation-and-compatibility.md).
A known-good baseline is:

```bash
python -m pip install \
  "keras-vis==0.5.0" \
  "Keras==2.2.4" \
  "tensorflow==1.15.5" \
  "protobuf<=3.20.3" \
  "numpy==1.18.5" \
  "scipy==1.5.4" \
  "h5py==2.10.0" \
  "scikit-image==0.16.2" \
  "matplotlib==3.3.4" \
  "importlib-metadata" \
  Pillow imageio
```

Minimal import check:

```bash
python -c "import vis; from vis.visualization import visualize_saliency; print('vis imported')"
```

If that fails, read [references/troubleshooting.md](references/troubleshooting.md) before changing workflow code.

## Route map

### Activation maximization
Use [sub-skills/activation-maximization/SKILL.md](sub-skills/activation-maximization/SKILL.md) when the task is to synthesize an input that maximizes a Dense unit, regression output, or convolutional filter.
Typical trigger phrases include: activation maximization, feature visualization, class prototype, softmax-to-linear, Jitter, or animated optimization progress.

### Saliency and Grad-CAM
Use [sub-skills/saliency-and-cam/SKILL.md](sub-skills/saliency-and-cam/SKILL.md) when the task is to explain an existing input with saliency maps, guided saliency, rectified saliency, Grad-CAM, or regression attention.
Typical trigger phrases include: heatmap, input attribution, guided backprop, penultimate layer, or Grad-CAM.

### Optimization building blocks
Use [sub-skills/optimization-building-blocks/SKILL.md](sub-skills/optimization-building-blocks/SKILL.md) when the task needs custom losses, regularizers, `Optimizer`, input or gradient modifiers, backprop modifiers, or callbacks.
Typical trigger phrases include: custom loss, `wrt_tensor`, `LPNorm`, `TotalVariation`, `GifGenerator`, or backend gradient override.

### Image utilities
Use [sub-skills/image-utilities/SKILL.md](sub-skills/image-utilities/SKILL.md) when the task is about image shapes, overlays, label lookup, loading, normalization, stitching, or optional Pillow/imageio diagnostics.
Typical trigger phrases include: channels first/last, overlay two heatmaps, draw labels, `lookup_imagenet_labels`, or `draw_text`.

## Shared checks

- Run [scripts/check_keras_vis_env.py](scripts/check_keras_vis_env.py) when you need a quick environment and import sanity check.
- Read [references/repo-provenance.md](references/repo-provenance.md) before deciding whether this skill matches the current checkout or before refreshing it.
- Read [references/installation-and-compatibility.md](references/installation-and-compatibility.md) when package installation or backend compatibility is the blocker.
- Read [references/troubleshooting.md](references/troubleshooting.md) when imports, protobuf, optional image packages, or legacy TensorFlow graph behavior fail.

## What not to do here

- Do not route new activation or saliency workflows directly into the root router when a focused sub-skill exists.
- Do not send future agents to original repo notebooks, examples, or tests as runtime instructions; the sub-skills contain the distilled workflows instead.
- Do not replace a visualization workflow with a prose-only description when the bundled scripts or references cover it safely.
- Do not assume `tensorflow.keras` is the supported API surface for this release; the package was built around standalone Keras.

## When the root router is enough

Use the root `SKILL.md` only when the user request spans multiple sub-skills or when you are still deciding which sub-skill owns the task family.
Examples include:

- "I need keras-vis installed and want the right workflow for a model explanation task."
- "I have a heatmap request, but I also need to know whether I should use saliency or Grad-CAM."
- "I want to customize the optimizer path and then visualize the result."

If the task clearly matches one sub-skill, jump there immediately.
