# Customization Reference

This reference distills the extension patterns that matter for MMDetection3D customization work:
custom registries, custom datasets, custom transforms, custom model components, and runtime wiring.
Use it when you need to create a starter implementation or when a config must be adapted to a new
module layout.

## 1) Pick the right registry

| What you are adding | Registry | Typical base class or pattern | Common config slot |
| --- | --- | --- | --- |
| Backbones, necks, heads, losses, data preprocessors, fusion modules, visualizers, inferencers | `MODELS` | `BaseModule` or `nn.Module` | `model.*` |
| Dataset classes and dataset wrappers | `DATASETS` | `Det3DDataset` or `BaseDataset` | `train_dataloader.dataset`, `val_dataloader.dataset` |
| Data pipeline steps and test-time augmentation steps | `TRANSFORMS` | `BaseTransform` | `train_pipeline`, `test_pipeline`, `eval_pipeline` |
| Custom hooks | `HOOKS` | `Hook` | `custom_hooks`, `default_hooks` |
| Optimizers | `OPTIMIZERS` | `torch.optim.Optimizer` | `optim_wrapper.optimizer` |
| Optimizer wrapper constructors | `OPTIM_WRAPPER_CONSTRUCTORS` | `DefaultOptimWrapperConstructor` | `optim_wrapper` |
| Assigners, samplers, box coders, IoU calculators, voxel generators | `TASK_UTILS` | task-specific helper classes | nested inside model config |
| Metrics and evaluators | `METRICS`, `EVALUATOR` | metric / evaluator classes | `val_evaluator`, `test_evaluator` |
| Visualizers and visualizer backends | `VISUALIZERS`, `VISBACKENDS` | visualizer classes | `visualizer`, `vis_backends` |

The extension rule is simple: register the class, import the module, and wire the config to the
class name exactly.

## 2) Use module registration correctly

Typical pattern:

```python
from mmengine.model import BaseModule
from mmdet3d.registry import MODELS

@MODELS.register_module()
class CustomBlock(BaseModule):
    def __init__(self, in_channels: int, out_channels: int, init_cfg=None):
        super().__init__(init_cfg=init_cfg)
        self.in_channels = in_channels
        self.out_channels = out_channels

    def forward(self, x):
        return x
```

For transforms:

```python
from mmcv.transforms import BaseTransform
from mmdet3d.registry import TRANSFORMS

@TRANSFORMS.register_module()
class CustomTransform(BaseTransform):
    def transform(self, results: dict) -> dict:
        results['custom_flag'] = True
        return results
```

For datasets:

```python
from mmdet3d.datasets import Det3DDataset
from mmdet3d.registry import DATASETS

@DATASETS.register_module()
class CustomDataset(Det3DDataset):
    METAINFO = {'classes': ('Car', 'Pedestrian')}
```

For runtime helpers:

```python
from torch.optim import Optimizer
from mmdet3d.registry import OPTIMIZERS

@OPTIMIZERS.register_module()
class CustomOptimizer(Optimizer):
    ...
```

### Import rule

Use `custom_imports` for external modules or optional project packages:

```python
custom_imports = dict(
    imports=['my_extension_package'],
    allow_failed_imports=False)
```

Import the module or package that defines the registered class. Do **not** point `imports` at the
class object itself.

If the config is meant to build core-package objects and project objects together, keep the default
registry scope set to `mmdet3d` and use scoped names only when a dependency comes from another
package, such as `mmdet.FocalLoss` or `mmdet.L1Loss`.

## 3) Model-component patterns

### Common component kinds

- **Voxel encoder / middle encoder**: usually consumes points or voxels and returns feature tensors.
- **Backbone**: produces one or more feature maps.
- **Neck**: fuses multi-scale features and keeps channel counts consistent.
- **Head**: computes predictions and usually owns `loss` and `predict` logic.
- **Loss**: wraps a function or module and exposes a registry entry.
- **Assigners / coders / samplers**: live in `TASK_UTILS` and are often nested under train/test config.

### Shape and config coupling to check

- `in_channels` must match the tensor channel count coming from the previous stage.
- `out_channels` must match the channel count expected by the next stage.
- Voxel-based models must keep `point_cloud_range`, `voxel_size`, and any middle-encoder output
  shape in sync.
- Anchor-based heads must keep class count, anchor ranges, anchor sizes, and bbox coder settings
  aligned with the dataset.
- Multi-modal models often need extra augmentation or calibration keys; make sure the model and
  pipeline agree on what the packed inputs contain.

### Practical model starter advice

- Use `BaseModule` for components that need `init_cfg` or complex submodules.
- Use `nn.Module` for very small loss wrappers or utility layers.
- Keep `forward` signatures narrow and match the calling code in the chosen config family.
- When the module is only useful through a config, prefer a concise `__init__` plus a clear
  docstring over a large inheritance tree.

## 4) Dataset patterns

### When to subclass `Det3DDataset`

Use `Det3DDataset` when the dataset follows the standard 3D annotation flow and needs the common
meta handling, `box_type_3d`, and annotation parsing behavior.

Typical pieces to define:

- `METAINFO`: class names and any dataset-specific metadata.
- `parse_ann_info`: convert raw info into `gt_bboxes_3d`, `gt_labels_3d`, and related fields.
- `data_prefix`, `ann_file`, `modality`, `test_mode`, and `box_type_3d` in config.

### Dataset contract reminders

- Class order in `METAINFO['classes']` must match the order used in annotations and configs.
- Empty annotation cases should be handled explicitly.
- If the dataset is custom KITTI-style, make sure the annotation format, category names, and metric
  choice stay consistent.
- If images are involved, add the required camera calibration and image-prefix keys to the config.

### What this sub-skill does not do

This sub-skill does **not** generate raw data converters or dataset-download scripts. It assumes the
annotation/info files already exist and focuses on the dataset class and the config wiring.

## 5) Data-pipeline patterns

### Transform contract

Pipeline steps should accept and return a `results` dictionary.
They may add keys, update keys, or drop the sample by returning `None`.
A transform should preserve all keys that later steps still need.

The most common keys in custom 3D pipelines are:

- `points`
- `img`
- `gt_bboxes_3d`
- `gt_labels_3d`
- `pts_instance_mask`
- `pts_semantic_mask`
- `pcd_rotation`
- `pcd_rotation_angle`
- `pcd_scale_factor`
- `pcd_trans`
- `pcd_horizontal_flip`
- `pcd_vertical_flip`
- `transformation_3d_flow`
- `lidar_aug_matrix` or similar project-specific augmentation matrices

If a transform changes geometry, update the related augmentation metadata as well.
If a later packer such as `Pack3DDetInputs` consumes the result, keep the packed keys and meta keys
consistent with the pipeline output.

### Good custom-transform habits

- Keep the transform pure: mutate only the fields that belong to the sample.
- Make failure modes explicit with `assert` or a clear exception.
- Prefer simple, composable transforms over one large monolithic step.
- If the transform is project-specific, keep it in the project package and import it with
  `custom_imports`.

## 6) Runtime customization patterns

### Optimizer and scheduler wiring

Use `optim_wrapper` for the optimizer, parameter-wise settings, and gradient clipping.
Use `param_scheduler` for LR or momentum scheduling.
Use `custom_hooks` for custom epoch/iter logic.
Use `default_hooks` when a standard hook only needs a parameter tweak.

Example shape:

```python
optim_wrapper = dict(
    type='OptimWrapper',
    optimizer=dict(type='AdamW', lr=1e-4, weight_decay=0.05),
    paramwise_cfg=dict(custom_keys={'backbone': dict(lr_mult=0.1)}),
    clip_grad=dict(max_norm=0.01, norm_type=2))

custom_hooks = [dict(type='MyHook', priority='NORMAL')]
```

### Runtime notes that matter for extensions

- Custom optimizers belong in `OPTIMIZERS`.
- Fine-grained parameter grouping belongs in a custom optimizer-wrapper constructor.
- Hooks should be registered in `HOOKS` and then referenced by name in config.
- Visualization is usually controlled through `default_hooks.visualization`, `visualizer`, and
  `vis_backends`.

## 7) Minimal validation path

After scaffolding or editing an extension, do a short static pass first:

1. Confirm the module imports cleanly.
2. Confirm the class is registered in the intended registry.
3. Confirm the config uses the exact class name and the right registry scope.
4. Confirm channel counts, dataset classes, and pipeline keys line up.
5. Only then move to any native backend-specific test or demo.

## 8) Best-fit handoffs

- Dataset and raw-format conversion questions should move to the data-preparation sub-skill.
- Config family and model-zoo lookup questions should move to the configuration sub-skill.
- Train/test command construction should move to the training sub-skill.
- Project-specific setup and optional compiled extras belong in [Project extensions](projects.md).
