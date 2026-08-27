# Training and Evaluation Workflows

Do not launch full training as a smoke check. First validate imports, config merge, dataset registration, class counts, output directory, checkpoint path, and GPU availability.

## Standard detection workflow

Use this route for YOLO-family detection configs (`YOLOV7`, `YOLOX`, `YOLOV5`, `YOLOV6`, `YOLOV7P`, `YOLOF`) unless the config clearly requires the instance or DETR route.

Command shape:

```bash
python train_det.py --config-file path/to/config.yaml --num-gpus 1 MODEL.WEIGHTS path/to/checkpoint.pth
```

The source trainer pattern:

- injects `add_yolo_config` before config merge;
- uses a custom dataset mapper (`MyDatasetMapper2`) for YOLO-style detection;
- builds `COCOEvaluator` for `cfg.DATASETS.TEST`;
- optionally appends a W&B writer when W&B is enabled and importable.

## Instance segmentation workflow

Use this route for `SparseInst`, `SOLOv2`, and mask-only configs.

Command shape:

```bash
python train_inseg.py --config-file path/to/sparseinst.yaml --num-gpus 1 MODEL.WEIGHTS path/to/checkpoint.pth
```

Important differences:

- uses `MyDatasetMapper`;
- uses `COCOMaskEvaluator`, which can serialize `Instances` without `pred_boxes` when masks are present;
- usually expects RGB input for SparseInst configs.

## DETR-family workflow

Use this route for `Detr`, `AnchorDetr`, `SMCADetr`, and `DetrD2go`.

Command shape:

```bash
python train_transformer.py --config-file path/to/detr.yaml --num-gpus 1 MODEL.WEIGHTS path/to/checkpoint.pth
```

Important differences:

- uses `DetrDatasetMapper` when the meta-architecture is DETR-like;
- uses `ADAMW`, backbone LR multipliers, and full-model gradient clipping in many configs;
- DETR configs often use RGB images and crop augmentation.

## Evaluation-only

All Detectron2 launcher patterns accept `--eval-only` and `--resume` from the default parser:

```bash
python train_det.py --config-file path/to/config.yaml --eval-only MODEL.WEIGHTS path/to/model.pth
```

Before evaluation, ensure the validation dataset name is registered and image/annotation files exist.

## Command builder

Use the bundled command builder to avoid mixing trainer routes:

```bash
python scripts/build_train_command.py --mode detr --config path/to/detr.yaml --num-gpus 2 --eval-only --opts MODEL.WEIGHTS path/to/model.pth
```

The printed command is a template for the user's YOLOv7-d2 working environment. If the root scripts are not available in the user's install, use the trainer patterns in this reference to recreate an equivalent launcher.
