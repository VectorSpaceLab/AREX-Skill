# Evaluation and metric records

**Primary evidence:** the repository's Evaluator, model box utilities,
plotting, and CSV-helper implementations. Validate the portable record shape
with [`validate_evaluation_records.py`](../scripts/validate_evaluation_records.py)
before invoking `Evaluator`.

## Input result nesting

`Evaluator.evaluate_predictions(results_list, monitor_metrics=None)` accepts two source forms:

- `mode='train'` or `mode='val_sampling'`: `[[batch_boxes, batch_pids], ...]`, where `batch_boxes` is a list of box-lists and `batch_pids` has one patient ID per batch element. The evaluator flattens batch elements.
- `mode='val_patient'` or `mode='test'`: `[[patient_boxes, pid], ...]`, where `patient_boxes` is a list of batch-instance box-lists. For 3D this normally has one dummy batch instance; for unmerged 2D it has one list per slice.

Each box-list can contain:

```python
# detection
{'box_type': 'det', 'box_coords': [y1, x1, y2, x2],
 'box_score': 0.0, 'box_pred_class_id': 1}
# or 3D coordinates [y1, x1, y2, x2, z1, z2]

# ground truth
{'box_type': 'gt', 'box_coords': [y1, x1, y2, x2], 'box_label': 1}
```

The validator accepts JSON/JSONL records with the equivalent lists/dictionaries and rejects non-finite values, invalid nesting, mixed 2D/3D coordinates in a box list, unknown types, missing fields, and invalid score/class values. It is deliberately independent of the checkout and does not calculate metrics.

## Matching and internal dataframe

For every configured `cf.ap_match_ious` and every class in `cf.class_dict`, the evaluator compares detections and GTs within each batch instance using `utils.model_utils.compute_overlaps`. A candidate is a match when its maximum GT IoU is **strictly greater** than the current matching IoU.

The source then records:

- matched detection: `det_tp`, score as emitted, binary label `1`;
- candidate with no match: `det_fp`, emitted score, binary label `0`;
- duplicate candidates assigned to the same GT: highest-score candidate remains `det_tp`, other assigned candidates become `det_fp`;
- unmatched GT: `det_fn`, synthetic score `0`, binary label `1`;
- patient/batch instance with no records for that class: one `patient_tn`, synthetic score `0`, binary label `0`.

The internal `self.test_df` has exactly these columns:

| Column | Meaning |
|---|---|
| `pred_score` | Detection confidence, or `0` for FN/TN synthetic entries. |
| `class_label` | `1` for matched GT/FN, `0` for FP/TN. |
| `pred_class` | Foreground class ID being evaluated. |
| `pid` | Patient identifier. |
| `det_type` | `det_tp`, `det_fp`, `det_fn`, or `patient_tn`. |
| `fold` | `cf.fold` at evaluation time. |
| `match_iou` | Matching IoU used for this row. |

A `patient_tn` preserves a negative patient for patient-level metrics and is excluded from ROI AP. `det_fn` contributes a zero-score positive to recall/AP but is not a plotted detection. There is no segmentation metric path in this evaluator.

## ROI-level AP

Set `cf.report_score_level` to include `'rois'` (the source uses the plural spelling). For each class:

1. Remove `patient_tn` rows.
2. Call `get_roi_ap_from_df([spec_df, cf.min_det_thresh, cf.per_patient_ap])`.
3. Exclude detection rows at or below the threshold (`pred_score > min_det_thresh` is strict).
4. Sort remaining `det_tp`/`det_fp` rows by descending score and compute a COCO-style 101-recall-bin AP through `compute_roi_ap`.

`cf.per_patient_ap=False` pools all ROI rows for each matching IoU and averages AP only over IoU settings that have at least one positive. `True` computes AP per patient and averages over patient/IoU cases; a patient with detections but no positives contributes zero, while no detections and no positives is skipped. ROI AUC/ROC/PRC are deliberately set to `0`/`None`: the source explains that ROI AUC would reward low-confidence false positives because true-negative ROI predictions do not exist.

The returned stats entry is named `fold_{fold} rois cl_{class_id}` and includes `ap`, `auc=0`, `roc=None`, and `prc=None`. `average_foreground_roi` is appended as the mean ROI AP across foreground classes. When multiple folds are aggregated, per-fold ROI APs also appear as `mean_ap`.

## Patient-level AP/AUC/curves

Set `cf.report_score_level` to include `'patient'`. For each class, rows are grouped by `pid`:

- patient label = maximum `class_label` (positive if any ROI of this class exists);
- patient score = maximum detection score for this class;
- fold = first fold value.

If both patient labels `0` and `1` exist, the source calls scikit-learn `roc_auc_score` and stores `roc_curve` as `(false_positive_rate, true_positive_rate, thresholds)`. If any positive patient exists, it calls `average_precision_score` and stores `precision_recall_curve` as `(precision, recall, thresholds)`. With only one patient label, AUC/ROC are `nan`; with no positive patient, AP/PRC are `nan`. These are dataset-availability outcomes, not evidence of model quality.

For multi-fold data, the source additionally computes `mean_auc` over folds with both labels and `mean_ap` over folds with positives. The overall patient score name is `fold_{fold} patient cl_{class_id}`. During validation monitoring, only patient metrics for `cf.patient_class_of_interest` are appended to `monitor_metrics`; other classes still appear in returned stats.

## Monitoring and threshold scans

`evaluate_predictions(..., monitor_metrics)` calls `return_metrics` and appends AP, and patient AUC, to the preallocated monitoring series. In validation modes, identical model-selection values may receive a tiny random perturbation to avoid ranking ties. This is bookkeeping, not a metric improvement.

If `cf.scan_det_thresh=True`, the evaluator scans thresholds `0.90, 0.91, ..., 0.99` using a multiprocessing pool and logs ROI AP. It does not automatically update `cf.min_det_thresh`. Do not use the scan as an unbiased test-set estimate.

## Fold output and provenance

`score_test_df(internal_df=True)`:

1. Pickles the current dataframe to `cf.exp_dir/{cf.fold}_test_df.pickle`.
2. Calls `return_metrics` and appends fold summaries to `cf.exp_dir/results.txt`.
3. If exactly `cf.n_cv_splits` test dataframe pickles are present, loads and concatenates them, relabels `fold` by file enumeration, computes overall and per-fold means, appends overall results, and writes a sibling `results_table.txt`.

Record the class map, `ap_match_ious`, `report_score_level`, `min_det_thresh`, `per_patient_ap`, fold list, and whether predictions were WBC/2D-to-3D merged. A score without these fields is not reproducible.
