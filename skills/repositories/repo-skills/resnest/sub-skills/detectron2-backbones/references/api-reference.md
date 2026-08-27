# Detectron2 ResNeSt API Reference

This reference distills the ResNeSt-specific Detectron2 surface. Detectron2 itself is optional; importing `resnest.d2` requires a compatible Detectron2 installation and compiled Detectron2 operators.

## Required import and merge order

Use this order in any Detectron2 launcher or notebook:

```python
from detectron2.config import get_cfg
from resnest.d2 import add_resnest_config  # also imports/registers ResNeSt backbones

cfg = get_cfg()
add_resnest_config(cfg)          # add ResNeSt fields and defaults first
cfg.merge_from_file("path/to/config.yaml")  # optional user config
cfg.merge_from_list([            # optional CLI-style overrides
    "MODEL.BACKBONE.NAME", "build_resnest_fpn_backbone",
])
cfg.freeze()
```

Why the order matters:

1. `resnest.d2` imports the backbone builders, registering them with Detectron2's `BACKBONE_REGISTRY`.
2. `add_resnest_config(cfg)` creates/overrides the ResNeSt-specific `MODEL.RESNETS` keys before YAML or `KEY VALUE` options are merged.
3. Model construction can then resolve `MODEL.BACKBONE.NAME: "build_resnest_fpn_backbone"`.

## Public entry points

| Entry point | Detectron2 role | Use it when | Notes |
|---|---|---|---|
| `resnest.d2.add_resnest_config(cfg)` | Config extension | Preparing a Detectron2 `CfgNode` that may contain ResNeSt backbone fields. | Mutates `cfg.MODEL.RESNETS` defaults; call before `merge_from_file` and `merge_from_list`. |
| `resnest.d2.build_resnest_backbone(cfg, input_shape)` | `BACKBONE_REGISTRY` builder | Building a bottom-up ResNeSt backbone without FPN. | Registered as `build_resnest_backbone`; returns a Detectron2 `Backbone` whose outputs are selected by `MODEL.RESNETS.OUT_FEATURES`. |
| `resnest.d2.build_resnest_fpn_backbone(cfg, input_shape)` | `BACKBONE_REGISTRY` builder | COCO R-CNN/FPN recipes and most detection/instance/panoptic uses. | Registered as `build_resnest_fpn_backbone`; wraps `build_resnest_backbone` in an FPN with `MODEL.FPN.IN_FEATURES`, `OUT_CHANNELS`, `NORM`, and `FUSE_TYPE`. |
| `resnest.d2.splat.SplAtConv2d` | Split-attention 3x3 convolution | Standard ResNeSt bottleneck blocks when `MODEL.RESNETS.RADIX > 1` and DCN is off. | Uses Detectron2 `Conv2d`/`get_norm`; attention is over radix splits within cardinality groups. |
| `resnest.d2.splat.SplAtConv2d_dcn` | Split-attention deformable convolution | DCN ResNeSt bottleneck blocks when a stage is enabled in `MODEL.RESNETS.DEFORM_ON_PER_STAGE`. | Wraps Detectron2 `DeformConv` or `ModulatedDeformConv`; needs Detectron2 compiled ops that support the selected torch/CUDA build. |

## ResNeSt config fields added by `add_resnest_config`

| Field | Default | ResNeSt meaning | Practical check |
|---|---:|---|---|
| `MODEL.RESNETS.STRIDE_IN_1X1` | `False` | Put stride on the 3x3 bottleneck conv, matching C2/Torch-style ResNeSt behavior rather than original MSRA ResNet. | Keep `False` for ResNeSt configs. |
| `MODEL.RESNETS.DEEP_STEM` | `True` | Replace the single 7x7 stem with three 3x3 convs. | ResNeSt builders also force deep stem when `RADIX > 1`. |
| `MODEL.RESNETS.AVD` | `True` | Apply average downsampling after conv2 in bottleneck blocks when stride is greater than one. | Should be paired with `STRIDE_IN_1X1: False`. |
| `MODEL.RESNETS.AVG_DOWN` | `True` | Use average pooling in the residual shortcut when downsampling. | ResNeSt builders also enable it when `RADIX > 1`. |
| `MODEL.RESNETS.RADIX` | `2` | Number of split-attention branches. | `2` selects ResNeSt split-attention; `1` falls back toward ordinary bottleneck conv behavior. |
| `MODEL.RESNETS.BOTTLENECK_WIDTH` | `64` | Width multiplier used with `WIDTH_PER_GROUP`/`NUM_GROUPS` to compute the grouped bottleneck width. | Keep `64` for the released ResNeSt recipes unless intentionally designing an ablation. |

## Backbone builder details that affect configs

- Supported depths in the builder include `18`, `34`, `50`, `101`, `152`, `200`, and `269`; the distilled COCO recipes use ResNeSt-50, ResNeSt-101, and ResNeSt-200.
- Stem width is depth-dependent: depth 50 uses `32`; depths 101, 152, 200, and 269 use `64`.
- Stage block counts include `50: [3, 4, 6, 3]`, `101: [3, 4, 23, 3]`, and `200: [3, 24, 36, 3]`.
- The builder also reads `MODEL.RESNETS.NUM_GROUPS` and `MODEL.RESNETS.WIDTH_PER_GROUP` from the active Detectron2 config. The released ResNeSt COCO recipes keep the standard Detectron2 cardinality/width defaults unless a recipe explicitly changes them.
- FPN recipes should keep `MODEL.RESNETS.OUT_FEATURES` and `MODEL.FPN.IN_FEATURES` aligned as `['res2', 'res3', 'res4', 'res5']` unless intentionally changing the pyramid.
- Standard ResNeSt bottlenecks use `SplAtConv2d` when `RADIX > 1`; DCN bottlenecks use `SplAtConv2d_dcn` in stages enabled by `DEFORM_ON_PER_STAGE`.
- DCN recipes use `DEFORM_ON_PER_STAGE: [False, True, True, True]`, `DEFORM_MODULATED: True`, and `DEFORM_NUM_GROUPS: 2` to activate modulated deformable conv in Res3/Res4/Res5.

## Minimal self-contained ResNeSt/FPN config fragment

Use this fragment as the ResNeSt-specific part of a larger Detectron2 R-CNN/FPN config:

```yaml
MODEL:
  BACKBONE:
    NAME: "build_resnest_fpn_backbone"
  RESNETS:
    DEPTH: 50
    OUT_FEATURES: ["res2", "res3", "res4", "res5"]
    STRIDE_IN_1X1: False
    DEEP_STEM: True
    AVD: True
    AVG_DOWN: True
    RADIX: 2
    BOTTLENECK_WIDTH: 64
    NORM: "SyncBN"
  FPN:
    IN_FEATURES: ["res2", "res3", "res4", "res5"]
    NORM: "SyncBN"
  PIXEL_MEAN: [123.68, 116.779, 103.939]
  PIXEL_STD: [58.393, 57.12, 57.375]
INPUT:
  FORMAT: "RGB"
```

For single-GPU, CPU-only, or debugging environments where SyncBN is not supported, change all matching `NORM: "SyncBN"` fields to a norm supported by that environment, such as `"BN"` or `"FrozenBN"`; this changes training/evaluation behavior and should not be treated as reproducing the released metrics.
