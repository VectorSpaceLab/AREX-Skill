# MambaVision training workflows

This reference distills the repo's training entry points into safe command recipes.
Use it to translate the bundled preset YAMLs and `train.sh` launch pattern into user-specific commands.

## Recommended build order

1. Pick the preset YAML that matches the target backbone.
2. Decide whether your dataset root uses `train` + `validation`, `train` + `val`, or the LMDB cache branch.
3. Choose single-GPU debug or multi-GPU `torchrun`.
4. Set the experiment tag, output root, batch size, and checkpoint policy.
5. If you change dataset size, update `--data_len` so the cosine schedule length stays correct.
6. Keep `--model-ema` enabled whenever `--mesa` is positive; the training loop uses the EMA model as a teacher for MESA.

## Safe preflight

- `python <training-entrypoint> --help`
- Keep this as a parser/import check only; do not treat it as a training launch.

## 8-GPU torchrun recipe

This is the pattern to use when adapting the published multi-GPU launch:

```bash
export CONFIG=mambavision_tiny_1k.yaml
export DATA_DIR=/path/to/imagenet
export OUTPUT_DIR=/path/to/output
export TAG=mambavision_tiny_1k_run
export MODEL=mamba_vision_T
export BATCH_SIZE=256
export LR=0.005
export WEIGHT_DECAY=0.05
export DROP_PATH=0.2

CUDA_VISIBLE_DEVICES=0,1,2,3,4,5,6,7 \
torchrun --standalone --nproc_per_node=8 <training-entrypoint> \
  --config "${CONFIG}" \
  --data_dir "${DATA_DIR}" \
  --train-split train \
  --val-split validation \
  --output "${OUTPUT_DIR}" \
  --tag "${TAG}" \
  --model "${MODEL}" \
  --input-size 3 224 224 \
  --crop-pct 0.875 \
  --batch-size "${BATCH_SIZE}" \
  --lr "${LR}" \
  --weight-decay "${WEIGHT_DECAY}" \
  --drop-path "${DROP_PATH}" \
  --amp \
  --model-ema \
  --channels-last
```

Notes:
- `--config` loads the YAML defaults first; repeated CLI flags override them.
- If your validation tree is named `val`, change `--val-split validation` to `--val-split val`.
- The command above is adapted from the repo's shell launcher; do not paste the original hard-coded paths.
- Add `--lmdb_dataset` only when you deliberately want the LMDB cache branch described in `data-formats.md`.

## Single-GPU debug recipe

Use this to validate model construction, loaders, and one short train/validation cycle before scaling up:

```bash
CUDA_VISIBLE_DEVICES=0 \
python <training-entrypoint> \
  --config mambavision_tiny_1k.yaml \
  --data_dir /path/to/imagenet \
  --train-split train \
  --val-split validation \
  --crop-pct 0.875 \
  --output /path/to/output \
  --tag debug_tiny \
  --model mamba_vision_T \
  --batch-size 8 \
  --workers 2 \
  --epochs 1 \
  --amp \
  --channels-last \
  --no_saver
```

Recommended debug adjustments:
- lower `--batch-size` before changing anything else for OOM
- use `--validation-batch-size` if eval is the memory bottleneck
- keep `--amp` on for memory savings, but turn it off temporarily if you are isolating numerical issues
- reduce `--workers` if the host is starved or dataloader startup is slow

## Important flag translations

| Flag | What it controls |
| --- | --- |
| `--config` / `-c` | Loads a YAML preset and seeds parser defaults before CLI overrides. |
| `--data_dir` | Dataset root, not a source checkout path. |
| `--train-split` / `--val-split` | Split names used by the timm dataset builder. |
| `--model` | Backbone factory name such as `mamba_vision_T`. |
| `--input-size` | Model and loader input shape, usually `3 224 224`. |
| `--crop-pct` | Validation crop percentage, often `0.875` for the shell recipe. |
| `--batch-size` | Per-GPU training batch size. |
| `--validation-batch-size` | Optional smaller eval batch size. |
| `--amp` | Mixed precision; prefers native AMP when available, then Apex. |
| `--native-amp` / `--apex-amp` | Force a specific AMP backend. |
| `--model-ema` | Tracks an EMA copy of the model; also needed for MESA. |
| `--resume` | Full checkpoint resume, including optimizer and scaler state. |
| `--initial-checkpoint` | Weight initialization only; does not resume optimizer state. |
| `--loadcheckpoint` | Partial shape-matched weight load. |
| `--output` | Output root for checkpoints and summaries. |
| `--tag` | Experiment tag appended to output and log names. |
| `--lr` | Base learning rate. |
| `--weight-decay` | Optimizer weight decay. |
| `--drop-path` | Stochastic depth / drop path rate. |
| `--channels-last` | Optional memory-format optimization. |
| `--mesa` | Memory efficient sharpness optimization coefficient. |
| `--data_len` | Samples-per-epoch estimate used by the LR scheduler. |
| `--workers` | Dataloader worker count. |

## Validation and outputs during training

- Validation runs after every epoch.
- When `--model-ema` is enabled, the script also evaluates the EMA weights.
- Logged metrics include train loss, validation loss, top-1, top-5, and learning rate.
- TensorBoard scalars go under the literal `<log_dir>_<tag>` path assembled by the script.
- The default output directory is relative to the launch directory unless `--output` is set.
- The script writes an `args.yaml` snapshot and checkpoint history under the experiment directory.

## Distributed launch notes

- The script switches to distributed mode when `WORLD_SIZE` is greater than 1.
- `torchrun` is the safest way to set `WORLD_SIZE` and `LOCAL_RANK` consistently.
- DDP uses NCCL and expects one GPU per process.
- For single-GPU debugging, omit `torchrun` entirely and let the script use `cuda:0`.
- On Slurm, prefer a launcher that keeps `CUDA_VISIBLE_DEVICES`, `MASTER_ADDR`, `MASTER_PORT`, `WORLD_SIZE`, and `LOCAL_RANK` aligned.

## Resume and fine-tune flow

- Use `--resume` when continuing the same run after interruption.
- Use `--initial-checkpoint` when you want to start from pretrained weights but do not want optimizer state restored.
- Use `--loadcheckpoint` when you want partial, shape-matched weight transfer into a changed model.
- If a checkpoint contains EMA weights, the script loads them with `use_ema=True` when resuming or validating.
- If you do not want optimizer state restored during resume, add `--no-resume-opt`.
