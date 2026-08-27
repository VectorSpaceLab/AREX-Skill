---
name: translation-workflows
description: "Train, test, and apply CycleGAN, pix2pix, and colorization models
  with correct dataset modes, checkpoint settings, device choices, and result
  paths."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Translation workflows

Use this sub-skill for requests to train or test CycleGAN, pix2pix, or colorization models; apply a pretrained generator; resume training; choose CPU/GPU/DDP settings; or diagnose checkpoint/result problems.

Route dataset layout, pair construction, image validation, downloads, and Cityscapes conversion to [`data-preparation`](../data-preparation/SKILL.md). Route new model/dataset classes and parser/registry changes to [`customization`](../customization/SKILL.md).

## Choose the workflow

- **CycleGAN, unpaired domains:** `--model cycle_gan --dataset_mode unaligned`; read [`references/workflows.md`](references/workflows.md).
- **pix2pix, paired domains:** `--model pix2pix --dataset_mode aligned`; read [`references/workflows.md`](references/workflows.md).
- **Colorization:** `--model colorization --dataset_mode colorization`; RGB images become Lab `L -> ab` pairs internally.
- **One-sided generator application:** `--model test` (which selects `single`) and, when needed, `--model_suffix _A` or `_B`.
- **Pretrained weights:** read [`references/pretrained-assets.md`](references/pretrained-assets.md) before any network download.

## Operating order

1. Validate the selected data root with [`data-preparation/scripts/validate_layout.py`](../data-preparation/scripts/validate_layout.py). The `--dataset_mode` and `--phase` determine which folders are read.
2. Choose the model/dataset pair and preserve the model's defaults unless the checkpoint or task requires an explicit override. See [`references/cli-reference.md`](references/cli-reference.md).
3. Select the device explicitly through the environment, because the current parser has no `--gpu_ids` option. Use a CPU-only PyTorch environment or prefix a Linux command with `CUDA_VISIBLE_DEVICES=` for CPU; prefix with `CUDA_VISIBLE_DEVICES=0,1` to choose visible GPUs; use `torchrun` only for the documented DDP path.
4. Generate or review the command with [`scripts/build_command.py`](scripts/build_command.py) before running a long job. It prints commands and never starts training or downloads.
5. Keep the training and test architecture settings aligned: `--netG`, `--norm`, channel counts, `--direction`, and dropout/checkpoint suffix choices must match the saved generator.
6. Inspect checkpoints and HTML output rather than treating oscillating GAN losses as a convergence proof. Use [`references/troubleshooting.md`](references/troubleshooting.md) when loading or preprocessing fails.

## Outputs and safety

Training writes options, loss logs, checkpoints, and optionally HTML samples under the configured checkpoint root, normally `checkpoints/<name>/`. Testing writes an HTML result page under `results/<name>/<phase>_<epoch>/` (or the configured `--results_dir`). Confirm those directories before launching a job that may overwrite an experiment name.

The repository imports W&B from its visualizer module even when `--use_wandb` is false, so the runtime environment must include `wandb`. W&B logging itself is opt-in; omit `--use_wandb` when credentials/network access are not available. HTML output is local and can be disabled during training with `--no_html`.

CUDA/DDP is an optional acceleration path in this skill. The verified inspection environment covers CPU only; do not claim CUDA success from a CPU import. Read the DDP caveat in [`references/troubleshooting.md`](references/troubleshooting.md) before using `torchrun`.
