---
name: data-transforms-datasets
description: "Prepare and validate GluonCV datasets, data transforms, batchify
  functions, metrics, and visualization helpers."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# GluonCV data transforms and datasets

Use this sub-skill when the task is about GluonCV dataset roots/layouts, object-detection records, segmentation/classification/video/tracking/re-id/depth datasets, image or bounding-box transforms, preset data transforms, `DataLoader` batchification, data metrics, or visualization helpers.

## Natural triggers

Load this sub-skill for requests mentioning:

- GluonCV datasets or `gluoncv.data.*` classes.
- Pascal VOC, COCO, ADE20K, Cityscapes, ImageNet, Kinetics, UCF101, HMDB51, Something-Something-V2, Market1501, OTB, KITTI, MHP, VisDrone, LST, or RecordIO.
- Bounding-box transforms, image resize/crop/flip/ten-crop, mask/pose/video transforms, or detector presets for SSD, Faster R-CNN, Mask R-CNN, YOLO, and CenterNet.
- `Stack`, `Pad`, `Append`, `Tuple`, `FasterRCNNTrainBatchify`, `MaskRCNNTrainBatchify`, `DetectionDataLoader`, or `RandomTransformDataLoader`.
- Dataset preparation helpers, frame extraction, train/val list building, `--download-dir`, `--no-download`, `--overwrite`, or ImageRecord conversion.
- Detection annotation validation before passing records into GluonCV transforms or training scripts.

## Route away

- Model name selection, model instantiation, custom heads, and MXNet model dry-runs: use `../mxnet-model-zoo/`.
- PyTorch action-recognition models, configs, DirectPose, or Torch DDP: use `../torch-video-workflows/`.
- Full training/evaluation/demo command assembly from the script zoo: use `../training-evaluation-scripts/`.
- AutoGluon wrappers, deployment, ONNX, TVM, or export: use `../automl-deployment-export/`.

## First workflow choice

1. **Identify the data family and root.** Use [datasets-and-transforms.md](references/datasets-and-transforms.md) to pick a dataset class, expected layout, split argument, and optional dependencies. Prefer passing explicit `root=`/`setting=` instead of relying on default user home directories when an experiment uses project-local data.
2. **Validate custom detection annotations early.** For simple JSON records, run [validate_detection_record.py](scripts/validate_detection_record.py) before involving MXNet/GluonCV. For LST/RecordIO or VOC-like data, compare against the schemas in [datasets-and-transforms.md](references/datasets-and-transforms.md).
3. **Wire transforms with label semantics.** Geometric image transforms that change size, crop, or flip require the corresponding bbox/mask/pose transform. Use [api-reference.md](references/api-reference.md) for coordinate order, size argument order, preset transform inputs, and batchify pairing.
4. **Choose batchify by output shape.** Use `Stack` only for same-shaped arrays, `Pad` for variable-length labels, `Append` for ragged per-sample structures, and `Tuple(...)` to apply a per-field function to `(image, label, ...)` samples.
5. **Add diagnostics and visual checks.** Use GluonCV visualization helpers (`plot_bbox`, `plot_image`, segmentation palettes) and metrics only after validating data format. Keep display/non-headless concerns separate from dataset parsing.
6. **If data is large or network-bound, plan without running downloads.** Dataset preparation scripts are reference-only for this skill; record the required archives, flags, generated folders/lists/RecordIO files, and storage constraints before asking to run a large command.

## Core facts to preserve

- Detection labels consumed by GluonCV dataset/transforms use `[xmin, ymin, xmax, ymax, class_id]` plus optional extra columns. VOC labels include an additional `difficult` column.
- Bbox size tuples are `(width, height)`, while image tensors are HWC. Mixing these orders is a common source of silent annotation corruption.
- COCO detection/instance/keypoints classes rely on `pycocotools` and the COCO category order matching the class list.
- Video datasets generally require decoded frame folders plus a setting/list file; `decord` is optional for direct video loading.
- Most built-in datasets default under `~/.mxnet/datasets/...`; production workflows should pass explicit roots when data is not there.

## References and helper

- [Dataset layouts and workflows](references/datasets-and-transforms.md)
- [API reference for transforms, batchify, metrics, and viz](references/api-reference.md)
- [Data troubleshooting](references/troubleshooting.md)
- [Custom detection record validator](scripts/validate_detection_record.py)
