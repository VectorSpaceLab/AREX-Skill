# Training CLI Reference

## Entry Points

Use the task-era training stack for new work:

```bash
python -m open_clip_train.main [training options]
```

Use the legacy compatibility shim only when an older image/text training script depends on the pre-task loop:

```bash
python -m open_clip_train.legacy_main [legacy-compatible options]
```

The task-era stack wraps model and loss in `TrainingTask` subclasses, uses dict batches, supports CLAP audio training, NaFlex image/audio paths, FSDP2, and multiple `torch.compile` strategies. The legacy stack preserves decode-first image/text loaders and older loop semantics; it is not the right target for new FSDP2, CLAP audio, NaFlex, length-bucketing, or task/step compile work.

## Baseline Command Skeletons

CSV or TSV image/text training:

```bash
python -m open_clip_train.main \
  --dataset-type csv \
  --train-data DATA/train.tsv \
  --csv-img-key filepath \
  --csv-caption-key title \
  --csv-separator $'\t' \
  --model ViT-B-32 \
  --batch-size 128 \
  --epochs 30 \
  --workers 8 \
  --lr 5e-4 \
  --wd 0.2 \
  --warmup 10000 \
  --precision amp_bf16
```

WebDataset image/text training:

```bash
python -m open_clip_train.main \
  --dataset-type webdataset \
  --train-data 'DATA/shards/{000000..000999}.tar' \
  --train-num-samples 1000000 \
  --model ViT-B-32 \
  --batch-size 256 \
  --epochs 32 \
  --workers 8
```

Synthetic smoke training:

```bash
python -m open_clip_train.main \
  --dataset-type synthetic \
  --train-num-samples 16 \
  --batch-size 4 \
  --epochs 1 \
  --workers 0 \
  --device cpu \
  --model RN50
```

Distributed launch shape:

```bash
torchrun --nproc_per_node 4 -m open_clip_train.main \
  --dataset-type webdataset \
  --train-data 'DATA/shards/{000000..000999}.tar' \
  --train-num-samples 1000000 \
  --batch-size 256 \
  --workers 4 \
  --model ViT-B-32 \
  --local-loss \
  --gather-with-grad
```

## Parser Defaults To Remember

`open_clip_train.params.parse_args([])` currently selects these important defaults:

- `--precision amp_bf16`.
- `--torchcompile-strategy task` when `--torchcompile` is enabled.
- `--dataset-type auto`.
- `--csv-separator` is tab, `--csv-img-key filepath`, and `--csv-caption-key title`.
- `--workers 4`, `--batch-size 64`, `--epochs 32`, `--warmup 10000`, `--wd 0.2`.
- `--opt adamw`, with model-name-dependent Adam defaults for non-`timm/` optimizers.
- `--audio-fill repeatpad`, `--audio-trunc rand_trunc`, `--audio-ext flac`.
- `--report-to ''`, so no wandb/trackio/tensorboard backend is active unless requested.

Use `scripts/training_arg_report.py` to confirm the defaults in the installed package before constructing a command.

## Dataset Type Routing

`--dataset-type auto` dispatches by `--train-data` extension:

- `.csv` or `.tsv` → CSV loader.
- `.tar` → WebDataset loader.
- Other extensions fail; pass `--dataset-type` explicitly.

Explicit types:

- `csv`: pandas-backed image path + caption table.
- `webdataset`: image/text tar shards.
- `synthetic`: generated RGB images and dummy captions.
- `webdataset-audio`: CLAP/NaFlexClap/GenLAP audio-caption tar shards.
- `synthetic-audio`: fixed CLAP audio smoke data; not for NaFlex audio models.

Training starts when `--train-data` is set or the dataset type is `synthetic`/`synthetic-audio`. Eval-only commands can pass `--val-data`, `--imagenet-val`, `--imagenet-v2`, or audio zero-shot flags without `--train-data`.

## Model And Loss Selection

Task-era `main` calls `open_clip.create_task(args, model, dist_model, naflex_data_config)`. Common selectors:

- Plain CLIP model → `CLIPTask` with `ClipLoss`.
- `--siglip` → `SigLIPTask` with `SigLipLoss`; `--loss-dist-impl gather` can select the distributed implementation.
- Model name containing `coca` → `CoCaTask` with `CoCaLoss`; use `--coca-caption-loss-weight` and `--coca-contrastive-loss-weight`.
- `--distill-model` plus `--distill-pretrained` → `DistillCLIPTask` with `DistillClipLoss`; requires `--accum-freq 1` and does not support CoCa.
- CLAP model instance → `CLAPTask`; CLAP distillation is rejected.
- Model name containing `genlip` → `GenLipTask`; enables NaFlex and rejects `--accum-freq > 1`.
- Model name containing `genlap` → `GenLapTask`; enables NaFlex and rejects `--accum-freq > 1`.

Route GenLIP/GenLAP and detailed NaFlex token-budget questions to `../naflex-generative/SKILL.md`; route CLAP audio model/data details to `../audio-clap/SKILL.md`.

## Optimizer Options

The task-era stack builds `OptimizerCfg` and calls `create_optimizer(task.trainable_module, cfg, device, tensorize=False)`.

Key flags:

- `--opt adamw` or `--opt nadamw` for builtin torch optimizers.
- `--opt timm/<name>` for timm optimizers.
- `--lr`, `--beta1`, `--beta2`, `--eps`, `--momentum`, `--wd`.
- `--opt-kwargs key=value ...` for optimizer-specific kwargs.
- `--wd-exclude PATTERN ...` to add parameter-name glob exclusions from weight decay.
- `--text-layer-decay`, `--image-layer-decay`, and `--audio-layer-decay` for layer-wise LR decay in `(0, 1]`; unset or `1.0` disables the tower.
- `--opt-fallback-list PATTERN ...` only applies to Muon-family `timm/` optimizers; using it with builtin torch optimizers raises.

Default no-weight-decay excludes all 1-D parameters plus model-declared no-weight-decay names/patterns, then applies user globs from `--wd-exclude`.

## Scheduler Options

Training creates a scheduler unless `--skip-scheduler` is set:

- `--lr-scheduler cosine` uses cosine decay after warmup.
- `--lr-scheduler const` warms up then holds LR constant.
- `--lr-scheduler const-cooldown` requires `--epochs-cooldown` and uses `--lr-cooldown-power` plus `--lr-cooldown-end`.
- Step count is `(data["train"].dataloader.num_batches // --accum-freq) * --epochs`.

Layer-wise LR decay scales per-parameter-group learning rates while `get_learning_rate()` reports the largest base LR.

## Precision Options

Accepted `--precision` values are `amp`, `amp_bf16`, `amp_bfloat16`, `bf16`, `fp16`, `pure_bf16`, `pure_fp16`, and `fp32`.

- Default `amp_bf16` uses bfloat16 autocast on CUDA-like devices and does not create a GradScaler.
- `amp` uses fp16 autocast and creates a GradScaler.
- `bf16`/`pure_bf16` and `fp16`/`pure_fp16` affect input dtype via `get_input_dtype`.
- Under FSDP, autocast is suppressed and FSDP mixed-precision policy derives param dtype from precision: fp16 for `amp`/`fp16`/`pure_fp16`, bfloat16 for `amp_bf16`/`amp_bfloat16`/`bf16`/`pure_bf16`, and no param cast for `fp32`.
- Raw `fp16` logs a warning recommending AMP mixed precision for training.

## Compile Options

Enable compile with `--torchcompile`; choose a strategy with `--torchcompile-strategy`:

- `task` compiles task train/eval forward callables. This is the default and keeps the `TrainingTask` object available for checkpointing, batch preparation, eval, and helpers.
- `model` compiles the underlying trainable module before distributed wrapping. With FSDP, root compile is skipped and per-block compile can be applied inside FSDP preparation.
- `step` compiles forward, loss, backward, optional grad clipping, optimizer step, and logit-scale clamp. It requires `--accum-freq 1` and a precision mode that does not use a GradScaler, such as default `amp_bf16` or `fp32`.

Pass `--torchcompile-backend` and `--torchcompile-mode` through to `torch.compile`. For task/step compile, mutable loss label caches are disabled to avoid compiled-region state mutation.

## Logging And Reports

`--report-to` is a comma-separated selector:

- `tensorboard` creates a tensorboard writer.
- `wandb` initializes wandb if installed.
- `trackio` initializes the local-first wandb-compatible backend if installed.
- `all` includes wandb and tensorboard, but not trackio.

`wandb` and `trackio` are mutually exclusive. `--log-every-n-steps`, `--log-metric-every-n-steps`, and `--train-loss-ema-samples` tune logging density and smoothing. `--train-loss-ema-samples 0` disables the EMA console smoothing; negative values are rejected.

## Legacy Entry Point Decision

Choose `legacy_main` only when adapting an old image/text script that assumes the frozen pre-task loop. Legacy does not support task-era feature sets such as FSDP2, task/step compile, CLAP audio training, NaFlex, or length bucketing. It also rejects audio dataset types in legacy training.
