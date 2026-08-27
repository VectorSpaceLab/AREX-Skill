# Training and Configuration API Reference

Verified live facts from the distilled source and inspection environment:

## `yolov7.config.add_yolo_config(cfg)`

Adds YOLOv7-d2 config keys to a Detectron2 `CfgNode`. Notable defaults include:

- `DATASETS.CLASS_NAMES = []`
- `MODEL.NMS_TYPE = "normal"`
- `MODEL.ONNX_EXPORT = False`
- `MODEL.PADDED_VALUE = 114.0`
- `MODEL.YOLO.CLASSES = 80`
- `MODEL.YOLO.CONF_THRESHOLD = 0.01`
- `MODEL.YOLO.NMS_THRESHOLD = 0.5`
- `MODEL.YOLO.HEAD.TYPE = "yolox"`
- `MODEL.YOLO.NECK.TYPE = "yolov3"`
- `MODEL.DETR.NUM_OBJECT_QUERIES = 100`
- `SOLVER.OPTIMIZER = "ADAMW"` after all defaults are injected
- `WANDB.ENABLED = False`

## Dataset mappers

- `MyDatasetMapper(is_train, *, augmentations, image_format, mosaic_trans, use_instance_mask=False, use_keypoint=False, instance_mask_format="polygon", recompute_boxes=False, add_meta_infos=False)`
- `MyDatasetMapper2(is_train, *, augmentations, image_format, mosaic_trans, use_instance_mask=False, use_keypoint=False, instance_mask_format="polygon", recompute_boxes=False, add_meta_infos=False, input_size=[640, 640])`
- `DetrDatasetMapper(cfg, is_train=True)`

`MyDatasetMapper2` owns the mosaic+mixup path. `DetrDatasetMapper` owns DETR crop/resize behavior.

## Optimizer registry

YOLOv7-d2 provides D2Go-style optimizer builders:

- `sgd`
- `adamw`
- `sgd_mt`
- `adamw_mt`

`build_optimizer_mapper(cfg, model)` selects `cfg.SOLVER.OPTIMIZER.lower()` from that registry and logs parameter-group summaries.

## Evaluation

`COCOMaskEvaluator` extends Detectron2 `COCOEvaluator` so mask-only instances can be serialized without requiring `pred_boxes`. Use it for SparseInst-like workflows.

## Registered model families

Observed registered meta-architectures include `AnchorDetr`, `Detr`, `DetrD2go`, `SMCADetr`, `SOLOv2`, `SparseInst`, `YOLO`, `YOLOF`, `YOLOMask`, `YOLOV5`, `YOLOV6`, `YOLOV7`, `YOLOV7P`, and `YOLOX`.
