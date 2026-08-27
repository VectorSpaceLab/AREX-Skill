# Registries and APIs

## Registry Map

MMDetection 3.3.0 defines registry nodes in `mmdet.registry` as children of MMEngine registries. Use the narrowest matching node so config dictionaries build the intended object.

| Registry | Typical config fields | Common classes |
|---|---|---|
| `MODELS` | `model`, `backbone`, `neck`, `bbox_head`, `roi_head`, `loss_*`, `data_preprocessor` | detectors, heads, backbones, losses, model wrappers |
| `TASK_UTILS` | `bbox_coder`, `assigner`, `sampler`, anchor/prior generators | box coders, assigners, samplers, task utilities |
| `DATASETS` | `train_dataloader.dataset`, `val_dataloader.dataset`, wrappers | datasets and dataset wrappers |
| `TRANSFORMS` | `train_pipeline`, `test_pipeline` | data pipeline transforms |
| `HOOKS` | `custom_hooks`, `default_hooks` | runtime hooks |
| `OPTIMIZERS` | `optim_wrapper.optimizer` | PyTorch and custom optimizer classes |
| `OPTIM_WRAPPERS` | `optim_wrapper` | optimizer wrappers |
| `OPTIM_WRAPPER_CONSTRUCTORS` | `optim_wrapper.constructor` or constructor configs | parameter-wise optimizer constructors |
| `PARAM_SCHEDULERS` | `param_scheduler` | learning-rate and momentum schedulers |
| `LOOPS` | `train_cfg`, `val_cfg`, `test_cfg` | train/val/test loops |
| `METRICS`, `EVALUATOR` | `val_evaluator`, `test_evaluator` | metrics and evaluator objects |
| `VISUALIZERS`, `VISBACKENDS` | `visualizer`, `vis_backends` | visualization frontends/backends |
| `RUNNERS`, `RUNNER_CONSTRUCTORS` | advanced runner configs | runner-level extensions |
| `DATA_SAMPLERS` | dataloader sampler/batch sampler | sampling logic |
| `LOG_PROCESSORS` | `log_processor` | log formatting/aggregation |

## Registration Pattern

Use decorators from `mmdet.registry`:

```python
from mmdet.registry import MODELS

@MODELS.register_module()
class MyBBoxHead(...):
    ...
```

For custom box structures, use the structure-specific registration API rather than MMEngine registry:

```python
from mmdet.structures.bbox import BaseBoxes, register_box, register_box_converter

@register_box('mybox')
class MyBoxes(BaseBoxes):
    ...
```

## Import and Scope Rules

- Registration happens when Python imports the module that contains the decorated class.
- Prefer config-level imports for external extensions:

```python
custom_imports = dict(
    imports=['my_project.models.my_bbox_head', 'my_project.datasets.my_transform'],
    allow_failed_imports=False)
```

- Import modules, not classes. Use `my_project.models.my_bbox_head`, not `my_project.models.my_bbox_head.MyBBoxHead`.
- If a config or script builds registries outside MMDetection entrypoints, initialize or keep the default scope as `mmdet`.
- If importing OpenMMLab packages together, scope-qualified types such as `mmdet.MyBBoxHead` can disambiguate registry ownership, but most MMDetection configs rely on `default_scope = 'mmdet'`.

## Structures Used by Extensions

`DetDataSample` is the standard interface between data pipelines, models, metrics, and visualizers. Common fields are:

| Field | Type | Purpose |
|---|---|---|
| `gt_instances` | `InstanceData` | training labels such as `bboxes`, `labels`, `masks` |
| `pred_instances` | `InstanceData` | detection outputs such as `bboxes`, `scores`, `labels`, `masks` |
| `ignored_instances` | `InstanceData` | ignored ground-truth instances |
| `proposals` | `InstanceData` | RPN or external proposals |
| `gt_sem_seg`, `pred_sem_seg` | `PixelData` | semantic segmentation fields |
| `gt_panoptic_seg`, `pred_panoptic_seg` | `PixelData` | panoptic segmentation fields |
| `pred_track_instances` | `InstanceData` | tracking predictions |

Box and mask extensions should preserve the expected tensor shapes and conversion behavior. `BaseBoxes` subclasses are registered with `register_box`; converters are registered with `register_box_converter`.

## 2.x to 3.x Migration Pointers

- Registries moved to the MMEngine-style registry system; use `mmdet.registry` and `@...register_module()` instead of legacy registry imports.
- Data containers are replaced by `DetDataSample`, `InstanceData`, and `PixelData` style structures.
- Runtime config is MMEngine-based: `optim_wrapper`, `param_scheduler`, `train_cfg`, `val_cfg`, `test_cfg`, `default_hooks`, and `custom_hooks` replace many 2.x runner/runtime patterns.
- Dataset config uses dataloader dictionaries such as `train_dataloader.dataset` and dataset `metainfo` instead of older `data.train` patterns.
- Model methods are organized around `loss`, `predict`, and tensor forward paths. New modules should match the signatures of the base class they extend.
