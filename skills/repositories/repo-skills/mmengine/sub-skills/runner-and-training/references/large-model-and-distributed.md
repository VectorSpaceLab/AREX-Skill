# Large-Model and Distributed Training

Use this reference for launcher selection, distributed Runner behavior, `FlexibleRunner`, and optional large-model strategies. All commands are templates for the user's own training entry point; they do not depend on original repository examples.

## Launcher Decision

| Scenario | Runner config | Launch command shape |
| --- | --- | --- |
| CPU or single process | `launcher='none'` | `python train.py` |
| Multi-GPU single node | `launcher='pytorch'` | `torchrun --nproc-per-node N train.py --launcher pytorch` |
| Multi-node PyTorch | `launcher='pytorch'` | `torchrun --nnodes M --node_rank R --master_addr HOST --master_port PORT --nproc-per-node N train.py --launcher pytorch` |
| Slurm allocation | `launcher='slurm'` | `srun ... python train.py --launcher slurm` |

Use `gloo` for CPU-oriented distributed smoke tests and `nccl` for CUDA GPU training. `nccl` requires compatible GPUs, drivers, and PyTorch CUDA support.

## Runner Distributed Config

A standard Runner uses `launcher` and `env_cfg`:

```python
runner = Runner(
    model=model,
    work_dir='work_dirs/experiment',
    train_dataloader=train_dataloader,
    train_cfg=dict(by_epoch=True, max_epochs=12),
    optim_wrapper=dict(optimizer=dict(type='AdamW', lr=1e-4)),
    launcher='pytorch',
    env_cfg=dict(dist_cfg=dict(backend='nccl')),
)
```

When switching a single-process config to distributed training, also check dataloader sampler configs and keep `DistSamplerSeedHook` enabled so distributed shuffling changes each epoch.

## Model Wrapper Config

Runner wraps models for distributed execution. Use `model_wrapper_cfg` when a task needs wrapper options such as `find_unused_parameters`.

```python
cfg = dict(
    model_wrapper_cfg=dict(type='MMDistributedDataParallel', find_unused_parameters=True)
)
runner = Runner(..., cfg=cfg)
```

Use this only when model graph behavior requires it. `find_unused_parameters=True` can hide model issues and may slow distributed training.

## FlexibleRunner

`FlexibleRunner` accepts most Runner inputs and adds strategy-aware preparation plus optional compile support. Verified constructor-only differences include `strategy`, `compile`, `resume` as `str | bool`, optional `launcher`, and default `work_dir='work_dirs'`.

```python
runner = FlexibleRunner(
    model=model,
    work_dir='work_dirs/flexible_experiment',
    strategy=None,
    train_dataloader=train_dataloader,
    optim_wrapper=dict(type='AmpOptimWrapper', optimizer=dict(type='AdamW', lr=1e-4)),
    param_scheduler=dict(type='LinearLR'),
    train_cfg=dict(by_epoch=True, max_epochs=12, val_interval=1),
    val_dataloader=val_dataloader,
    val_cfg=dict(),
    val_evaluator=metric,
    compile=False,
)
```

Use `FlexibleRunner` when a task explicitly asks for strategy plugins, DeepSpeed, FSDP, ColossalAI, or compile in the FlexibleRunner API. Otherwise, prefer `Runner` for stable general workflows.

## DeepSpeed Strategy

Dependency and hardware gated: requires the `deepspeed` package, distributed launch, and a compatible GPU environment.

```python
strategy = dict(
    type='DeepSpeedStrategy',
    fp16=dict(enabled=True, loss_scale=0),
    zero_optimization=dict(
        stage=3,
        allgather_partitions=True,
        reduce_scatter=True,
        overlap_comm=True,
        contiguous_gradients=True,
        cpu_offload=False,
    ),
)
optim_wrapper = dict(
    type='DeepSpeedOptimWrapper',
    optimizer=dict(type='AdamW', lr=1e-3),
)
```

Use DeepSpeed when optimizer, gradient, or parameter sharding is required. If `DeepSpeedStrategy` or `DeepSpeedOptimWrapper` cannot be imported, treat it as an optional dependency issue, not a core MMEngine import failure.

## FSDP Strategy

Dependency and hardware gated: MMEngine's FSDP strategy expects a distributed environment and modern PyTorch FSDP support.

```python
strategy = dict(
    type='FSDPStrategy',
    model_wrapper=dict(auto_wrap_policy=auto_wrap_policy),
)
optim_wrapper = dict(
    type='AmpOptimWrapper',
    optimizer=dict(type='AdamW', lr=1e-3),
)
```

Use FSDP when model parameter sharding is needed. Verify PyTorch version, CUDA availability, and distributed initialization before blaming Runner config.

## ColossalAI Strategy

Dependency and hardware gated: requires `colossalai`, distributed launch, and compatibility between ColossalAI, PyTorch, CUDA, and model operations.

```python
strategy = dict(type='ColossalAIStrategy')
optim_wrapper = dict(optimizer=dict(type='HybridAdam', lr=1e-3))
```

Use ColossalAI only after confirming the optional package and optimizer are installed. In-place model operations can interact poorly with custom tensor operators; route model graph fixes to `models-metrics-and-inference`.

## AMP and Compile

Standard Runner enables AMP with `AmpOptimWrapper`:

```python
optim_wrapper = dict(
    type='AmpOptimWrapper',
    dtype='float16',
    optimizer=dict(type='AdamW', lr=1e-4),
)
```

FlexibleRunner has a top-level `compile` argument. Standard Runner can receive compile options inside `cfg`:

```python
runner = Runner(..., cfg=dict(compile=True))
runner = Runner(..., cfg=dict(compile=dict(backend='inductor', mode='max-autotune')))
```

`torch.compile` requires PyTorch 2.x support and can fail on dynamic or unsupported model code. Keep a non-compiled fallback path.

## Memory-Saving Recipes

| Technique | Config owner | Caution |
| --- | --- | --- |
| Gradient accumulation | `optim_wrapper.accumulative_counts` | Changes effective batch size; batch norm may behave differently. |
| AMP | `optim_wrapper.type='AmpOptimWrapper'` | Hardware and dtype support vary. |
| Gradient clipping | `optim_wrapper.clip_grad` | Choose norm/value semantics intentionally. |
| Activation checkpointing | `cfg.activation_checkpointing` | Saves memory by recomputing activations; can slow training. |
| FSDP/model wrapper | `strategy` or `cfg.model_wrapper_cfg` | Requires distributed initialization and compatible PyTorch/CUDA. |

## Launch Review Checklist

- The command uses the same launcher string configured in Runner.
- `WORLD_SIZE`, ranks, ports, and visible devices are provided by `torchrun`, Slurm, or the selected launcher.
- The backend matches hardware (`nccl` for CUDA, `gloo` for CPU-safe checks).
- Optional strategies are installed in the runtime environment before config review proceeds.
- Validation and checkpoint intervals are reasonable for distributed runtime cost.
- The training script parses and forwards `--launcher` or otherwise supplies the launcher to Runner.
