---
name: fast-style-transfer
description: "Guides TensorFlow Fast Style Transfer training, image stylization,
  and video stylization workflows from checkpoints, VGG/COCO assets, and
  script-oriented CLIs."
disable-model-invocation: true
metadata:
  disco-role: operating
license: CC BY-NC 4.0
---

# Fast Style Transfer Repo Skill

Use this skill when a task involves Logan Engstrom's TensorFlow Fast Style Transfer repository, real-time neural style transfer, the bundled training runtime, the bundled image stylization runtime, the bundled video stylization runtime, transform-network checkpoints, VGG19 `.mat` assets, or COCO-style training image directories.

This repo is script-oriented rather than an installable Python package. This skill is self-contained: the workflow details, adapted runtime wrappers, CLI flags, validation helpers, troubleshooting, and provenance needed for normal use are bundled here.

## Read first

- Read [references/repo-provenance.md](references/repo-provenance.md) before deciding whether this skill matches a checkout or should be refreshed.
- Read [references/setup-and-assets.md](references/setup-and-assets.md) when preparing TensorFlow dependencies, VGG19 `.mat`, COCO training images, pretrained checkpoints, or ffmpeg/moviepy assets.
- Read [references/troubleshooting.md](references/troubleshooting.md) for cross-cutting install/import, TensorFlow version, asset download, checkpoint, and backend failures.
- Run or adapt [scripts/inspect_fast_style_transfer.py](scripts/inspect_fast_style_transfer.py) for a safe dependency/source-surface check. It does not download assets, restore checkpoints, train, or process media.

## Route by task

| User task | Read |
| --- | --- |
| Train a style transform network, choose loss weights, validate style/train/VGG inputs, or plan a long GPU run | [sub-skills/training/SKILL.md](sub-skills/training/SKILL.md) |
| Stylize one image or a directory of images from a trained checkpoint, debug dimensions, output paths, devices, or checkpoint restore | [sub-skills/image-stylization/SKILL.md](sub-skills/image-stylization/SKILL.md) |
| Stylize a video from a trained checkpoint, check moviepy/ffmpeg, plan batch/device settings, or debug video output | [sub-skills/video-stylization/SKILL.md](sub-skills/video-stylization/SKILL.md) |

## Public prerequisites

The historical repository documentation names TensorFlow-era dependencies. For modern inspection and command planning, verify a Python environment with:

```bash
python - <<'PY'
import tensorflow as tf, numpy, scipy, imageio, PIL, moviepy
print('tensorflow', tf.__version__)
print('gpu devices', tf.config.list_physical_devices('GPU'))
PY
```

For practical full training or large video/image batches, use a compatible GPU TensorFlow stack. CPU can validate parsers and run small image inference, but full training on CPU is normally impractical.

Core runtime surfaces:

- Training script: `python sub-skills/training/scripts/run_training.py --checkpoint-dir ... --style ... --train-path ... --vgg-path ...`
- Image stylization script: `python sub-skills/image-stylization/scripts/run_image_stylization.py --checkpoint ... --in-path ... --out-path ...`
- Video stylization script: `python sub-skills/video-stylization/scripts/run_video_stylization.py --checkpoint ... --in-path ... --out-path ...`
- Bundled runtime modules used by those scripts: `scripts/fast_style_transfer_runtime/transform.py`, `scripts/fast_style_transfer_runtime/optimize.py`, `scripts/fast_style_transfer_runtime/vgg.py`, and `scripts/fast_style_transfer_runtime/utils.py`.

The generated validation helpers in this skill check paths, numeric options, media shapes, optional dependencies, and command readiness without running expensive neural style transfer.

## Asset model

This skill does not bundle model weights, VGG networks, COCO data, checkpoints, or example media. Treat these as user-supplied runtime assets:

- VGG19 `.mat` for training losses.
- A directory of training content images such as COCO `train2014` or an equivalent image corpus.
- A style image used to train a new transform network.
- A trained Fast Style Transfer checkpoint for image or video stylization.
- `ffmpeg`/moviepy support for video workflows.

## Minimum safe checks

Before a costly run, prefer these safe checks:

```bash
python scripts/inspect_fast_style_transfer.py --json
python sub-skills/training/scripts/validate_training_inputs.py --help
python sub-skills/image-stylization/scripts/validate_image_stylization_inputs.py --help
python sub-skills/video-stylization/scripts/validate_video_stylization_inputs.py --help
```

When a local checkout is available and you want source-surface inspection, pass its directory to the root inspector:

```bash
python scripts/inspect_fast_style_transfer.py --repo-root /path/to/fast-style-transfer --json
```

Do not use these checks as proof that pretrained checkpoints, VGG assets, COCO data, GPU speed, or full video encoding work; those require separate runtime assets and backend verification.

## Common decisions

- Need a checkpoint? Use the training sub-skill if creating one; use image/video sub-skills if consuming one.
- Need the fastest path to stylize a still image? Use `image-stylization`; pass `/cpu:0` only for small or debugging runs, and a GPU device for throughput when TensorFlow GPU is configured.
- Need to process mixed-size image directories? Use `image-stylization` and either normalize image dimensions first or enable the script's different-dimensions grouping path.
- Need video output? Use `video-stylization`; verify checkpoint, moviepy, ffmpeg, and device/batch choices before processing frames.
- Need downloads? Read setup/assets guidance; do not run network or large-data downloads implicitly.

## Do not use this skill when

- The task is about a different style-transfer implementation, PyTorch neural style transfer, diffusion image generation, or a generic TensorFlow tutorial unrelated to this repository.
- The user needs legal/commercial licensing advice beyond the repository's public research-use notice and citation metadata.
- The task asks to modify the repository source code rather than use its public workflows; use a repository-maintenance workflow instead.
