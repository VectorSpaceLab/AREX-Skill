# FCOS Internal API Reference

## Key builders and classes

| Component | Signature / role | Notes |
| --- | --- | --- |
| `build_fcos(cfg, in_channels)` | returns `FCOSModule` | Used by RPN builder when FCOS is enabled. |
| `FCOSHead(cfg, in_channels)` | builds towers and output heads | Consumes `MODEL.FCOS.NUM_CLASSES`, `FPN_STRIDES`, `NUM_CONVS`, `NORM_REG_TARGETS`, `CENTERNESS_ON_REG`, `USE_DCN_IN_TOWER`, and `PRIOR_PROB`. |
| `FCOSModule.forward(images, features, targets=None)` | training returns losses; eval returns boxes | Requires `ImageList` and feature tensors from backbone. |
| `make_fcos_postprocessor(config)` | returns `FCOSPostProcessor` | Consumes inference threshold, top-k, NMS, detections-per-image, bbox augmentation. |
| `BoxList(bbox, image_size, mode="xyxy")` | stores boxes and extra fields | Used throughout post-processing and evaluator paths. |

## Config keys that often affect internals

- `MODEL.FCOS.NUM_CLASSES`: output channels are `NUM_CLASSES - 1` for foreground classes.
- `MODEL.FCOS.FPN_STRIDES`: location grid spacing and regression scaling.
- `MODEL.FCOS.PRIOR_PROB`: initializes classification bias.
- `MODEL.FCOS.CENTERNESS_ON_REG`: determines which tower feeds centerness.
- `MODEL.FCOS.NORM_REG_TARGETS`: changes regression parameterization at train/test.
- `MODEL.FCOS.IOU_LOSS_TYPE`: loss type, commonly `iou` or `giou`.
- `MODEL.RESNETS.STAGE_WITH_DCN`, `MODEL.FCOS.USE_DCN_IN_TOWER`: can require compiled deformable convolution code.

## Safe inspection

Use the bundled inspector instead of constructing a full detector when only signatures/config-derived facts are needed:

```bash
python sub-skills/internals-maintenance/scripts/inspect_fcos_components.py --config configs/fcos/fcos_imprv_R_50_FPN_1x.yaml
```
