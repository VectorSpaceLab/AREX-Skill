# Customization Recipes

## Choose the Extension Pattern

Use source-tree extension when contributing to MMSegmentation itself:

1. Add a module file under the matching importable package for the extension point, such as a `models/backbones`, `models/decode_heads`, `models/losses`, `evaluation/metrics`, or `engine/optimizers` package in the project being edited.
2. Decorate the class or function wrapper with the right registry decorator.
3. Import it from the nearest package `__init__.py` so the decorator executes when MMSegmentation imports that package.
4. Reference the registered `type` in config.

Use external/project extension when building on an installed MMSegmentation package:

1. Put custom code in an importable Python package or project directory.
2. Register classes with MMSegmentation registries, not ad-hoc factories.
3. Add config-level imports, for example `custom_imports = dict(imports=['my_project.models'], allow_failed_imports=False)`.
4. Ensure the project package is importable via normal packaging or `PYTHONPATH` before running train/test/build commands.
5. Smoke-check with `scripts/inspect_registry.py --imports my_project.models --models MyHead`.

## Registry Basics

Model-family components use `MODELS`:

```python
from mmseg.registry import MODELS

@MODELS.register_module()
class MyBackbone(nn.Module):
    ...
```

Metric components use `METRICS`:

```python
from mmseg.registry import METRICS

@METRICS.register_module()
class MyMetric(BaseMetric):
    ...
```

Optimizer extensions use optimizer registries:

```python
from mmseg.registry import OPTIMIZERS, OPTIM_WRAPPER_CONSTRUCTORS
```

Configuration can then use the registered names:

```python
custom_imports = dict(imports=['my_project.models'], allow_failed_imports=False)
default_scope = 'mmseg'
model = dict(type='EncoderDecoder', backbone=dict(type='MyBackbone'), ...)
```

`register_all_modules(init_default_scope=True)` is useful for scripts because it imports MMSegmentation modules and sets the default scope to `mmseg`. If composing with other OpenMMLab packages, be explicit about scope and imports to avoid looking in the wrong registry node.

## Add a Backbone

Minimum contract:

- Subclass `nn.Module` or an MMEngine module base.
- Register with `@MODELS.register_module()`.
- Accept config parameters in `__init__`.
- Implement `forward(self, x)` and return a tuple/list of feature maps expected by the neck/head.
- Provide `init_weights()` or `init_cfg` behavior if pretrained initialization is required.

Config checklist:

- `backbone=dict(type='MyBackbone', ...)`.
- Decode head `in_channels`, `in_index`, and `input_transform` match the feature maps.
- If using `pretrained` or `init_cfg`, do not set conflicting pretrained fields at both segmentor and backbone level.

Common failure modes:

- Head expects four feature stages but backbone returns one tensor.
- Feature channels do not match `decode_head.in_channels`.
- Feature strides do not match crop size or head assumptions.
- The module registered successfully but was not imported in the train/test process.

## Add a Decode Head

Minimum contract:

- Subclass `BaseDecodeHead` for ordinary semantic segmentation heads.
- Register with `@MODELS.register_module()`.
- Let `BaseDecodeHead.__init__` consume common arguments such as `in_channels`, `channels`, `num_classes`, `in_index`, `input_transform`, `loss_decode`, and `align_corners`.
- Implement `forward(self, inputs)`; use `self._transform_inputs(inputs)` to respect `in_index`/`input_transform`.
- Return raw segmentation logits from `forward`; `BaseDecodeHead.loss()` and `predict()` handle loss/prediction wrappers.

Tiny pattern:

```python
from mmseg.models.decode_heads.decode_head import BaseDecodeHead
from mmseg.registry import MODELS

@MODELS.register_module()
class MyHead(BaseDecodeHead):
    def forward(self, inputs):
        x = self._transform_inputs(inputs)
        return self.cls_seg(x)
```

Config checklist:

- `decode_head=dict(type='MyHead', in_channels=..., channels=..., num_classes=..., in_index=..., loss_decode=...)`.
- Set `input_transform='resize_concat'` or `'multiple_select'` only when `in_channels` and `in_index` are sequences.
- Keep `align_corners` consistent with the selected model family/crop-size convention.
- For binary segmentation, decide whether `out_channels=1` and threshold behavior are intended.

## Add a Loss

Minimum contract:

- Register the loss class with `@MODELS.register_module()`.
- Subclass `nn.Module`.
- Implement `forward(pred, target, weight=None, avg_factor=None, reduction_override=None, **kwargs)` when following built-in loss style.
- Return a tensor loss. If it should participate in normal log/loss parsing, name it with a `loss_` prefix through the class `loss_name` or the key returned by the head.

Config patterns:

```python
loss_decode=dict(type='MyLoss', loss_weight=1.0)
```

or multiple losses:

```python
loss_decode=[
    dict(type='CrossEntropyLoss', loss_name='loss_ce', loss_weight=1.0),
    dict(type='DiceLoss', loss_name='loss_dice', loss_weight=0.5),
]
```

Check label shape and ignore behavior before blaming registry/build errors. Cross-entropy-style losses commonly expect logits shaped `[N, C, H, W]` and labels shaped `[N, H, W]`; binary/mask/depth losses may differ.

## Add a Segmentor

Use a custom segmentor only when a new algorithm cannot fit `EncoderDecoder` or `CascadeEncoderDecoder` composition.

Minimum contract:

- Subclass `BaseSegmentor`.
- Register with `@MODELS.register_module()`.
- Implement `loss()`, `predict()`, and `_forward()` for the three forward modes.
- Build internal components with `MODELS.build(...)`.
- Return losses as a dict and predictions as `SegDataSample` lists with expected fields.

Prefer using custom backbones/heads/losses with `EncoderDecoder` whenever possible; it preserves runner, inference, and test-time behavior.

## Add a Data Preprocessor

Register a custom data preprocessor into `MODELS` and set it under `model.data_preprocessor`. It should behave like an MMEngine data preprocessor: accept the collated data dict, move tensors to the target device, and return data in the format expected by the segmentor.

Only customize this layer when padding/normalization/channel conversion/batch augmentation cannot be represented by `SegDataPreProcessor` arguments.

## Add a Metric

Minimum contract:

- Subclass `mmengine.evaluator.BaseMetric`.
- Register with `@METRICS.register_module()`.
- Implement `process(self, data_batch, data_samples)` to append processed per-batch results to `self.results`.
- Implement `compute_metrics(self, results)` to return a metric dictionary.
- Reference it in `val_evaluator` and `test_evaluator`.

Config example:

```python
custom_imports = dict(imports=['my_project.metrics'], allow_failed_imports=False)
val_evaluator = dict(type='MyMetric', arg1='value')
test_evaluator = dict(type='MyMetric', arg1='value')
```

## Add Optimizers, Constructors, and Schedulers

Use MMEngine optimizer wrappers unless you need a new optimizer class or parameter grouping strategy.

- Custom optimizer class: register into `OPTIMIZERS`, then set `optim_wrapper.optimizer.type`.
- Custom optimizer constructor: subclass `DefaultOptimWrapperConstructor` or a compatible base, register into `OPTIM_WRAPPER_CONSTRUCTORS`, then set `optim_wrapper.constructor`.
- Parameter schedulers: register scheduler classes into `PARAM_SCHEDULERS` and configure `param_scheduler`.

Example optimizer config shape:

```python
optim_wrapper = dict(
    type='OptimWrapper',
    optimizer=dict(type='MyOptimizer', lr=0.01),
    clip_grad=None)
```

Example constructor shape:

```python
optim_wrapper = dict(
    type='OptimWrapper',
    optimizer=dict(type='AdamW', lr=0.0001, weight_decay=0.05),
    constructor='MyOptimizerConstructor',
    paramwise_cfg=dict(...))
```

Layer-wise/stage-wise learning-rate decay is sensitive to backbone naming. Validate parameter groups on a toy model or one dry build before full training.

## Add or Use a Project

MMSegmentation project extensions are intentionally separate from the core package. Use this pattern:

- Put project Python modules in an importable package under the project directory.
- Register custom components into MMSegmentation registries.
- Add `custom_imports` in configs, such as `custom_imports = dict(imports=['my_project.models'], allow_failed_imports=False)`.
- Ensure the project directory or package root is importable before launching commands.
- Document prerequisites, commands, results, and whether weights are converted or trained from scratch.

Treat project extensions as optional. They often require extra packages, custom import paths, converted weights, or hardware-specific dependencies.

## Smoke Tests

Run these before expensive training:

1. `python skills/mmsegmentation/sub-skills/model-customization/scripts/inspect_registry.py --models MyType --imports my_project.models`
2. Build the config with a tiny dummy input or a unit-test-like forward if dependencies are available.
3. If changing an optimizer constructor, build the optimizer wrapper and inspect parameter groups.
4. If adding a loss/head, test one loss forward with synthetic logits and labels that match the intended shapes.

## Difficult Synthetic Usability Cases

- Custom decode head case: create a minimal external package with `@MODELS.register_module() class ToyHead(BaseDecodeHead)`, import it through `custom_imports`, build a small `EncoderDecoder` config, and verify `inspect_registry.py --models ToyHead EncoderDecoder` reports both as registered.
- Registry recovery case: intentionally omit `custom_imports` for a registered custom class, capture the missing registry entry, add `custom_imports`, rerun inspection, and confirm the model build proceeds to the next shape/config validation stage.

## Provenance Notes

These recipes distill MMSegmentation's public customization guides, project-extension examples, core registry behavior, and test-backed model component patterns. Treat original repository paths as evidence already incorporated here, not as files a future agent must open while using the skill.
