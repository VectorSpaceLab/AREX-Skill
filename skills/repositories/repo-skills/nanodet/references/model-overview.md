# Model overview

NanoDet is a config-driven one-stage anchor-free detector. The model family is assembled from a backbone, an optional neck/FPN, and a head.

## Core model assemblies

| Assembly | Backbone | Neck | Head | Notes |
| --- | --- | --- | --- | --- |
| `OneStageDetector` | one of the supported backbones | optional FPN / PAN / TAN / GhostPAN | `GFLHead`, `NanoDetHead`, or `SimpleConvHead` | Basic one-stage detection path |
| `NanoDetPlus` | one of the supported backbones | `GhostPAN` or another FPN family | `NanoDetPlusHead` + `aux_head` | NanoDet-Plus training path with auxiliary head and optional EMA |
| `GFL` | same as `OneStageDetector` | same as `OneStageDetector` | same as `OneStageDetector` | Deprecated alias; the build path warns and maps to `OneStageDetector` |

## Supported backbones

| Backbone | Useful config notes |
| --- | --- |
| `ResNet` | Standard residual backbone from the repo |
| `ShuffleNetV2` | Used by the default NanoDet / NanoDet-Plus configs |
| `GhostNet` | Lightweight alternative backbone |
| `MobileNetV2` | Lightweight alternative backbone |
| `EfficientNetLite` | Used by legacy configs |
| `CustomCspNet` | Custom CSP-style backbone |
| `RepVGG` | Needs deploy conversion for export / deployment |
| `TIMMWrapper` | Wraps any compatible `timm` backbone; requires `timm` at runtime |

## Supported necks / FPNs

| Neck | Notes |
| --- | --- |
| `FPN` | Standard feature pyramid |
| `PAN` | Lightweight PAN-style neck used in older configs |
| `TAN` | Transformer attention neck |
| `GhostPAN` | NanoDet-Plus default neck |

## Supported heads

| Head | Notes |
| --- | --- |
| `GFLHead` | Generalized Focal Loss head |
| `NanoDetHead` | Original NanoDet detection head |
| `NanoDetPlusHead` | NanoDet-Plus head with dynamic soft label assignment |
| `SimpleConvHead` | Auxiliary or simplified head used in NanoDet-Plus configs |

## Loss families used by the heads

| Loss | Notes |
| --- | --- |
| `QualityFocalLoss` | Classification loss used in GFL-style heads |
| `DistributionFocalLoss` | Distribution regression loss used with discrete regression bins |
| `GIoULoss` | Bounding-box loss used in the default configs |
| `IoULoss`, `BoundedIoULoss`, `DIoULoss`, `CIoULoss` | Additional IoU variants covered by the unit tests |

## Dataset families used by the configs

| Dataset | Notes |
| --- | --- |
| `CocoDataset` | COCO JSON annotation format |
| `XMLDataset` | VOC-style XML annotations converted to a COCO-like internal representation |
| `YoloDataset` | YOLO TXT annotations paired with nearby image files |

## Common config families

- NanoDet-Plus-M 320
- NanoDet-Plus-M 416
- NanoDet-Plus-M-1.5x 320
- NanoDet-Plus-M-1.5x 416
- Custom XML dataset config
- ConvNeXt NanoDet-Plus config
- Legacy v0.x configs for older NanoDet / NanoDet-Plus variants

## Deployment notes

- ONNX export follows the repo's ONNX-aware forward branches in the heads.
- `RepVGG` models need deploy conversion before export or backend conversion.
- The external C++ deployment demos are useful evidence for deployment backends, but the generated skill uses distilled notes rather than depending on those source trees at runtime.
