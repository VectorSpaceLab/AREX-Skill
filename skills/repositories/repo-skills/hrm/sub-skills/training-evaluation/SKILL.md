---
name: training-evaluation
description: "Run and troubleshoot HRM CUDA training, checkpoint evaluation, W&B
  logging, and ARC prediction post-processing."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# HRM Training and Evaluation

Use this sub-skill when the task is to launch HRM experiments, adapt Hydra
training overrides, evaluate checkpoints, interpret saved prediction shards, or
troubleshoot CUDA/W&B/checkpoint failures.

## When to use

- The user wants to run `pretrain.py`, `torchrun ... pretrain.py`, or
  `evaluate.py checkpoint=<CHECKPOINT_PATH>`.
- The task mentions `global_batch_size`, `epochs`, `eval_interval`, W&B,
  checkpoint paths, `all_config.yaml`, `*_all_preds.<rank>`, `eval/exact_accuracy`,
  or ARC top-K aggregation.
- A run fails due to CUDA, FlashAttention, `adam_atan2_backend`, Hydra
  overrides, distributed launch, dataset batch sizing, W&B login/offline mode,
  or checkpoint/config mismatch.

## Route map

1. Read [references/workflows.md](references/workflows.md) for verified train,
   evaluate, checkpoint, and ARC post-processing commands.
2. Read [references/configuration.md](references/configuration.md) for Hydra
   defaults and important overrides.
3. Read [references/troubleshooting.md](references/troubleshooting.md) for CUDA,
   W&B, checkpoint, distributed, and evaluation failures.
4. Run [scripts/check_training_env.py](scripts/check_training_env.py) before a
   long run to validate imports and CUDA dependency readiness without training.
5. Use [scripts/arc_postprocess.py](scripts/arc_postprocess.py) after
   `evaluate.py` saves ARC prediction shards.

## Baseline commands

Single-GPU Sudoku quick demo after dataset creation:

```bash
OMP_NUM_THREADS=8 python pretrain.py \
  data_path=data/sudoku-extreme-1k-aug-1000 \
  epochs=20000 eval_interval=2000 global_batch_size=384 \
  lr=7e-5 puzzle_emb_lr=7e-5 \
  weight_decay=1.0 puzzle_emb_weight_decay=1.0
```

Eight-GPU ARC-1 default training:

```bash
OMP_NUM_THREADS=8 torchrun --nproc-per-node 8 pretrain.py
```

ARC-2:

```bash
OMP_NUM_THREADS=8 torchrun --nproc-per-node 8 pretrain.py data_path=data/arc-2-aug-1000
```

Evaluate an ARC checkpoint:

```bash
OMP_NUM_THREADS=8 torchrun --nproc-per-node 8 evaluate.py checkpoint=<CHECKPOINT_PATH>
```

## Bounded readiness check

```bash
python <skill>/sub-skills/training-evaluation/scripts/check_training_env.py \
  --repo-root /path/to/HRM --require-cuda
```

This imports `pretrain.py` and `evaluate.py`, checks PyTorch CUDA, and verifies
FlashAttention/adam-atan2 backend imports. It does not start training, download
data, contact W&B, or require checkpoints.

## Boundaries

- Use `data-preparation` for dataset creation and validation before training.
- Use `model-architecture` for model internals, losses, identifiers, and
  architecture-level CUDA import issues.
- This sub-skill treats real HRM training/evaluation as CUDA-required. CPU-only
  runs are not a verified substitute.
- Do not run full training or checkpoint evaluation as a smoke test unless the
  user explicitly accepts runtime, GPU, data, storage, and W&B implications.
