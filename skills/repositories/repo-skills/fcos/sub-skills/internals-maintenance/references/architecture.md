# FCOS Architecture Notes

## Detector stack

FCOS is implemented inside a maskrcnn-benchmark-style `GeneralizedRCNN` detector. Configs set `MODEL.RPN_ONLY=True` and `MODEL.FCOS_ON=True`, so the RPN branch is the FCOS detection head rather than an anchor RPN.

High-level flow:

1. Build backbone/FPN from config.
2. Build RPN using `build_fcos(cfg, in_channels)` when `MODEL.FCOS_ON` is true.
3. `FCOSModule.forward(images, features, targets)` computes head outputs and feature locations.
4. Training path calls `FCOSLossComputation` and returns `loss_cls`, `loss_reg`, and `loss_centerness`.
5. Test path calls `FCOSPostProcessor` to convert logits/regression/centerness into `BoxList` detections.

## FCOS head

`FCOSHead(cfg, in_channels)` builds two towers with `MODEL.FCOS.NUM_CONVS` convolution/group-norm/ReLU blocks:

- classification tower → `cls_logits`
- box tower → `bbox_pred`
- centerness head on either box tower or class tower depending on `CENTERNESS_ON_REG`

Each FPN level has a learned `Scale` module. If `NORM_REG_TARGETS` is true, regression output is ReLU-normalized and multiplied by stride at inference.

## Post-processing

`FCOSPostProcessor` thresholds per-location class logits, multiplies class score by centerness, decodes distances around FCOS locations, clips boxes, removes small boxes, applies multi-label NMS, and caps detections per image.

## Compiled layer dependency

NMS, ROI ops, sigmoid focal loss, and deformable convolution/pooling rely on `fcos_core._C`. Configs using deformable convolutions require the relevant compiled support.
