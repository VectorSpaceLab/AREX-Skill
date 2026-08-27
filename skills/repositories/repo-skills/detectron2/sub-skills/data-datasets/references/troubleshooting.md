# Data and Dataset Troubleshooting

Use this when Detectron2 fails before or during data loading. Fix the data/registration issue first; route model/config changes to the appropriate training/config sub-skill.

## Registration Failures

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `Dataset 'x' is not registered` | `cfg.DATASETS.TRAIN` / `TEST` names do not match process-local registration. | Import and run the registration code before building loaders/trainers; check `DatasetCatalog.list()`. |
| Duplicate-name assertion in `DatasetCatalog.register` | Re-registering the same name in one process. | Guard with `if name not in DatasetCatalog.list(): ...`, choose a unique split name, or remove only in isolated tests. |
| Dataset changes between epochs/runs | Dataset function shuffles, samples, reads unsorted directory listings, or mutates records. | Make the function deterministic: sort inputs, return fresh records, keep randomness in samplers/mappers. |
| Empty dataset assertion | Loader resolved a name but the registered function returned `[]`, or all records were filtered. | Validate paths/filters; if images with no objects are intentional, review `DATALOADER.FILTER_EMPTY_ANNOTATIONS`. |
| Metadata `Attribute ... cannot be set to a different value` | Same dataset name reused with different metadata. | Use unique names per dataset/split/version, or set metadata once consistently. |

## Dataset Dict Errors

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Missing `file_name`, `height`, `width`, or `image_id` | Record is not in the standard format expected by builtin components. | Add common image fields for standard tasks; if intentionally custom, provide a custom mapper and avoid default assumptions. |
| Image size mismatch | `height`/`width` do not match the loaded image after EXIF handling or conversion. | Recompute dimensions from the actual image files; validate with a small loader smoke test. |
| Invalid `bbox_mode` or box conversion errors | Unsupported relative mode, typo, or raw string instead of `BoxMode` integer/enum. | Use `BoxMode.XYXY_ABS`, `BoxMode.XYWH_ABS`, or `BoxMode.XYWHA_ABS`; JSON fixtures can use integers `0`, `1`, or `4`. |
| Bad `category_id` assertion or histogram error | Category ids are not zero-based contiguous or exceed class count. | Remap raw ids to `[0, num_classes - 1]`; ensure `thing_classes` length matches. |
| Polygon mask error | Polygon has odd coordinate count, fewer than 3 points, or wrong nesting. | Use `[[x1, y1, x2, y2, x3, y3, ...]]`; for bitmasks use valid COCO RLE with `INPUT.MASK_FORMAT='bitmask'`. |
| Keypoint flip error | Keypoint list count differs from metadata or flip indices are missing. | Set `keypoint_names` and `keypoint_flip_map`; ensure each annotation has `3 * len(keypoint_names)` values. |
| Images with annotations disappear from training | All annotations are crowd, empty, or filtered after transforms. | Check `iscrowd`, `DATALOADER.FILTER_EMPTY_ANNOTATIONS`, crop settings, and empty boxes/masks after augmentation. |

Run `scripts/validate_dataset_dicts.py fixture.json --num-classes N` to catch many of these before loader construction.

## COCO Helper Failures

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| File-not-found from JSON or images | Wrong `json_file`, `image_root`, current working directory, or `DETECTRON2_DATASETS`. | Use application-resolved paths and confirm images referenced by JSON exist under `image_root`. |
| `Encountered category_id=... but this id does not exist in categories` | Annotation references a raw COCO category id absent from JSON `categories`. | Fix the JSON categories or annotation ids before loading. |
| Empty bbox error | COCO annotation has `bbox: []`. | Remove or repair invalid annotations. |
| Duplicate annotation id assertion | Non-unique annotation ids in a COCO JSON. | Assign unique annotation ids or regenerate the JSON. |
| Missing metadata for COCO evaluation | Dataset registered manually without `json_file`, `thing_classes`, or id mapping. | Prefer `register_coco_instances`, or set equivalent metadata explicitly. |
| Cached COCO conversion seems stale | Converted COCO JSON cache was reused after dataset changed. | Delete the cached conversion output or disable cached conversion where the evaluator exposes that option. |

## Metadata and Evaluation Readiness

| Need | Required metadata/config | Notes |
| --- | --- | --- |
| Instance visualization/evaluation | `thing_classes`; for COCO also `json_file` and id mapping | `register_coco_instances` sets COCO metadata. |
| Semantic segmentation | `stuff_classes`, `ignore_label`, `SEM_SEG_HEAD.NUM_CLASSES` | Semantic label ids must match the training/eval expectation. |
| Keypoints | `keypoint_names`, `keypoint_flip_map`, `ROI_KEYPOINT_HEAD.NUM_KEYPOINTS`, OKS sigmas for eval | Keypoint arrays must align with metadata order. |
| Mixed datasets | Consistent metadata values across names | Detectron2 checks some metadata consistency when loading multiple datasets. |

If a failure is about number of classes, incompatible predictor layers, solver schedule, evaluator choice, distributed launch, or checkpoints, stop data debugging and route to training/evaluation/config guidance.

## Mapper and Loader Failures

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `KeyError: 'image'` or model input missing fields | Mapper did not return builtin model input format. | Return `image` tensor and task fields such as `instances` or `sem_seg`. |
| Custom keys vanish | Default `DatasetMapper` ignores or removes fields not wired into its logic. | Write a custom mapper that consumes and returns task-specific fields. |
| Custom annotations are not transformed | Extra coordinates/masks are not passed through the returned transform. | Use `transform.apply_coords`, `apply_polygons`, `apply_segmentation`, or a registered transform type. |
| Multiprocessing loader hangs or pickling errors | Dataset records or mapper closure contain unpickleable objects. | Keep records JSON-like and mapper functions importable; first debug with `num_workers=0`. |
| Aspect-ratio grouping error | Records lack `height`/`width`, or custom mapper removes them before grouping. | Keep dimensions available or disable `aspect_ratio_grouping`. |
| Iterable dataset sampler assertion | Iterable datasets were passed with a sampler. | Use `sampler=None` for iterable datasets. |
| Batch-size divisibility assertion | `total_batch_size` not divisible by distributed world size. | Adjust total batch size in config/training setup. |

## A Minimal Debug Order

1. Confirm registration names: `DatasetCatalog.list()` includes every name in config.
2. Retrieve records twice and compare length/order/image ids.
3. Validate a JSON fixture with `scripts/validate_dataset_dicts.py`.
4. Confirm metadata: `MetadataCatalog.get(name).as_dict()` includes the keys your task needs.
5. Build a one-batch loader with `num_workers=0`, minimal augmentations, and an explicit mapper.
6. Re-enable custom augmentations, multiprocessing workers, samplers, and full training one at a time.
