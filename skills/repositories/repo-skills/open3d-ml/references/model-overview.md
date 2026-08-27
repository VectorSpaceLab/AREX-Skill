# Open3D-ML Model and Workflow Overview

## Purpose

Read this when you need the big-picture route map for Open3D-ML.
Use the sub-skills for detailed instructions and keep this page as a quick
index.

## Main workflow families

### Install and inspect

Use `install-and-inspect` when the first task is to make Open3D-ML importable
and verify the backend stack.

### Dataset processing and customization

Use `datasets-and-preprocessing` when the task is about dataset directories,
splits, custom point-cloud layouts, or preprocessing validation.

### Training and pipelines

Use `training-and-pipelines` when the task is about model selection,
config-driven training, inference, evaluation, or registry lookup.

### Visualization and extensions

Use `visualization-and-extensions` when the task is about point-cloud
inspection, bounding boxes, TensorBoard summaries, or OpenVINO.

## Common model families

- Semantic segmentation: RandLANet, KPConv/KPFCNN, SparseConvUnet,
  PointTransformer, PVCNN
- Object detection: PointPillars, PointRCNN

## Common dataset families

- SemanticKITTI
- KITTI
- S3DIS
- Toronto3D
- Semantic3D
- ParisLille3D
- ScanNet
- Waymo
- nuScenes
- Lyft
- Argoverse
- Pandaset
- ShapeNet
- SunRGBD
- MatterportObjects
- TUMFacade

## Extension notes

- PyTorch is the primary verified backend for this skill bundle.
- TensorFlow is optional and depends on the Open3D build.
- OpenVINO is optional and only covers a subset of models.
- GUI visualization may be unavailable in headless environments, so keep the
  fixture and summary helpers handy.

## Quick selection rule

If the user mentions a model name, choose `training-and-pipelines`.
If the user mentions a dataset path or split, choose
`datasets-and-preprocessing`.
If the user mentions a window, box drawing, or TensorBoard summary, choose
`visualization-and-extensions`.
If the user cannot import the package yet, choose `install-and-inspect`.
