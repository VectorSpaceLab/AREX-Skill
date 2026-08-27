---
name: saliency-and-cam
description: "Routes users who need saliency, guided or rectified saliency,
  Grad-CAM, custom-loss saliency, or regression attention workflows for
  keras-vis."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Saliency and CAM

Use this sub-skill when the user wants input-space attention maps from a trained keras-vis model.

## Covers

- `visualize_saliency`
- `visualize_saliency_with_losses`
- `visualize_cam`
- `visualize_cam_with_losses`
- regression attention with `grad_modifier`
- guided or rectified saliency with `backprop_modifier`
- penultimate-layer selection for Grad-CAM

## Routes out

- Activation image synthesis belongs in `../activation-maximization/SKILL.md`.
- New loss/optimizer internals belong in `../optimization-building-blocks/SKILL.md`.
- Heatmap overlay, color conversion, and image composition belong in `../image-utilities/SKILL.md`.

## What to read first

- `references/api-reference.md` for exact signatures, defaults, shapes, and modifiers.
- `references/workflows.md` for classification, regression, and Grad-CAM recipes.
- `references/troubleshooting.md` for penultimate-layer, modifier, and shape recovery.

## Smoke check

Use `scripts/saliency_smoke.py` to build a tiny deterministic model and print saliency and optional CAM heatmap shapes and value ranges.

## Practical rule

Prefer saliency when the model has no close convolutional or pooling layer before the target. Use CAM when a nearby spatial layer exists and you want a class-localized spatial explanation.
