# Config template guide

EasyCV is config-first. This page helps you pick the smallest starter config that matches the task.

## Choose the family first

- **Classification**: `CLASSIFICATION_RESNET`, `CLASSIFICATION_SWINT`, `CLASSIFICATION_VIT`, `CLASSIFICATION_HRNET`, `CLASSIFICATION_RESNEXT`
- **Metric learning**: `METRICLEARNING`, `MODELPARALLEL_METRICLEARNING`
- **Detection**: `YOLOX`, `YOLOX_COCO_EASY`, `YOLOX_ITAG`, `FCOS_COCO_EASY`, `FCOS_ITAG_EASY`
- **Segmentation**: `FCN_SEG`, `UPERNET_SEG`, `SEGFORMER_SEG`
- **Self-supervised**: `MOCO_*`, `SWAV_*`, `MOBY_TIMM_TFRECORD_OSS`, `DINO_*`, `MAE`
- **Pose**: `TOPDOWN_HRNET`, `TOPDOWN_LITEHRNET`
- **Video**: `X3D_*`, `VIDEO_SWIN_*`, `SWIN_BERT`
- **Edge / deployment-oriented**: `YOLOX_EDGE`, `YOLOX_EDGE_ITAG`

## When to use `--model_type`

Use `--model_type` only when the task matches one of the supported starter keys in the root model-zoo overview. It is a convenience alias for a known template.

Use an explicit config path when you need:

- an OCR or 3D config
- a custom backbone or neck
- a dataset-specific variant
- a recipe that already has non-default hooks, evaluation, or export settings

## What to edit after selecting a starter

- dataset roots and filelists
- class lists or label maps
- `work_dir`
- optimizer, LR schedule, and total epochs
- validation pipelines and metrics
- logging hooks
- backend-specific settings such as fp16, DALI, or TorchAcc

## Good habit

Start from the smallest matching template, then change only the data paths and the settings you actually need.

