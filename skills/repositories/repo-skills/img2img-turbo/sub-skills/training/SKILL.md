---
name: training
description: "Guide Pix2Pix-Turbo and CycleGAN-Turbo training, dataset
  validation, safe example downloads, checkpoints, metrics, and
  troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# img2img-turbo Training

Use this sub-skill when a user wants to train or fine-tune `img2img-turbo` models, validate paired or unpaired training data, acquire the small documented example datasets, reason about training checkpoints/metrics, or debug training launches.

Do **not** run full training, model inference, dataset downloads, or metric model downloads by default. Start with data validation and command construction; ask before launching expensive CUDA jobs or network actions.

## Route by task

- **Paired Pix2Pix-Turbo training**: use [data formats](references/data-formats.md) for `train_A`/`train_B` plus prompt JSON requirements, then use [training workflows](references/training-workflows.md#paired-pix2pix-turbo-training) for `accelerate launch` patterns.
- **Unpaired CycleGAN-Turbo training**: use [data formats](references/data-formats.md) for `train_A`/`train_B`, `test_A`/`test_B`, and fixed prompt files, then use [training workflows](references/training-workflows.md#unpaired-cyclegan-turbo-training) for `accelerate launch` patterns.
- **Dataset validation before training**: run the bundled [dataset validator](scripts/validate_training_dataset.py). It uses only the filesystem and JSON parsing; it does not import tokenizers, models, CUDA, or metric packages.
- **Example data acquisition**: use the bundled [safe downloader](scripts/download_example_dataset.sh) only after user approval. It requires `--dataset`, `--output-dir`, and `--yes` before any network action.
- **Training failures**: consult [training troubleshooting](references/troubleshooting.md), especially for prompt mismatches, missing fixed prompts, W&B/offline logging, FID/LPIPS/DINO dependencies, xformers/CUDA, `accelerate` ports/processes, `NCCL_P2P_DISABLE`, and storage growth.
- **Inference with a trained checkpoint**: route Pix2Pix-Turbo checkpoint usage to [paired-inference](../paired-inference/SKILL.md) and CycleGAN-Turbo checkpoint usage to [unpaired-inference](../unpaired-inference/SKILL.md). This sub-skill only explains the checkpoint handoff.

## Safe first steps

From this `training/` sub-skill directory, validate the dataset before any expensive launch:

```bash
python scripts/validate_training_dataset.py --mode paired --dataset-folder data/my_fill50k
python scripts/validate_training_dataset.py --mode unpaired --dataset-folder data/my_horse2zebra
```

For documented example datasets, show the action first; only run with explicit user approval:

```bash
bash scripts/download_example_dataset.sh --help
bash scripts/download_example_dataset.sh --dataset fill50k --output-dir data --yes
bash scripts/download_example_dataset.sh --dataset horse2zebra --output-dir data --yes
```

## Operating constraints

- Training is a CUDA-first workflow. Source training code constructs CUDA discriminators/metrics and does not have a verified CPU substitute for truthful training.
- Full training and full model inference were intentionally not used as default verification checks because they are long-running, GPU-heavy, write checkpoints/logs, and may download pretrained or metric assets.
- Keep runtime guidance self-contained: use the references here instead of reopening original repository training documents or scripts.
