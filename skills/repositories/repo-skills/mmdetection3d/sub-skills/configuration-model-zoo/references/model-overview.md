# Model-Zoo and Config Selection Reference

Use this reference to map user-facing model names, checkpoint aliases, datasets, and tasks to MMDetection3D config families. It is intentionally self-contained; if a local checkout or package exposes `model-index.yml`, family metafiles, or config READMEs, use them as extra evidence but do not require them for the first routing decision.

## How MMDetection3D organizes model-zoo evidence

- The model index is an import list of per-family metafiles. Each imported family metafile corresponds to a config folder such as `pointpillars`, `centerpoint`, `minkunet`, or `pv_rcnn`.
- Family READMEs contain human result tables: config filename, backbone/settings, schedule, memory, FPS when reported, metrics, checkpoint/log availability, and notes.
- The model-zoo overview groups baselines by algorithm family and points to either core configs or optional project families.
- The dataset index maps dataset keys such as `kitti`, `nuscenes`, and `semantickitti` to default download/data-root metadata. Treat that as dataset-preparation evidence, not proof that the dataset exists locally.
- Some result rows provide logs but no pretrained model because of dataset licensing or release limitations. Waymo rows are a common example.

## Fast selection recipe

1. Identify task and modality: outdoor LiDAR 3D detection, monocular/camera 3D detection, multi-modality detection, indoor 3D detection, point-cloud semantic segmentation, or nuImages-style 2D/instance baseline.
2. Identify dataset token and class setting: e.g. `kitti-3d-car`, `kitti-3d-3class`, `nus-3d`, `waymoD5-3d-car`, `scannet-3d`, `s3dis-seg`, `semantickitti`, `nuim`.
3. Match model/checkpoint alias tokens against config basename tokens: algorithm, component/backbone/neck, voxel/pillar/backend setting, GPU x batch, AMP/TTA flags, schedule, dataset.
4. Prefer a config from the same package era and same family as the checkpoint. If only a checkpoint URL or basename is available, find the closest config basename before executing inference or evaluation.
5. Check backend requirements before choosing sparse or project families. Sparse convolution backends and project modules often require optional packages beyond the core Python stack.
6. Run [`../scripts/check_config.py`](../scripts/check_config.py) on the candidate config before handing it to `training-evaluation` or `inference`.

## Core model-family map

| User intent | Likely families | Typical datasets | Selection notes |
| --- | --- | --- | --- |
| Fast outdoor LiDAR 3D detection | PointPillars, SECOND | KITTI, nuScenes, Lyft, Waymo | Good first baselines. PointPillars names often expose pillar/voxel settings, SECFPN/FPN, AMP, and dataset/class tokens. |
| Strong outdoor LiDAR 3D detection | CenterPoint, PV-RCNN, Part-A2, SA-SSD, 3DSSD, PointRCNN | KITTI, nuScenes, Waymo | Match voxel size, center/head options, class count, and schedule carefully. CenterPoint rows may include DCN, circle NMS, double-flip, or scale TTA variants. |
| Dynamic or fusion-style outdoor detection | Dynamic Voxelization, MVXNet, RegNetX, SSN | KITTI, nuScenes, Lyft | Inspect whether the model is LiDAR-only or multi-modal and whether image branches require extra dataset fields. |
| Indoor 3D object detection | VoteNet, H3DNet, Group-Free-3D, FCAF3D | ScanNet, SUN RGB-D, S3DIS | Indoor configs depend on indoor dataset annotation conventions and coordinate settings; route layout questions to `data-preparation`. |
| Monocular/camera 3D detection | FCOS3D, PGD, SMOKE, MonoFlex, ImVoxelNet | KITTI, nuScenes | Verify camera-only modality, image pipeline, camera calibration fields, and dataset-specific evaluator. |
| Point-cloud segmentation | PointNet++, PAConv, DGCNN, MinkUNet, Cylinder3D, SPVCNN | S3DIS, ScanNet, SemanticKITTI | Sparse/backbone backend tokens matter. MinkUNet variants may name `torchsparse`, `minkowski`, or `spconv`; PAConv has CUDA and non-CUDA variants. |
| nuImages 2D/instance baselines | Mask R-CNN, Cascade Mask R-CNN, HTC | nuImages | These are image instance/semantic segmentation baselines inside MMDetection3D's nuImages support; check class-order and conversion notes before comparing old models. |
| Optional project families | BEVFusion, CenterFormer, TR3D, DETR3D, PETR, TPVFormer | nuScenes, Waymo, ScanNet/SUN RGB-D/S3DIS | Config selection can start here, but importing project modules or installing project dependencies belongs to `customization-extensions`. |

## Reading config/checkpoint aliases

A checkpoint or config basename usually carries this structure:

```text
algorithm_component-settings_gpuxbatch-schedule_dataset[-extra].py
```

Examples of information encoded in names:

- `pointpillars_hv_secfpn_8xb6-160e_kitti-3d-car`: PointPillars, hard-voxel style, SECFPN, 8 GPUs x batch 6, 160 epochs, KITTI car-only 3D detection.
- `centerpoint_voxel0075_second_secfpn_head-dcn-circlenms_8xb4-cyclic-20e_nus-3d`: CenterPoint, 0.075 voxel, SECOND/SECFPN, DCN, circle NMS, cyclic 20 epochs, nuScenes 3D detection.
- `minkunet34_w32_spconv_8xb2-amp-laser-polar-mix-3x_semantickitti`: MinkUNet, width 32, spconv backend, AMP, laser-polar mix, 3x schedule, SemanticKITTI.
- `mask-rcnn_r50_fpn_coco-2x_1x_nuim`: Mask R-CNN, R-50/FPN, COCO pretraining schedule token, nuImages schedule.

Do not assume two names are compatible because they share only the algorithm token. Component, class-count, dataset, schedule, and backend tokens can change tensor shapes or preprocessing.

## Model-zoo row triage

When a user asks for “best”, “fastest”, “lowest memory”, or “same as this checkpoint”, collect these columns from the result row or metafile when available:

- Metric name and split: KITTI AP/AP11/AP40, nuScenes mAP/NDS, Waymo L1/L2 mAP/mAPH, segmentation mIoU, nuImages box/mask AP.
- Memory and inference time, noting that model-zoo memory often reports allocated CUDA memory and inference timing excludes data loading.
- Checkpoint availability and license caveats.
- Training hardware/batch schedule, AMP flag, TTA flag, and backend.
- Dataset split or reduced-data marker such as Waymo `D5`.

If metrics come from different datasets, class settings, schedules, or backend variants, present them as non-comparable rather than ranking them directly.

## Project vs core configs

Core config families are importable from normal MMDetection3D package modules when the OpenMMLab stack and required backend packages are installed. Project configs are shipped as optional research extensions and may rely on additional project packages or custom imports. For project-family config selection:

- It is acceptable to identify the likely project family and config/checkpoint match here.
- Do not promise that a project config will build until custom imports and optional dependencies are checked.
- Route project installation, registry wiring, or custom imports to `customization-extensions`.
- Route actual inference/training once the project import path is verified.

## Dataset-index implications

The dataset index confirms common dataset roots and converter scripts for some datasets, but config selection still needs the exact prepared files:

| Dataset key | Usual data root | Config implications |
| --- | --- | --- |
| `kitti` | `data/kitti` | Car-only vs 3-class configs change class names, heads, metrics, and annotations. |
| `nuscenes` | `data/nuscenes` | Multi-sweep loading, 10-class metadata, and NDS/mAP evaluators are common. |
| `semantickitti` | `data/semantickitti` | Semantic segmentation configs often include sparse backends and mIoU evaluation. |

If a user has raw data, missing info files, stale v1 info pickles, or a custom layout, route to `data-preparation` before treating a model-zoo config as runnable.
