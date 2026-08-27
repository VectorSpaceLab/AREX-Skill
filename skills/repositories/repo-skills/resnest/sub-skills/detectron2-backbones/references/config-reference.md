# Detectron2 ResNeSt Config Reference

This catalog is self-contained and distilled from the ResNeSt Detectron2 recipe set. It names recipe keys for orientation but does not require access to the original config files. Use the YAML fragments and field tables here to build your own Detectron2 config.

## Shared RCNN/FPN baseline defaults

Most recipes inherit these common Detectron2 settings:

| Area | Default pattern |
|---|---|
| Meta architecture | `MODEL.META_ARCHITECTURE: "GeneralizedRCNN"` for detection/instance segmentation. |
| Backbone/FPN features | `MODEL.RESNETS.OUT_FEATURES` and `MODEL.FPN.IN_FEATURES` are `['res2', 'res3', 'res4', 'res5']`. |
| RPN features | `['p2', 'p3', 'p4', 'p5', 'p6']`; anchors `[[32], [64], [128], [256], [512]]`; aspect ratios `[[0.5, 1.0, 2.0]]`. |
| ROI heads | `StandardROIHeads` for non-cascade; `CascadeROIHeads` for cascade recipes. |
| Box head | `FastRCNNConvFCHead`; many SyncBN recipes use `NUM_CONV: 4`, `NUM_FC: 1`, `NORM: "SyncBN"`. |
| Mask head | `MaskRCNNConvUpsampleHead` with `NUM_CONV: 4` by default; 3x all-tricks cascade mask recipes use `NUM_CONV: 8`. |
| Datasets | Detection/instance recipes default to `coco_2017_train` and `coco_2017_val`. |
| Solver 1x | Usually `IMS_PER_BATCH: 16`, `BASE_LR: 0.02`, `STEPS: (60000, 80000)`, `MAX_ITER: 90000`. |
| Scale augmentation | 1x range-scale recipes use `MIN_SIZE_TRAIN: (640, 800)`, `MIN_SIZE_TRAIN_SAMPLING: "range"`, and `MAX_SIZE_TRAIN: 1333`. |
| Precise BN | SyncBN recipes set `TEST.PRECISE_BN.ENABLED: True`. |

A ResNeSt/FPN recipe changes the backbone to:

```yaml
MODEL:
  BACKBONE:
    NAME: "build_resnest_fpn_backbone"
```

The builder still reads Detectron2's standard `MODEL.RESNETS.NUM_GROUPS` and `MODEL.RESNETS.WIDTH_PER_GROUP`; the released recipes keep those defaults unless a row says otherwise. A ResNeSt recipe should also include the ResNeSt fields added by `add_resnest_config`:

```yaml
MODEL:
  RESNETS:
    STRIDE_IN_1X1: False
    DEEP_STEM: True
    AVD: True
    AVG_DOWN: True
    RADIX: 2
    BOTTLENECK_WIDTH: 64
```

Released ResNeSt recipes also use RGB model statistics:

```yaml
MODEL:
  PIXEL_MEAN: [123.68, 116.779, 103.939]
  PIXEL_STD: [58.393, 57.12, 57.375]
INPUT:
  FORMAT: "RGB"
```

## Backbone initialization weights used inside configs

These are external resources used as `MODEL.WEIGHTS` to initialize the ResNeSt backbone before COCO fine-tuning:

| Backbone | URL |
|---|---|
| ResNeSt-50 | `https://s3.us-west-1.wasabisys.com/resnest/detectron/resnest50_detectron-255b5649.pth` |
| ResNeSt-101 | `https://s3.us-west-1.wasabisys.com/resnest/detectron/resnest101_detectron-486f69a8.pth` |
| ResNeSt-200 | `https://s3.us-west-1.wasabisys.com/resnest/detectron/resnest200_detectron-02644020.pth` |

For evaluation of a fully trained detector/segmenter, override `MODEL.WEIGHTS` with the released task checkpoint URL from the relevant catalog row below.

## COCO object detection catalog

| Recipe key | Task/head | Backbone | ResNeSt fields | Extra head/config fields | Init weights | Released task checkpoint | Reported metric |
|---|---|---|---|---|---|---|---|
| `faster_rcnn_ResNeSt_50_FPN_syncbn_range-scale_1x` | Faster R-CNN, box only | ResNeSt-50 FPN | `DEPTH: 50`, `RADIX: 2`, `STRIDE_IN_1X1: False`, SyncBN | `MASK_ON: False`, range-scale 640-800 | ResNeSt-50 init URL above | `https://s3.us-west-1.wasabisys.com/resnest/detectron/faster_rcnn_ResNeSt_50_FPN_syncbn_range-scale_1x-ad123c0b.pth` | bbox mAP 42.33 |
| `faster_rcnn_ResNeSt_50_FPN_dcn_syncbn_range-scale_1x` | Faster R-CNN with DCNv2 | ResNeSt-50 FPN DCN | ResNeSt-50 fields plus `DEFORM_ON_PER_STAGE: [False, True, True, True]`, `DEFORM_MODULATED: True`, `DEFORM_NUM_GROUPS: 2` | `MASK_ON: False`, range-scale 640-800 | ResNeSt-50 init URL above | `https://s3.us-west-1.wasabisys.com/resnest/detectron/faster_rcnn_ResNeSt_50_FPN_dcn_syncbn_range-scale_1x.pth` | bbox mAP 44.11 |
| `faster_rcnn_ResNeSt_101_FPN_syncbn_range-scale_1x` | Faster R-CNN, box only | ResNeSt-101 FPN | `DEPTH: 101`, `RADIX: 2`, `STRIDE_IN_1X1: False`, SyncBN | `MASK_ON: False`, range-scale 640-800 | ResNeSt-101 init URL above | `https://s3.us-west-1.wasabisys.com/resnest/detectron/faster_rcnn_ResNeSt_101_FPN_syncbn_range-scale_1x-d8f284b6.pth` | bbox mAP 44.72 |
| `faster_cascade_rcnn_ResNeSt_50_FPN_syncbn_range-scale-1x` | Cascade R-CNN, box only | ResNeSt-50 FPN | `DEPTH: 50`, `RADIX: 2`, `STRIDE_IN_1X1: False`, SyncBN | `ROI_HEADS.NAME: CascadeROIHeads`, `ROI_BOX_HEAD.CLS_AGNOSTIC_BBOX_REG: True`, `RPN.POST_NMS_TOPK_TRAIN: 2000` | ResNeSt-50 init URL above | `https://s3.us-west-1.wasabisys.com/resnest/detectron/faster_cascade_rcnn_ResNeSt_50_FPN_syncbn_range-scale-1x-e9955232.pth` | bbox mAP 45.41 |
| `faster_cascade_rcnn_ResNeSt_101_FPN_syncbn_range-scale_1x` | Cascade R-CNN, box only | ResNeSt-101 FPN | `DEPTH: 101`, `RADIX: 2`, `STRIDE_IN_1X1: False`, SyncBN | Cascade ROI heads, class-agnostic bbox reg, RPN train top-k 2000 | ResNeSt-101 init URL above | `https://s3.us-west-1.wasabisys.com/resnest/detectron/faster_cascade_rcnn_ResNeSt_101_FPN_syncbn_range-scale_1x-3627ef78.pth` | bbox mAP 47.50 |
| `faster_cascade_rcnn_ResNeSt_200_FPN_syncbn_range-scale_1x` | Cascade R-CNN, box only | ResNeSt-200 FPN | `DEPTH: 200`, `RADIX: 2`, `STRIDE_IN_1X1: False`, SyncBN | Cascade ROI heads, class-agnostic bbox reg, RPN train top-k 2000 | ResNeSt-200 init URL above | `https://s3.us-west-1.wasabisys.com/resnest/detectron/faster_cascade_rcnn_ResNeSt_200_FPN_syncbn_range-scale_1x-1be2a87e.pth` | bbox mAP 49.03 |

Baseline Faster/Cascade R-CNN ResNet-50/101 SyncBN recipes are present for comparison. They use Detectron2's standard `build_resnet_fpn_backbone`, `detectron2://ImageNetPretrained/MSRA/R-50.pkl` or `R-101.pkl`, and should not be confused with the ResNeSt backbone registry name.

## COCO instance segmentation catalog

| Recipe key | Task/head | Backbone | ResNeSt fields | Extra head/config fields | Init weights | Released task checkpoint | Reported metric |
|---|---|---|---|---|---|---|---|
| `mask_rcnn_ResNeSt_50_FPN_syncBN_1x` | Mask R-CNN | ResNeSt-50 FPN | `DEPTH: 50`, `RADIX: 2`, `STRIDE_IN_1X1: False`, SyncBN | `MASK_ON: True`, mask head SyncBN | ResNeSt-50 init URL above | `https://s3.us-west-1.wasabisys.com/resnest/detectron/mask_rcnn_ResNeSt_50_FPN_syncBN_1x-f442d863.pth` | bbox 42.81, mask 38.14 |
| `mask_rcnn_ResNeSt_101_FPN_syncBN_1x` | Mask R-CNN | ResNeSt-101 FPN | `DEPTH: 101`, `RADIX: 2`, `STRIDE_IN_1X1: False`, SyncBN | `MASK_ON: True`, mask head SyncBN | ResNeSt-101 init URL above | `https://s3.us-west-1.wasabisys.com/resnest/detectron/mask_rcnn_ResNeSt_101_FPN_syncBN_1x-528502c6.pth` | bbox 45.75, mask 40.65 |
| `mask_cascade_rcnn_ResNeSt_50_FPN_syncBN_1x` | Cascade Mask R-CNN | ResNeSt-50 FPN | `DEPTH: 50`, `RADIX: 2`, `STRIDE_IN_1X1: False`, SyncBN | `ROI_HEADS.NAME: CascadeROIHeads`, `ROI_BOX_HEAD.CLS_AGNOSTIC_BBOX_REG: True`, `RPN.POST_NMS_TOPK_TRAIN: 2000` | ResNeSt-50 init URL above | `https://s3.us-west-1.wasabisys.com/resnest/detectron/mask_cascade_rcnn_ResNeSt_50_FPN_syncBN_1x-c58bd325.pth` | bbox 46.19, mask 39.55 |
| `mask_cascade_rcnn_ResNeSt_101_FPN_syncBN_1x` | Cascade Mask R-CNN | ResNeSt-101 FPN | `DEPTH: 101`, `RADIX: 2`, `STRIDE_IN_1X1: False`, SyncBN | Cascade ROI heads, class-agnostic bbox reg, RPN train top-k 2000 | ResNeSt-101 init URL above | `https://s3.us-west-1.wasabisys.com/resnest/detectron/mask_cascade_rcnn_ResNeSt_101_FPN_syncBN_1x-62448b9c.pth` | bbox 48.30, mask 41.56 |
| `mask_cascade_rcnn_ResNeSt_200_FPN_syncBN_all_tricks_3x` | Cascade Mask R-CNN all-tricks 3x | ResNeSt-200 FPN | `DEPTH: 200`, `RADIX: 2`, `STRIDE_IN_1X1: False`, SyncBN | `ROI_MASK_HEAD.NUM_CONV: 8`, crop enabled, `STEPS: (240000, 255000)`, `MAX_ITER: 270000`, range-scale 640-864, max size 1440 | ResNeSt-200 init URL above | `https://s3.us-west-1.wasabisys.com/resnest/detectron/mask_cascade_rcnn_ResNeSt_200_FPN_syncBN_all_tricks_3x.pth` | bbox 50.54, mask 44.21 |
| `mask_cascade_rcnn_ResNeSt_200_FPN_dcn_syncBN_all_tricks_3x` | Cascade Mask R-CNN DCN all-tricks 3x | ResNeSt-200 FPN DCN | ResNeSt-200 fields plus `DEFORM_ON_PER_STAGE: [False, True, True, True]`, `DEFORM_MODULATED: True`, `DEFORM_NUM_GROUPS: 2` | Same 3x all-tricks fields as above | ResNeSt-200 init URL above | `https://s3.us-west-1.wasabisys.com/resnest/detectron/mask_cascade_rcnn_ResNeSt_200_FPN_dcn_syncBN_all_tricks_3x-e1901134.pth` | bbox 50.91, mask 44.50; multi-scale test-dev result marked as 53.30/47.10 |

Baseline Mask/Cascade Mask R-CNN ResNet-50/101 SyncBN recipes are present for comparison. Use them only when the task asks for a ResNet baseline, not a ResNeSt backbone.

## COCO panoptic segmentation catalog

| Recipe key | Task/head | Backbone | ResNeSt fields | Extra head/config fields | Init weights | Released task checkpoint | Reported metric |
|---|---|---|---|---|---|---|---|
| `panoptic_ResNeSt_200_FPN_syncBN_tricks_3x` | Panoptic FPN | ResNeSt-200 FPN | `DEPTH: 200`, `RADIX: 2`, `STRIDE_IN_1X1: False`, SyncBN | `MODEL.META_ARCHITECTURE: "PanopticFPN"`, `MASK_ON: True`, `SEM_SEG_HEAD.LOSS_WEIGHT: 0.5`, cascade ROI box head, `SEM_SEG_HEAD.NORM: "SyncBN"`, range-scale 400-1000, max size 1440, `TEST.AUG.ENABLED: True` | ResNeSt-200 init URL above | `https://s3.us-west-1.wasabisys.com/resnest/detectron/panoptic_ResNeSt_200_FPN_syncBN_tricks_3x-43f8b731.pth` | bbox 51.00, mask 43.68, PQ 47.90 |

Panoptic recipes use separated COCO panoptic dataset names: `coco_2017_train_panoptic_separated` and `coco_2017_val_panoptic_separated`.

## DCN variant fragment

Add this only when using a DCN catalog row and your Detectron2 build supports deformable convolution operators:

```yaml
MODEL:
  RESNETS:
    DEFORM_ON_PER_STAGE: [False, True, True, True]
    DEFORM_MODULATED: True
    DEFORM_NUM_GROUPS: 2
```

## All-tricks 3x fragment

The ResNeSt-200 all-tricks instance and panoptic recipes increase image scale, schedule, and memory pressure:

```yaml
SOLVER:
  IMS_PER_BATCH: 16
  BASE_LR: 0.02
  STEPS: (240000, 255000)
  MAX_ITER: 270000
INPUT:
  MIN_SIZE_TRAIN_SAMPLING: "range"
  MAX_SIZE_TRAIN: 1440
```

Instance all-tricks recipes use `MIN_SIZE_TRAIN: (640, 864)` with crop enabled. Panoptic all-tricks uses `MIN_SIZE_TRAIN: (400, 1000)` and enables test-time augmentation.
