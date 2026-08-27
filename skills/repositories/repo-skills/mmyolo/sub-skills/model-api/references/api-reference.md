# MMYOLO model API reference

This reference summarizes MMYOLO 0.6.0 public registry and component facts for safe extension work. It is intentionally API-focused: choose concrete training/inference/config workflows through the neighboring sub-skills.

## Registry initialization and default scope

MMYOLO uses MMEngine registries. Before building modules directly from config dictionaries, initialize registrations:

```python
from mmyolo.utils import register_all_modules
from mmyolo.registry import MODELS

register_all_modules()  # sets the default scope to "mmyolo" when needed
model = MODELS.build(dict(type='YOLODetector', ...))
```

Installed signature:

```text
mmyolo.utils.register_all_modules(init_default_scope: bool = True)
```

Behavior to preserve:

- Imports MMDetection engine/visualization and MMYOLO datasets/engine/models so decorators populate registries.
- With `init_default_scope=True`, creates or switches the current MMEngine `DefaultScope` to `mmyolo`.
- If another default scope is active, it warns before forcing a new `mmyolo` scope instance.
- Use `init_default_scope=False` when you only need registration side effects and the caller intentionally owns the active default scope.

For config-driven custom modules, use `custom_imports` or otherwise import the module before registry build. A class decorated with `@MODELS.register_module()` is not visible by string name until Python has imported the defining module.

## MMYOLO registry objects

The public registry module defines child registries rooted in MMEngine. The most common extension targets are `MODELS`, `DATASETS`, `TRANSFORMS`, `TASK_UTILS`, `VISUALIZERS`, `HOOKS`, and optimizer/runtime registries.

| Registry | Scope | Typical use | Location package |
| --- | --- | --- | --- |
| `MODELS` | model | detectors, backbones, necks, heads, losses, data preprocessors, plugins, wrappers | `mmyolo.models` |
| `DATASETS` | dataset | dataset classes such as COCO/VOC/DOTA/pose wrappers | `mmyolo.datasets` |
| `TRANSFORMS` | transform | pipeline transforms and mix-image augmentations | `mmyolo.datasets.transforms` |
| `TASK_UTILS` | task util | assigners, bbox coders, batch shape policies | `mmyolo.models` and dataset utilities |
| `VISUALIZERS` | visualizer | visualizers and project visualizer extensions | `mmyolo.utils` |
| `VISBACKENDS` | vis_backend | visualization backends | `mmyolo.utils` |
| `HOOKS`, `LOOPS`, `RUNNERS`, `RUNNER_CONSTRUCTORS` | runtime | MMEngine runner behavior | `mmyolo.engine` |
| `OPTIMIZERS`, `OPTIM_WRAPPERS`, `OPTIM_WRAPPER_CONSTRUCTORS`, `PARAM_SCHEDULERS` | optimization | optimizer and scheduler extensions | `mmyolo.engine.optimizers` |
| `METRICS` | metric | evaluator metrics | `mmyolo.engine` |
| `MODEL_WRAPPERS`, `WEIGHT_INITIALIZERS`, `DATA_SAMPLERS` | wrappers/init/sampling | advanced framework integration | model/dataset packages |

Use prefixes such as `mmdet.ResNet` when intentionally building a parent-registry component from another OpenMMLab package. Import external package modules first when their decorators are not imported by MMYOLO itself.

## Detector and model composition

Installed signature:

```text
YOLODetector(backbone, neck, bbox_head, train_cfg=None, test_cfg=None, data_preprocessor=None, init_cfg=None, use_syncbn=True)
```

`YOLODetector` subclasses MMDetection's single-stage detector. It builds three primary config subtrees through registries:

- `backbone`: feature extractor. MMYOLO backbones usually expose `deepen_factor`, `widen_factor`, `out_indices`, `frozen_stages`, `norm_cfg`, `act_cfg`, and optional `plugins`.
- `neck`: feature pyramid/fusion module. MMYOLO YOLO necks derive from `BaseYOLONeck`, taking `in_channels`, `out_channels`, depth/width factors, normalization, activation, and construction hooks.
- `bbox_head`: dense prediction/loss module. MMYOLO separates many heads into a wrapper head and a nested `head_module` for architecture-specific forward logic.

`use_syncbn=True` only converts to SyncBatchNorm when the distributed world size is greater than 1. On normal single-process CPU inspection it has no effect.

## Backbones

Core public names imported by `mmyolo.models.backbones` include:

```text
BaseBackbone, YOLOv5CSPDarknet, YOLOv8CSPDarknet, YOLOXCSPDarknet,
CSPNeXt, YOLOv6EfficientRep, YOLOv6CSPBep, YOLOv7Backbone,
PPYOLOECSPResNet
```

Installed signature facts:

```text
YOLOv5CSPDarknet(arch='P5', plugins=None, deepen_factor=1.0, widen_factor=1.0, input_channels=3, out_indices=(2, 3, 4), frozen_stages=-1, norm_cfg={'type': 'BN', 'momentum': 0.03, 'eps': 0.001}, act_cfg={'type': 'SiLU', 'inplace': True}, norm_eval=False, init_cfg=None)
YOLOv8CSPDarknet(arch='P5', last_stage_out_channels=1024, plugins=None, deepen_factor=1.0, widen_factor=1.0, input_channels=3, out_indices=(2, 3, 4), frozen_stages=-1, norm_cfg={'type': 'BN', 'momentum': 0.03, 'eps': 0.001}, act_cfg={'type': 'SiLU', 'inplace': True}, norm_eval=False, init_cfg=None)
YOLOXCSPDarknet(arch='P5', plugins=None, deepen_factor=1.0, widen_factor=1.0, input_channels=3, out_indices=(2, 3, 4), frozen_stages=-1, use_depthwise=False, spp_kernal_sizes=(5, 9, 13), norm_cfg={'type': 'BN', 'momentum': 0.03, 'eps': 0.001}, act_cfg={'type': 'SiLU', 'inplace': True}, norm_eval=False, init_cfg=None)
CSPNeXt(arch='P5', deepen_factor=1.0, widen_factor=1.0, input_channels=3, out_indices=(2, 3, 4), frozen_stages=-1, plugins=None, use_depthwise=False, expand_ratio=0.5, arch_ovewrite=None, channel_attention=True, conv_cfg=None, norm_cfg={'type': 'BN'}, act_cfg={'type': 'SiLU', 'inplace': True}, norm_eval=False, init_cfg={'type': 'Kaiming', ...})
```

BaseBackbone construction notes:

- P5-style backbones use a stem plus four stages; P6-style designs use a stem plus five stages.
- Subclasses implement `build_stem_layer()` and `build_stage_layer(stage_idx, setting)`; the inherited forward returns a tuple of outputs whose indices match `out_indices`.
- `frozen_stages` must be in `[-1, num_stages]`; tests assert out-of-range values raise.
- `norm_eval=True` keeps normalization layers in eval mode during training.
- `plugins` are appended after selected stages; see [extension patterns](extension-patterns.md#plugin-patterns).

When replacing a backbone with an MMDetection/MMClassification/MMSelfSup/timm-backed component, make the neck `in_channels`, neck `out_channels`, and head-module `in_channels` match the replacement backbone outputs.

## Necks

Core public names imported by `mmyolo.models.necks` include:

```text
BaseYOLONeck, YOLOv5PAFPN, YOLOv8PAFPN, YOLOXPAFPN, CSPNeXtPAFPN,
YOLOv6RepPAFPN, YOLOv6CSPRepPAFPN, YOLOv6RepBiPAFPN,
YOLOv6CSPRepBiPAFPN, YOLOv7PAFPN, PPYOLOECSPPAFPN
```

BaseYOLONeck construction notes:

- Requires `in_channels` and `out_channels`, plus depth/width, normalization, activation, and optional `freeze_all`.
- Subclasses implement `build_reduce_layer`, `build_upsample_layer`, `build_top_down_layer`, `build_downsample_layer`, `build_bottom_up_layer`, and `build_out_layer`.
- The forward path asserts `len(inputs) == len(in_channels)`; shape or channel mismatches normally originate in the backbone/neck/head config relationship.

## Dense heads, head modules, and losses

Core public dense-head names include:

```text
YOLOv5Head, YOLOv5HeadModule, YOLOv5InsHead, YOLOv5InsHeadModule,
YOLOv6Head, YOLOv6HeadModule, YOLOv7Head, YOLOv7HeadModule,
YOLOv7p6HeadModule, YOLOv8Head, YOLOv8HeadModule, YOLOXHead,
YOLOXHeadModule, YOLOXPoseHead, YOLOXPoseHeadModule, RTMDetHead,
RTMDetSepBNHeadModule, RTMDetInsSepBNHead, RTMDetInsSepBNHeadModule,
RTMDetRotatedHead, RTMDetRotatedSepBNHeadModule, PPYOLOEHead,
PPYOLOEHeadModule
```

Installed signature facts for common heads:

```text
YOLOv5Head(head_module, prior_generator={'type': 'mmdet.YOLOAnchorGenerator', ...}, bbox_coder={'type': 'YOLOv5BBoxCoder'}, loss_cls={'type': 'mmdet.CrossEntropyLoss', ...}, loss_bbox={'type': 'IoULoss', 'iou_mode': 'ciou', 'bbox_format': 'xywh', ...}, loss_obj={'type': 'mmdet.CrossEntropyLoss', ...}, prior_match_thr=4.0, near_neighbor_thr=0.5, ignore_iof_thr=-1.0, obj_level_weights=[4.0, 1.0, 0.4], train_cfg=None, test_cfg=None, init_cfg=None)
YOLOv5HeadModule(num_classes, in_channels, widen_factor=1.0, num_base_priors=3, featmap_strides=(8, 16, 32), init_cfg=None)
YOLOv8Head(head_module, prior_generator={'type': 'mmdet.MlvlPointGenerator', 'offset': 0.5, 'strides': [8, 16, 32]}, bbox_coder={'type': 'DistancePointBBoxCoder'}, loss_cls={'type': 'mmdet.CrossEntropyLoss', ...}, loss_bbox={'type': 'IoULoss', 'iou_mode': 'ciou', 'bbox_format': 'xyxy', ...}, loss_dfl={'type': 'mmdet.DistributionFocalLoss', ...}, train_cfg=None, test_cfg=None, init_cfg=None)
YOLOv8HeadModule(num_classes, in_channels, widen_factor=1.0, num_base_priors=1, featmap_strides=(8, 16, 32), reg_max=16, norm_cfg={'type': 'BN', 'momentum': 0.03, 'eps': 0.001}, act_cfg={'type': 'SiLU', 'inplace': True}, init_cfg=None)
RTMDetHead(head_module, prior_generator={'type': 'mmdet.MlvlPointGenerator', 'offset': 0, 'strides': [8, 16, 32]}, bbox_coder={'type': 'DistancePointBBoxCoder'}, loss_cls={'type': 'mmdet.QualityFocalLoss', ...}, loss_bbox={'type': 'mmdet.GIoULoss', 'loss_weight': 2.0}, train_cfg=None, test_cfg=None, init_cfg=None)
RTMDetSepBNHeadModule(num_classes, in_channels, widen_factor=1.0, num_base_priors=1, feat_channels=256, stacked_convs=2, featmap_strides=[8, 16, 32], share_conv=True, pred_kernel_size=1, conv_cfg=None, norm_cfg={'type': 'BN'}, act_cfg={'type': 'SiLU', 'inplace': True}, init_cfg=None)
```

Model-design guidance:

- MMYOLO's `head_module` pattern keeps architecture-specific forward layers inside the nested module while the head wrapper owns losses, assigners/coders, and train/test logic.
- Many losses are registry-built through `MODELS`; e.g. installed facts confirm `IoULoss(iou_mode='ciou', bbox_format='xywh', eps=1e-07, reduction='mean', loss_weight=1.0, return_iou=True)` and `bbox_overlaps(pred, target, iou_mode='ciou', bbox_format='xywh', siou_theta=4.0, eps=1e-07)`.
- Use MMDetection loss prefixes (`mmdet.CrossEntropyLoss`, `mmdet.GIoULoss`, etc.) when the loss class is owned by MMDetection.

## Task modules

`TASK_UTILS` owns coders, assigners, and related task utilities.

Installed signature fact:

```text
YOLOv5BBoxCoder(use_box_type: bool = False, **kwargs)
```

Core public names imported by `mmyolo.models.task_modules` include `YOLOv5BBoxCoder`, `YOLOXBBoxCoder`, `BatchATSSAssigner`, and `BatchTaskAlignedAssigner`; additional assigners/coders are registered from task-module subpackages. In configs, these usually appear under `bbox_coder` or `train_cfg=dict(assigner=...)` rather than as top-level models.

## Data preprocessors and dataset/transform APIs

MMYOLO registers data preprocessors in `MODELS`, datasets in `DATASETS`, and transforms in `TRANSFORMS`.

Common data preprocessors:

```text
YOLOv5DetDataPreprocessor
PPYOLOEDetDataPreprocessor
YOLOXBatchSyncRandomResize
PPYOLOEBatchRandomResize
```

Important preprocessor constraints:

- `YOLOv5DetDataPreprocessor` is intended to work with `mmyolo.datasets.utils.yolov5_collate` during training.
- `PPYOLOEDetDataPreprocessor` expects list inputs in training mode and a compatible collate function.
- Batch-random-resize augments assume specific tensor/list data formats; inspect their error messages before changing collate behavior.

Installed dataset/transform signature facts:

```text
YOLOv5CocoDataset(*args, **kwds)
YOLOv5KeepRatioResize(scale, keep_ratio=True, **kwargs)
LetterResize(scale, pad_val={'img': 0, 'mask': 0, 'seg': 255}, use_mini_pad=False, stretch_only=False, allow_scale_up=True, half_pad_param=False, **kwargs)
YOLOv5RandomAffine(max_rotate_degree=10.0, max_translate_ratio=0.1, scaling_ratio_range=(0.5, 1.5), max_shear_degree=2.0, border=(0, 0), border_val=(114, 114, 114), bbox_clip_border=True, min_bbox_size=2, min_area_ratio=0.1, use_mask_refine=False, max_aspect_ratio=20.0, resample_num=1000)
LoadAnnotations(mask2bbox=False, poly2mask=False, merge_polygons=True, **kwargs)
Mosaic(img_scale=(640, 640), center_ratio_range=(0.5, 1.5), bbox_clip_border=True, pad_val=114.0, pre_transform=None, prob=1.0, use_cached=False, max_cached_images=40, random_pop=True, max_refetch=15)
Mosaic9(img_scale=(640, 640), bbox_clip_border=True, pad_val=114.0, pre_transform=None, prob=1.0, use_cached=False, max_cached_images=50, random_pop=True, max_refetch=15)
YOLOv5MixUp(alpha=32.0, beta=32.0, pre_transform=None, prob=1.0, use_cached=False, max_cached_images=20, random_pop=True, max_refetch=15)
```

Route dataset file formats, converters, annotation validation, and data-pipeline recipes to `data-tools`; keep this reference for extension API names and registration behavior.

## Plugins and layers

Plugin support is implemented through backbone `plugins` arguments and MMEngine/MMCV model building. MMYOLO's own plugin module includes `CBAM` registered in `MODELS`; docs also describe using `GeneralizedAttention`, `NonLocal2d`, and `ContextBlock` plugin configs from the OpenMMLab stack.

Common deploy-capable layer:

```text
RepVGGBlock(in_channels, out_channels, kernel_size=3, stride=1, padding=1, dilation=1, groups=1, padding_mode='zeros', norm_cfg={'type': 'BN', 'momentum': 0.03, 'eps': 0.001}, act_cfg={'type': 'ReLU', 'inplace': True}, use_se=False, use_alpha=False, use_bn_first=True, deploy=False)
```

Installed utility signature:

```text
mmyolo.utils.switch_to_deploy(model)
```

`switch_to_deploy` iterates through `model.modules()` and calls `switch_to_deploy()` only on MMYOLO `RepVGGBlock` instances. It fuses training branches into a re-parameterized conv, deletes training-time branch attributes, sets `deploy=True`, and is therefore appropriate for inference/export preparation, not for continued training.

## Registry inspection helper

Use the bundled helper when you need current registry contents instead of guessing names:

```bash
python scripts/inspect_mmyolo_registry.py --registry MODELS --contains YOLO --with-signatures --limit 30
python scripts/inspect_mmyolo_registry.py --registry DATASETS --registry TRANSFORMS --json
python scripts/inspect_mmyolo_registry.py --custom-import my_project.my_modules --contains Dummy
```

The helper reports module names and optional signatures without building models or touching datasets/checkpoints.
