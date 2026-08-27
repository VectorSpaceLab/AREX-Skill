# Runner Workflows

This reference covers MMEngine 0.11.0rc2 Runner-oriented training, validation, testing, checkpoint, and resume workflows. It is self-contained; do not require future agents to open original examples or repository docs.

## Entry Points

| Entry point | Use when | Key outputs |
| --- | --- | --- |
| `Runner.from_cfg(cfg)` | A project already has an MMEngine config dict or `Config` object. | A configured `Runner`; call `train()`, `val()`, or `test()`. |
| `Runner(...)` | Building a tiny experiment programmatically or adapting a config into Python objects. | Same as above; components may be objects or registry dicts. |
| `FlexibleRunner(...)` | A task needs `strategy`, optional compile, or experimental large-model orchestration. | Same training/validation/testing surface with strategy-aware preparation. |

Verified public methods:

- `Runner.from_cfg(cfg)` builds a runner from config keys that map to `Runner.__init__`.
- `Runner.train()` launches training and returns the model.
- `Runner.val()` launches validation and returns a metrics dict.
- `Runner.test()` launches testing and returns a metrics dict.
- `Runner.register_hook(hook, priority=None)` inserts hooks by priority and registration order.
- `Runner.save_checkpoint(...)` and `Runner.resume(...)` are used by checkpoint/resume flows.

## Minimum Training Config Shape

Training requires a model, work directory, train dataloader, train loop config, and optimizer wrapper. Validation and testing are optional but must be complete when enabled.

```python
runner = Runner(
    model=model_or_model_cfg,
    work_dir='work_dirs/experiment_name',
    train_dataloader=train_dataloader_or_cfg,
    train_cfg=dict(by_epoch=True, max_epochs=12, val_interval=1),
    optim_wrapper=dict(optimizer=dict(type='SGD', lr=0.01, momentum=0.9)),
    val_dataloader=val_dataloader_or_cfg,
    val_cfg=dict(),
    val_evaluator=metric_or_metric_cfg,
    default_hooks=dict(checkpoint=dict(type='CheckpointHook', interval=1)),
)
runner.train()
```

Use registry dicts for config-driven projects and live objects for small scripts. The model and evaluator contracts are owned by `models-metrics-and-inference`; this sub-skill assumes they already satisfy Runner expectations.

## Train, Val, and Test Completeness

| Workflow | Required fields | Common optional fields |
| --- | --- | --- |
| Train only | `model`, `work_dir`, `train_dataloader`, `train_cfg`, `optim_wrapper` | `param_scheduler`, `default_hooks`, `custom_hooks`, `randomness`, `log_processor`, `load_from`, `resume` |
| Train + validation | Train fields plus `val_dataloader`, `val_cfg`, `val_evaluator` | `train_cfg.val_begin`, `train_cfg.val_interval`, checkpoint `save_best` |
| Validation only | `model`, `work_dir`, `val_dataloader`, `val_cfg`, `val_evaluator` | `load_from`, visualizer/logging fields |
| Testing only | `model`, `work_dir`, `test_dataloader`, `test_cfg`, `test_evaluator` | `load_from`, output/dump metrics in evaluator |

Avoid partial validation/test configs. For example, `val_cfg=dict()` without `val_dataloader` or `val_evaluator` is not a runnable validation workflow.

## Epoch-Based Training

Epoch-based training is the default mental model. Keep all time-related settings in epoch units.

```python
train_cfg = dict(by_epoch=True, max_epochs=12, val_begin=1, val_interval=1)
param_scheduler = dict(type='MultiStepLR', by_epoch=True, milestones=[8, 11], gamma=0.1)
default_hooks = dict(
    logger=dict(type='LoggerHook', interval=50, log_metric_by_epoch=True),
    checkpoint=dict(type='CheckpointHook', interval=1, by_epoch=True),
)
log_processor = dict(by_epoch=True)
```

Use epoch units for `max_epochs`, scheduler `milestones`, scheduler `begin`/`end`, logger metric labels, and checkpoint intervals.

## Iter-Based Training Conversion

When converting an epoch-based config to iteration-based training, update all time-unit owners together.

```python
train_cfg = dict(by_epoch=False, max_iters=10000, val_interval=2000)
default_hooks = dict(
    logger=dict(type='LoggerHook', interval=50, log_metric_by_epoch=False),
    checkpoint=dict(type='CheckpointHook', interval=2000, by_epoch=False),
)
log_processor = dict(by_epoch=False)
param_scheduler = [
    dict(type='LinearLR', start_factor=0.001, by_epoch=False, begin=0, end=500),
    dict(type='MultiStepLR', by_epoch=False, milestones=[6000, 8000], gamma=0.1),
]
```

If you want smooth iteration updates while preserving epoch milestones, set scheduler `by_epoch=True` plus `convert_to_iter_based=True` when the epoch length is stable. Do not mix an iter-based train loop with default epoch-based checkpoint/log display unless the mismatch is intentional and documented.

## Checkpoint and Resume Semantics

`load_from` and `resume` answer different questions:

| Config | Behavior |
| --- | --- |
| `load_from='checkpoint.pth', resume=False` | Load model weights, then start a new training schedule. Optimizer and scheduler state are not resumed. |
| `resume=True, load_from=None` | Resume from the latest checkpoint under `work_dir` when one exists; otherwise start normally. |
| `resume=True, load_from='checkpoint.pth'` | Resume model, optimizer, scheduler, epoch/iter counters, and metadata from the specified checkpoint. |

Use `resume=True` for interrupted training and schedule continuation. Use `load_from` without resume for fine-tuning or initialization. For `FlexibleRunner`, `resume` may be a boolean or checkpoint string; keep this distinction explicit in reviews.

## Validation Interval and Best Checkpoint

Best checkpoint saving depends on validation metrics being available at the same time unit as the loop.

```python
train_cfg = dict(by_epoch=True, max_epochs=24, val_interval=1)
val_cfg = dict()
val_evaluator = dict(type='Accuracy')
default_hooks = dict(
    checkpoint=dict(
        type='CheckpointHook',
        interval=1,
        by_epoch=True,
        save_best='accuracy',
        rule='greater',
        max_keep_ckpts=3,
    )
)
```

Use `save_best='auto'` only when the first evaluator metric is the intended selection metric. Otherwise name the metric and set `rule='greater'` or `rule='less'`, especially for custom metric names.

## Randomness and Reproducibility

`randomness` is passed to the runner and commonly includes `seed`, `deterministic`, and rank-related seed controls. Use a fixed integer seed for reproducible smoke or regression runs, and document when nondeterministic backend performance settings are intentionally enabled.

```python
randomness = dict(seed=3407, deterministic=False)
```

Distributed training additionally needs sampler seed behavior through the default `DistSamplerSeedHook`; do not remove it unless a replacement hook owns distributed sampler epoch updates.

## Work Directory and Runtime Outputs

`work_dir` is the primary output directory for checkpoints, logs, config snapshots, and local visualization files. `log_processor`, `LoggerHook`, and the visualizer decide formatting and sink details. Avoid hard-coding machine-specific absolute paths in reusable configs; prefer project-relative or user-supplied output directories.

## Auto Scale LR

`auto_scale_lr` is useful when a config declares a reference batch size and the actual global batch size can differ.

```python
auto_scale_lr = dict(enable=True, base_batch_size=256)
```

Only enable it when the intended base batch size is known. Otherwise, changing GPU count or per-GPU batch size can silently change learning rate assumptions.

## Direct Construction vs Config Construction

Most Runner inputs accept either built objects or registry dictionaries. Prefer config dictionaries when a future agent needs reusable experiments, command-line overrides, or `Runner.from_cfg`. Prefer direct Python objects when demonstrating a tiny local proof of concept.

When registry construction fails, route to `configuration-and-registry`; when a model returns the wrong `loss` or `predict` shape, route to `models-metrics-and-inference`.
