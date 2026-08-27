---
name: neural-style-tf
description: "Use the legacy TensorFlow neural-style-tf script for artistic
  image and video style transfer, command planning, runtime checks, and
  troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: GPL 3.0
---

# neural-style-tf

Use this repo skill when the task involves Cameron Smith's `neural-style-tf` implementation of Gatys-style neural style transfer: constructing `neural_style.py` commands, preparing TensorFlow 1.x runtime checks, choosing image/video flags, preserving original colors, using segmentation masks, or diagnosing VGG/OpenCV/ffmpeg/legacy TensorFlow failures.

Do not use this skill for modern TensorFlow 2/Keras style-transfer APIs, PyTorch neural style examples, Stable Diffusion/Diffusers generation, or general image augmentation unless the user specifically names `neural-style-tf` or its script-style VGG-19 workflow.

## First checks

1. Confirm the target checkout or working directory has a `neural_style.py` script. This repository is not an installable package with console entry points; it is operated by running the script.
2. Read [references/repo-provenance.md](references/repo-provenance.md) when deciding whether this skill is current for a checkout or should be refreshed.
3. Read [references/runtime-and-installation.md](references/runtime-and-installation.md) before installing dependencies, downloading VGG-19 weights, or choosing CPU/GPU. For a disposable CPU-compatible check environment, use a private Python 3.7 runtime with TensorFlow 1.15, OpenCV, SciPy, NumPy, and `protobuf<3.21`.
4. Run [scripts/check_runtime.py](scripts/check_runtime.py) from the candidate runtime to verify TensorFlow v1 APIs, OpenCV/SciPy/NumPy imports, optional VGG weights, and optional ffmpeg availability.
5. Use [scripts/inspect_cli_defaults.py](scripts/inspect_cli_defaults.py) when a user asks for source-verified defaults without importing TensorFlow.

## Route by task

| User intent | Read next | Why |
| --- | --- | --- |
| Build a still-image style-transfer command from content/style paths, choose output names, or replace the interactive shell wrapper. | [sub-skills/image-stylization/SKILL.md](sub-skills/image-stylization/SKILL.md) | Owns base `python neural_style.py` image command construction, output layout, CPU/GPU choice, VGG path, and basic optimizer/image-size controls. |
| Blend multiple styles, use style masks/segmentation, preserve original colors, adjust layers/losses, or tune initialization/pooling/Adam. | [sub-skills/advanced-controls/SKILL.md](sub-skills/advanced-controls/SKILL.md) | Owns expert flags and validation for count-sensitive advanced parameters. |
| Plan video stylization, frame extraction, optical flow, temporal consistency, frame formats, or video assembly. | [sub-skills/video-stylization/SKILL.md](sub-skills/video-stylization/SKILL.md) | Owns video/frame pipeline planning and optical-flow file expectations. |
| Explain every `neural_style.py` argument by group. | [references/cli-reference.md](references/cli-reference.md) | Compact source-verified CLI catalog with defaults and caveats. |
| Diagnose installation, TensorFlow 2 incompatibility, protobuf descriptor errors, missing VGG, bad image reads, GPU fallback, or ffmpeg/deepflow issues. | [references/troubleshooting.md](references/troubleshooting.md) | Cross-cutting failure map before drilling into sub-skill-specific troubleshooting. |

## Minimal command pattern

A basic still-image command has this shape:

```bash
python neural_style.py \
  --content_img lion.jpg --content_img_dir ./image_input \
  --style_imgs kandinsky.jpg --style_imgs_dir ./styles \
  --model_weights imagenet-vgg-verydeep-19.mat \
  --device /cpu:0 --img_output_dir ./image_output --img_name result
```

Prefer the bundled image command builder for user-supplied file paths:

```bash
python sub-skills/image-stylization/scripts/build_image_command.py \
  --script neural_style.py \
  --content ./image_input/lion.jpg \
  --style ./styles/kandinsky.jpg \
  --device /cpu:0 --max-size 64 --max-iterations 1 --optimizer adam
```

The builder prints a command and runs nothing unless `--run` is explicitly supplied.

## Runtime constraints to preserve in answers

- `neural_style.py` uses TensorFlow 1.x symbols such as `tf.Session` and `tf.contrib.opt.ScipyOptimizerInterface`; TensorFlow 2.x without compatibility changes is not a drop-in replacement.
- Full renders require external VGG-19 MatConvNet weights named or passed as `imagenet-vgg-verydeep-19.mat`.
- The script defaults to `--device /gpu:0`, but CPU is accepted with `--device /cpu:0`; video is normally impractical without a compatible GPU.
- OpenCV reads images in BGR order; bad paths surface as `No such file` from the source `check_image(...)` path.
- Source CLI facts in this skill were verified by static parser inspection and CLI help under a TensorFlow 1.x CPU-compatible inspection runtime; full image/video renders are optional and model-weight dependent.

## Router metadata

Managed repo-skill import uses [references/repo-routing-metadata.json](references/repo-routing-metadata.json). Do not hand-edit live router Markdown; use the verified import helper only when a user later asks to import this skill.
