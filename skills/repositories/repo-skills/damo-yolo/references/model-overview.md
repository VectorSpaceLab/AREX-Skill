# DAMO-YOLO model and config overview

DAMO-YOLO is a YOLO-style object detector built from TinyNAS backbones, RepGFPN/Giraffe necks, and a ZeroHead detection head. Public workflows revolve around Python config files that instantiate `damo.config.Config` subclasses.

## Common model/config families

| Family | Typical config name | Image size | Notes |
|---|---|---:|---|
| DAMO-YOLO-T | `damoyolo_tinynasL20_T.py` | 640 | Tiny general model; often used for custom dataset tutorials. |
| DAMO-YOLO-S | `damoyolo_tinynasL25_S.py` | 640 | Small/general baseline; README examples use this often. |
| DAMO-YOLO-M | `damoyolo_tinynasL35_M.py` | 640 | Medium model; can serve as teacher for smaller students. |
| DAMO-YOLO-L | `damoyolo_tinynasL45_L.py` | 640 | Large model; higher accuracy and heavier runtime. |
| DAMO-YOLO-Ns | `damoyolo_tinynasL18_Ns.py` | 416 | Nano/small CPU-oriented light model. |
| DAMO-YOLO-Nm | `damoyolo_tinynasL18_Nm.py` | 416 | Nano/middle light model. |
| DAMO-YOLO-Nl | `damoyolo_tinynasL20_Nl.py` | 416 | Nano/large light model. |

The README also describes a 701-category DAMO-YOLO-S pretrained model for broad pretraining/finetuning scenarios. When using it, make sure `class_names`, `num_classes`, and checkpoint head shape match the downstream config.

## Architecture objects that show up in configs

- `TinyNAS_res`, `TinyNAS_csp`, and `TinyNAS_mob`: backbone families built from TinyNAS structure text.
- `GiraffeNeckV2`: feature-pyramid neck configured with `in_channels`, `out_channels`, `depth`, `hidden_ratio`, and `block_name`.
- `ZeroHead`: detection head. Important keys include `num_classes`, `in_channels`, `stacked_convs`, `reg_max`, `nms_conf_thre`, `nms_iou_thre`, and `legacy`.
- `train.augment` / `test.augment`: resize, flip, normalization, and optional SADA/mosaic/mixup augmentation settings.

## Config portability cautions

- Many source configs read TinyNAS structure text through relative paths. When using bundled scripts, pass `--workdir` so those relative reads resolve, or edit config paths to be absolute/user-owned.
- `DatasetCatalog.DATA_DIR` and `DatasetCatalog.DATASETS` drive base dataset resolution. `cfg.dataset.data_dir` is not used by the default `get_data()` implementation.
- `Config.merge()` only updates exact top-level attributes; use edited config files for nested changes.
