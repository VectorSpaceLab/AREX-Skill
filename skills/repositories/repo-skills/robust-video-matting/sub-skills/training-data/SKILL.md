---
name: training-data
description: "Use when preparing RobustVideoMatting datasets, DATA_PATHS,
  augmentations, losses, or four-stage training commands with GPU and
  data-layout caveats."
disable-model-invocation: true
metadata:
  disco-role: operating
license: GPL 3.0
---

# RobustVideoMatting Training and Data

Use this sub-skill for training setup, dataset schemas, path validation,
augmentation behavior, and adapting the official four-stage RVM training recipe.

## Read this when

- The user asks how to train or fine-tune RVM.
- The task mentions `train.py`, `train_config.py`, `DATA_PATHS`, VideoMatte240K,
  ImageMatte, COCO panoptic, Supervisely Person Dataset, or YouTubeVIS.
- You need to validate dataset folders before editing a config.
- The user hits training dependency, dataloader, NCCL, CUDA, OOM, or path
  errors.

Route other tasks elsewhere:

- Model forward-call details: [model-api](../model-api/SKILL.md).
- Inference/conversion: [inference-workflows](../inference-workflows/SKILL.md).
- Evaluation metrics and synthetic test composites:
  [evaluation-tools](../evaluation-tools/SKILL.md).

## Training setup workflow

1. Treat full RVM training as a large multi-GPU workflow, not a smoke test. The
   official training reference used data-center scale hardware and large
   external datasets.
2. Prepare dataset roots using the schemas in
   [references/data-layouts.md](references/data-layouts.md). Edit the
   `DATA_PATHS` mapping in a local training checkout to point at those roots.
3. Validate obvious directory mistakes before launching training:

   ```bash
   python scripts/rvm_validate_data_layout.py \
     --videomatte-train /data/VideoMatte240K_JPEG_SD/train \
     --background-images-train /data/Backgrounds/train \
     --background-videos-train /data/BackgroundVideos/train \
     --strict
   ```

4. Choose the stage command from
   [references/training-reference.md](references/training-reference.md), then
   adjust paths, GPU count, `--num-workers`, batch size, checkpoint locations,
   and logging directories for the target machine.
5. Validate failures against
   [references/troubleshooting.md](references/troubleshooting.md) before
   retrying a long run.

## Bundled references and script

- Read [references/data-layouts.md](references/data-layouts.md) for required
  directory shapes and `DATA_PATHS` keys.
- Read [references/training-reference.md](references/training-reference.md) for
  training flags, four official stages, distributed behavior, losses, and scale
  warnings.
- Read [references/dataset-api.md](references/dataset-api.md) for dataset and
  augmentation class behavior, sample outputs, and tensor shapes.
- Read [references/troubleshooting.md](references/troubleshooting.md) for
  missing data, relative paths, dependency pins, dataloader workers, CUDA/NCCL,
  and OOM recovery.
- Run [scripts/rvm_validate_data_layout.py](scripts/rvm_validate_data_layout.py)
  for safe filesystem validation. It does not import torch or start training.

## Key decisions

- Use `mobilenetv3` for the documented official stage examples unless the user
  asks to train the ResNet50 variant.
- Do not start `train.py` on CPU as a validation shortcut. The script discovers
  `torch.cuda.device_count()` and uses multiprocessing, NCCL, DDP,
  SyncBatchNorm, and AMP-oriented logic.
- Reduce `--num-workers` first when dataloaders exit unexpectedly on machines
  with limited CPU memory.
- Keep exact legacy requirement pins as historical repo evidence. For modern
  inspection or helper execution, use compatible PyTorch/TorchVision versions,
  but do not claim that full legacy training was verified unless it was.

## Acceptance check for training/data answers

A good answer names the dataset roots and expected subdirectories, distinguishes
matting and segmentation datasets, gives the stage command or config change,
states GPU/data scale limitations, recommends a safe layout validation step,
and avoids presenting full training as a quick smoke test.
