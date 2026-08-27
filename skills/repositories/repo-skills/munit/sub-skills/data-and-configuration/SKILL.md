---
name: data-and-configuration
description: "Validate MUNIT dataset layouts, YAML configs, demo-data
  assumptions, and data-preparation plans before training or inference."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Data and Configuration

Use this sub-skill when the task is about MUNIT YAML files, folder/list dataset layouts, demo data, path repair, preprocessing scripts, or data-loader failures. The goal is to catch layout and config mistakes before a long CUDA training or checkpointed inference run.

## Responsibilities

- Explain the two supported dataset modes: folder mode with `data_root` and list mode with paired `data_folder_*` plus `data_list_*` keys.
- Validate the required training, model, optimizer, logging, resize/crop, and trainer-specific config keys.
- Diagnose image discovery, list-root mismatches, missing domain splits, invalid image extensions, `display_size` mistakes, and crop/resize issues.
- Distill the repo demo shell scripts into safe data-preparation guidance without running downloads, ImageMagick conversion, or training.
- Provide safe bundled validators that do not import MUNIT, allocate CUDA, download datasets, or mutate user data.

## Start Here

1. Read `references/configuration.md` when editing or reviewing a YAML file.
2. Read `references/data-formats.md` when the user asks how to arrange folders or list files.
3. Read `references/dataset-preparation.md` before adapting edges2shoes, edges2handbags, Yosemite, or another unpaired image-to-image dataset.
4. Run the config validator from this sub-skill directory, or from any directory with an explicit path:

   ```bash
   python scripts/validate_munit_config.py --config /path/to/config.yaml --repo-root /path/to/user/munit-checkout
   ```

5. Inspect a dataset layout before a training run:

   ```bash
   python scripts/inspect_munit_dataset.py --config /path/to/config.yaml --repo-root /path/to/user/munit-checkout
   ```

## Route Elsewhere

- Runtime installation, PyTorch/CUDA compatibility, and dependency imports: `../environment-and-setup/`.
- Launching or resuming training after the data/config checks pass: `../training/`.
- Single-image or batch checkpointed translation commands: `../inference-and-evaluation/`.
- Network/trainer class modifications or PyTorch porting: `../model-internals/`.

## Safety Gates

- Do not run demo shell scripts blindly. They delete and recreate dataset folders, download public archives, call external `convert`, and launch a full training command.
- Do not treat a successful YAML parse as sufficient. Check whether the chosen mode's paths and domain splits exist for the user's checkout.
- Do not change a full dataset in place while debugging. Build a tiny copy or validate paths first.
- Do not rely on the original generation checkout's sample images. Future runs should use the user's own dataset and config paths.

## Reference Map

- `references/configuration.md` - required YAML keys, trainer-specific fields, resize/crop rules, and config editing patterns.
- `references/data-formats.md` - folder mode, list mode, image extensions, and loader behavior.
- `references/dataset-preparation.md` - safe adaptation of the repo's dataset download/crop scripts.
- `references/troubleshooting.md` - symptoms, causes, and fixes for config/data-loader failures.
- `scripts/validate_munit_config.py` - static config validator with path checks.
- `scripts/inspect_munit_dataset.py` - image-count and list-file inspection helper.
