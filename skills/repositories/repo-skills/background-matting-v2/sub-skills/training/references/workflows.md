# Training workflows

## Purpose

Use this file for the concrete training and validation flow, including the data
layout and the important CLI quirks.

## Base training

`train_base.py` trains the coarse model.

Safe wrapper first:

```bash
python sub-skills/training/scripts/run_training.py \
  --repo-root <repo-checkout> \
  --stage base \
  --dry-run \
  -- \
  --dataset-name videomatte240k \
  --model-backbone resnet50 \
  --model-name bgm-base-demo \
  --epoch-end 1
```

Important facts:

- `--model-pretrain-initialization` is the pretraining hook.
- `--model-last-checkpoint` resumes from a checkpoint.
- Logs go to `log/<model-name>` and checkpoints go to `checkpoint/<model-name>`.
- Validation uses the paired foreground/alpha and background datasets.

## Refine training

`train_refine.py` trains the full refinement model and is the CUDA/DDP-heavy
workflow.

Safe wrapper first:

```bash
python sub-skills/training/scripts/run_training.py \
  --repo-root <repo-checkout> \
  --stage refine \
  --dry-run \
  -- \
  --dataset-name videomatte240k \
  --model-backbone resnet50 \
  --model-name bgm-refine-demo \
  --epoch-end 1
```

Important facts:

- the script uses `torch.cuda.device_count()` to determine world size
- the batch size must be divisible by the GPU count
- the script uses NCCL for distributed training
- the help text exposes `--model-refine-thresholding` with an `-ing` suffix,
  not `--model-refine-threshold`
- `--model-refine-kernel-size` accepts `1` or `3`

## Data layout

`data_path.py` must point at real directories for the foreground/alpha pairs and
background images.

- foreground/alpha trees need matching relative structure
- both trees can contain nested `jpg` or `png` files
- `backgrounds.train` and `backgrounds.valid` are auxiliary image roots
- the `backgrounds` key appears in the CLI choices, but it is not a sensible
  foreground dataset choice for the main training loop because the code expects
  a foreground/alpha pair under `DATA_PATH[dataset_name]`

## Evaluation benchmark

The Octave/MATLAB benchmark script expects:

- `pha/`
- `fgr/`
- `trimap/`

It computes MSE, SAD, gradient, connectivity, and foreground MSE over the
benchmark set.

## When to use the smoke helpers

- Run `scripts/check_data_layout.py` after editing `data_path.py`.
- Run the dry-run wrapper before launching expensive training.
- Use the smoke helper rather than a full training run when you only need to
  prove the data layout or command shape.
