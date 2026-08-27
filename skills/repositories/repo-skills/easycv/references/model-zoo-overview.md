# Model zoo overview

EasyCV uses config-driven workflows. The `CONFIG_TEMPLATE_ZOO` map in `easycv.utils.config_tools` swaps a small `--model_type` key for a concrete config file.

## Template families

| Family | Template keys | Representative config paths | Notes |
| --- | --- | --- | --- |
| Classification | `CLASSIFICATION_RESNET`, `CLASSIFICATION_RESNEXT`, `CLASSIFICATION_HRNET`, `CLASSIFICATION_VIT`, `CLASSIFICATION_SWINT`, `CLASSIFICATION_M0BILENET`, `CLASSIFICATION_INCEPTIONV4`, `CLASSIFICATION_INCEPTIONV3` | `configs/classification/imagenet/...` | Use for standard image classification and feature-style backbones. |
| Metric learning | `METRICLEARNING`, `MODELPARALLEL_METRICLEARNING` | `configs/metric_learning/...` | Use for retrieval / embedding workflows. |
| Detection | `YOLOX`, `YOLOX_ITAG`, `YOLOX_ITAG_EASY`, `YOLOX_COCO_EASY`, `FCOS_ITAG_EASY`, `FCOS_COCO_EASY` | `configs/detection/...`, `configs/config_templates/yolox*.py` | Use for COCO, iTAG, VOC, and edge variants. |
| Segmentation | `FCN_SEG`, `UPERNET_SEG`, `SEGFORMER_SEG` | `configs/segmentation/...` | Use for semantic, instance, and panoptic segmentation. |
| Self-supervised learning | `MOCO_R50_TFRECORD`, `MOCO_R50_TFRECORD_OSS`, `MOCO_TIMM_TFRECORD`, `MOCO_TIMM_TFRECORD_OSS`, `SWAV_R50_TFRECORD`, `SWAV_R50_TFRECORD_OSS`, `MOBY_TIMM_TFRECORD_OSS`, `DINO_TIMM`, `DINO_TIMM_TFRECORD_OSS`, `DINO_R50_TFRECORD_OSS`, `MAE` | `configs/selfsup/...`, `configs/config_templates/...` | Use for contrastive, masked-image-modeling, and ViT/Swin self-supervised training. |
| Pose | `TOPDOWN_HRNET`, `TOPDOWN_LITEHRNET` | `configs/pose/...`, `configs/config_templates/topdown_*.py` | Use for 2D keypoints and whole-body pose. |
| Video | `X3D_XS`, `X3D_M`, `X3D_L`, `VIDEO_SWIN_T`, `VIDEO_SWIN_S`, `VIDEO_SWIN_B`, `SWIN_BERT` | `configs/video_recognition/...` | Use for skeleton-based or clip-level video recognition. |
| Edge / deployment-oriented | `YOLOX_EDGE`, `YOLOX_EDGE_ITAG` | `configs/config_templates/yolox_edge*.py` | Use for smaller deployment-oriented YOLOX variants. |

## How to use the map

- Use `--model_type` only for the families above.
- Use an explicit config path for OCR, 3D detection, or any workflow not covered by the template zoo.
- When the same task has multiple config roots, prefer the simplest config that matches the dataset layout and backend you actually have.

## Common selection rule

Choose the config family before editing data paths. In EasyCV, the config often determines:

- dataset root variables
- pipeline shape
- export metadata
- predictor compatibility
- backend assumptions such as CUDA, DALI, or TorchAccelerator
