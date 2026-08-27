---
name: image-utilities
description: "Guides agents through keras-vis image utilities for data formats,
  overlays, labels, optional image dependencies, and diagnostics."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# keras-vis image utilities

Use this sub-skill when a task needs keras-vis utility behavior rather than visualization semantics: image/data-format shape handling, channel-order helpers, synthetic arrays, overlays, label lookup, text drawing, image loading, model-layer lookup, model graph refresh after activation edits, or optional Pillow/imageio diagnostics.

## Route first

- For activation-maximization recipes, loss weighting, seed images, or softmax-to-linear visualization advice, use the `activation-maximization` sub-skill instead.
- For saliency, guided saliency, Grad-CAM, heatmap interpretation, or map-overlay workflow semantics, use the `saliency-and-cam` sub-skill instead; return here only for low-level array overlays and shape checks.
- For custom losses, regularizers, optimizer callbacks, gradient modifiers, input modifiers, or backprop modifier internals, use the `optimization-building-blocks` sub-skill instead.

## Runtime workflow

1. Decide the array contract: Keras backend `image_data_format`, tensor rank, and whether the array is channels-first tensor data or channels-last display image data. Use [data-and-format-guide.md](references/data-and-format-guide.md).
2. Pick the helper and exact import path from [api-reference.md](references/api-reference.md). Most helpers live under `vis.utils.utils`; `overlay` lives under `vis.visualization`.
3. For environment or compatibility questions, run the bundled deterministic diagnostic script from this sub-skill tree:

   ```bash
   python scripts/check_image_utilities.py
   ```

   The script uses only synthetic arrays and reports optional Pillow/imageio availability without requiring original images.
4. If a failure involves missing optional image packages, package data, array shape mismatch, graph refresh, or legacy Keras/TensorFlow behavior, use [troubleshooting.md](references/troubleshooting.md).

## Keep outputs self-contained

When giving future instructions, copy or generate any tiny image data needed for demonstrations. Do not depend on repository-local sample assets or external data to explain these utilities.
