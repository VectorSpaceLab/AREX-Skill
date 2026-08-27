# CVAT formats and data flows

CVAT can import/export annotations at both task and project scope. The correct workflow depends on whether the user needs CVAT fidelity, ML training compatibility, images, video tracks, or a backup.

## Operation map

| Need | CLI | SDK | Notes |
|---|---|---|---|
| Create task with data | `cvat-cli task create NAME local|remote|share RES...` | `client.tasks.create_from_data(...)` | Requires labels or existing project id. |
| Import task annotations | `cvat-cli task import-dataset --format FMT TASK_ID FILE` | `task.import_annotations(FMT, FILE)` | Existing task data/labels must match. |
| Export task dataset | `cvat-cli task export-dataset --format FMT --with-images yes|no TASK_ID OUT` | `task.export_dataset(FMT, OUT, include_images=...)` | Use `--with-images yes` only when downstream needs image files. |
| Project import | `cvat-cli project import-dataset --format FMT PROJECT_ID FILE` | `project.import_dataset(FMT, FILE)` | Can create/update project tasks from a dataset. |
| Project export | `cvat-cli project export-dataset --format FMT --with-images yes|no PROJECT_ID OUT` | `project.export_dataset(FMT, OUT, include_images=...)` | Good for complete project-level ML export. |
| Backup/restore | `task backup`, `project backup`, `create-from-backup` | `download_backup()`, `create_from_backup()` | CVAT-to-CVAT restore, not a generic training format. |
| Frames | `cvat-cli task frames TASK_ID FRAME...` | `task.download_frames(...)` | Use for QA/sample extraction, not full dataset export. |

## Supported format families

| Format family | Best for | Common caveats |
|---|---|---|
| CVAT image/video XML | CVAT round-trip, preserving CVAT-specific shapes and attributes | Choose image vs video variant to match task type; not every external ML tool reads it. |
| COCO / COCO Keypoints | Detection, instance/semantic segmentation, keypoints | Verify category/attribute mapping and mask/polygon expectations. |
| YOLO 1.1 | Detection workflows | Usually boxes/class ids; attributes and complex shapes are limited. |
| Ultralytics YOLO Detection/Segmentation/Pose/OBB/Classification | YOLOv8-style pipelines | Pick the exact variant matching labels/shapes; pose and oriented boxes have stricter label layouts. |
| Datumaro | Conversion and dataset tooling | Good interchange format, but downstream conversions may lose unsupported fields. |
| Pascal VOC | Detection/classification XML pipelines | Limited attribute/shape support. |
| KITTI | 2D/3D detection and point-cloud related workflows | Match camera/point-cloud expectations carefully. |
| MOT / MOTS | Video tracking/detection | Track ids and frame indexing matter; not for generic image classification. |
| Cityscapes / CamVid / Segmentation Mask | Semantic segmentation | Masks/polygons and label palettes must be validated. |
| Open Images / WIDER Face / VGGFace2 / LFW / Market-1501 / ICDAR / ImageNet / LabelMe | Dataset-specific ML tasks | Use only when the target tool expects that exact layout. |

## Choosing `include_images` / `--with-images`

- Use `false`/`no` when only annotations are needed and the downstream system already has the images.
- Use `true`/`yes` for portable training archives, backups for external processing, or handoff to a user without the original image source.
- Large projects can create large archives and long background jobs. Test on a small task first and document expected storage.

## Format compatibility checklist

Before import/export, answer:

1. Is the task image, video, or 3D/point-cloud?
2. Which shape types are present: tags, rectangles, oriented boxes, polygons, polylines, points, cuboids, skeletons, ellipses, masks, tracks?
3. Are attributes important? Does the target format preserve them?
4. Are video tracks needed or only per-frame shapes?
5. Does the format require images, a specific directory layout, or a label map file?
6. Is mask conversion requested (`conv_mask_to_poly` / "return masks as polygons")?
7. Are labels named exactly as expected by the downstream model/tool?

## SDK examples

```python
# Export annotations only.
task.export_dataset("COCO 1.0", "task-coco.zip", include_images=False)

# Import annotations and let CVAT convert masks to polygons if supported.
task.import_annotations("CVAT 1.1", "annotations.zip", conv_mask_to_poly=True)

# Project-level data exchange.
project.import_dataset("Datumaro 1.0", "dataset.zip")
project.export_dataset("YOLO 1.1", "project-yolo.zip", include_images=True)
```

## CLI examples

```bash
cvat-cli --profile prod task export-dataset --format "CVAT for images 1.1" --with-images no 42 annotations.zip
cvat-cli --profile prod project export-dataset --format "Datumaro 1.0" --with-images yes 7 dataset.zip
cvat-cli --profile prod task import-dataset --format "COCO 1.0" 42 annotations.zip
```

Use `cvat-cli <resource> export-dataset --help` to confirm flag spelling for the installed CLI version.
