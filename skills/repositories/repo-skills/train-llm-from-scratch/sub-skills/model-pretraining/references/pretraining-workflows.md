# Modern Base-Pretraining Workflows

Use the modern workflow for new base checkpoints. It trains the same custom Transformer as the legacy path, but adds JSON config resolution, DistributedDataParallel launch support, bf16 autocast, gradient accumulation, warmup plus cosine learning-rate decay, checkpoint metadata, and JSONL metrics.

## When to Use This Path

Use modern pretraining when the user wants any of the following:

- a base checkpoint for later alignment stages;
- multi-GPU DDP launch with `torchrun`;
- bf16 CUDA training;
- JSON config files plus command-line overrides;
- checkpoint metadata that stores stage, config, step, optimizer state, and metrics;
- a tiny smoke config/parser check before a long run.

Use the legacy reference only for the older single-GPU script, its Python-constant config, or its periodic checkpoint pruning helpers.

## Data Contract

The pretraining data is a flat HDF5 token stream:

| Requirement | Detail |
|---|---|
| File format | HDF5 readable by `h5py`. |
| Dataset key | `tokens`. |
| Token shape | One-dimensional integer array. |
| Batch construction | Random windows of length `context_length + 1`; `xb = window[:-1]`, `yb = window[1:]`. |
| Minimum size | At least `context_length + 1` tokens; practically, many more than `batch_size * context_length`. |

If token files are missing or the schema is uncertain, route to the data-preparation sub-skill before building a training command.

## Config Resolution

Modern stages resolve config in this order, lowest to highest precedence:

1. dataclass defaults in the stage config class;
2. shared `base.json` in the config directory;
3. stage JSON, usually `pretrain.json`;
4. CLI `--field value` overrides.

When the chosen stage JSON lives under a `smoke/` directory with its own `base.json`, that sibling base file is used. This is why smoke configs can shrink model dimensions without changing full-run configs.

Important pretraining fields:

| Field | Meaning | Notes |
|---|---|---|
| `vocab_size` | LM vocabulary size and output width | Must match tokenizer and checkpoint. |
| `context_length` | Model max sequence length and training window length | Memory grows roughly with `context_length^2` in attention. |
| `n_embed`, `n_head`, `n_blocks` | Model width, attention heads, block count | `n_embed` must divide evenly by `n_head`. |
| `device` | `cuda` or `cpu` | Full training expects CUDA; CPU is for smoke and parser checks. |
| `amp_dtype` | `bf16` or `null` | bf16 autocast activates only on CUDA. |
| `batch_size` | Per-rank microbatch size | Effective batch also includes accumulation and world size. |
| `grad_accum` | Microsteps per optimizer step | Increase to restore effective batch after lowering `batch_size`. |
| `train_steps` | Optimizer steps | Budget driver. |
| `eval_steps`, `eval_iters` | Loss evaluation cadence and sample count | Lower for quick checks. |
| `warmup_steps`, `lr`, `min_lr` | Linear warmup and cosine decay schedule | LR is recomputed each step. |
| `weight_decay` | AdamW decay for matrix parameters | Biases/norms/1-D params are no-decay. |
| `grad_clip` | Global norm clipping threshold | Stabilizes long runs. |
| `out_ckpt` | Checkpoint file to write | Use a user-controlled path. |
| `save_every` | Periodic checkpoint cadence | Rank 0 writes checkpoints. |
| `log_dir`, `use_wandb` | JSONL and optional external logging | JSONL logging is always local when the logger is enabled. |

Replace machine-specific data, log, and checkpoint defaults with user-controlled paths before a real run.

## Build Commands Safely

From this sub-skill directory, the bundled command builder prints a command and never runs it.

Parser/config smoke, no training if the printed command is only reviewed or run with `--print-config`:

```bash
python scripts/build_pretrain_command.py --mode modern --smoke --extra=--print-config
```

Single-process modern pretraining command:

```bash
python scripts/build_pretrain_command.py \
  --mode modern \
  --config configs/pretrain.json \
  --extra='--train_path data/pile_train.h5' \
  --extra='--dev_path data/pile_dev.h5' \
  --extra='--out_ckpt checkpoints/base_pretrained.pt'
```

Two-process DDP command:

```bash
python scripts/build_pretrain_command.py \
  --mode modern \
  --nproc 2 \
  --extra='--batch_size 8' \
  --extra='--grad_accum 12'
```

The emitted command uses repo-relative entrypoints and includes `PYTHONPATH=.` so it can run from a normal source checkout or equivalent installed environment.

## Training Loop Semantics

For each optimizer step:

1. Resolve LR using linear warmup followed by cosine decay.
2. Zero gradients with `set_to_none=True`.
3. For each gradient-accumulation microstep:
   - read one HDF5 batch;
   - use DDP `no_sync()` for all but the last microstep in multi-process mode;
   - run the model under bf16 autocast when `amp_dtype == "bf16"` and CUDA is active;
   - divide loss by `grad_accum` before backward.
4. Clip gradients by global norm.
5. Step AdamW.
6. Rank 0 logs loss, LR, throughput, eval losses, and checkpoints.

Effective batch size in sequences is:

```text
batch_size * grad_accum * world_size
```

Tokens per optimizer step are:

```text
batch_size * context_length * grad_accum * world_size
```

## Checkpoints and Resume

Modern pretraining checkpoints contain:

- `model_state_dict` from the unwrapped model;
- `optimizer_state_dict`;
- `stage: "pretrain"`;
- serialized config under `cfg`;
- `step`;
- metrics such as current train loss;
- PyTorch/CUDA version metadata.

Resume uses an explicit checkpoint path:

```bash
python scripts/build_pretrain_command.py \
  --mode modern \
  --extra='--resume checkpoints/base_pretrained.pt'
```

When loading later stages or evaluation, prefer the checkpoint's stored config. If a user overrides dimensions at load time, state-dict shape mismatches are expected.

## Smoke Strategy

A safe smoke sequence is:

1. Run `scripts/smoke_transformer.py` to prove imports, constructor dims, forward pass, and CE loss.
2. Build a modern smoke command with `--smoke --extra=--print-config` to inspect resolved config without reading data.
3. Only if a tiny HDF5 `tokens` file exists, remove `--print-config` and run the emitted smoke command for a bounded number of steps.
4. For full training, switch to the full config and explicitly override data and checkpoint paths.

## Health Signals

| Signal | Healthy | Problem |
|---|---|---|
| initial loss | near `ln(vocab_size)` for random weights | NaN or far below random before learning, indicating data/target leakage or bad targets. |
| train loss | trends downward | flat near random baseline after many steps. |
| dev loss | trends downward then stabilizes | rises while train loss falls, indicating overfit or bad split. |
| tokens/sec | stable after warmup | sudden collapse suggests data stalls, compilation overhead, or communication issues. |
| peak memory | stable for fixed shape | grows until OOM, suggesting fragmentation or unexpected shape changes. |
