---
name: data-and-training
description: "Prepare pix2code paired datasets, convert screenshots to arrays,
  and plan or troubleshoot the legacy training workflow."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Data and Training

Use this sub-skill for the preprocessing side of pix2code: verifying paired `.gui` and image files, splitting the archive into training and evaluation sets, converting screenshots to compressed arrays, and understanding the legacy training command lines.

## Read first

- [references/data-formats.md](references/data-formats.md) for directory layouts, file naming, and the `.npz` feature contract.
- [references/training-workflows.md](references/training-workflows.md) for command patterns, memory mode, and what the legacy training script expects.
- [references/troubleshooting.md](references/troubleshooting.md) for pairing errors, archive issues, OpenCV problems, and training-environment warnings.
- [scripts/prepare_pix2code_dataset.py](scripts/prepare_pix2code_dataset.py) for portable validation, splitting, and conversion.

## Quick workflow

1. Validate the input directory first:

```bash
python sub-skills/data-and-training/scripts/prepare_pix2code_dataset.py validate --input datasets/web/all_data
```

2. Split a directory of paired `.gui`/`.png` files into train/eval sets:

```bash
python sub-skills/data-and-training/scripts/prepare_pix2code_dataset.py split --input datasets/web/all_data --distribution 6
```

3. Convert training images to `.npz` features when you want smaller files or faster uploads:

```bash
python sub-skills/data-and-training/scripts/prepare_pix2code_dataset.py convert --input datasets/web/training_set --output datasets/web/training_features
```

4. If the user wants to train, use the legacy command patterns from `training-workflows.md`. Treat training as expensive and dataset-specific.

## Boundaries

This sub-skill owns dataset preparation and training planning. It does not own screenshot-to-DSL generation; route that to [../sampling-and-generation/SKILL.md](../sampling-and-generation/SKILL.md). It does not own `.gui` compilation; route that to [../dsl-compilation/SKILL.md](../dsl-compilation/SKILL.md).

## Validation checklist

- Input directories contain paired `.gui` and `.png` files with matching basenames.
- Split counts are integral for the chosen distribution.
- Duplicate `.gui` content is kept out of the evaluation set when possible.
- Converted `.npz` files contain a `features` array alongside copied `.gui` files.
- Training advice names the legacy dependency stack and warns when OpenCV or TensorFlow pins are unavailable.
