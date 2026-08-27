---
name: advanced-controls
description: "Tune neural-style-tf multi-style, masks, original-color,
  layer/loss, initialization, pooling, and optimizer controls for image
  workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: GPL 3.0
---

# advanced-controls

Use this sub-skill when a `neural_style.py` image run needs expert controls beyond a basic content/style command: multiple styles, style interpolation weights, segmentation masks, original-color transfer, layer/loss weighting, initialization, pooling, or optimizer tuning.

Do not use this sub-skill for:

- building the base single-image command, choosing content/style directories, or locating image outputs; use [image-stylization](../image-stylization/SKILL.md).
- video frame loops, optical-flow files, temporal consistency, or video assembly; use [video-stylization](../video-stylization/SKILL.md).
- install/import/runtime setup, VGG weights, TensorFlow 1.x compatibility, or cross-cutting failures; use the root [runtime notes](../../references/runtime-and-installation.md) and [root troubleshooting](../../references/troubleshooting.md).

## Operating route

1. Start from a valid base command from [image-stylization](../image-stylization/SKILL.md).
2. Read [references/advanced-parameters.md](references/advanced-parameters.md) to choose the right flag family and confirm source-verified defaults and quirks.
3. Use [scripts/plan_advanced_args.py](scripts/plan_advanced_args.py) before editing a long command. It validates count-sensitive options such as style weights, masks, and layer weights, prints normalized weights, and emits a shell-safe flag fragment.
4. If a run fails or the intended effect does not appear in output, read [references/troubleshooting.md](references/troubleshooting.md) before changing multiple weights at once.

## High-value controls

- **Multiple styles and interpolation**: pass several style image filenames with `--style_imgs` and matching raw weights through `--style_imgs_weights`; the source normalizes weights internally.
- **Masked/segmented transfer**: add `--style_mask` and provide one mask filename per style with `--style_mask_imgs`; masks are loaded from the content image directory.
- **Original colors**: add `--original_colors` and choose `--color_convert_type yuv|ycrcb|luv|lab` when preserving content-image chroma is more important than copying style colors.
- **Layer/loss tuning**: change `--content_layers`, `--style_layers`, corresponding weight lists, `--content_loss_function`, and `--pooling_type` only after recording a baseline command.
- **Optimizer and memory**: use `--optimizer adam` and lower `--max_size` when L-BFGS or large images exhaust memory; tune `--learning_rate` only for Adam.

## Source-verified caveats

- `neural_style.py` normalizes style-image, content-layer, and style-layer weights after parsing; raw ratios such as `2 8` and `0.2 0.8` are equivalent.
- The source does not validate list lengths. Python `zip(...)` can silently ignore extra style weights or layer weights, so validate counts before running.
- `--style_mask` expects `--style_mask_imgs`; missing masks can produce runtime errors before useful output.
- `--color_convert_time` is parsed with choices `after|before`, but the source conversion path runs after stylization. Treat `before` as unsupported unless the target checkout changed.
