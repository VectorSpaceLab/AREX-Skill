# MMYOLO extension patterns

Use these patterns when implementing or reviewing model-side MMYOLO extensions. They distill the repository's model design, replacement-backbone guidance, plugin guidance, custom project examples, assigner-visualization project, model tests, and installed API facts.

## Minimal custom module rule

Every registry extension needs three things:

1. A Python class/function decorated into the correct MMYOLO registry.
2. An import path that executes that decorator before registry build.
3. A config or builder call that uses the registered name under the correct default scope.

For standalone experiments, the caller normally initializes MMYOLO once:

```python
from mmyolo.utils import register_all_modules

register_all_modules()  # imports mmyolo modules and establishes DefaultScope('mmyolo')
```

For reusable extension packages, avoid calling `register_all_modules()` inside module import. Register the class with a decorator and let the caller or config own registration order and default scope.

## Add a dummy backbone or project module

A safe project-local pattern is:

```text
my_mmyolo_project/
  __init__.py
  backbones.py
  configs/
    yolov5_custom_backbone.py
```

`backbones.py`:

```python
from mmyolo.models import YOLOv5CSPDarknet
from mmyolo.registry import MODELS


@MODELS.register_module()
class DummyYOLOv5CSPDarknet(YOLOv5CSPDarknet):
    """Small wrapper that preserves the parent backbone contract."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
```

`__init__.py`:

```python
from .backbones import DummyYOLOv5CSPDarknet

__all__ = ['DummyYOLOv5CSPDarknet']
```

Config-side registration trigger:

```python
custom_imports = dict(imports=['my_mmyolo_project'], allow_failed_imports=False)
model = dict(backbone=dict(type='DummyYOLOv5CSPDarknet'))
```

If editing an inherited config, the same idea can be expressed by changing the inherited backbone type after the base config is loaded. Route the exact config mutation pattern to `config-customization`; this sub-skill owns only the registry/API side.

Checklist before relying on the custom backbone:

- The project package is importable on `PYTHONPATH` or installed in the environment.
- The class has been imported before `MODELS.build` looks up `DummyYOLOv5CSPDarknet`.
- The custom constructor accepts the arguments passed by the config.
- The forward output count, output strides, and channel counts still match the neck `in_channels` and head-module `in_channels`.
- If the custom class subclasses a MMYOLO backbone, preserve `out_indices`, `frozen_stages`, `norm_cfg`, `act_cfg`, `plugins`, `deepen_factor`, and `widen_factor` behavior unless you intentionally document a narrower contract.

## Replace a backbone with another OpenMMLab component

MMYOLO's registries inherit from MMEngine root registries, so components from sibling OpenMMLab projects can be built by prefix when imported and installed.

Typical pattern:

```python
custom_imports = dict(imports=['mmcls.models'], allow_failed_imports=False)

model = dict(
    backbone=dict(
        _delete_=True,
        type='mmcls.ConvNeXt',
        arch='tiny',
        out_indices=(1, 2, 3),
        init_cfg=dict(type='Pretrained', checkpoint='...', prefix='backbone.')),
    neck=dict(
        type='YOLOv5PAFPN',
        in_channels=[192, 384, 768],
        out_channels=[192, 384, 768]),
    bbox_head=dict(
        type='YOLOv5Head',
        head_module=dict(
            type='YOLOv5HeadModule',
            in_channels=[192, 384, 768])))
```

Rules:

- Use `_delete_=True` when replacing a whole inherited subtree that still contains incompatible old keys.
- Keep `neck.in_channels`, `neck.out_channels`, and `bbox_head.head_module.in_channels` synchronized with the replacement backbone's actual outputs.
- Import external registries explicitly (`custom_imports`) when MMYOLO does not import them for you.
- Use registry prefixes (`mmdet.ResNet`, `mmcls.ConvNeXt`, `mmselfsup.ResNet`, etc.) to disambiguate ownership.
- Do not assume external pretrained checkpoint URLs are available or suitable; checkpoint acquisition belongs to the user workflow and environment policy.

## Model design inheritance points

MMYOLO's YOLO-family code is organized around reusable base classes:

- `BaseBackbone`: subclasses implement `build_stem_layer()` and `build_stage_layer(stage_idx, setting)`. The inherited forward iterates the stem/stages and returns `tuple(outs)` selected by `out_indices`.
- `BaseYOLONeck`: subclasses implement `build_reduce_layer`, `build_upsample_layer`, `build_top_down_layer`, `build_downsample_layer`, `build_bottom_up_layer`, and `build_out_layer`. The inherited forward performs top-down and bottom-up feature fusion.
- Dense heads usually separate wrapper responsibilities from `head_module` architecture. The wrapper owns losses, coders, assigner behavior, and train/test result logic; the head module owns convolutional prediction layers.

Use inheritance when preserving an existing interface, and use a fresh registered class when the shape/forward contract changes enough that downstream configs and tests must be explicit.

## Plugin patterns

Backbone plugin configs have the form:

```python
model = dict(
    backbone=dict(
        plugins=[
            dict(
                cfg=dict(type='mmdet.DropBlock', drop_prob=0.1, block_size=3),
                stages=(False, False, True, True)),
            dict(
                cfg=dict(type='CBAM', reduce_ratio=16),
                stages=(False, True, True, True)),
        ]))
```

Rules from the implementation and tests:

- Each plugin entry must include `cfg`; `stages` is optional.
- When `stages` is present, its length must equal the backbone's number of stages.
- A `True` value inserts the plugin after that stage. With no `stages`, the plugin is applied to every stage.
- The plugin builder receives the stage's calculated `in_channels`; plugin classes must accept the channel argument used by MMEngine/MMCV plugin construction.
- Prefix plugin types from parent registries when needed (`mmdet.DropBlock`, `mmcv`/MMCV plugin aliases, etc.).
- MMYOLO's own `CBAM` is registered in `MODELS` and can be referenced by type after MMYOLO registrations are loaded.

## Custom dense head, loss, coder, or assigner

Choose the registry by where the object is built:

- Heads, head modules, losses, and many layers use `MODELS`.
- Coders, assigners, and task-specific utilities use `TASK_UTILS`.
- Dataset transforms use `TRANSFORMS`.

Example custom loss wrapper:

```python
from mmyolo.registry import MODELS


@MODELS.register_module()
class MyLoss(...):
    ...
```

Example custom assigner:

```python
from mmyolo.registry import TASK_UTILS


@TASK_UTILS.register_module()
class MyBatchAssigner(...):
    ...
```

Then import the module and reference it in the relevant config subtree, such as `loss_bbox=dict(type='MyLoss', ...)` or `train_cfg=dict(assigner=dict(type='MyBatchAssigner', ...))`.

When extending heads, inspect the parent head's expected attributes before overriding methods. For example, assignment-visualization extensions subclass YOLO-family heads and add `assign(...)` / `assign_by_gt_and_feat(...)` methods while preserving the original head's loss and forward contracts.

## Custom dataset transforms and preprocessors

Dataset transforms should register into `TRANSFORMS`:

```python
from mmyolo.registry import TRANSFORMS


@TRANSFORMS.register_module()
class MyTransform:
    def __init__(self, ...):
        ...

    def transform(self, results):
        ...
```

Data preprocessors are model components and register into `MODELS`. Be careful with collate contracts:

- `YOLOv5DetDataPreprocessor` is designed to work with MMYOLO's YOLOv5 collate format in training.
- `PPYOLOEDetDataPreprocessor` expects list inputs in training mode.
- Batch random resize components mutate tensor and bbox scales, so the input data structure must match the preprocessor's assumptions.

Route dataset file layout, annotation conversion, and transform-pipeline validation to `data-tools`.

## Project-style extension pattern

The repository's project examples show two useful patterns:

- A minimal project can define a registered wrapper class, expose it in the project package, and import it from a custom config before changing the model subtree.
- A more involved project can register multiple components: detector subclass, head subclasses, and a visualizer subclass. The config imports those modules and swaps the detector/head types while a separate script uses the added methods.

For runtime skills, distill the project pattern instead of depending on project scripts. When creating a new project extension, keep the public contract narrow: registered classes, import path, config swap, and a tiny smoke check that imports the project and asks the registry whether the new names exist.

## `switch_to_deploy` decision pattern

Installed utility:

```python
from mmyolo.utils import switch_to_deploy

model.eval()
switch_to_deploy(model)
```

Use it when all of these are true:

- The model has already been trained or checkpoint weights have already been loaded.
- The model contains MMYOLO `RepVGGBlock` modules, common in RepVGG-style YOLOv6/YOLOv7/PPYOLOE components.
- The next operation is inference, benchmarking, or export, not further training.
- You accept that the function mutates modules by fusing branches, deleting training-time branch attributes, and setting block `deploy=True`.

Do not use it when:

- You intend to resume training or fine-tune the same model object.
- The model has no `RepVGGBlock`; it will only print a success message and change nothing meaningful.
- You need a non-mutating comparison; make or load a separate model instance first.

A safe review snippet for a model object is:

```python
from mmyolo.models import RepVGGBlock

rep_blocks = [m for m in model.modules() if isinstance(m, RepVGGBlock)]
print(len(rep_blocks), 'RepVGGBlock modules')
```

If the count is zero, route export/inference concerns to the appropriate sub-skill instead of forcing deploy conversion.
