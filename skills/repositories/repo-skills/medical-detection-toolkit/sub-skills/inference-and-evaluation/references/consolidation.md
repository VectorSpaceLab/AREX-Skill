# Consolidation and dimensional merging

**Primary evidence:** the repository's WBC/merging implementation and README
description of Weighted Box Clustering. The formulas here are source-backed;
their accuracy on a particular dataset is not verified.

## Weighted box clustering (WBC)

`apply_wbc_to_patient([boxes_by_batch, pid, class_dict, wcs_iou, n_ens])` processes each batch instance and foreground class. It selects only `box_type == 'det'` and `box_pred_class_id == class_id`, passes an array plus patch IDs to `weighted_box_clustering`, emits new detection dictionaries, and appends all `gt` boxes unchanged. Consolidated detections intentionally do not retain patch metadata.

For 2D, each row passed to `weighted_box_clustering` is:

```text
[y1, x1, y2, x2, box_score, box_patch_center_factor, box_n_overlaps]
```

For 3D it is:

```text
[y1, x1, y2, x2, z1, z2, box_score, box_patch_center_factor, box_n_overlaps]
```

`box_patch_id` is a parallel array. Validate this exact shape and metadata with [`validate_wbc_inputs.py`](../scripts/validate_wbc_inputs.py) before a large analysis run.

### Matching and weighted average

For each highest-scoring remaining detection, the implementation:

1. Computes inclusive box areas (`end - start + 1`) in 2D or 3D.
2. Computes IoU against every remaining detection, including the seed itself.
3. Defines a cluster using the **strict** condition `IoU > thresh`; `IoU == thresh` does not match. `thresh` is the configured `cf.wcs_iou`.
4. Computes each member's weight as `IoU_to_seed * member_area * member_box_patch_center_factor`.
5. Multiplies member scores by those weights for the weighted score/coordinate averages.
6. Estimates expected predictions as `n_expected_preds = n_ens * mean(box_n_overlaps)`. `n_ens` is the number of temporal models times four if XY test augmentation is enabled, and additionally times the number of folds in hold-out aggregation.
7. Computes missing predictions as `max(0, n_expected_preds - number_of_unique_patch_ids_in_cluster)`, assigns missing entries the mean cluster weight, and divides the weighted score sum by present plus missing weights.
8. Averages coordinates using the weighted scores of present members. It retains a cluster only when the resulting score is strictly greater than `0.01`.
9. Removes matched rows and repeats with the next highest remaining score.

Consequences to make explicit in experiment notes:

- WBC is not ordinary NMS: box size, patch-centering, overlap count, ensemble count, and score all affect the result.
- Changing `test_aug`, `test_n_epochs`, fold aggregation, or patching changes `n_ens`; applying the wrong count changes missing-prediction penalties and final scores.
- A high `wcs_iou` splits more nearby detections; a low value joins more boxes. The source does not provide a universally correct threshold. Tune only on an explicitly identified validation protocol.
- Empty classes are skipped. Non-finite coordinates/scores, missing metadata, zero/negative areas, or zero total weights are not repaired by the source and must be rejected before calling it.

## 2D-to-3D merge

`merge_2D_to_3D_preds_per_patient([boxes_by_slice, pid, class_dict, merge_3D_iou])` is used when a 2D model's slice detections must be evaluated as 3D cubes. It operates class-by-class:

1. Collects all `det` boxes from all slice lists and records the batch index as `slice_id`.
2. Calls `nms_2to3D` on `[y1, x1, y2, x2, score, slice_id]`.
3. The NMS-like match uses XY IoU only and the strict condition `IoU > merge_3D_iou` (default `cf.merge_3D_iou` is `0.1`).
4. The highest-score matching box is the core slice. Matching slices are kept only across a contiguous interval around the core; a missing slice (“hole”) stops the interval on that side. The output z coordinates are one slice beyond the valid minimum and maximum: `[min_connected_slice - 1, max_connected_slice + 1]`.
5. The kept seed's XY coordinates and score become a cube; all GT boxes from all input slices are appended, and the result is wrapped in one dummy batch list.

This is not volumetric IoU and does not fill arbitrary holes. A noisy low-confidence detection can bridge slices and alter a cube boundary, while a missing slice can split a lesion into multiple clusters. The source docstring itself recommends a suitable minimum confidence in the broader pipeline, but this function does not apply a separate confidence threshold.

## Ordering and safety checks

- Apply WBC before 2D-to-3D merging when using the normal `Predictor`/`analysis` flow. Merging first would treat patch/epoch/mirror duplicates as separate slice detections.
- Do not apply WBC twice: consolidated boxes no longer have `patch_id`, `box_patch_center_factor`, and `box_n_overlaps`.
- Preserve `pid` and list nesting when mapping over patients. A mismatch in patient order during hold-out fold aggregation can silently associate boxes with the wrong ID, so compare IDs before flattening.
- Use the same class map and coordinate convention in model output, WBC, merger, evaluator, and CSV writer. 2D coordinates are `[y1,x1,y2,x2]`; 3D coordinates append `[z1,z2]`.
- Keep raw pickle files. If a threshold experiment changes output, record `wcs_iou`, `merge_3D_iou`, `test_aug`, `test_n_epochs`, patching, fold list, and `min_det_thresh` alongside the derived result.

## Cross-links

- Input shape and patch creation: [data-and-preprocessing](../../data-and-preprocessing/SKILL.md).
- Configuration and CLI flags: [configuration-and-experiments](../../configuration-and-experiments/SKILL.md).
- Model output dictionaries: [models-and-architectures](../../models-and-architectures/SKILL.md).
- Native NMS/RoIAlign prerequisites (not WBC): [cuda-extensions](../../cuda-extensions/SKILL.md).
- Downstream record/metric meaning: [evaluation](evaluation.md).
