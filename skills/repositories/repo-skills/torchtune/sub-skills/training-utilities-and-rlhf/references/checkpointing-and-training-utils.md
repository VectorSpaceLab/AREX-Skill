# Checkpointing And Training Utilities

This reference covers torchtune training utility APIs that future agents commonly need while planning, debugging, or adapting post-training runs. It is intentionally about mechanics and failure analysis; use the recipe sibling skill for choosing full finetune, LoRA, DPO, PPO, KD, QAT, GRPO, or launch commands.

## Runtime Preflight

Before a distributed, QLoRA, RLHF, logging, or checkpoint-heavy run, execute the bundled side-effect-free checker from this sub-skill directory:

```bash
python scripts/check_training_runtime.py
```

It reports torch/CUDA state, `torchao` import health, torchtune training/RLHF import health, `torchtune.rlhf.loss` status, and optional async RL packages. It does not initialize process groups, touch GPUs beyond availability probes, load checkpoints, start Ray/vLLM, or run training.

## Checkpointer Components

Torchtune checkpointers are config components. They load source checkpoints into torchtune state dicts and save outputs back in compatible formats.

| Component | Use when | Practical notes |
| --- | --- | --- |
| `torchtune.training.FullModelHFCheckpointer` | Source checkpoint is Hugging Face `safetensors`/transformers-style | Default for many configs; expects HF metadata such as `config.json`; can shard final outputs and optionally enable DCP loading. |
| `torchtune.training.FullModelMetaCheckpointer` | Source checkpoint is original Meta `.pth` format | Expects Meta-style files such as `consolidated.00.pth` plus params metadata; saves back in Meta-compatible state-dict keys. |
| `torchtune.training.FullModelTorchTuneCheckpointer` | Source checkpoint already uses torchtune model state-dict keys | Mostly useful for tests, quantized generation paths, or already-converted torchtune artifacts; no HF/Meta key conversion. |
| `torchtune.training.DistributedCheckpointer` | Intermediate distributed checkpointing or async checkpoint saves | Uses PyTorch Distributed Checkpointing format; output differs from rank-0 consolidated final checkpoints. |

Common public constructors in the current code:

```python
FullModelHFCheckpointer(
    checkpoint_dir,
    checkpoint_files,
    model_type,
    output_dir=None,
    adapter_checkpoint="adapter_model.pt",
    recipe_checkpoint="recipe_state.pt",
    resume_from_checkpoint=False,
    safe_serialization=True,
    should_load_recipe_state=False,
    keep_last_n_checkpoints=None,
    enable_dcp=False,
)
FullModelMetaCheckpointer(
    checkpoint_dir,
    checkpoint_files,
    model_type,
    output_dir,
    adapter_checkpoint=None,
    recipe_checkpoint=None,
    resume_from_checkpoint=False,
    should_load_recipe_state=False,
)
FullModelTorchTuneCheckpointer(
    checkpoint_dir,
    checkpoint_files,
    model_type,
    output_dir,
    adapter_checkpoint=None,
    recipe_checkpoint=None,
    resume_from_checkpoint=False,
    should_load_recipe_state=False,
)
DistributedCheckpointer(checkpoint_dir, output_dir, process_group=None)
```

Save/load methods to recognize in code and stack traces:

```python
FullModelHFCheckpointer.load_checkpoint()
FullModelHFCheckpointer.save_checkpoint(state_dict, epoch, intermediate_checkpoint=False, adapter_only=False, step=None, max_shard_size="5GB", dir_prefix="epoch")
FullModelMetaCheckpointer.load_checkpoint()
FullModelMetaCheckpointer.save_checkpoint(state_dict, epoch, intermediate_checkpoint=False, adapter_only=False, **kwargs)
FullModelTorchTuneCheckpointer.load_checkpoint(weights_only=True)
FullModelTorchTuneCheckpointer.save_checkpoint(state_dict, epoch, intermediate_checkpoint=False, adapter_only=False, **kwargs)
DistributedCheckpointer.load_checkpoint(state_dict, adapter_only=False)
DistributedCheckpointer.save_checkpoint(state_dict, epoch, save_async=False, adapter_only=False, step=None, dir_prefix="epoch")
```

## Checkpoint Format Checklist

When a run fails around load/save, inspect these in order:

1. `checkpointer._component_`: HF, Meta, TorchTune, or Distributed must match the actual checkpoint layout.
2. `checkpoint_dir`: directory contains expected weight files and lightweight metadata files for the format.
3. `checkpoint_files`: names exactly match files to load; HF shards can be listed in any order, but missing shards fail.
4. `model_type`: conversion enum matches model family/version, for example Llama variants are not interchangeable.
5. `output_dir`: writable and not inside the input checkpoint directory unless the recipe explicitly supports that layout.
6. Adapter fields: `adapter_checkpoint`, `adapter_config`, `adapter_only`, and `recipe_checkpoint` are present when resuming LoRA/adapter training.
7. Resume flags: `resume_from_checkpoint` and `should_load_recipe_state` match whether the output has recipe state and optimizer/RNG state.

Final training checkpoints are saved synchronously in the source-compatible format. Intermediate checkpoints may include `recipe_state.pt` and recipe-state folders; async checkpointing uses DCP for intermediate state and is not the same layout as a final HF/Meta output folder.

## Resume And Async Checkpointing

Torchtune resume behavior combines model weights, optimizer state, dataloader progress, seed/RNG state, epoch/step counters, and optional adapter state. For normal resume, make sure `resume_from_checkpoint: True` points to a compatible torchtune output with the recipe state file expected by that recipe.

Async checkpointing is configured with `enable_async_checkpointing: True`. When enabled, intermediate checkpoints are written through `DistributedCheckpointer` so training can continue while save work runs. To resume from async checkpoints, keep both `resume_from_checkpoint: True` and `enable_async_checkpointing: True` so the distributed checkpointer can locate the latest intermediate checkpoint. The final checkpoint remains synchronous to ensure durable HF/Meta/torch-save artifacts.

Current checkpoint-client behavior to recognize:

```python
CheckpointClient(cfg, checkpointer=None)
CheckpointClient.save_checkpoint(model, optimizer, training_progress, epoch, adapter_config=None, adapter_only=False, single_device=False, full_tensors=True, dir_prefix="epoch")
```

`full_tensors=False` with async checkpointing chooses the async DCP path; `full_tensors=True` or disabled async checkpointing chooses the synchronous path. If an async save is still running, synchronous save waits before proceeding.

## Precision And Dtype

Core precision helpers:

```python
get_dtype(dtype=None, device=None)
set_default_dtype(dtype)
validate_expected_param_dtype(named_params, dtype, exclude_param_names=None)
```

`get_dtype` maps `None` to `torch.float32`, accepts `fp16`, `bf16`, `fp32`, and `fp64`, and raises if a requested dtype is unsupported. For `bf16`, it checks hardware/backend support except when the target device is CPU. Use it to validate assumptions before changing `dtype: bf16` in a config.

Practical dtype rules:

- Prefer `bf16` only when the hardware/backend supports it; otherwise use `fp32` or choose a smaller/adapter workflow.
- Treat full `fp16` training as recipe-specific, not a universal replacement for `bf16`.
- Use `validate_expected_param_dtype` after model construction when mixed dtype errors suggest some parameters loaded in the wrong dtype.
- Keep dtype decisions near recipe config fields; do not silently change checkpoint format to compensate for dtype errors.

## Seeding And Reproducibility

```python
set_seed(seed=None, debug_mode=None)
```

`set_seed` sets PyTorch, NumPy, and Python random seeds and incorporates rank-aware behavior through torchtune utilities. If `seed` is omitted, torchtune chooses one. `debug_mode` maps to PyTorch deterministic debug settings. Use the returned seed in logs or reports so a run can be repeated.

## Distributed Utilities

Important public helpers:

```python
get_distributed_backend(device_type, offload_ops_to_cpu=False)
init_distributed(**kwargs)
is_distributed()
get_world_size_and_rank()
set_torch_num_threads()
gather_cpu_state_dict(model, is_rank_zero, device=None, adapter_weights_only=False)
get_full_optimizer_state_dict(model, opt, is_rank_zero, device=None)
load_from_full_model_state_dict(model, full_sd, device, strict=False, cpu_offload=False, use_distributed_state_dict=False, release_sd=True)
load_from_full_optimizer_state_dict(model, opt, full_sd, device)
get_shard_conditions(name, module, names_to_match=None, *args, **kwargs)
shard_model(model, shard_conditions, cpu_offload, reshard_after_forward=True, dp_mesh=None)
get_train_context(enable_loss_parallel)
```

`get_distributed_backend` returns the backend string used for `torch.distributed.init_process_group`: `cuda` usually maps to `nccl`, CPU to `gloo`, and `offload_ops_to_cpu=True` produces a composite backend such as `cuda:nccl,cpu:gloo` for CPU offload or async DCP work.

Do not call `init_distributed` as a probe. It initializes process groups based on launch environment and may fail or hang without `RANK`, `WORLD_SIZE`, `MASTER_ADDR`, and related torchrun environment. Use the runtime checker and command inspection first; initialize only inside an approved recipe run or controlled smoke test.

## Memory Utilities

Core memory helpers:

```python
cleanup_before_training()
set_activation_checkpointing(model, auto_wrap_policy, **kwargs)
create_optim_in_bwd_wrapper(model, optim_dict)
register_optim_in_bwd_hooks(model, optim_dict)
get_memory_stats(device, reset_stats=True)
log_memory_stats(stats, message="Memory stats after model init:")
```

Memory guidance:

- `cleanup_before_training` runs garbage collection, empties accelerator cache where supported, and resets peak memory stats.
- `set_activation_checkpointing` accepts a set of module classes or a callable policy and wraps model modules through PyTorch activation checkpointing.
- Optimizer-in-backward utilities are intended for single-device workflows; do not use them as a drop-in for FSDP optimizer state handling.
- `get_memory_stats` supports CUDA/MPS-like accelerator devices and raises on CPU; do not use it as a CPU-only preflight.
- For QLoRA/QAT paths, also check optional quantization dependencies in the inference/quantization sibling skill.

## Activation Offloading And Compile

Relevant public exports include:

```python
get_act_offloading_ctx_manager(model, enable_activation_offloading, ...)
NoOpManager
OffloadActivations
compile_model(model, verbose=False)
compile_loss(loss, verbose=False)
```

Activation offloading trades accelerator memory for CPU memory and data movement. It interacts with distributed backend selection because CPU offload may require composite process-group backends. Treat compile/offload settings as performance features to enable after a functional baseline, not as first-line fixes for checkpoint or dataset errors.

## Schedulers

```python
get_cosine_schedule_with_warmup(optimizer, num_warmup_steps, num_training_steps, num_cycles=0.5, last_epoch=-1)
get_lr(optimizer)
```

`get_cosine_schedule_with_warmup` returns a PyTorch `LambdaLR`-style scheduler with linear warmup followed by cosine decay. Verify that `num_training_steps` reflects the actual optimizer-step count after gradient accumulation, epochs, `max_steps_per_epoch`, and distributed world size. `get_lr` works with a normal optimizer or `OptimizerInBackwardWrapper`.

## Metric Logging

Metric logger config components live under `torchtune.training.metric_logging`.

| Logger | Constructor | Notes |
| --- | --- | --- |
| `DiskLogger` | `DiskLogger(log_dir, output_fmt="txt", filename=None, **kwargs)` | Safe local default; creates `txt` or `jsonl` log file. |
| `StdoutLogger` | `StdoutLogger()` | Prints scalar logs to stdout. |
| `WandBLogger` | `WandBLogger(project="torchtune", entity=None, group=None, log_dir=None, **kwargs)` | Requires `wandb` install and login; may create networked runs. |
| `CometLogger` | `CometLogger(api_key=None, workspace=None, project=None, experiment_key=None, mode=None, online=None, experiment_name=None, tags=None, log_code=True, **kwargs)` | Requires `comet_ml` install and credentials; avoid embedding API keys. |
| `TensorBoardLogger` | `TensorBoardLogger(log_dir, organize_logs=True, **kwargs)` | Requires TensorBoard package support. |
| `MLFlowLogger` | `MLFlowLogger(experiment_name=None, tracking_uri=None, run_id=None, run_name=None)` | Requires MLflow package and tracking configuration. |

All loggers implement `log(name, data, step)`, `log_dict(payload, step)`, `log_config(config)`, and `close()`. Use `DiskLogger` or `StdoutLogger` as safe defaults unless the user explicitly asks for W&B/Comet/MLflow/TensorBoard and confirms credentials/network behavior.

## Profiling

```python
setup_torch_profiler(
    enabled=False,
    cpu=True,
    cuda=True,
    xpu=True,
    hpu=False,
    profile_memory=False,
    with_stack=False,
    record_shapes=True,
    with_flops=False,
    wait_steps=None,
    warmup_steps=None,
    active_steps=None,
    num_cycles=None,
    output_dir=None,
)
DummyProfiler
```

When `enabled=False`, `setup_torch_profiler` returns `DummyProfiler()` plus a config marking profiling disabled. When enabled, it chooses profiler activities and schedule defaults if unspecified. Profiling slows training; `profile_memory=True`, stack capture, and shape recording can generate large trace files. In recipes, profiler stepping is tied to optimizer-step or gradient-accumulation scope depending on where `profiler.step()` is called.

## Synthetic Hard Cases

- Check training runtime before a distributed QLoRA run on a machine with no `torchao`, no CUDA, and no distributed environment. The expected outcome is a clear report and recommendation to install/choose hardware, not a hung process group.
- Diagnose a resume failure where `enable_async_checkpointing=True` was used for intermediate saves but the user points `resume_from_checkpoint=True` at a final HF-format epoch folder without the expected DCP/recipe state.
