# Datasets and Weights

Read this before planning YOLOv5 training, validation, download, or checkpoint workflows. Dataset scripts and named weights can perform network downloads and write outside the repository; plan paths and budgets before running them.

## Dataset config patterns

### Detection YAMLs

Detection training/validation uses YAML files with image locations and class metadata. Common examples include `coco128.yaml`, `coco.yaml`, `VOC.yaml`, `Objects365.yaml`, `VisDrone.yaml`, `xView.yaml`, `SKU-110K.yaml`, and `GlobalWheat2020.yaml`.

Typical fields:

```yaml
path: ../datasets/coco128
train: images/train2017
val: images/train2017
names:
  0: person
  1: bicycle
```

Guidance:

- Resolve `path`, `train`, `val`, and optional `test` relative to the working directory/config semantics before launching a run.
- The number of names must match the model head's class count when training from scratch or when remapping a checkpoint.
- Detection labels are YOLO text files with normalized `class x_center y_center width height` rows.
- `coco128.yaml` is the usual tiny smoke dataset; full COCO downloads are large.

### Segmentation YAMLs

Segmentation uses detection-like YAMLs but labels include polygon segments. `coco128-seg.yaml` is the small segmentation smoke configuration; full COCO segments require explicit download flags and much larger storage.

Guidance:

- Use `*-seg.pt` checkpoints with segmentation scripts.
- Detection-only label files are not enough for segmentation training.
- Validate whether mask options such as `--overlap`, `--mask-ratio`, or `--retina-masks` apply to the selected script/mode.

### Classification data

Classification workflows accept named datasets or directories. Directory data follows an ImageFolder-style layout:

```text
root/
  train/
    class_a/*.jpg
    class_b/*.jpg
  val/
    class_a/*.jpg
    class_b/*.jpg
```

Guidance:

- Named datasets such as `mnist`, `fashion-mnist`, `cifar10`, `cifar100`, `imagenette`, `imagewoof`, and `imagenet` may download data.
- Full ImageNet downloads are huge and may require external access; prefer small named datasets or local fixtures for tests.
- Class order is inferred from directory names unless a workflow states otherwise.

## Download scripts and side effects

The repository includes data/model download helpers. Do not run them by default during planning or verification.

| Script family | Purpose | Side effects / risk |
| --- | --- | --- |
| `download_weights.sh` | Downloads P5, P6, classification, and segmentation checkpoints. | Network access and multiple checkpoint files. |
| `get_coco128.sh` | Downloads COCO128. | About tens of MB; writes under a datasets directory. |
| `get_coco.sh` | Downloads COCO labels/images; optional segments. | Can download 1 GB to 20+ GB depending on train/val/test/segments flags. |
| `get_imagenet*.sh` | Downloads ImageNet subsets or full ImageNet. | Ranges from small subsets to 100+ GB; may require upstream dataset access. |

Prefer explicit user approval, disk estimates, and output paths before running download scripts.

## Checkpoint families

| Family | Examples | Task |
| --- | --- | --- |
| P5 detection | `yolov5n.pt`, `yolov5s.pt`, `yolov5m.pt`, `yolov5l.pt`, `yolov5x.pt` | 640-pixel object detection. |
| P6 detection | `yolov5n6.pt`, `yolov5s6.pt`, `yolov5m6.pt`, `yolov5l6.pt`, `yolov5x6.pt` | 1280-pixel object detection. |
| Segmentation | `yolov5n-seg.pt`, `yolov5s-seg.pt`, `yolov5m-seg.pt`, `yolov5l-seg.pt`, `yolov5x-seg.pt` | Instance segmentation. |
| Classification | `yolov5n-cls.pt`, `yolov5s-cls.pt`, `yolov5m-cls.pt`, `yolov5l-cls.pt`, `yolov5x-cls.pt` | Image classification. |
| TorchVision classifiers | `resnet50`, `efficientnet_b0`, etc. | Classification training through torchvision model names. |

Use the checkpoint family that matches the task script. A detection checkpoint in a segmentation workflow or a segmentation checkpoint in detection autoshape paths can produce confusing shape or unsupported-output behavior.

## Data/weight planning checklist

Before executing a command, confirm:

1. Task family: detection, segmentation, or classification.
2. Dataset source: local path, named dataset, YAML, or download script.
3. Download approval: network, size, output directory, and cache behavior.
4. Class count and names.
5. Checkpoint family and whether it is local or downloadable.
6. Device and precision expectations.
7. Output directory (`project`, `name`, `exist_ok`) to avoid overwriting or mixing runs.
