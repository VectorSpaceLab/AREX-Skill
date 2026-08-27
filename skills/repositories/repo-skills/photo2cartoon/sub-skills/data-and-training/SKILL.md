---
name: data-and-training
description: "Guide dataset layout, batch preprocessing outputs, ImageFolder
  loader semantics, GAN training CLI/options, checkpoint/resume behavior, and
  validation before training."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Data and Training

Use this sub-skill when you need to prepare Photo2Cartoon training data, validate the `dataset/photo2cartoon` layout, understand preprocessing outputs, or review the GAN training launch and checkpoint flow.

Route away from this sub-skill when the main topic is:
- generator/discriminator architecture or tensor internals: `../model-internals/SKILL.md`
- face alignment, segmentation, or crop math: `../preprocessing/SKILL.md`
- `.pt` / `.onnx` inference assets or prediction flow: `../portrait-inference/SKILL.md`

## Start Here

1. Read `references/data-formats.md` for the dataset tree, supported image extensions, `ImageFolder` semantics, and preprocessing output naming.
2. Read `references/training-workflow.md` for the `train.py` CLI, defaults, result-directory naming, checkpoint keys, and resume behavior.
3. Read `references/troubleshooting.md` when a split is missing, a folder is empty, an extension is ignored, a checkpoint load fails, or GPU memory is tight.
4. Run the bundled validator before training:

```bash
python scripts/validate_dataset_layout.py --dataset-root /path/to/dataset/photo2cartoon
```

5. Build the guarded training command from this skill instead of copying a source-script command by hand:

```bash
python scripts/build_training_command.py --repo-root /path/to/photo2cartoon-checkout --dataset photo2cartoon
```

Use `--strict` when unsupported files should fail the dataset check and `--check-images` when Pillow decode validation is useful.

## Covered Facts

- `dataset/photo2cartoon/{trainA,trainB,testA,testB}` layout
- allowed image suffixes and recursive `ImageFolder` scanning
- preprocessing output naming and white-background face crops
- `train.py` defaults, result-directory naming, and checkpoint keys
- `--resume` / `--pretrained_weights` expectations
- loss weights, GPU limits, and batch-size cautions

## Not Covered

- generator/discriminator internals
- face detection / segmentation implementation details
- inference recipes for model assets
- network downloads, training runs, or file writes outside the bundled validator

## Bundled Helper

- `scripts/validate_dataset_layout.py`: safe, argparse-based dataset layout validator with explicit `--dataset-root` and optional stricter checks.
- `scripts/build_training_command.py`: guarded command builder for source-compatible train/test launches; dry-run by default and executes only with `--execute`.
