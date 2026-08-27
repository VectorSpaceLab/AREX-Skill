# Checkpoints, Distributed, Compile, Precision, And Schedules

## Distributed Initialization

Task-era `main` initializes distributed state before model/task wrapping decisions. Single-process training is allowed; distributed launches typically use `torchrun` or a cluster launcher that sets rank/world-size environment variables.

Important flags:

```bash
--device cuda
--dist-url env://
--dist-backend nccl
--ddp-static-graph
--use-bn-sync
--local-loss
--gather-with-grad
```

`--local-loss` plus `--gather-with-grad` reduces distributed contrastive-loss memory pressure compared with a naive full global logit matrix while preserving numerical intent for CLIP-style losses.

## FSDP2

Enable FSDP2 with:

```bash
--fsdp
--fsdp-checkpoint full
```

Optional flags:

```bash
--fsdp-no-reshard-after-forward
--fsdp-offload-cpu
--fsdp-checkpoint sharded
```

Decision rules:

- `--fsdp` requires distributed mode. In single-process training, it is ignored with a warning.
- `--fsdp-checkpoint sharded` requires `--fsdp`; otherwise the parser path falls back to full checkpoints with a warning.
- FSDP2 reshapes 0-D scalar parameters such as `logit_scale` and `logit_bias` to `[1]` before sharding, then normalizes them back for checkpoint compatibility.
- FSDP2 registers `encode_text` and `encode_image` as FSDP forward methods when present so eval and zero-shot helper calls trigger gather/reshard hooks correctly.
- EMA must be set up before FSDP. FSDP2 sharded parameters are not compatible with setting up `ModelEmaV3` afterward.

## FSDP Mixed Precision

When FSDP is active, autocast is suppressed and FSDP mixed-precision policy owns parameter dtype:

- `amp`, `fp16`, `pure_fp16` → fp16 parameter dtype.
- `amp_bf16`, `amp_bfloat16`, `bf16`, `pure_bf16` → bfloat16 parameter dtype.
- `fp32` → no parameter dtype cast, fp32 reductions.

Reduce dtype is fp32. This is different from non-FSDP AMP, where `open_clip_train.precision.get_autocast()` provides autocast contexts.

## `torch.compile` Strategies

Enable compile:

```bash
--torchcompile --torchcompile-strategy task
```

Strategies:

- `task`: compile task train/eval forward callables. This is the common path and default strategy.
- `model`: compile `task.trainable_module` before distributed wrapping. With FSDP, root compile is skipped; FSDP preparation can compile discovered blocks before activation checkpointing and sharding.
- `step`: compile a complete single-batch train step, including forward, loss, backward, optional gradient clipping, optimizer step, and logit-scale clamp.

`step` constraints:

- Requires `--accum-freq 1`.
- Requires a precision mode without GradScaler; default `amp_bf16` or `fp32` are typical.
- If `--precision amp` creates a GradScaler, step compile raises.
- Tensor learning rates are used for step compile to avoid optimizer-step recompiles.

Compile options:

```bash
--torchcompile-backend inductor
--torchcompile-mode reduce-overhead
```

When DDP plus compile is used with grad checkpointing or GenLIP dynamic shapes, the code disables the DDP dynamo optimizer to avoid graph splitting problems.

## Gradient Checkpointing

Use:

```bash
--grad-checkpointing
```

Ordering matters:

- Non-FSDP uses inline activation checkpointing directly on the model.
- FSDP plus compile defers composable activation checkpointing into `prepare_fsdp()` so ordering is compile → activation checkpointing → FSDP.
- This avoids hooks landing on the wrong side of `torch.compile` wrappers.

Gradient accumulation with `--accum-freq > 1` uses feature caching for contrastive tasks. Generative `GenLipTask` and `GenLapTask` reject accumulation greater than one.

## Checkpoint Types

Full checkpoint:

- Saved as one `.pt` file, usually `epoch_K.pt`.
- Contains `epoch`, `name`, `state_dict`, optimizer state, optional `state_dict_ema`, optional scaler state, and optional `global_step` / `samples_seen` counters.
- Under FSDP, gathering a full checkpoint is collective and all ranks must participate, though only the master writes.

Sharded checkpoint:

- Enabled by `--fsdp --fsdp-checkpoint sharded`.
- Saved as a directory, usually `epoch_K/`, using PyTorch Distributed Checkpoint (DCP).
- All ranks write shard files.
- Master writes `_metadata_extra.pt` with epoch, scaler, and counter metadata.
- Useful for lower memory and faster checkpointing at scale.

## Resume Behavior

Explicit resume:

```bash
--resume PATH_OR_URI
```

If `PATH_OR_URI` is a directory, task-era `main` treats it as a sharded DCP checkpoint. Otherwise it loads a full `.pt` checkpoint through the task checkpoint utilities. Remote files are loaded through the repository's file utilities when supported by fsspec.

Latest resume:

```bash
--resume latest
```

The trainer looks under the run's checkpoint directory and selects the newest checkpoint. It recognizes full `.pt` files and DCP checkpoint directories. Under distributed training, rank 0 determines the resume path and checkpoint type, then broadcasts both so all ranks agree.

Legacy checkpoints without explicit `global_step` or `samples_seen` are estimated from epoch, dataloader size, and `--accum-freq` so logging counters remain usable.

## Save Options

Main checkpoint flags:

```bash
--save-frequency 1
--save-most-recent
--delete-previous-checkpoint
```

Behavior:

- `--save-frequency N` writes epoch checkpoints every `N` completed epochs and at the final epoch.
- `--save-most-recent` maintains `epoch_latest.pt` for full checkpoints or `epoch_latest/` for sharded FSDP checkpoints.
- `--delete-previous-checkpoint` removes older checkpoints after saving newer ones.
- Sharded latest uses a temporary directory and rename sequence so at least one valid latest directory should survive interrupted swaps.

## Remote Sync

Remote sync options:

```bash
--logs LOCAL_LOG_ROOT
--remote-sync REMOTE_ROOT
--remote-sync-frequency 300
--remote-sync-protocol s3
```

`remote-sync` first tests syncing the run directory to the remote path; if it fails, training exits. When it succeeds, a background sync process runs at the requested frequency and a final sync runs at the end.

Warnings:

- `--resume latest` with `--remote-sync` only supports `--remote-sync-protocol s3`.
- `--resume latest` with both `--remote-sync` and `--save-most-recent` is rejected.
- Background sync can lag behind the latest local checkpoint.
- Remote sync excludes changing `epoch_latest.pt` in helper utilities to avoid copying partial latest files.

## Precision And GradScaler

Non-FSDP precision behavior:

- `amp` uses fp16 autocast and creates a GradScaler.
- `amp_bf16` / `amp_bfloat16` uses bfloat16 autocast and no GradScaler.
- `bf16` / `pure_bf16` and `fp16` / `pure_fp16` set input tensor dtype through `get_input_dtype`.
- `fp32` suppresses autocast and leaves input dtype unchanged.

`fp16` emits a warning recommending AMP mixed precision for training. If CUDA is available, task-era `main` enables TF32 matmul and cuDNN benchmark defaults.

## Optimizer And Scheduler Order

When training data is present, task-era `main` constructs:

1. Task and distributed/FSDP wrappers.
2. Optimizer with `create_optimizer(task.trainable_module, OptimizerCfg(...), device=device, tensorize=step_compile)`.
3. GradScaler when required.
4. Checkpoint resume, loading task, optimizer, scaler, and counters.
5. Data loaders.
6. Scheduler if train data exists and `--skip-scheduler` is not set.

Scheduler total steps use dataloader `num_batches`, divided by `--accum-freq`, multiplied by `--epochs`. If using `const-cooldown`, `--epochs-cooldown` must be set.

## Checkpoint Compatibility Notes

- Training checkpoints saved on the task-era stack include a `state_dict` key and preserve optimizer, EMA, scaler, and counter metadata when present.
- Loading reconciles 0-D and `[1]` scalar parameter shapes when moving checkpoints between DDP and FSDP contexts.
- If a checkpoint has no `epoch` key, it is treated as bare model weights and loaded into the task state dict with start epoch `0`.
- Recent PyTorch defaults require safe loading semantics; custom optimizer state containing non-allowlisted Python objects may need explicit `torch.serialization.add_safe_globals([...])` before loading.

## Safe Decision Matrix

- Single GPU or CPU smoke: no distributed flags, no FSDP, consider `--dataset-type synthetic` and `--workers 0`.
- Multi-GPU baseline: use `torchrun`, DDP defaults, `--local-loss --gather-with-grad` for contrastive memory pressure.
- Large model/distributed memory pressure: consider `--fsdp`, `--precision amp_bf16`, and `--fsdp-checkpoint sharded`.
- Compile quick win: `--torchcompile --torchcompile-strategy task`.
- Aggressive compile: `--torchcompile-strategy step` only with `--accum-freq 1` and no GradScaler.
- Remote preemption workflow: use explicit run names, cautious checkpoint frequency, and avoid unsupported `remote-sync` + latest combinations.
