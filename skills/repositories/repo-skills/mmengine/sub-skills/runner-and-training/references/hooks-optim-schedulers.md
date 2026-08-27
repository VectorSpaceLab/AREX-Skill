# Hooks, Optimizers, and Schedulers

Use this reference when adapting MMEngine default hooks, custom hooks, checkpoint policy, optimizer wrappers, AMP, gradient accumulation, clipping, or parameter schedulers.

## Hook Ordering Model

Hooks run at Runner mount points in priority order; lower numeric priority runs earlier. Hooks with equal priority run in registration order.

| Priority name | Value | Typical use |
| --- | ---: | --- |
| `HIGHEST` | 0 | Emergency pre-processing or global guards. |
| `VERY_HIGH` | 10 | Runtime info updates. |
| `HIGH` | 30 | Early custom coordination. |
| `ABOVE_NORMAL` | 40 | Custom hooks before normal defaults. |
| `NORMAL` | 50 | Most custom hooks. |
| `BELOW_NORMAL` | 60 | Logger-like behavior. |
| `LOW` | 70 | Parameter scheduler updates. |
| `VERY_LOW` | 90 | Checkpoint/profiler actions after state updates. |
| `LOWEST` | 100 | Last observers. |

Do not casually raise checkpoint priority above parameter scheduler priority; saved optimizer and scheduler state should reflect the latest scheduler step.

## Default Hooks

A typical default hook config is:

```python
default_hooks = dict(
    runtime_info=dict(type='RuntimeInfoHook'),
    timer=dict(type='IterTimerHook'),
    sampler_seed=dict(type='DistSamplerSeedHook'),
    logger=dict(type='LoggerHook', interval=50),
    param_scheduler=dict(type='ParamSchedulerHook'),
    checkpoint=dict(type='CheckpointHook', interval=1),
)
```

Common edits:

- Change `logger.interval` to control terminal/log update cadence.
- Set `logger.log_metric_by_epoch=False` for iter-based training.
- Change `checkpoint.interval`, `checkpoint.by_epoch`, `checkpoint.max_keep_ckpts`, `checkpoint.save_best`, and `checkpoint.rule` for checkpoint policy.
- Keep `sampler_seed` enabled in distributed training unless a custom sampler hook replaces it.

## Custom Hooks

Custom hooks belong in `custom_hooks`, not `default_hooks`, unless replacing a default hook role.

```python
custom_hooks = [
    dict(type='EMAHook', priority='NORMAL'),
    dict(type='EmptyCacheHook', after_epoch=True),
]
```

Register new hook classes through the hook registry in the user project, then configure them by registry name. If registry lookup fails, route to `configuration-and-registry`.

## CheckpointHook Recipes

Save every epoch and keep only recent checkpoints:

```python
default_hooks = dict(
    checkpoint=dict(type='CheckpointHook', interval=1, max_keep_ckpts=3)
)
```

Save best validation metric explicitly:

```python
default_hooks = dict(
    checkpoint=dict(
        type='CheckpointHook',
        interval=1,
        save_best='accuracy',
        rule='greater',
        max_keep_ckpts=3,
    )
)
```

Save by iteration:

```python
default_hooks = dict(
    checkpoint=dict(type='CheckpointHook', interval=2000, by_epoch=False)
)
```

Use `save_best='auto'` only when the first evaluator metric is the desired selection key. For custom metrics, always provide `rule` or configure `greater_keys`/`less_keys`.

## Useful Built-In Custom Hooks

| Hook | Use | Main caution |
| --- | --- | --- |
| `EMAHook` | Evaluate/test with an exponential moving average model. | Resume and load behavior must preserve EMA state when continuing training. |
| `EmptyCacheHook` | Release cached GPU memory at chosen mount points. | Can slow training if used too frequently. |
| `SyncBuffersHook` | Synchronize buffers, such as batch norm state, in distributed training. | Only useful when distributed buffer drift matters. |
| `ProfilerHook` | Capture operator timing or memory profiles. | Produces extra runtime outputs and can slow training. |
| `EarlyStoppingHook` | Stop when a monitored validation metric plateaus. | `monitor` and `rule` must match evaluator metric keys. |

## OptimWrapper Basics

Runner expects an optimizer wrapper, not a raw optimizer config alone.

```python
optim_wrapper = dict(
    type='OptimWrapper',
    optimizer=dict(type='SGD', lr=0.01, momentum=0.9, weight_decay=0.0001),
)
```

The `type='OptimWrapper'` field may be omitted for standard single-precision training:

```python
optim_wrapper = dict(optimizer=dict(type='AdamW', lr=1e-4, weight_decay=0.05))
```

Use constructor configs or parameter-wise options for advanced optimizer grouping. If optimizer registry names or constructors fail, route registry mechanics to `configuration-and-registry`.

## AMP, Accumulation, and Clipping

Enable automatic mixed precision by switching wrapper type:

```python
optim_wrapper = dict(
    type='AmpOptimWrapper',
    dtype='float16',
    optimizer=dict(type='AdamW', lr=1e-4),
)
```

Add gradient accumulation:

```python
optim_wrapper = dict(
    type='AmpOptimWrapper',
    accumulative_counts=4,
    optimizer=dict(type='AdamW', lr=1e-4),
)
```

Add gradient clipping:

```python
optim_wrapper = dict(
    optimizer=dict(type='SGD', lr=0.01),
    clip_grad=dict(max_norm=1.0),
)
```

Use positive integer `accumulative_counts`. Remember that accumulation changes the effective batch size and can interact poorly with batch normalization in small-batch regimes.

## Multiple Optimizers

Multi-optimizer algorithms such as GANs usually use `OptimWrapperDict` or a custom optimizer wrapper constructor. Do not assume `OptimWrapperDict` has a single `update_params` method; model training logic must select the correct sub-wrapper for each component.

```python
optim_wrapper = dict(
    constructor='MultiOptimWrapperConstructor',
    generator=dict(optimizer=dict(type='Adam', lr=2e-4)),
    discriminator=dict(optimizer=dict(type='Adam', lr=2e-4)),
)
```

Pair multi-optimizer configs with model `train_step` logic that knows which wrapper key to update.

## Parameter Scheduler Basics

A single scheduler can be a dict:

```python
param_scheduler = dict(type='MultiStepLR', by_epoch=True, milestones=[8, 11], gamma=0.1)
```

Warmup plus main schedule is a list:

```python
param_scheduler = [
    dict(type='LinearLR', start_factor=0.001, by_epoch=False, begin=0, end=500),
    dict(type='CosineAnnealingLR', T_max=9500, by_epoch=False, begin=500, end=10000),
]
```

`ParamSchedulerHook` is registered by default and steps all configured schedulers.

## Scheduler Time Units

| Field | Epoch-based meaning | Iter-based meaning |
| --- | --- | --- |
| `by_epoch` | Scheduler steps by epoch. | Scheduler steps by iteration when `False`. |
| `milestones` | Epoch numbers. | Iteration numbers. |
| `begin`/`end` | Valid epoch interval `[begin, end)`. | Valid iteration interval `[begin, end)`. |
| `T_max` | Epoch period for cosine schedules. | Iteration period when `by_epoch=False`. |

When `train_cfg.by_epoch=False`, either convert scheduler numbers to iterations or use `convert_to_iter_based=True` on epoch-defined schedulers when the train dataloader length is stable.

## Scheduler Review Checklist

- `param_scheduler` is a dict or list of dicts.
- Every scheduler has a valid `type` and intended `by_epoch` value.
- Warmup schedulers usually use `by_epoch=False`, `begin=0`, and a short iteration `end`.
- Adjacent schedulers have non-overlapping or intentionally overlapping `[begin, end)` intervals.
- Checkpoint and logger units match the train loop units.
- Resume workflows save and restore scheduler state through checkpointing.
