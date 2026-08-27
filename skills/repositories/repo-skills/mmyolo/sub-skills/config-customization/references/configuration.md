# Configuration Editing Guide

This guide distills the MMYOLO v0.6.0 config behavior needed to choose, edit, and validate model-family configs before handing them to a run workflow. It is intentionally config-only: do not launch training, testing, inference, deployment export, downloads, or dataset conversion from this sub-skill.

## MMYOLO config model

MMYOLO uses MMEngine Python config files. A config is executable Python whose top-level variables become the runtime configuration. Common top-level sections are:

| Section | What to inspect or edit |
| --- | --- |
| `_base_` | Parent config path(s). Relative paths are resolved from the current config file. |
| `model` | Detector, data preprocessor, backbone, neck, head, loss/assigner, train/test settings. |
| `train_dataloader` | Training batch size, workers, sampler, dataset type, data root, annotations, image prefix, pipeline. |
| `val_dataloader`, `test_dataloader` | Validation/test batch size, workers, test-mode dataset, annotation file, image prefix, pipeline, `batch_shapes_cfg`. |
| `val_evaluator`, `test_evaluator` | Metric type, annotation file, metric name, `format_only`, output prefix. |
| `train_cfg`, `val_cfg`, `test_cfg` | Loop type, `max_epochs`, validation interval, dynamic intervals. |
| `optim_wrapper` | Optimizer wrapper, optimizer type/lr/momentum/weight decay, batch-size scaling field. |
| `param_scheduler` | Top-level LR/momentum scheduler list, or `None` when a YOLO-specific hook owns scheduling. |
| `default_hooks`, `custom_hooks` | Checkpoint interval, logger interval, YOLO parameter scheduler hooks, EMA, mode-switch hooks. |
| `load_from`, `resume` | Fine-tune checkpoint source versus resume behavior. |
| `default_scope`, `env_cfg`, `visualizer`, `log_processor`, `log_level` | Registry scope, distributed/runtime settings, visualization/logging. |

Always inspect the expanded config after inheritance and command-line overrides. Use the bundled helper:

```bash
python scripts/print_mmyolo_config_summary.py /path/to/config.py
```

Add `--cfg-options key=value ...` to preview simple overrides and `--check-tta` to fail fast if a TTA request lacks the required config variables.

## Inheritance patterns that matter

### `_base_`

A child config can inherit one parent config:

```python
_base_ = 'yolov5_s-v61_syncbn_fast_8xb16-300e_coco.py'
```

or multiple parents:

```python
_base_ = [
    './family_base.py',
    '../_base_/default_runtime.py',
]
```

The recommended MMYOLO pattern is to keep one primitive config per family folder and make variants inherit it. For a user customization, prefer a new child config that inherits the closest model-family baseline instead of editing the baseline.

### `_delete_=True`

MMEngine merges dicts by key. Use `_delete_=True` when replacing a component with a different schema. Example: replacing an RTMDet `CSPNeXt` backbone with a YOLOv6 backbone should delete incompatible RTMDet-only keys such as `channel_attention` or `expand_ratio`:

```python
model = dict(
    backbone=dict(
        _delete_=True,
        type='YOLOv6EfficientRep',
        deepen_factor=deepen_factor,
        widen_factor=widen_factor,
        norm_cfg=dict(type='BN', momentum=0.03, eps=0.001),
        act_cfg=dict(type='ReLU', inplace=True)))
```

If you omit `_delete_=True`, stale keys from the base can survive and cause constructor errors.

### Intermediate variables must be rebound

Many MMYOLO configs define helper variables such as `img_scale`, `pre_transform`, `train_pipeline`, `test_pipeline`, `batch_shapes_cfg`, `max_epochs`, or `train_batch_size_per_gpu`. Changing a helper variable alone is not always enough: reassign the final config field that consumes it.

For example, after defining a new `test_pipeline`, also set:

```python
val_dataloader = dict(dataset=dict(pipeline=test_pipeline))
test_dataloader = dict(dataset=dict(pipeline=test_pipeline))
```

After changing `train_batch_size_per_gpu`, also update the dataloader and any optimizer batch-size scaling field used by that family.

### Reusing values from the base

MMEngine supports using `_base_` values in children, for example:

```python
pre_transform = _base_.pre_transform
_base_.optim_wrapper.optimizer.batch_size_per_gpu = train_batch_size_per_gpu
```

Use this when a child config needs to modify a small part of the inherited schedule, optimizer, or pipeline while preserving family-specific defaults.

## One-class COCO-style fine-tuning recipe

Use this pattern when a user has COCO-format annotation JSONs and one class such as `cat`.

```python
_base_ = 'nearest_family_baseline.py'

data_root = './data/my_dataset/'
class_name = ('cat', )
num_classes = len(class_name)
metainfo = dict(classes=class_name, palette=[(20, 220, 60)])

max_epochs = 40
train_batch_size_per_gpu = 12
train_num_workers = 4

load_from = 'path-or-url-to-compatible-pretrained-checkpoint.pth'

model = dict(
    backbone=dict(frozen_stages=4),
    bbox_head=dict(head_module=dict(num_classes=num_classes)))

train_dataloader = dict(
    batch_size=train_batch_size_per_gpu,
    num_workers=train_num_workers,
    dataset=dict(
        data_root=data_root,
        metainfo=metainfo,
        ann_file='annotations/trainval.json',
        data_prefix=dict(img='images/')))

val_dataloader = dict(
    dataset=dict(
        data_root=data_root,
        metainfo=metainfo,
        ann_file='annotations/test.json',
        data_prefix=dict(img='images/')))

test_dataloader = val_dataloader

val_evaluator = dict(ann_file=data_root + 'annotations/test.json')
test_evaluator = val_evaluator

default_hooks = dict(
    checkpoint=dict(interval=10, max_keep_ckpts=2, save_best='auto'),
    logger=dict(type='LoggerHook', interval=5))
train_cfg = dict(max_epochs=max_epochs, val_interval=10)
```

Then apply the family-specific additions below.

### Family-specific `num_classes` and fine-tune edits

| Family | Required or common extra edits |
| --- | --- |
| YOLOv5 | Anchor-based. Set `model.bbox_head.head_module.num_classes`; if anchors are adapted, also set `model.bbox_head.prior_generator.base_sizes`. Update `_base_.optim_wrapper.optimizer.batch_size_per_gpu` when reducing per-GPU batch size. A single-class YOLOv5 head can warn that classification loss is zero; this is expected behavior for this head. |
| YOLOv6 | Set `model.bbox_head.head_module.num_classes`, plus `model.train_cfg.initial_assigner.num_classes` and `model.train_cfg.assigner.num_classes`. Update `_base_.optim_wrapper.optimizer.batch_size_per_gpu` and any last-stage switch hook epoch. |
| YOLOv7 | Anchor-based. Set head `num_classes`, optionally adapted anchors, and optimizer batch-size scaling. Some filenames use `8x16b` rather than `8xb16`; preserve the family naming style. |
| YOLOv8 | Set head `num_classes` and `model.train_cfg.assigner.num_classes`. For mosaic close-stage configs, update the relevant custom hook switch epoch after changing `max_epochs`. |
| YOLOX | Set head `num_classes`; update the YOLOX mode-switch custom hook when changing `num_last_epochs`; keep the scheduler list consistent with the shortened run. |
| RTMDet | Set head `num_classes` and `model.train_cfg.assigner.num_classes`; adjust stage-2 hook/scheduler when changing `max_epochs`. |
| PPYOLOE / PPYOLOE+ | Set head `num_classes`, `initial_assigner.num_classes`, and `assigner.num_classes`; note that PPYOLOE+ small configs can still be memory-heavy. |

## Custom classes, metainfo, and palette

- Put metadata inside each dataset config that needs it: `train_dataloader.dataset.metainfo`, `val_dataloader.dataset.metainfo`, and `test_dataloader.dataset.metainfo`.
- Use lowercase metadata keys. MMYOLO train/test logic checks this and expects keys such as `classes` and `palette`, not `CLASSES`.
- `classes` should be a tuple or list with the exact class order used in the annotation category ids.
- `palette` is used for visualization. Its length must be at least the number of classes.
- `num_classes` must match `len(metainfo['classes'])` for every relevant head, assigner, and loss component.
- When fine-tuning from a COCO checkpoint to a different class count, final head weights may not match. Treat the head mismatch as expected if the checkpoint is only used as pretrained initialization.

## Dataset and evaluator keys to verify

For each dataloader, inspect:

```python
data_root = './data/my_dataset/'
ann_file = 'annotations/trainval.json'
data_prefix = dict(img='images/')
pipeline = train_pipeline or test_pipeline
batch_size = train_batch_size_per_gpu
num_workers = train_num_workers
```

For validation/test:

```python
val_evaluator = dict(ann_file=data_root + 'annotations/test.json')
test_evaluator = val_evaluator
```

`ann_file` inside the dataset and `ann_file` inside the evaluator must point to the same validation/test annotations unless the user intentionally evaluates a different target.

## Runtime edits to check before handing off

- `train_cfg.max_epochs`: shortened runs should update hooks and schedulers that also store epoch counts.
- `train_cfg.val_interval`: validation frequency; small fine-tunes often use 10 epochs.
- `train_cfg.dynamic_intervals`: if present, ensure its switch epoch is within the new `max_epochs`.
- `default_hooks.checkpoint.interval`: checkpoint frequency; align with validation interval for small fine-tunes.
- `default_hooks.checkpoint.max_keep_ckpts`: bound disk usage.
- `default_hooks.checkpoint.save_best`: use `'auto'` when the evaluator metric is standard.
- `default_hooks.logger.interval`: reduce for short runs, increase for long runs.
- `default_hooks.param_scheduler.max_epochs`, `warmup_mim_iter`, `warmup_min_iter`, `warmup_epochs`, or family-specific hook fields: shorten warmup for tiny datasets.
- `param_scheduler`: if a list is used, update `begin`, `end`, `T_max`, and `convert_to_iter_based` consistently.
- `optim_wrapper.optimizer.batch_size_per_gpu`: update when the family uses it for learning-rate scaling.
- `load_from`: pretrained initialization; should point to a compatible checkpoint when fine-tuning.
- `resume`: use only to resume a previous run, not to initialize from a different pretrained model.

## `--cfg-options` syntax and when not to use it

MMYOLO train/test-style CLIs accept MMEngine `--cfg-options` with `key=value` pairs.

Good uses:

```bash
--cfg-options train_cfg.max_epochs=12 train_cfg.val_interval=3
--cfg-options model.backbone.norm_eval=False
--cfg-options default_hooks.logger.interval=10
--cfg-options model.data_preprocessor.mean="[0,0,0]"
```

Rules:

- Use dot paths through nested dicts: `model.bbox_head.head_module.num_classes=1`.
- Use integer indexes for list entries when needed: `train_dataloader.dataset.pipeline.0.type=LoadImageFromFile`.
- Quote list/tuple values and remove whitespace inside the quotes: `"[127,127,127]"`.
- Use Python booleans (`True`, `False`) for MMEngine-compatible parsing.

Prefer a child config file rather than `--cfg-options` when the change touches:

- `metainfo`, dataset roots, annotation files, or image prefixes across train/val/test.
- multiple `num_classes` sites across head and assigners.
- anchors or prior generator structure.
- train/test pipelines, TTA pipelines, or intermediate variables.
- scheduler lists, custom hooks, or dynamic intervals.
- anything that should be reviewed, committed, or reused.

## TTA config requirements

A TTA request requires both top-level variables:

```python
tta_model = dict(
    type='mmdet.DetTTAModel',
    tta_cfg=dict(nms=dict(type='nms', iou_threshold=0.65), max_per_img=300))

tta_pipeline = [
    dict(type='LoadImageFromFile'),
    dict(type='TestTimeAug', transforms=[...])
]
```

Typical P5 TTA uses three scales, for example `(640, 640)`, `(320, 320)`, `(960, 960)`, and two flip branches. To customize TTA, edit `img_scales` and/or the `TestTimeAug.transforms` list in a child config.

Caveats:

- If `--tta` is requested but the expanded config lacks `tta_model` or `tta_pipeline`, the test workflow will assert and stop.
- MMYOLO test logic disables `test_dataloader.dataset.batch_shapes_cfg` when TTA is active because batch-shape padding forces output image shapes and is incompatible with TTA. If a user requires TTA, ensure the config can tolerate `batch_shapes_cfg = None` for test.
- Use the bundled summary helper with `--check-tta` to diagnose a TTA request before handing off to a testing workflow.

## Config validation handoff checklist

Before routing to `training-evaluation` or `inference-visualization`, record:

- Chosen family and baseline pattern.
- Whether the user made a child config or only `--cfg-options` overrides.
- Expanded head `num_classes` and class names.
- Dataset roots, train/val/test annotation files, image prefixes, and evaluator annotation files.
- Train/val/test batch sizes and workers.
- `max_epochs`, `val_interval`, checkpoint interval, logger interval, scheduler/hook epoch counts.
- `load_from` and `resume` intent.
- TTA readiness and `batch_shapes_cfg` status if TTA is requested.
