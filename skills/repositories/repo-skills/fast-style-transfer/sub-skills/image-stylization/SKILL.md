---
name: image-stylization
description: "Guides Fast Style Transfer evaluate.py still-image and
  image-directory checkpoint inference, input validation, dimensions, device
  choices, and output troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: CC BY-NC 4.0
---

# Image Stylization

Use this sub-skill when the user has a trained Fast Style Transfer checkpoint and wants to apply it to one image or a directory of images with the bundled image stylization runtime, or when they need to debug checkpoint, image dimensions, output paths, device strings, batch size, or image IO behavior.

## Read and run

- Read [references/image-stylization-workflow.md](references/image-stylization-workflow.md) for single-image and directory recipes, checkpoint expectations, shape handling, device/batch decisions, and validation steps.
- Read [references/api-and-cli-reference.md](references/api-and-cli-reference.md) for verified CLI flags and callable signatures from the bundled image stylization runtime, the bundled `transform.py` module, and the bundled `utils.py` module.
- Read [references/troubleshooting.md](references/troubleshooting.md) for missing checkpoints, dimension assertions, restore errors, CPU slowness, output path issues, and image format problems.
- Run [scripts/validate_image_stylization_inputs.py](scripts/validate_image_stylization_inputs.py) before restoring a checkpoint or processing a directory. It validates paths, dimensions, and option semantics without running TensorFlow inference.

## When to use this route

Use this route for requests like:

- "Stylize this photo using a trained Fast Style Transfer checkpoint."
- "Batch process a directory of content images with the bundled image stylization runtime."
- "Why does the bundled image stylization runtime say images have different dimensions?"
- "Should I pass a checkpoint directory or a `.ckpt` path?"
- "How do I run on CPU for a small debug case?"

Route away when:

- The user needs to train or create a checkpoint first: [../training/SKILL.md](../training/SKILL.md)
- The user needs to process video: [../video-stylization/SKILL.md](../video-stylization/SKILL.md)

## Command patterns

Single image:

```bash
python sub-skills/image-stylization/scripts/run_image_stylization.py \
  --checkpoint checkpoints/udnie \
  --in-path content/stata.jpg \
  --out-path outputs/stata_udnie.jpg \
  --device /cpu:0 \
  --batch-size 1
```

Directory of same-size images:

```bash
mkdir -p outputs/batch
python sub-skills/image-stylization/scripts/run_image_stylization.py \
  --checkpoint checkpoints/udnie \
  --in-path content/batch \
  --out-path outputs/batch \
  --device /gpu:0 \
  --batch-size 4
```

Directory with mixed dimensions:

```bash
python sub-skills/image-stylization/scripts/run_image_stylization.py \
  --checkpoint checkpoints/udnie \
  --in-path content/mixed \
  --out-path outputs/mixed \
  --allow-different-dimensions
```

Preflight with the bundled helper:

```bash
python sub-skills/image-stylization/scripts/validate_image_stylization_inputs.py \
  --checkpoint checkpoints/udnie \
  --in-path content/mixed \
  --out-path outputs/mixed \
  --allow-different-dimensions
```

## Behavior facts

- The bundled image stylization runtime accepts `--in-path` as either a file or a directory.
- When `--in-path` is a file and `--out-path` is an existing directory, output uses the input basename inside that directory.
- When `--in-path` is a directory, output paths are formed by joining `--out-path` with each top-level filename from the input directory.
- Without `--allow-different-dimensions`, directory mode assumes all images have the same shape as the first image.
- With `--allow-different-dimensions`, the script groups images by shape and processes each shape group separately.
- Default device in the CLI is `/gpu:0`, but `ffwd_to_img` defaults to `/cpu:0`; choose explicitly.

## Validation limits

The bundled helper does not restore checkpoints or run the transform network. It cannot prove visual correctness, checkpoint compatibility, or TensorFlow GPU execution. It is designed to catch path, dimension, and option issues before a costly run.
