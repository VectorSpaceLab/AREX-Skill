# PyTorch-StudioGAN overview

## When to read

Read this for a compact map of StudioGAN capabilities, entry points, dependencies, and limitations before choosing a sub-skill.

## Project shape

StudioGAN is a PyTorch library/checkout for conditional and unconditional image-generation GAN experiments. It provides unified YAML-driven implementations and benchmark recipes for representative GANs such as DCGAN, LSGAN, WGAN variants, SNGAN, SAGAN, BigGAN, BigGAN-Deep, ContraGAN, ReACGAN, StyleGAN2/3, and data-efficient/regularized variants.

The repository is script-first:

- Primary training/checkpoint entry point: `python src/main.py` in a StudioGAN checkout.
- Standalone image-folder metric entry point: `python src/evaluate.py` in a StudioGAN checkout.
- YAML configs live under `src/configs/` and drive model, data, loss, optimizer, augmentation, and StyleGAN-specific settings.
- No packaging metadata or console script is provided, so helpers in this skill validate a user-supplied checkout with `--repo-root`.

## Main capability groups

| Capability group | Important files in a StudioGAN checkout | Skill route |
| --- | --- | --- |
| Training/configuration | `src/main.py`, `src/config.py`, `src/configs/**`, `src/data_util.py`, `src/utils/hdf5.py`, `src/models/model.py`, `src/utils/ckpt.py` | `sub-skills/training-and-configuration/` |
| Standalone metrics | `src/evaluate.py`, `src/metrics/features.py`, `src/metrics/fid.py`, `src/metrics/ins.py`, `src/metrics/prdc.py`, `src/metrics/preparation.py`, `src/metrics/inception_net.py` | `sub-skills/evaluation-metrics/` |
| Checkpoint sampling/analysis | `src/main.py`, `src/loader.py`, `src/worker.py`, `src/utils/sample.py`, `src/utils/sefa.py`, `src/utils/misc.py` | `sub-skills/sampling-and-analysis/` |

## Config catalog summary

The distilled source tree contains 196 YAML config files under `src/configs/`. Dataset families include CIFAR10, CIFAR100, CIFAR1000-named configs, Tiny/Baby/Papa/Grandpa ImageNet, ImageNet, AFHQ/AFHQv2, CUB200, and FFHQ. Backbones include `deep_conv`, `resnet`, `big_resnet`, `big_resnet_deep_legacy`, `big_resnet_deep_studiogan`, `stylegan2`, and `stylegan3`. Discriminator conditioning methods represented in configs include `W/O`, `AC`, `PD`, `MH`, `MD`, `2C`, `D2DCE`, and `SPD`.

Use the training sub-skill before editing a config because `src/config.py` enforces many compatibility rules that are easy to violate.

## Runtime dependencies

The README documents installing PyTorch first for the user's hardware, then runtime libraries including `tqdm`, `ninja`, `h5py`, `kornia`, `matplotlib`, `pandas`, `sklearn`/`scikit-learn`, `scipy`, `seaborn`, `wandb`, `PyYAML`, `click`, `requests`, `pyspng`, `imageio-ffmpeg`, and `timm`.

Observed import surfaces also use `PIL`, `numpy`, `torchvision`, and optional/legacy `tensorflow` for `src/metrics/ins_tf13.py`. Do not install TensorFlow 1.x unless a user explicitly asks for the legacy script.

## Backend and side-effect reality

- Training and checkpoint workflows are CUDA-oriented. The code calls CUDA device APIs and places models/tensors on GPU devices.
- DDP uses PyTorch distributed settings and defaults to `nccl` on CUDA.
- Metric backbones may download pretrained weights through PyTorch/TorchVision/Torch Hub style loaders.
- W&B is initialized in the training worker; users need a login/offline policy before long runs.
- StyleGAN2/3 paths may compile C++/CUDA plugins under PyTorch extension caches on first use; CUDA toolkit/compiler issues are distinct from merely having a CUDA PyTorch wheel.

## Selected limitations

- This skill does not bundle StudioGAN itself or its benchmark datasets/checkpoints.
- Native benchmark training and meaningful IS/FID/PRDC values were not run during distillation; the skill provides operating guidance, validation helpers, and command builders.
- Historical `logs/**` and `docs/figures/**` were treated as reference evidence only and are not bundled.
- The legacy TensorFlow 1.3 inception-score path is documented as optional/obsolete, not part of the verified current metric workflow.
