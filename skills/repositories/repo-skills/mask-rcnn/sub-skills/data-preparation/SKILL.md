---
name: data-preparation
description: "Guides Mask_RCNN dataset subclassing, mask formats, sample dataset
  layouts, validation, resizing, and synthetic fixtures."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Data Preparation

Use this sub-skill when a task asks how to prepare images, masks, polygons, COCO annotations, VIA JSON, nucleus challenge folders, or custom `mrcnn.utils.Dataset` subclasses for Mask_RCNN.

## Read first by need

- Read [dataset-contract.md](references/dataset-contract.md) for the `Dataset` subclass lifecycle and mask/image requirements.
- Read [data-formats.md](references/data-formats.md) for Shapes, Balloon/VIA, COCO, and Nucleus layouts.
- Read [troubleshooting.md](references/troubleshooting.md) when masks are empty, classes mismatch, polygons fail, or image sizes are wrong.
- Run [scripts/validate_dataset_layout.py](scripts/validate_dataset_layout.py) to check known sample layout conventions without importing Mask_RCNN.
- Run [scripts/generate_shapes_fixture.py](scripts/generate_shapes_fixture.py) to create a tiny synthetic fixture for smoke tests or documentation examples.

## Dataset preparation workflow

1. Subclass `mrcnn.utils.Dataset`.
2. In a loader method, call `add_class(source, class_id, class_name)` and `add_image(source, image_id, path, **metadata)` for each image.
3. Implement `load_mask(image_id)` to return:

   ```python
   mask: np.ndarray  # shape [height, width, instance_count], bool or 0/1
   class_ids: np.ndarray  # shape [instance_count], dtype int32
   ```

4. Override `load_image()` only when images are generated or not stored as ordinary files.
5. Call `dataset.prepare()` before using `dataset.image_ids`, `class_names`, `source_class_ids`, `load_image_gt`, training, or visualization.
6. Use `mrcnn.model.load_image_gt(dataset, config, image_id, augmentation=..., use_mini_mask=...)` to check the full preprocessing path.

## Data-specific routes

- **VIA polygons / Balloon-style one-class dataset**: validate folder split and `via_region_data.json`; read [data-formats.md](references/data-formats.md#balloon--via-polygons).
- **COCO**: validate `annotations/instances_<subset><year>.json` plus `<subset><year>/` images; pycocotools is required for actual loading and evaluation.
- **Nucleus / Data Science Bowl**: validate `<image_id>/images/<image_id>.png` and optional `<image_id>/masks/*.png`; RLE output is owned by [inference-evaluation](../inference-evaluation/SKILL.md).
- **Synthetic Shapes**: use generated shapes for quick data-pipeline checks; do not treat them as proof of real dataset quality.

## Boundary notes

This sub-skill validates and explains data. For training schedules, layer choices, checkpoints, and weight loading, route to [training](../training/SKILL.md). For prediction outputs, COCO AP, visualization, color splash, or RLE submission files, route to [inference-evaluation](../inference-evaluation/SKILL.md).
