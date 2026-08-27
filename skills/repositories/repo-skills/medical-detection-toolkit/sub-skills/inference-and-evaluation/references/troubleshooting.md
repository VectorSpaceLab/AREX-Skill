# Inference and evaluation troubleshooting

| Symptom | Likely cause | Recovery |
|---|---|---|
| Predictor cannot construct a network | Missing checkpoint, wrong model path, or legacy custom-op import failure | Validate config/snapshot first, then route model imports to [models-and-architectures](../../models-and-architectures/SKILL.md) and [cuda-extensions](../../cuda-extensions/SKILL.md). |
| Patient output has the wrong nesting | `boxes` are grouped by batch/slice/patient differently from the evaluator contract | Validate with `validate_evaluation_records.py`; preserve patient IDs and distinguish 2D slices from 3D records. |
| WBC merges unrelated lesions | `wcs_iou` is too high/low, class IDs were mixed, or patch overlap metadata is missing | Validate raw detections with `validate_wbc_inputs.py`, keep raw outputs immutable, and adjust one threshold at a time. |
| WBC rejects an input | Detection rows do not use 2D five-column or 3D seven-column shape, or `box_patch_id` is not parallel | Fix the input schema; do not pad coordinates or invent patch IDs. |
| 2D-to-3D merging produces missing slices | Slice coordinates, `merge_3D_iou`, or patient shape metadata are inconsistent | Check the data route's `patch_crop_coords`, z ordering, and original image shape before changing consolidation thresholds. |
| AP/AUC is empty or errors | No detections, missing ground truth fields, or only one patient class | Validate records and class coverage; a single-class cohort cannot support a meaningful ROC/AUC claim. |
| Fold aggregation misses outputs | Fold directory, saved epoch count, or stored prediction filename is inconsistent | Confirm experiment lifecycle and stored settings through [configuration-and-experiments](../../configuration-and-experiments/SKILL.md); do not recompute missing checkpoints silently. |
| Plotting fails on a headless machine | Interactive Matplotlib backend or unwritable output path | Choose a non-interactive backend and disposable output directory; separate visualization failure from metric correctness. |
| A metric looks unexpectedly good/bad | Threshold, class mapping, IoU convention, or data split changed | Record `cf.class_dict`, `ap_match_ious`, `min_det_thresh`, fold split, and raw prediction provenance before interpreting results. |

Never present a metric as a model-quality result without checkpoint, dataset,
fold, class, threshold, and preprocessing provenance. External data, long
inference, and custom CUDA runtime failures remain explicit stop conditions.
