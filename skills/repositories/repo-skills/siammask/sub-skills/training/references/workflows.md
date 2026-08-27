# Training Workflows

## When to Read

Read this before composing a SiamMask training command or answering training/runtime planning questions.

## Common Training Preconditions

- CUDA-capable PyTorch environment verified with the root check helper.
- Checkout-local Cython extensions built.
- Training datasets prepared as `crop511` directories plus JSON indexes.
- Config file selected from the experiment family.
- Checkpoint/pretrained file availability confirmed before `--run`.
- Runtime approved: the README reports base training around 10 hours on four Tesla V100 GPUs.

## SiamMask Base Training

Purpose: train the base SiamMask tracker with RPN classification/regression and mask losses.

Typical config behavior:

- Uses COCO, ImageNet DET, ImageNet VID, and YouTube-VOS crop/index data.
- Uses `loss.weight` with classification, localization, and mask weights.
- Uses log LR schedule with warmup and ResNet feature unfreezing during training.

Dry-run command:

```bash
python scripts/run_training.py --repo-root <siammask-checkout> --gpu 0,1,2,3 base \
  --config config.json --batch 64 --workers 20 --epochs 20
```

Execution command after approval:

```bash
python scripts/run_training.py --repo-root <siammask-checkout> --run --gpu 0,1,2,3 base \
  --config config.json --batch 64 --workers 20 --epochs 20
```

Outputs are experiment-local snapshots and logs. After training, use the tracking sub-skill to test checkpoints instead of embedding evaluation into a long training run.

## SiamMask Refine/Sharp Training

Purpose: train the refine module on top of a base SiamMask checkpoint.

Required decision: choose `--pretrained <base-checkpoint>` or resume from an existing refine checkpoint.

Dry-run command:

```bash
python scripts/run_training.py --repo-root <siammask-checkout> --gpu 0,1,2,3 refine \
  --config config.json --pretrained <base-checkpoint.pth> --batch 64 --workers 20 --epochs 20
```

Notes:

- The refine config uses COCO and YouTube-VOS data and sets mask loss weight while classification/localization loss weights are zero.
- The script freezes feature/RPN components and trains mask/refine components.
- Use tracking `test` with `--mask --refine` after checkpoints are produced.

## SiamRPN ResNet Training

Purpose: train the unofficial SiamRPN/ResNet box-only baseline.

Dry-run command:

```bash
python scripts/run_training.py --repo-root <siammask-checkout> --gpu 0,1,2,3 siamrpn \
  --config config.json --batch 256 --workers 20 --epochs 20
```

Notes:

- The loss config has classification and localization weights only.
- Do not use `--mask` or `--refine` in downstream tracking evaluation.
- Dataset requirements mirror the base training mix.

## Resume and Pretraining

- `--resume` restores model and optimizer state from a checkpoint and continues from `--start-epoch`.
- `--pretrained` loads model weights without optimizer state. It is required for refine training from a selected base checkpoint and useful for backbone/model initialization.
- The repo's `load_pretrain` handles checkpoints with and without `state_dict`, removes `module.` prefixes, and can retry by prefixing `features.` for feature-only pretraining.

## Post-Training Evaluation

Do not run broad post-training evaluation until checkpoint creation has succeeded. Use the tracking sub-skill to compose dry-run evaluation commands for selected epochs, datasets, GPU visibility, and mask/refine flags.
