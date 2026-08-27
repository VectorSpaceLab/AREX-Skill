# Registry-based customization

## Registry map

| What you are adding | Registry | Usual base class | Typical config entry |
| --- | --- | --- | --- |
| Dataset | `DATASETS` | `BaseDataset` | `dataset=dict(type='MyDataset', ...)` |
| Transform | `TRANSFORMS` | `BaseTransform` | `pipeline=[dict(type='MyTransform')]` |
| Backbone / neck / head / loss / full model | `MODELS` | `nn.Module` or `BaseModule` | nested inside `model=...` |
| Metric | `METRICS` | `BaseMetric` | `val_evaluator=dict(type='MyMetric')` |
| Hook | `HOOKS` | `Hook` | `custom_hooks=[dict(type='MyHook')]` |
| Optimizer | `OPTIMIZERS` | `torch.optim.Optimizer` subclass | `optim_wrapper=dict(optimizer=dict(type='MyOptim'))` |

`MODELS` is the shared registry for backbones, necks, heads, losses, and task models. There is no separate head or loss registry in the OpenMMLab 2.0 style.

## General registration rule

1. Put the class in a module that is importable.
2. Decorate it with the right registry.
3. Make sure the module is imported before config building or inspection.
4. Reference the class name in config with `type=...`.

If the class lives in a project package, import that package module through the package initializer or through `custom_imports`.

```python
custom_imports = dict(
    imports=['my_project.datasets', 'my_project.metrics'],
    allow_failed_imports=False,
)
```

## Dataset pattern

Use `BaseDataset` when you already have sample dictionaries and only need to fill `load_data_list()`.

```python
from mmpretrain.registry import DATASETS
from mmpretrain.datasets import BaseDataset

@DATASETS.register_module()
class MyDataset(BaseDataset):
    def load_data_list(self):
        ...
```

Good habits:

- Return a list of dictionaries.
- Keep image paths in `img_path` when the pipeline loads images later.
- Put labels in `gt_label` or `gt_score`.
- Keep extra task fields in the sample dict if `PackInputs` or `PackMultiTaskInputs` will consume them later.

## Transform pattern

Use `BaseTransform` for pipeline steps.

```python
from mmcv.transforms import BaseTransform
from mmpretrain.registry import TRANSFORMS

@TRANSFORMS.register_module()
class MyTransform(BaseTransform):
    def transform(self, results):
        return results
```

Pipeline rule of thumb:

- `LoadImageFromFile` first when the sample only carries `img_path`.
- Image augmentation in the middle.
- `PackInputs` or `PackMultiTaskInputs` last.

## Model, head, and loss pattern

Register every model-side component with `MODELS`.

```python
import torch.nn as nn
from mmpretrain.registry import MODELS

@MODELS.register_module()
class MyBackbone(nn.Module):
    ...
```

```python
from mmengine.model import BaseModule
from mmpretrain.registry import MODELS

@MODELS.register_module()
class MyHead(BaseModule):
    ...
```

```python
import torch.nn as nn
from mmpretrain.registry import MODELS

@MODELS.register_module()
class MyLoss(nn.Module):
    ...
```

Common model config shape:

```python
model = dict(
    type='ImageClassifier',
    backbone=dict(type='MyBackbone', ...),
    neck=dict(type='MyNeck', ...),
    head=dict(type='MyHead', loss=dict(type='MyLoss', ...)),
)
```

## Metric pattern

Use `BaseMetric` and implement both `process()` and `compute_metrics()`.

```python
from mmengine.evaluator import BaseMetric
from mmpretrain.registry import METRICS

@METRICS.register_module()
class MyMetric(BaseMetric):
    def process(self, data_batch, data_samples):
        ...

    def compute_metrics(self, results):
        return {'score': ...}
```

Config entry point:

```python
val_evaluator = dict(type='MyMetric')
```

## Hook and optimizer pattern

Hooks and optimizers follow the same registration rule.

- Hooks go through `HOOKS`.
- Optimizers go through `OPTIMIZERS`.
- Keep the config type names distinct from other packages when possible.
- If a custom hook or optimizer is not found, check that the module import actually ran.

Typical config entry points:

```python
custom_hooks = [dict(type='MyHook')]
optim_wrapper = dict(optimizer=dict(type='MyOptimizer', lr=1e-3))
```

## Project-module rules

Project code is not a separate registry. It just registers more classes into the same registry objects.

Use a project module when you need:

- a dataset that only belongs to one project,
- a metric that only one project evaluates,
- a hook or optimizer tuned for a custom experiment,
- a custom model component that should still be built through config.

Keep these rules in mind:

- Import the module before building configs.
- Prefer stable, unique type names.
- If two packages use the same type name, the active scope controls which one wins.
- The helper script in this skill tree can confirm registry visibility without building a dataset.
