---
name: training
description: "Guides command-line stylegan2_pytorch training, checkpoint
  resume/restart, image generation, interpolation, augmentation, logging, and
  CUDA troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Training and CLI Workflows

Use this sub-skill for the installed `stylegan2_pytorch` command. It covers
training from image folders, checkpoint behavior, sample generation,
interpolation GIFs, low-data augmentation, optional logging/FID features,
transparent images, and memory/backend choices.

## Start here

1. Confirm the package imports and CUDA is available with the root checker:
   [`../../scripts/check_install.py`](../../scripts/check_install.py).
2. Read [references/data-layout.md](references/data-layout.md) before building a
   command, especially when the user's data folder may be empty, nested, or have
   unsupported file extensions.
3. Use [references/cli-reference.md](references/cli-reference.md) to translate
   user intent into exact CLI flags and defaults.
4. Use [references/workflows.md](references/workflows.md) for complete recipes:
   new training, resume/restart, generation, interpolation, FID/logging, and
   multi-GPU variants.
5. Use [references/troubleshooting.md](references/troubleshooting.md) when the
   command fails, diverges, runs out of memory, cannot find images, cannot load
   a checkpoint, or hits an optional dependency issue.

## Common task routes

- **Train a new model:** choose `--data`, `--name`, `--image_size`,
  `--batch_size`, `--gradient_accumulate_every`, `--network_capacity`, output
  directories, and whether `--new` is needed.
- **Resume training:** keep the same project `--name` and output directories;
  omit `--new` so the latest `model_<n>.pt` is loaded.
- **Restart with changed architecture/data settings:** add `--new` and make the
  output path decision explicit because the command clears the existing project
  model/results directories.
- **Generate still samples:** run with `--generate` after a checkpoint exists;
  use `--load_from` and `--trunc_psi` when the user requests a specific
  checkpoint or truncation.
- **Generate interpolation:** run with `--generate_interpolation`, tune
  `--interpolation_num_steps`, and add `--save_frames` only when individual
  frame files are desired.
- **Low-data training:** use `--aug_prob` and `--aug_types`; document that
  supported differentiable augmentation types come from the package's
  DiffAugment map.
- **Memory-sensitive training:** reduce `--batch_size`, raise
  `--gradient_accumulate_every`, and lower `--network_capacity` before changing
  core architecture flags.
- **Optional add-ons:** FID (`--calculate_fid_every`) needs `pytorch-fid`; Aim
  logging (`--log`) needs an Aim service/UI setup for visualization; Apex fp16
  (`--fp16`) needs a compatible Apex install.

## Bundled helper scripts

- [`scripts/make_tiny_fixture.py`](scripts/make_tiny_fixture.py) creates a small
  deterministic RGB or RGBA image folder for smoke commands when the user has no
  safe local fixture.
- [`scripts/train_smoke.py`](scripts/train_smoke.py) wraps the installed CLI with
  one-step, low-capacity defaults and temporary output directories. Use
  `--dry-run` first when explaining or reviewing commands; execute it only in a
  CUDA environment.

## Boundaries

- Do not use this sub-skill for Python `ModelLoader` checkpoint sampling; route
  that to [programmatic-api](../programmatic-api/SKILL.md).
- Do not use this sub-skill for source-code refactors, release publishing, or
  general GAN theory detached from this package.
- Do not direct future agents to read or run files from the original repository
  checkout. Use the installed package command and bundled references/scripts in
  this skill.
