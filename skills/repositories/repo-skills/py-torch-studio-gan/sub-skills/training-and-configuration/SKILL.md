---
name: training-and-configuration
description: "Choose, validate, and build safe StudioGAN training
  configurations, datasets, HDF5 flows, checkpoint resumes, DDP, mixed
  precision, and logging commands."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# StudioGAN training and configuration router

Use this sub-skill when the task is to choose or edit a StudioGAN YAML config, validate a training dataset layout, plan HDF5 or in-memory data loading, resume from checkpoints, freeze discriminator blocks, or build a safe `python src/main.py` training command for a separate StudioGAN checkout.

Do **not** use this sub-skill for standalone image-folder metrics or checkpoint visualization/latent analysis. Route those to sibling skills:

- Standalone IS/FID/PRDC/iFID/CAS folder metrics: [evaluation metrics](../evaluation-metrics/SKILL.md).
- Checkpoint image saving, KNN, interpolation, frequency, TSNE, SeFa, CAS commands after training: [sampling and analysis](../sampling-and-analysis/SKILL.md).

## Operating assumptions

- StudioGAN is script-first: run commands from a StudioGAN checkout with `python src/main.py`; do not expect package metadata or an installed console entry point.
- Training is a CUDA-oriented PyTorch workflow. CPU-only environments can validate configs and build commands, but practical training/evaluation requires CUDA-capable PyTorch and compatible dependent packages.
- W&B logging is imported by the training path. Decide before running whether to login with an API key, set offline mode, or redirect logs according to the execution environment policy.
- Use generic placeholders such as `/path/to/PyTorch-StudioGAN`, `/path/to/data`, `/path/to/save`, and `/path/to/checkpoint` in plans and commands.

## Start here

1. Identify the training scenario:
   - New training from an existing YAML config.
   - Custom ImageFolder adaptation.
   - Resume from `-ckpt`, optionally `-best`.
   - Transfer/freezeD training with `--freezeD` and a source checkpoint.
   - Single GPU, DataParallel, DistributedDataParallel, mixed precision, sync-BN, HDF5, or in-memory loading.
2. Read [training workflows](references/training-workflows.md) for command patterns and flag combinations.
3. Read [configuration reference](references/configuration-reference.md) before editing YAML; then run the config validator.
4. Read [data and HDF5](references/data-and-hdf5.md) before changing `DATA.name`, `DATA.num_classes`, image size, HDF5, or custom folders.
5. For StyleGAN2/3 or ADA/APA configs, read [StyleGAN ADA guide](references/stylegan-ada-guide.md).
6. If a command fails, map the message through [troubleshooting](references/troubleshooting.md) before retrying.

## Bundled safe helpers

All helpers are dry-run/validation tools. They do not train, download datasets intentionally, log into services, or modify checkpoints.

```bash
python sub-skills/training-and-configuration/scripts/validate_studiogan_config.py \
  --repo-root /path/to/PyTorch-StudioGAN \
  --cfg /path/to/PyTorch-StudioGAN/src/configs/CIFAR10/ContraGAN.yaml \
  --data-dir /path/to/data --save-dir /path/to/save --train --gpus 1
```

```bash
python sub-skills/training-and-configuration/scripts/check_studiogan_dataset.py \
  --data-dir /path/to/imagefolder --require-valid --min-classes 2 --min-images-per-class 1
```

```bash
python sub-skills/training-and-configuration/scripts/build_studiogan_train_command.py \
  --repo-root /path/to/PyTorch-StudioGAN \
  --cfg /path/to/PyTorch-StudioGAN/src/configs/CIFAR10/ContraGAN.yaml \
  --data-dir /path/to/data --save-dir /path/to/save \
  --gpus 0 --metrics is fid prdc --mixed-precision --hdf5 --load-in-memory
```

## Required checks before giving a run command

- `src/main.py` exists under the requested `--repo-root`.
- The YAML file is accepted by `config.Configurations` and `check_compatability` with parser-equivalent RUN defaults.
- `DATA.num_classes`, `DATA.img_size`, and `MODEL.backbone` match the dataset and intended command mode.
- Custom datasets have `train/<class>/...` and, for validation/reference evaluation, `valid/<class>/...`.
- `OPTIMIZATION.batch_size` is divisible by GPU world size; for analysis/CAS paths, keep it divisible by 8.
- `-l` is used only with `-hdf5`; iFID with HDF5 also requires in-memory loading.
- DDP is not combined with visualization, KNN, interpolation, frequency, TSNE, SeFa, Langevin/DDLS, or CAS flags.
- `--freezeD` includes `-ckpt` and uses a compatible source checkpoint.
