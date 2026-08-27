# Model Overview

## Purpose

Read this when you need to choose a model family or confirm which tasks and
datasets are commonly paired with a given Open3D-ML workflow.

## Verified model families

### Semantic segmentation

- RandLANet
- KPFCNN / KPConv
- SparseConvUnet
- PointTransformer
- PVCNN

Common dataset pairings in this repo include:

- SemanticKITTI
- S3DIS
- Toronto3D
- Semantic3D
- ParisLille3D
- ScanNet

### Object detection

- PointPillars
- PointRCNN

Common dataset pairings in this repo include:

- KITTI
- Waymo
- nuScenes
- Lyft
- Argoverse

## Backend notes

- PyTorch was verified in the private inspection environment.
- TensorFlow support is optional and depends on how Open3D was built.
- CUDA/GPU workflows exist in the repo, but they are optional for the CPU smoke
  path used to verify this skill bundle.
- OpenVINO is supported for a subset of models, but it is an optional
  extension, not a core requirement.

## Checkpoint conventions

- `ckpt_path` is the usual field for pretrained weights.
- Model zoo entries are named by model family and dataset, for example:
  `randlanet_semantickitti`, `kpconv_s3dis`, `pointpillars_kitti`.
- Keep checkpoint downloads out of the default smoke path; treat them as an
  optional or downstream task-specific step.

## How to choose

- Choose RandLANet when you want a straightforward semantic-segmentation
  workflow.
- Choose KPConv when you need another strong segmentation baseline.
- Choose PointPillars for KITTI-style object detection.
- Choose PointRCNN when you need a two-stage detection workflow.

## Practical advice

If a user only knows the dataset, start from the repo's matching config file
and then inspect the model family and pipeline name before changing the task.
