---
name: image-stylization
description: "Build and run single-image neural-style-tf stylization commands
  from content/style paths, VGG weights, device, optimizer, image-size, and
  output controls."
disable-model-invocation: true
metadata:
  disco-role: operating
license: GPL 3.0
---

# image-stylization

Use this sub-skill when the user needs a single-image `neural_style.py` run: choose content/style image paths, pass VGG-19 weights, select CPU/GPU, tune image size or optimizer iterations, choose initialization, and locate the output bundle.

Do not use this sub-skill for:

- masks, original-colors, layer weights, or multi-style weighting/interpolation; use [advanced-controls](../advanced-controls/SKILL.md).
- video frames, optical flow, or `stylize_video.sh`; use [video-stylization](../video-stylization/SKILL.md).
- install/import/runtime setup or VGG download policy; use the root [runtime notes](../../references/runtime-and-installation.md) and [root troubleshooting](../../references/troubleshooting.md), then return here for image commands.

## Operating route

1. Work from the repository checkout root. This repository is script-style, not an installable package; run `python neural_style.py ...` rather than importing a package.
2. Prefer the bundled non-interactive command builder over `stylize_image.sh` when the user gives content/style file paths:
   - [scripts/build_image_command.py](scripts/build_image_command.py) validates content/style/script paths, derives `--content_img_dir`, `--content_img`, `--style_imgs_dir`, and `--style_imgs`, prints an argv-safe command, and only executes when `--run` is explicitly supplied.
3. For concrete recipes and output layout, open [references/workflows.md](references/workflows.md).
4. For verified parser defaults and important single-image flags, open [references/output-and-parameters.md](references/output-and-parameters.md).
5. For failures involving TensorFlow v1, protobuf, VGG `.mat`, image reads, CPU/GPU, memory, shell prompts, `~` paths, or missing outputs, open [references/troubleshooting.md](references/troubleshooting.md).

## Required inputs for a normal image run

- `neural_style.py` reachable as a file, usually from the checkout root.
- One readable content image path.
- At least one readable style image path; one style is the normal path here.
- VGG-19 MatConvNet weights (`imagenet-vgg-verydeep-19.mat`) in the working directory or passed via `--model_weights`/builder `--model-weights`.
- A TensorFlow 1.x-compatible runtime with `tf.Session` and `tf.contrib.opt.ScipyOptimizerInterface` for L-BFGS runs.

Full stylized renders require the external VGG weights and are not assumed available by this sub-skill. The verified local evidence for this generated skill covered CLI help/import-level behavior, source inspection, and command construction rather than a full render.
