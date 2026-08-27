---
name: dataset-ops
description: "Move CVAT data between tasks, projects, dataset formats,
  manifests, backups, frames, and optional PyTorch dataset adapters."
metadata:
  disco-role: operating
disable-model-invocation: true
license: MIT
---

# CVAT dataset operations

Use this sub-skill when the user asks how to import/export annotations or datasets, choose a CVAT-supported format, include or exclude images, prepare local/remote/share/cloud data sources, create dataset manifests, download frames, back up projects/tasks, convert source data before upload, or consume CVAT data through SDK/PyTorch dataset adapters.

## Route first

- Read `references/formats-and-data-flows.md` to select formats and map import/export operations to CLI and SDK calls.
- Read `references/data-preparation.md` for local/remote/share/cloud inputs, manifests, DICOM-to-image preparation, frame extraction, and validation before upload.
- Read `references/pytorch-datasets.md` for `cvat_sdk.datasets` and optional `cvat_sdk.pytorch` usage.
- Read `references/troubleshooting.md` for format/label/archive/image/mask/video-track/cache errors.
- Use `scripts/manifest_command_builder.py` to generate safe dataset-manifest commands without depending on the original repository utility script.

## Choose the interface

- Terminal automation: use `../cli-automation/SKILL.md` and its command builder.
- Python automation: use `../sdk-automation/SKILL.md` for task/project objects and import/export methods.
- Model-assisted annotation: route to `../auto-annotation/SKILL.md`.
- Server storage, Docker, Helm, browser access, or deployment storage configuration: route to `../deployment-admin/SKILL.md`.

## Common task/project data commands

```bash
# Export task annotations only.
cvat-cli --profile prod task export-dataset --format "COCO 1.0" --with-images no 42 task-coco.zip

# Export task with images when a downstream tool needs complete data.
cvat-cli --profile prod task export-dataset --format "YOLO 1.1" --with-images yes 42 task-yolo.zip

# Import annotations into an existing task.
cvat-cli --profile prod task import-dataset --format "CVAT 1.1" 42 annotations.zip

# Create project tasks from a dataset archive.
cvat-cli --profile prod project import-dataset --format "Datumaro 1.0" 7 dataset.zip

# Back up for CVAT-to-CVAT restore.
cvat-cli --profile prod task backup 42 task-backup.zip
```

The Python SDK equivalents are `Task.import_annotations()`, `Task.export_dataset()`, `Project.import_dataset()`, `Project.export_dataset()`, `download_backup()`, and `create_from_backup()`.

## Format selection rules

- Use `CVAT 1.1` / `CVAT for images 1.1` / `CVAT for video 1.1` for round-tripping CVAT annotations with maximum CVAT fidelity.
- Use `COCO 1.0` for common detection/segmentation pipelines with bounding boxes, polygons, masks, and categories.
- Use `YOLO 1.1` or Ultralytics YOLO variants for YOLO training pipelines; verify whether the task is detection, segmentation, pose, oriented boxes, or classification.
- Use `Datumaro 1.0` when interoperating with Datumaro-style conversion pipelines.
- Use format-specific references for KITTI, MOT/MOTS, Pascal VOC, Open Images, Cityscapes, CamVid, ImageNet, LabelMe, WIDER Face, VGGFace2, LFW, ICDAR, Market-1501, and segmentation masks.

Always verify shape types, attributes, tracks, video support, and whether images are included before choosing a format.
