# Legacy Single-GPU Training Reference

The legacy path is the original single-process pretraining loop. It is useful for educational one-GPU runs, checkpoint/resume behavior, and memory-flag experiments. Prefer the modern workflow for new DDP/bf16 base checkpoints.

## When to Use Legacy

Use this path when the user asks for:

- the older single-GPU recipe;
- Python-constant config values rather than JSON config merging;
- `--resume latest` behavior;
- periodic checkpoint files with pruning;
- opt-in memory flags: AMP, activation checkpointing, gradient accumulation, and memory reporting.

Do not use this path for multi-GPU DDP. The legacy trainer is single-process only.

## Config Model

Legacy training reads a Python dictionary built from config constants. The key groups are:

| Key | Meaning | Pitfall |
|---|---|---|
| `vocab_size` | LM vocabulary size | Must match tokenizer and checkpoint. |
| `context_length` | Maximum position-embedding length in the model | Checkpoint shape changes if altered. |
| `n_embed`, `n_head`, `n_blocks` | Model dimensions | `n_embed` must divide by `n_head`; all must match on resume. |
| `train_path`, `dev_path` | HDF5 token files | Must contain flat `tokens` arrays. |
| `t_batch_size` | Microbatch size | Reduce first on OOM. |
| `t_context_length` | Training window length | Must be `<= context_length`; smaller than model max is allowed. |
| `t_train_steps` | Total optimizer steps | Long-run budget driver. |
| `t_eval_steps`, `t_eval_iters` | Evaluation cadence and samples | Large values make eval expensive. |
| `t_lr`, `t_lr_decayed`, `t_lr_decay_step` | Step LR schedule | Legacy uses a simple step decay. |
| `t_out_path` | Final checkpoint path | Final save avoids overwriting by adding a suffix if needed. |
| `t_checkpoint_steps`, `t_keep_last_checkpoints`, `t_checkpoint_dir` | Periodic checkpoint behavior | CLI flags can override. |
| `use_amp`, `amp_dtype`, `use_gradient_checkpointing`, `grad_accum_steps`, `report_memory_budget` | Memory features | All are off by default unless configured or passed on CLI. |
| `device` | `cuda` if available, else `cpu` | AMP is disabled automatically when CUDA is unavailable. |

## Build Commands Safely

From this sub-skill directory, generate a dry-run legacy command:

```bash
python scripts/build_pretrain_command.py --mode legacy
```

Periodic checkpointing and pruning:

```bash
python scripts/build_pretrain_command.py \
  --mode legacy \
  --extra='--checkpoint-every 1000' \
  --extra='--keep-last 3'
```

Resume the latest periodic checkpoint in the configured checkpoint directory:

```bash
python scripts/build_pretrain_command.py --mode legacy --extra=--resume
```

Resume an explicit checkpoint:

```bash
python scripts/build_pretrain_command.py --mode legacy --extra='--resume checkpoints/checkpoint_step_00001000.pt'
```

Memory-saving launch:

```bash
python scripts/build_pretrain_command.py \
  --mode legacy \
  --extra=--amp \
  --extra='--amp-dtype bf16' \
  --extra=--grad-checkpointing \
  --extra='--grad-accum 8' \
  --extra=--report-memory
```

The builder only prints commands. Review data paths, output path, device, and model size before executing any emitted command.

## Checkpoint Behavior

Periodic checkpoints use stable names:

```text
checkpoint_step_00000000.pt
checkpoint_step_00001000.pt
...
```

Important behavior:

- `--resume` with no value or `--resume latest` resolves the newest periodic checkpoint.
- Explicit `--resume path/to/file.pt` loads that file.
- Restored state includes model weights, optimizer state when present, and loss history.
- The next step is `last_completed_step + 1` for new checkpoints.
- If an older checkpoint has no optimizer state, LR is restored from the configured step schedule.
- Periodic saves are atomic: a failed save removes the temporary file instead of leaving a partial checkpoint.
- `--keep-last N` deletes older periodic checkpoints after a successful save; `0` keeps all.
- The final checkpoint save avoids overwriting an existing file by adding a numeric suffix.

## Memory Flags

| Flag | Effect | Notes |
|---|---|---|
| `--amp` | Enables CUDA autocast | Ignored on CPU. |
| `--amp-dtype bf16` | Uses bf16 autocast | No GradScaler needed. Best on modern data-center GPUs. |
| `--amp-dtype fp16` | Uses fp16 autocast | Uses a GradScaler to avoid underflow. |
| `--grad-checkpointing` | Recomputes block activations during backward | Saves activation memory; costs extra compute. |
| `--grad-accum N` | Accumulates `N` microbatches before optimizer step | Keeps effective batch while lowering per-step memory. |
| `--report-memory` | Prints rough parameter/optimizer VRAM budget and peak memory | CUDA only; activation memory is extra. |

Memory estimate floor for AdamW training is roughly 16 bytes per parameter for fp32 weights, gradients, and two moment buffers, plus activation memory. Activation memory is often dominated by attention at long context lengths.

## Legacy Versus Modern Decision

| Need | Pick |
|---|---|
| Multi-GPU DDP | Modern |
| JSON config and CLI field overrides | Modern |
| bf16 H100-style base pretraining with cosine LR | Modern |
| Resume latest periodic checkpoint by directory scan | Legacy |
| Test checkpoint pruning or atomic save helper behavior | Legacy |
| Single-GPU educational loop with Python constants | Legacy |
