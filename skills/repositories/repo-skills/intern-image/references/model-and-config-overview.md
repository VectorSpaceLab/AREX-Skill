# InternImage Model and Config Overview

## Purpose

Read this when choosing an InternImage model/config/checkpoint family or deciding which sub-skill should own a task. This reference is distilled from the repository's public model tables, configs, task READMEs, and source entry points.

## Project shape

InternImage is a DCNv3-based vision foundation model repository with separate workflow roots:

| Workflow root | Stack | Primary tasks | Route |
| --- | --- | --- | --- |
| Classification | PyTorch + YACS + timm + optional DeepSpeed/Accelerate | ImageNet/iNaturalist training/evaluation, throughput, feature extraction, Hugging Face use | `sub-skills/classification/` |
| Detection | MMDetection 2.28-era stack | COCO/LVIS/OpenImages/VOC/CrowdHuman object detection and instance segmentation, SAM-prompted masks | `sub-skills/detection/` |
| Segmentation | MMSegmentation 0.27-era stack | ADE20K/Cityscapes/COCO-Stuff/Mapillary/NYU/Pascal semantic segmentation | `sub-skills/segmentation/` |
| Autonomous driving | mmdet3d challenge baselines + OpenLane-V2 devkit | Occupancy prediction, online HD map construction, OpenLane-V2 topology | `sub-skills/autonomous-driving/` |
| Deployment | CUDA/DCNv3/mmdeploy/TensorRT | DCNv3 operator build, ONNX/TensorRT export, backend diagnostics | `sub-skills/deployment/` |

## Backbone sizes and common released models

| Family | Typical params/FLOPs in docs | Common use |
| --- | --- | --- |
| InternImage-T | small/tiny, ~30M classification backbone | Smoke tests, lower-memory classification/detection/segmentation examples. |
| InternImage-S | ~50M classification backbone | Mid-size classification and autonomous baselines. |
| InternImage-B | ~97M classification backbone | Higher-accuracy ImageNet and COCO Mask R-CNN examples. |
| InternImage-L | ~223M classification backbone | 22K-pretrained classification, large detection/segmentation. |
| InternImage-XL | ~335M classification backbone | Large detection/segmentation and 22K fine-tuning. |
| InternImage-H | ~1B classification backbone | Very large classification/segmentation/DINO workflows; often requires memory-saving settings. |
| InternImage-G | ~3B classification backbone | Largest published classification/DINO workflows; not a smoke-test target. |
| CB-InternImage-H/G | composite backbones | Strongest DINO detection configs; very high memory. |

Performance tables in the repository document top-line benchmark results such as ImageNet 90.1 Top-1, COCO 65.5 mAP, and ADE20K 62.9 mIoU. Treat those as published model-zoo claims, not as evidence that a local run has reproduced them.

## Config naming patterns

### Classification

Classification configs are YAML files. Common families:

- `configs/internimage_t_1k_224.yaml`, `internimage_s_1k_224.yaml`, `internimage_b_1k_224.yaml` for ImageNet-1K 224px models.
- `configs/internimage_l_22kto1k_384.yaml`, `internimage_xl_22kto1k_384.yaml`, `internimage_h_22kto1k_640.yaml`, `internimage_g_22kto1k_512.yaml` for 22K-to-1K fine-tuned models.
- `configs/without_lr_decay/*` for paper-result training variants without layer-wise LR decay.
- `configs/inaturalist2018/internimage_h_22ktoinat18_384.yaml` for iNaturalist 2018.
- `configs/accelerate/*` for Accelerate/DeepSpeed launch configs.

Classification uses a YACS config with groups such as `DATA`, `MODEL`, `MODEL.INTERN_IMAGE`, `TRAIN`, `AUG`, `TEST`, `AMP_TYPE`, and `OUTPUT`. Route exact override questions to classification configuration reference.

### Detection

Detection configs are Python MMDetection 2.x configs. Common families:

- COCO Mask R-CNN: `mask_rcnn_internimage_{t,s,b}_fpn_{1x,3x}_coco`.
- COCO Cascade: `cascade_internimage_{l,xl}_fpn_{1x,3x}_coco`.
- COCO DINO: `dino_4scale_internimage_{t,l,h,g}...` and `dino_4scale_cbinternimage_h...`.
- Transfer datasets: LVIS, OpenImages, VOC, CrowdHuman.

Route config selection, metric pairing, image demo, and SAM questions to detection.

### Segmentation

Segmentation configs are Python MMSegmentation 0.x configs. Common families:

- ADE20K UperNet and Mask2Former configs.
- Cityscapes UperNet/SegFormer/Mask2Former, including Mapillary-to-Cityscapes variants.
- COCO-Stuff 10K/164K, Mapillary, NYU Depth V2, Pascal Context.

Native image-demo palette choices are limited to `ade20k`, `cityscapes`, and `cocostuff`; not every config family has a built-in demo palette.

### Autonomous driving

- Occupancy prediction: `projects/configs/bevformer/bevformer_intern-s_occ.py`, mmdet3d 0.18.x-era stack, nuScenes/Occ3D data.
- Online HD map: `src/configs/vectormapnet_intern.py`, VectorMapNet-style Argoverse2 workflow, mmdet3d 1.0.0rc6-era stack.
- OpenLane-V2: `plugin/mmdet3d/configs/internimage-s.py`, OpenLane-V2 data/devkit/topology workflow, mmdet3d 1.0.0rc6-era stack.

Route OpenLane-V2 schema, topology matrix, country-code, metric, or submission validation tasks to autonomous-driving even if they do not require model execution.

## Checkpoint pairing rules

- Use a checkpoint from the same task family and config family for full-model evaluation. A COCO Mask R-CNN detector checkpoint should not be loaded into a DINO detector config.
- Classification pretrained weights may initialize a downstream backbone when a config field expects a pretrained backbone; they are not full detector/segmentor checkpoints.
- H/G and CB models are large. Before recommending a run, check batch size, image resolution, gradient checkpointing (`with_cp=True` where supported), number of GPUs, and checkpoint availability.
- Download URLs in public docs often point to Hugging Face, Google Drive, or release assets. Do not download them unless the user has approved network and storage use.

## Validation strategy

- Command builders validate command shape only.
- `check_internimage_environment.py` validates import and backend signals only.
- OpenLane-V2 JSON validator validates schema only.
- Native model quality requires actual datasets, checkpoints, GPU runtime, and task-specific evaluation commands.
