# Extension Workflows

## Custom Model Component

Use this for backbones, necks, dense heads, RoI heads, bbox heads, detectors, model wrappers, and losses.

1. Pick the nearest existing base class and mirror its constructor and forward/loss/predict contract.
2. Register the class in `MODELS` unless the component is a task utility such as an assigner or bbox coder.
3. Import the module through package `__init__.py` or config `custom_imports`.
4. Replace the relevant config node and use `_delete_=True` when replacing an inherited nested dict with incompatible keys.
5. For detection heads, set `num_classes` consistently with dataset `metainfo.classes` and loss outputs.
6. Unit-test construction with a minimal config before running training.

Minimal backbone pattern:

```python
from torch import nn
from mmdet.registry import MODELS

@MODELS.register_module()
class MyBackbone(nn.Module):
    def __init__(self, out_channels=256):
        super().__init__()
        self.out_channels = out_channels

    def forward(self, x):
        return (x,)
```

Minimal loss pattern:

```python
from torch import nn
from mmdet.registry import MODELS
from mmdet.models.losses.utils import weighted_loss

@weighted_loss
def my_l1(pred, target):
    return (pred - target).abs()

@MODELS.register_module()
class MyL1Loss(nn.Module):
    def __init__(self, reduction='mean', loss_weight=1.0):
        super().__init__()
        self.reduction = reduction
        self.loss_weight = loss_weight

    def forward(self, pred, target, weight=None, avg_factor=None, reduction_override=None):
        reduction = reduction_override or self.reduction
        return self.loss_weight * my_l1(pred, target, weight, reduction=reduction, avg_factor=avg_factor)
```

## Custom Dataset Class

Use a new `DATASETS` class only when conversion to an existing supported format is not enough.

1. Inherit from a compatible MMDetection dataset base such as `BaseDetDataset` or a nearby concrete dataset.
2. Register with `DATASETS`.
3. Define or pass `metainfo` with `classes` and optional `palette`.
4. Implement annotation loading so returned records contain fields expected by the pipeline and evaluator.
5. Configure under `train_dataloader.dataset`, `val_dataloader.dataset`, and `test_dataloader.dataset`.
6. Keep data layout and conversion details in the datasets/evaluation workflow; keep class implementation and registry debugging here.

## Custom Transform

Transforms use `TRANSFORMS` and `mmcv.transforms.BaseTransform`.

```python
from mmcv.transforms import BaseTransform
from mmdet.registry import TRANSFORMS

@TRANSFORMS.register_module()
class MyTransform(BaseTransform):
    def __init__(self, prob=0.5):
        self.prob = prob

    def transform(self, results):
        results['my_flag'] = True
        return results
```

Checklist:

- Accept and return a `dict`; return `None` only when intentionally filtering a sample.
- Preserve keys needed by later transforms: usually `img`, `img_shape`, `ori_shape`, `gt_bboxes`, `gt_bboxes_labels`, `gt_masks`, `gt_ignore_flags`, and metadata keys.
- Place the transform before `PackDetInputs` if it changes raw image or annotation fields.
- Test with a synthetic `results` dict and the same pipeline order as the config.

## Custom Hooks and Runtime

Hooks use `HOOKS` and MMEngine hook method names.

```python
from mmengine.hooks import Hook
from mmdet.registry import HOOKS

@HOOKS.register_module()
class MyHook(Hook):
    def before_train_iter(self, runner, batch_idx, data_batch=None):
        ...
```

Configure with:

```python
custom_hooks = [dict(type='MyHook', priority='NORMAL')]
```

Default runtime hooks are configured in `default_hooks`. Modify those for logger/checkpoint/visualization behavior; use `custom_hooks` for new behavior. Avoid putting expensive validation inside every iteration unless intentionally debugging.

## Custom Optimizer or Constructor

- Use `OPTIMIZERS` for custom `torch.optim.Optimizer` subclasses.
- Use `OPTIM_WRAPPER_CONSTRUCTORS` for parameter-wise grouping beyond `paramwise_cfg`.
- Put the optimizer under `optim_wrapper.optimizer`, not under old 2.x `optimizer` top-level style.

Example config shape:

```python
optim_wrapper = dict(
    type='OptimWrapper',
    optimizer=dict(type='MyOptimizer', lr=1e-4, a=1, b=2),
    clip_grad=dict(max_norm=35, norm_type=2))
```

## Project Plugin Layout

A self-contained extension package can follow the `projects/` plugin style without modifying MMDetection internals:

```text
my_project/
  __init__.py
  models/
    __init__.py
    my_backbone.py
  datasets/
    __init__.py
    my_transform.py
  configs/
    my_detector.py
```

In the config:

```python
custom_imports = dict(imports=['my_project.models', 'my_project.datasets'], allow_failed_imports=False)
model = dict(backbone=dict(type='MyBackbone'))
```

The important rule is import side effects: package `__init__.py` files should import modules that define registered classes, or `custom_imports` should name each module that contains decorators.

## Structure Extensions

- Use `DetDataSample` for model/metric/visualizer interfaces.
- Put per-instance tensors in `InstanceData`, not arbitrary sample attributes, when the downstream component expects instance fields.
- For new box representations, subclass `BaseBoxes`, register with `register_box`, and implement converters where existing transforms or heads require another representation.
- For masks, preserve bitmap/polygon expectations and check shape conventions before feeding heads or evaluators.
