---
name: inference-and-evaluation
description: "Use the MedicalDetectionToolkit Predictor, post-processing,
  Evaluator, and plotting contracts to run bounded inference, consolidate
  detections, score ROI/patient results, and inspect saved outputs."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# Inference and evaluation

Use this node after a valid experiment configuration, data-loader batch, model output, or saved prediction pickle exists. It explains the source-backed prediction/evaluation pipeline; it does **not** provide a checkpoint, dataset, trained-model performance claim, or a replacement for the legacy CUDA path.

## Evidence and compatibility boundary

The operating facts below were distilled from the repository's predictor,
evaluator, plotting, execution, defaults, and README evidence. Public
signatures were inspected with a modern isolated stack; that inspection did
not prove the historical custom CUDA operators or model inference.

- **Source-backed:** function signatures, mode branches, array/key conventions, file names, thresholds, matching rules, metric formulas, and output-writing behavior described in the linked references.
- **Verified portable boundary:** pure-Python/NumPy/Pandas/scikit-learn helper behavior is suitable for small CPU probes, subject to the legacy API caveats in [troubleshooting](references/troubleshooting.md).
- **Unverified:** accuracy, runtime, memory use, checkpoint quality, dataset-specific thresholds, and exact detector execution. The source requirements pin Python-3.6-era packages including torch 0.4.1; the repository is unmaintained and README points to nnDetection, whose APIs must not be assumed compatible.

## Route and workflow

1. **Start with configuration and data contracts.** Confirm `cf.dim`, `cf.class_dict`, `cf.patch_size`, `cf.batch_size`, `cf.fold_dir`, `cf.test_n_epochs`, `cf.test_aug`, `cf.wcs_iou`, `cf.merge_2D_to_3D_preds`, `cf.merge_3D_iou`, `cf.ap_match_ious`, `cf.report_score_level`, `cf.min_det_thresh`, and output paths. Route configuration questions to [configuration-and-experiments](../configuration-and-experiments/SKILL.md) and batch/patch shape questions to [data-and-preprocessing](../data-and-preprocessing/SKILL.md).
2. **Choose the Predictor mode.** Use `Predictor(cf, net, logger, mode='val')` for patient validation/monitoring, `mode='test'` for checkpoint inference, and `mode='analysis'` only for `load_saved_predictions` in `exec.py`'s analysis branch. See [prediction workflows](references/prediction-workflows.md).
3. **Preserve raw predictions before post-processing.** `predict_test_set` collects epochs and XY mirrors, writes `raw_pred_boxes_list.pickle` or `raw_pred_boxes_hold_out_list.pickle`, and optionally applies WBC and 2D-to-3D merging. Use `load_saved_predictions(apply_wbc=True)` for repeatable analysis without a network forward. See [consolidation](references/consolidation.md).
4. **Evaluate only schema-valid results.** `Evaluator.evaluate_predictions` matches `det` boxes to `gt` boxes class-by-class at each configured IoU, creates the internal dataframe, and then `return_metrics` computes ROI AP and patient AP/AUC. Validate records with `scripts/validate_evaluation_records.py` before expensive analysis; see [evaluation](references/evaluation.md).
5. **Write or inspect artifacts.** `score_test_df` writes fold dataframes/results text and aggregates all fold pickles when available. Hold-out analysis calls `utils.exp_utils.create_csv_output`; monitoring/curves use [monitoring and outputs](references/monitoring-and-outputs.md). Do not interpret a plot or score as a performance guarantee without dataset and checkpoint provenance.

## Result contract at a glance

A patient result is `[boxes_by_batch_instance, pid]`. `boxes_by_batch_instance` is a list of lists; 3D uses one dummy batch instance, while unmerged 2D uses one list per slice/batch element. Each detection box needs `box_type: 'det'`, `box_coords` (`[y1, x1, y2, x2]` or `[y1, x1, y2, x2, z1, z2]`), `box_score` in the model's confidence scale (normally `[0, 1]`), and integer `box_pred_class_id`. Ground truth entries use `box_type: 'gt'`, `box_coords`, and `box_label`. Raw patch detections additionally carry `patch_id`, `box_patch_center_factor`, and `box_n_overlaps`; WBC consumes these and emits consolidated detections.

A batch passed to `predict_patient` must include model input `data`, `pid`, `original_img_shape`, and patient targets/labels when validation needs ground truth; patched batches additionally include `patch_crop_coords`. Prediction outputs contain `boxes`, `seg_preds`, and (in validation) `monitor_values`. Segmentation averaging is implemented in tiling, but instance/semantic segmentation evaluation is explicitly not implemented by `Evaluator`.

## Cross-links and progressive disclosure

- Read [prediction workflows](references/prediction-workflows.md) for mode prerequisites, patching, mirroring, checkpoint/epoch ensembling, and saved-prediction lifecycle.
- Read [consolidation](references/consolidation.md) for WBC math, `wcs_iou`, `n_ens`, patch-center/overlap weights, and 2D-to-3D connected-slice merging.
- Read [evaluation](references/evaluation.md) for dataframe records, ROI/patient matching, AP/AUC/ROC/PRC semantics, and fold aggregation.
- Read [monitoring and outputs](references/monitoring-and-outputs.md) for CSV, pickle, text, histogram, stat-curve, and sampled prediction outputs.
- Read [troubleshooting](references/troubleshooting.md) before changing thresholds or attempting old CUDA-backed detectors; route model/custom-op failures to [models-and-architectures](../models-and-architectures/SKILL.md) and [cuda-extensions](../cuda-extensions/SKILL.md).
- Use `scripts/validate_wbc_inputs.py` for small, dependency-free structural checks on WBC inputs and `scripts/validate_evaluation_records.py` for dependency-free record checks. They never download models, import the checkout, or run inference.

## Safe-stop rules

Stop and fix the input rather than silently continuing when patient IDs, batch-instance nesting, class IDs, coordinate dimensionality, `box_type`, or required patch metadata disagree. Stop before claiming a result when epoch ranking/checkpoints are missing, fold counts do not match, custom CUDA imports fail, or metric inputs contain only one patient class for AUC. Keep raw pickle outputs immutable while experimenting with WBC/thresholds so analysis remains reproducible.
