---
name: data-training
description: "Prepare Pytorch-UNet segmentation datasets and training runs,
  including data layout validation, CLI flags, checkpoints, W&B, CUDA, and AMP
  decisions."
disable-model-invocation: true
metadata:
  disco-role: operating
license: GPL 3.0
---

# data-training

Use this sub-skill when the task is about preparing image/mask data or running a Pytorch-UNet training job for semantic segmentation.

## Route here for

- Building a flat `data/imgs` and `data/masks` dataset for the stock training code.
- Choosing Carvana-style masks named `<id>_mask.<ext>` versus generic masks named `<id>.<ext>`.
- Validating image/mask pairing, duplicate IDs, subdirectories, size matches, scale, and discovered mask values before training.
- Constructing `train.py` commands and explaining `--epochs`, `--batch-size`, `--learning-rate`, `--load`, `--scale`, `--validation`, `--amp`, `--bilinear`, and `--classes`.
- Understanding W&B logging, checkpoint contents, train/validation splitting, CUDA/AMP acceleration, and CUDA out-of-memory recovery.
- Classifying the Kaggle Carvana download helper as credentialed/networked setup that must not be run as a default smoke check.

## Do not use this sub-skill for

- Architecture internals, `UNet(n_channels, n_classes, bilinear)`, decoder shape details, or checkpoint architecture mismatches outside a training workflow; route to `model-api`.
- Prediction output naming, converting class-index predictions back to images, visualization, or Dice evaluation on an existing dataloader; route to `prediction-evaluation`.
- Running Kaggle downloads, Docker workflows, W&B online jobs, or full training runs unless the user explicitly approves the network, credentials, disk, and runtime cost.

## First actions

1. Read [references/data-formats.md](references/data-formats.md) to confirm the dataset naming convention, mask suffix, scale, and mask-value expectations.
2. Run the bundled layout validator before expensive training:

   ```bash
   python scripts/validate_dataset_layout.py --images data/imgs --masks data/masks --scale 0.5
   ```

   Run this command from this sub-skill directory, or call the script by its copied path inside the generated skill tree.

   Add `--carvana` when masks use the Carvana `_mask` suffix.
3. Read [references/cli-reference.md](references/cli-reference.md) to assemble the exact `train.py` command.
4. Read [references/training-workflows.md](references/training-workflows.md) for checkpoint, W&B, CUDA/AMP, and resume/fine-tune decisions.
5. If the validator or training loop fails, read [references/troubleshooting.md](references/troubleshooting.md) and fix the data or command before retrying.

## Bundled safe helper

[scripts/validate_dataset_layout.py](scripts/validate_dataset_layout.py) is a no-network Python checker. It prints JSON and checks the flat folder contract, hidden-file handling, pair matching, optional Carvana suffixes, duplicate IDs, scale bounds, image/mask size equality, and sampled or full mask values without importing W&B or starting training.

[scripts/training_cli_wrapper.py](scripts/training_cli_wrapper.py) is a dry-run-first wrapper for a user-provided Pytorch-UNet checkout. Use it to preview the underlying `train.py` command and only pass `--execute` after the user approves training cost, W&B behavior, checkpoint writes, and backend use.
