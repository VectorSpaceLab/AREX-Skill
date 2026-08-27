# MMDetection Configuration Workflows

MMDetection 3.3.0 uses MMEngine's config system. Treat configs as executable Python configuration files that may inherit from `_base_` files, import variables from base configs, and define nested dictionaries for models, datasets, loops, hooks, evaluators, and runtime behavior.

## Config Anatomy

Common top-level keys to inspect:

| Key | Purpose | Notes |
| --- | --- | --- |
| `_base_` | Inherits one or more config files | Relative paths must resolve from the config file location. |
| `default_scope` | Registry scope | MMDetection configs should normally resolve under `mmdet`. |
| `model` | Detector/segmenter/tracker architecture | Includes `data_preprocessor`, backbone/neck/head, `train_cfg`, and `test_cfg`. |
| `train_dataloader`, `val_dataloader`, `test_dataloader` | Dataset and loader definitions | In 3.x, dataset config lives under each dataloader's `dataset`. |
| `val_evaluator`, `test_evaluator` | Metric/evaluator definitions | Often COCO/LVIS/panoptic metrics. |
| `train_cfg`, `val_cfg`, `test_cfg` | Runner loop definitions | Do not confuse with `model.train_cfg` / `model.test_cfg`. |
| `param_scheduler`, `optim_wrapper` | LR schedule and optimizer | Use training/testing guidance before executing. |
| `auto_scale_lr` | Optional LR scaling metadata | Requires `enable` and `base_batch_size` for `--auto-scale-lr`. |

## Inspect Before Mutating

1. Resolve the intended config file path or model-zoo entry.
2. Flatten inheritance with `inspect_config.py CONFIG.py --full` or inspect only key sections with `--keys model train_dataloader val_evaluator auto_scale_lr`.
3. Check `default_scope`; if it is absent, tools commonly default to `mmdet`, but explicit `default_scope = 'mmdet'` is clearer for copied/custom configs.
4. Check `model.type`, task heads, and `num_classes` before pairing a checkpoint or dataset.
5. Check `model.data_preprocessor`, `test_pipeline`, and evaluator settings before inference/testing.
6. For training changes, check `train_dataloader.batch_size`, `optim_wrapper.optimizer.lr`, and `auto_scale_lr.base_batch_size`; then reroute to `training-testing`.

Safe read-only command:

```bash
python sub-skills/configuration-model-zoo/scripts/inspect_config.py configs/mask_rcnn/mask-rcnn_r50_fpn_1x_coco.py --summary
```

## `_base_` Inheritance

MMDetection configs commonly use either:

```python
_base_ = [
    '../_base_/models/mask-rcnn_r50_fpn.py',
    '../_base_/datasets/coco_instance.py',
    '../_base_/schedules/schedule_1x.py',
    '../_base_/default_runtime.py',
]
```

or a single parent such as:

```python
_base_ = './rtmdet_s_8xb32-300e_coco.py'
```

Some package-style configs under `mmdet/configs/` use Python imports from `.._base_`. For installed-package contexts, prefer official model names with MIM or copied standalone config files that keep their relative base files together.

When a child config uses base variables, preserve MMEngine syntax such as:

```python
train_pipeline = [
    dict(type='LoadImageFromFile', backend_args={{_base_.backend_args}}),
]
```

Do not manually edit these expressions unless you know which base variable is being referenced.

## Config Overrides

MMDetection tools accept `--cfg-options` using MMEngine `DictAction`, then merge values into the loaded config. Equivalent Python behavior is `cfg.merge_from_dict({...})`.

Examples:

```bash
--cfg-options model.test_cfg.rcnn.score_thr=0.3
--cfg-options train_dataloader.batch_size=4
--cfg-options model.data_preprocessor.mean=[0,0,0]
--cfg-options test_dataloader.dataset.pipeline.0.type=LoadImageFromWebcam
```

Rules of thumb:

- Use dotted paths for nested dictionaries and numeric indices for lists.
- Quote shell-sensitive lists/tuples: `--cfg-options 'model.data_preprocessor.mean=[0,0,0]'`.
- Validate overrides with `inspect_config.py` before training/testing.
- For model-zoo checkpoints, avoid changing architecture-defining keys unless you intentionally stop using that checkpoint.

## Variable Replacement

MMDetection's source `print_config.py` applies `mmdet.utils.replace_cfg_vals`, which expands string placeholders such as `${cfg_name}` or `${model.train_cfg.rpn_proposal.nms.iou_threshold}`. Replacement supports string interpolation and object substitution when the whole value is a placeholder; embedding dict/list/tuple values inside longer strings can raise assertions.

Use `inspect_config.py --replace-cfg-vals` when you need to verify these substitutions.

## `auto_scale_lr`

Training configs commonly include:

```python
auto_scale_lr = dict(enable=False, base_batch_size=16)
```

`base_batch_size` records the reference global batch size, often `(8 GPUs) x (2 samples per GPU) = 16`. Some large-scale jitter configs use `base_batch_size=64`. If a training command enables automatic LR scaling but the config lacks `auto_scale_lr.enable` or `auto_scale_lr.base_batch_size`, MMDetection raises an error instead of guessing.

Before enabling LR scaling:

1. Inspect the final merged config for `auto_scale_lr`.
2. Confirm `base_batch_size` matches the config family's documented training batch, not the current machine.
3. Reroute actual train command construction to `training-testing`.

## 2.x to 3.x Migration Pointers

MMDetection 3.x changed config structure in several high-impact areas:

| 2.x Pattern | 3.x Pattern |
| --- | --- |
| `data = dict(train=..., val=..., test=...)` | `train_dataloader`, `val_dataloader`, `test_dataloader` |
| `samples_per_gpu`, `workers_per_gpu` | `batch_size`, `num_workers` under each dataloader |
| `Normalize` and `Pad` in pipelines | `model.data_preprocessor` handles normalization/padding |
| `DefaultFormatBundle` / `Collect` | `PackDetInputs` |
| `MultiScaleFlipAug` | Separate test-time augmentation config |
| Inline metric settings in legacy test flow | `val_evaluator` and `test_evaluator` |

For a migrated config, inspect these sections first:

```bash
python sub-skills/configuration-model-zoo/scripts/inspect_config.py CONFIG.py --keys model train_dataloader val_dataloader test_dataloader val_evaluator test_evaluator auto_scale_lr
```

## Validation Checklist

- Config loads with `mmengine.Config.fromfile` after all `_base_` paths are copied together.
- `default_scope` is `mmdet` or the caller initializes the `mmdet` scope before registry construction.
- `model.type` and head types exist in installed MMDetection 3.3.0.
- Checkpoint architecture, task, classes, and preprocessing match the config.
- `auto_scale_lr.base_batch_size` exists before enabling automatic LR scaling.
- Any `--cfg-options` changes appear in `inspect_config.py --full` output.
- The task requested is still config/model-zoo selection; execution belongs to another sub-skill.
