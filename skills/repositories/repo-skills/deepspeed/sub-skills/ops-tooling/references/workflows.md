# Workflows

Use these workflows to plan DeepSpeed operational tasks while avoiding accidental builds, training runs, remote execution, or storage writes.

## Install and Op Compatibility Triage

1. Run `python scripts/check_deepspeed_tools.py` from this skill to verify tool discovery and safe imports.
2. Run `ds_report` or `python -m deepspeed.env_report` to capture op installed/compatible status.
3. Separate issues into:
   - Python package import problems.
   - Torch/accelerator version mismatches.
   - CUDA toolkit or `nvcc` discovery problems.
   - Missing JIT build prerequisites such as `ninja`.
   - Missing optional system libraries such as `libaio-dev` for `async_io`.
4. Decide whether to keep JIT mode or reinstall/prebuild selected ops with `DS_BUILD_*` flags.
5. If the user uses multiple Python environments, recommend a per-environment `TORCH_EXTENSIONS_DIR` to avoid stale extension cache collisions.

## JIT Versus Prebuilt Ops

Prefer JIT when:

- The user wants quick installation.
- The exact GPU architecture is only known at runtime.
- The workload uses only a small subset of ops.

Prefer prebuilding when:

- Startup latency or first-use build failures are unacceptable.
- Deploying a wheel to machines with matching Python, Torch, CUDA/HIP, and GPU architecture.
- `ds_report` shows the target op is compatible and the user wants repeatable packaging.

Before recommending prebuilds, check that PyTorch is installed first, `nvcc` matches Torch CUDA sufficiently, and the desired `DS_BUILD_*` flag exists. For CUDA cards, include `TORCH_CUDA_ARCH_LIST` when the user knows target compute capabilities.

## Autotuning Workflow

Autotuning belongs here for operational launch planning, while training semantics belong in `training-config`. Treat it as a real workload launcher, not a dry run.

### Dry-Run and Offline Validation First

Before showing or executing any `deepspeed --autotuning` launch command:

1. Confirm the base training command already works without autotuning.
2. Keep `autotuning.enabled` false, or review the candidate config without launching, until the user approves a real tuning run.
3. Keep `wandb.enabled` and `comet.enabled` false unless the user explicitly confirms credentials, network behavior, and project/workspace names.
4. Prefer `csv_monitor` or `tensorboard` with a user-approved local output directory for dry-run validation.
5. Run only read-only checks first: `deepspeed --help`, `python scripts/check_deepspeed_tools.py`, config parsing, and training-config validation.
6. Ask for GPU budget, time limit, output directories, log retention, and whether `tune` or `run` is approved.

Candidate autotuning config after approval:

```json
{
  "autotuning": {
    "enabled": true,
    "fast": true,
    "results_dir": "autotuning_results",
    "exps_dir": "autotuning_exps"
  }
}
```

If the training script exposes batch-size arguments, add `arg_mappings` for fields such as `train_micro_batch_size_per_gpu` and `gradient_accumulation_steps`.

Only after explicit approval, use `deepspeed --autotuning tune ...` to find a config only, or `deepspeed --autotuning run ...` to tune and then run the selected config. Autotuning launches real experiments, consumes GPUs, writes result directories, and can run many trials.

After a run, inspect `ds_config_optimal.json`, `cmd_optimal.txt`, and tuning summaries under the configured results directory.

Key tuning controls include `fast`, `tuner_type`, `tuner_num_trials`, `max_train_batch_size`, `min_train_batch_size`, `max_train_micro_batch_size_per_gpu`, `num_tuning_micro_batch_sizes`, `metric`, `metric_path`, `mp_size`, and experiment/resource sizing fields.

## FLOPS Profiler Workflow

Use `get_model_profile` for standalone profiling or config-driven profiler fields for DeepSpeed runtime profiling.

Standalone API facts:

```python
from deepspeed.profiling.flops_profiler import get_model_profile, FlopsProfiler
```

`get_model_profile` accepts a model plus `input_shape`, `args`, `kwargs`, `print_profile`, `detailed`, `module_depth`, `top_modules`, `warm_up`, `as_string`, `output_file`, `ignore_modules`, and `mode`.

`FlopsProfiler(model, ds_engine=None, recompute_fwd_factor=0.0)` supports explicit start/stop/reset-style workflows around a PyTorch module.

Operational guidance:

- Use a small representative input first.
- Keep `output_file` local to a user-provided run directory.
- Treat latency/FLOPS as environment-specific and compare only under the same accelerator, precision, and batch-size conditions.
- For distributed runs, remember model parallel size affects per-GPU profile interpretation more than data-parallel size.

## Monitor Workflow

DeepSpeed monitor configuration lives in the DeepSpeed config and can enable multiple backends at once:

```json
{
  "tensorboard": {"enabled": true, "output_path": "output/ds_logs/", "job_name": "train"},
  "csv_monitor": {"enabled": true, "output_path": "output/ds_logs/", "job_name": "train"},
  "wandb": {"enabled": false, "project": "my_project"},
  "comet": {"enabled": false, "project": "my_project"}
}
```

API entry points include `MonitorMaster`, `TensorBoardMonitor`, `WandbMonitor`, and `csvMonitor`. Prefer `MonitorMaster(ds_config.monitor_config)` when using a DeepSpeed config object.

Safety guidance:

- Prefer `tensorboard` or `csv_monitor` when credentials/network access are not confirmed.
- Keep WandB and Comet disabled during dry runs unless the user explicitly requests and configures a documented offline mode.
- Do not put API keys, tokens, workspace secrets, or private project names in examples.
- Do not invent WandB or Comet credentials.
- Ask where logs should be written before enabling persistent outputs.
- Custom events are 3-tuples such as `("metric/name", value, engine.global_samples)`.

## DeepNVMe, AIO, and GDS Workflow

DeepNVMe APIs use op builders and can write directly to storage. Do not run writes until the user provides a scratch path and approves the operation.

Readiness checks:

1. Run `ds_report` and inspect `async_io` and `gds` rows.
2. For AIO, confirm `async_io` is compatible and system `libaio` headers/libraries are installed if needed.
3. For GDS, confirm both `async_io` and `gds` compatibility plus NVIDIA GDS installation.
4. Inspect help only: `ds_io --help` and `ds_nvme_tune --help`.

API entry points:

```python
from deepspeed.ops.op_builder import AsyncIOBuilder, GDSBuilder
```

- `AsyncIOBuilder().load().aio_handle(...)` works for AIO paths when the op can load.
- `GDSBuilder().load().gds_handle(...)` requires GDS support and CUDA tensors.
- Key handle parameters include `block_size`, `queue_depth`, `single_submit`, `overlap_events`, and `intra_op_parallelism`.

Non-blocking I/O safety:

- Always call `wait()` before mutating source tensors after async writes.
- Always call `wait()` before reading destination tensors after async reads.
- Pin host/device tensors when measuring realistic performance.

## Compression Workflow

Compression is an operational API area here; model/training strategy belongs with the training skill.

Core imports:

```python
from deepspeed.compression.compress import init_compression, redundancy_clean
```

Use `init_compression(model, deepspeed_config, teacher_model=None, mpu=None)` after model construction and before training/evaluation setup that depends on compressed modules. Use `redundancy_clean(model, deepspeed_config, mpu=None)` before saving cleaned compressed weights when the selected compression method requires it.

Configuration families include layer reduction, weight quantization, activation quantization, sparse pruning, row pruning, head pruning, and channel pruning. Confirm that the user accepts accuracy/performance trade-offs and has a validation plan before applying compression.
