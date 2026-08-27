# Data formats and layouts

## Common file I/O

EasyCV uses `easycv.file.io` for both local and OSS paths.
When you need OSS, configure credentials before any read or write.

## Major dataset families

| Family | Expected layout | Notes |
| --- | --- | --- |
| ImageNet raw | `train/<class>/...`, `val/<class>/...`, optional `meta/*.txt` | Used by classification and SSL recipes. |
| ImageNet TFRecord | paired record and `.idx` files under `train/` and `validation/` | Used by TFRecord-based classification and SSL recipes. |
| CIFAR-10 / CIFAR-100 | extracted CIFAR batch directory | Used by the small classification examples. |
| COCO | `annotations/*.json`, `train2017/`, `val2017/` | Used by detection and segmentation configs. |
| VOC 2007 / 2012 | `Annotations/`, `JPEGImages/`, `ImageSets/`, optional segmentation masks | Used by detection, segmentation, and low-shot helpers. |
| PAI-iTAG detection | image folders plus manifest files | Used by itag detection configs and conversion helpers. |
| nuScenes | dataset root plus generated info files | Used by BEVFormer and 3D detection helpers. |
| Market1501 | query / gallery / train / val splits | Used by ReID recipes. |
| CrowdHuman / MOT / COCO-Stuff | dataset-specific folders and conversion outputs | Used by the repo's conversion scripts. |

## Table-based prediction inputs

Batch prediction can also use ODPS / MaxCompute tables.
The image column must contain either:

- a URL string, or
- a base64-encoded image string

The table usually keeps the original identifier column plus a result column.

## Rule of thumb

If a config mentions `data_root`, `data_train_root`, `data_train_list`, `ann_file`, `img_prefix`, `manifest`, or `tfrecord`, check the corresponding family layout before training.

