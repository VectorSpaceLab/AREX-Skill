# Configuration Reference

This reference explains the config pieces that matter for training and evaluation planning. Use the bundled `scripts/print_config.py` first when you need the fully merged result of `_base_` inheritance and CLI overrides.

## Inheritance and override rules

- `_base_` may be a string or a list of strings.
- Keep inheritance shallow; three levels is a practical upper bound for readable configs.
- Use `_delete_=True` when you want to replace an inherited dict branch instead of merging new keys into stale inherited keys.
- Use `_base_.name` when a child config needs to reuse a value defined in a base config.
- Intermediate variables such as `train_pipeline`, `test_pipeline`, or `bgr_mean` are meant to be overridden directly when the input recipe changes.

## Core fields

| Field | What it controls | Common edits |
| --- | --- | --- |
| `model` | Backbone, neck, head, losses, and task-specific training augments. | Swap the backbone, change `num_classes`, add CutMix or Mixup in `train_cfg`, or change `data_preprocessor`. |
| `model.data_preprocessor` | Model-side input normalization and preprocessing. | Adjust mean/std, resize policy, or color conversion. It takes precedence over top-level `data_preprocessor`. |
| `train_dataloader` | Training data loader, sampler, batch size, workers, and dataset pipeline. | Change `data_root`, `ann_file`, `data_prefix`, `batch_size`, `sampler`, or `pipeline`. |
| `val_dataloader` / `test_dataloader` | Validation and test loaders. | Use a larger batch size, reuse the test pipeline, or point at a different split. |
| `train_evaluator` / `val_evaluator` / `test_evaluator` | Metric objects used during training and evaluation. | Change top-k accuracy, retrieval metrics, or offline metric selection. |
| `optim_wrapper` | Optimizer and wrapper behavior. | Tune SGD/AdamW settings, param-wise rules, or AMP wrapper type. |
| `param_scheduler` | Learning-rate or momentum schedule. | Replace milestone, cosine, or linear warmup schedules; use `_delete_=True` when changing schedule family. |
| `train_cfg` | Training loop settings. | Set `max_epochs`, `val_interval`, or batch augmentation such as CutMix. |
| `val_cfg` / `test_cfg` | Validation and test loop settings. | Rarely changed unless a custom loop or fp16 test setting is needed. |
| `auto_scale_lr` | Automatic LR scaling metadata. | Set `base_batch_size` so `--auto-scale-lr` has a reference point. |
| `default_scope` | Registry scope used for building modules. | Usually `mmpretrain`. |
| `default_hooks` | Timer, logger, checkpoint, sampler seed, and visualization hooks. | Enable the visualization hook when using `--show` or `--show-dir`. |
| `env_cfg` | Distributed and multiprocessing settings. | Backend choice, OpenCV thread count, or multiprocessing start method. |
| `visualizer` / `vis_backends` | How visual outputs are saved or rendered. | Add or change local visualization backends. |
| `work_dir` | Where logs, checkpoints, and evaluation outputs are written. | Set explicitly for repeatable experiments. |
| `load_from` | Checkpoint used as initialization. | Use for fine-tuning or evaluation from a pretrained weight file. |
| `resume` | Resume state for interrupted training. | Use `--resume` or `--resume PATH` rather than `load_from` when continuing the same run. |

## CLI override syntax

The train and test launchers apply CLI-derived changes first, then merge `--cfg-options`.

Common patterns:

```bash
--cfg-options model.backbone.norm_eval=False
--cfg-options data.train.pipeline.1.flip_prob=0.0
--cfg-options val_evaluator.topk="(1,3)"
--cfg-options train_cfg.max_epochs=300
--cfg-options model.head.num_classes=10
```

Rules to keep in mind:

- Use dotted keys to reach nested dicts.
- Use list indexes for pipeline edits.
- Quote tuple or list values when the shell would otherwise split them.
- Do not add whitespace inside a quoted tuple/list value.
- If a value contains commas and should stay a single string, quote it.

## Good edit patterns

### Replace an inherited schedule branch

```python
param_scheduler = dict(type='CosineAnnealingLR', by_epoch=True, _delete_=True)
```

### Adapt a base recipe for custom data and CutMix

```python
_base_ = 'path/to/base_config.py'

model = dict(
    train_cfg=dict(augments=dict(type='CutMix', alpha=1.0)))

train_cfg = dict(max_epochs=300, val_interval=10)
param_scheduler = dict(
    type='MultiStepLR',
    milestones=[150, 200, 250],
    gamma=0.1,
    _delete_=True)

auto_scale_lr = dict(base_batch_size=256)

train_dataloader = dict(dataset=dict(data_root='path/to/train'))
val_dataloader = dict(dataset=dict(data_root='path/to/val'))
test_dataloader = dict(dataset=dict(data_root='path/to/test'))
```

### Inspect the resolved config

```bash
python scripts/print_config.py path/to/config.py --cfg-options model.backbone.norm_eval=False
```

## Practical notes

- `model.data_preprocessor` overrides the top-level `data_preprocessor` when both are present.
- `train_dataloader`, `val_dataloader`, and `test_dataloader` receive default dataloader settings from the launchers unless you override them.
- `--no-pin-memory` and `--no-persistent-workers` only change dataloader behavior; they do not change the dataset itself.
- `--auto-scale-lr` only enables scaling; the config still needs a sensible `auto_scale_lr.base_batch_size`.
- If a config becomes hard to reason about, flatten the inheritance chain before changing the launch command.
