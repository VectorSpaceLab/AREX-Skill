---
name: data-datasets
description: "Register and validate Detectron2 datasets, metadata, COCO helpers,
  mappers, and data loaders."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Detectron2 Data & Datasets

Use this sub-skill when a task is about getting data into Detectron2: registering custom datasets, checking Detectron2-standard dataset dicts, setting metadata, using COCO helpers, designing mappers, or building train/test data loaders.

## Read First

- `references/dataset-format.md` for `DatasetCatalog`, `MetadataCatalog`, standard dataset dict fields, COCO registration, metadata keys, and dataset-root conventions.
- `references/data-loading.md` for `DatasetMapper`, custom mapper patterns, augmentations, and `build_detection_train_loader` / `build_detection_test_loader` usage.
- `references/troubleshooting.md` for common registration, annotation, metadata, class-count, COCO path, and mapper failures.

## Common Workflows

1. Register a dataset by name with `DatasetCatalog.register(name, callable)`; the callable must take no arguments and return the same ordered records on every call.
2. Attach shared dataset facts through `MetadataCatalog.get(name).set(...)`, especially class names and evaluator/COCO metadata.
3. Validate records with `scripts/validate_dataset_dicts.py` before wiring them into a loader or config.
4. Use `register_coco_instances` or `load_coco_json` when annotations are COCO instance/keypoint style.
5. Pass the registered names into `cfg.DATASETS.TRAIN` / `cfg.DATASETS.TEST`, and route class-count or solver changes to the config/training sub-skills.
6. Customize loading through `DatasetMapper(..., augmentations=...)` or a custom mapper passed to `build_detection_train_loader(..., mapper=...)`.

## Bundled Helpers

- `scripts/validate_dataset_dicts.py`: validates a JSON list of Detectron2-standard dataset dicts and reports actionable schema/data-shape errors.
- `scripts/validate_dataset_registration.py`: smoke-checks catalog registration and metadata behavior with a synthetic dataset, and optionally validates a user JSON fixture.

## Boundaries

- This sub-skill owns dataset registration, metadata, dataset dict structure, COCO helpers, mapper design, loader construction, dataset roots, and annotation/loader troubleshooting.
- Use the training/evaluation sub-skill for `DefaultTrainer`, launch commands, evaluators, class-count config changes, and metrics.
- Use the inference/visualization sub-skill for rendering predictions or dataset visualizations.
- Use extension-projects guidance for project-specific dataset converters or custom task heads.
