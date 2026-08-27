---
name: methods-and-api
description: "Routes expert pytorch-grad-cam method selection, public
  signatures, lifecycle, backend, and edge-case API troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Methods and API

Use this sub-skill when the user asks which CAM method to choose, what a class
signature or default parameter is, why a method behaves differently, how the
context manager and hook lifecycle work, or how advanced methods such as
FinerCAM, SegEigenCAM, ShapleyCAM, KPCA-CAM, or AblationCAM variants differ.

## Read first

- [`references/methods-reference.md`](references/methods-reference.md) for the
  method catalog and selection guidance.
- [`references/api-signatures.md`](references/api-signatures.md) for the
  verified installed constructor signatures.
- [`references/backend-and-lifecycle.md`](references/backend-and-lifecycle.md)
  for context manager, hook, and device behavior.
- [`references/troubleshooting.md`](references/troubleshooting.md) for expert
  API mistakes and backend-specific gotchas.

## Common tasks

- Choose a method for speed, faithfulness, or transformer compatibility.
- Check an installed constructor signature before writing a prompt or helper.
- Understand why a method needs `comparison_categories`, `alpha`,
  `ablation_layer`, or a `reshape_transform`.
- Debug FinerCAM on a binary/ternary classifier or check SVD projection helpers
  for mutation-free behavior.

## Distinguish from other sub-skills

- Use `cam-generation` for the ordinary end-to-end workflow of producing and
  overlaying heatmaps.
- Use `model-task-adaptation` for custom targets and reshape transforms.
- Use `metrics-and-evaluation` for ROAD, ARCC, RefineCAM, and DFF.
