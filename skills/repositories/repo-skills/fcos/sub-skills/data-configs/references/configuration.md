# FCOS Configuration Reference

## Merge model

FCOS uses a YACS-style global `cfg` object. Workflows typically clone or mutate it by:

1. `cfg.merge_from_file(<yaml>)`
2. `cfg.merge_from_list(opts)` for trailing CLI overrides
3. `cfg.freeze()` before constructing models or data loaders

CLI overrides are flat token pairs. Examples:

```bash
MODEL.WEIGHT FCOS_imprv_R_50_FPN_1x.pth TEST.IMS_PER_BATCH 1 OUTPUT_DIR eval_out
```

## Core FCOS options

| Key | Meaning |
| --- | --- |
| `MODEL.FCOS_ON` | Enables FCOS RPN module. |
| `MODEL.RPN_ONLY` | FCOS configs usually set this true. |
| `MODEL.FCOS.NUM_CLASSES` | Number of classes including background; COCO defaults to 81. |
| `MODEL.FCOS.FPN_STRIDES` | Feature strides, default `[8, 16, 32, 64, 128]`. |
| `MODEL.FCOS.INFERENCE_TH` | Pre-NMS score threshold. |
| `MODEL.FCOS.NMS_TH` | NMS threshold. |
| `MODEL.FCOS.PRE_NMS_TOP_N` | Candidate limit before NMS. |
| `MODEL.FCOS.NORM_REG_TARGETS` | Regression target normalization; improved configs set true. |
| `MODEL.FCOS.CENTERNESS_ON_REG` | Places centerness on regression branch in improved configs. |
| `MODEL.FCOS.CENTER_SAMPLING_RADIUS` | Center sampling radius; improved configs use `1.5`. |
| `MODEL.FCOS.IOU_LOSS_TYPE` | `iou` or `giou`; improved configs use `giou`. |
| `MODEL.FCOS.USE_DCN_IN_TOWER` | Uses deformable conv in last tower layer; needs extension support. |

## Validation helper

```bash
python sub-skills/data-configs/scripts/validate_fcos_config.py configs/fcos/fcos_imprv_R_50_FPN_1x.yaml --opts TEST.IMS_PER_BATCH 1
```

The helper tries to import FCOS config support and merge the file. If imports are missing, it falls back to YAML parsing and reports that full schema validation was unavailable.
