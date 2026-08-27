# Monitoring and output artifacts

**Primary evidence:** the repository's plotting, execution, CSV-output, and
README monitoring evidence. Plot/file behavior is source-backed; appearance,
scale, and model performance are not verified.

## Prediction artifacts

| Producer | Artifact | Schema/meaning |
|---|---|---|
| `Predictor.predict_test_set` | `fold_dir/raw_pred_boxes_list.pickle` | Raw non-hold-out patient list: `[[boxes_by_batch_instance, pid], ...]`, including patch/epoch/mirror metadata on detections and appended GT when provided. |
| `Predictor.predict_test_set` | `fold_dir/raw_pred_boxes_hold_out_list.pickle` | Same raw structure for a hold-out test set; intended for later cross-fold aggregation. |
| `Evaluator.score_test_df` | `exp_dir/{fold}_test_df.pickle` | Pandas dataframe with `pred_score,class_label,pred_class,pid,det_type,fold,match_iou`. |
| `Evaluator.score_test_df` | `exp_dir/results.txt` | Appended fold and, when all fold pickles exist, overall AUC/AP text summaries. Re-running appends rather than replaces. |
| `Evaluator.score_test_df` | sibling `results_table.txt` | Appended compact overall entries after all folds are available. |
| `create_csv_output` | `exp_dir/results_{fold}.csv` or `results_hold_out.csv` | One row per consolidated detection at or above `cf.min_det_thresh`: `patientID,predictionID,coords,score,pred_classID`. |

The CSV writer loops only over `r[0][0]`: it assumes one dummy batch instance, which is appropriate for 3D or 2D predictions already merged to 3D. For raw/unmerged 2D slice lists it would omit every list after the first. It also asserts every traversed entry is a detection, so do not pass evaluation lists that still contain `gt` boxes. The logger message says `results.csv`, but the actual filename contains the fold/hold-out suffix.

`coords` correspond to the **preprocessed image coordinate system used for testing**, not necessarily raw scanner/world coordinates. The source includes only commented resampling hooks. Preserve preprocessing scale/crop/affine provenance and perform explicit inverse mapping before using CSV boxes on raw clinical data.

## Prediction image plots

`plot_batch_prediction(batch, results_dict, cf, outfile=None)` expects:

- `batch['data']`, `batch['seg']`, and `batch['pid']`;
- `results_dict['seg_preds']` and `results_dict['boxes']`;
- plot config including `cf.dim`, `cf.plot_dir`, `cf.fold`, `cf.num_seg_classes`, and `cf.box_color_palette`.

If `outfile` is omitted, output is `plot_dir/pred_example_{fold}.png`. The function checks batch/spatial agreement between data, segmentation, and predicted segmentation. For 3D it randomly chooses one patient, projects cubes to slice boxes, and selects a small z section around the first GT if available, otherwise around the center. Therefore repeated plots are not deterministic unless random state and data are controlled.

Detection boxes are shown only when predicted class is foreground (`>0`) and score is greater than `0.1`; GT is red/text-labeled. Plotting uses matplotlib's noninteractive `Agg` backend, so no GUI/display is required. A successful plot proves only shape/serialization compatibility, not metric correctness.

## Histograms and curves

`Evaluator.return_metrics` can call:

- `plot_prediction_hist(labels, scores, type_list, outfile)` when `cf.plot_prediction_histograms=True`. ROI plots include counts of `det_tp`, `det_fp`, `det_fn`; patient plots omit those type counts. False negatives appear as positive labels at synthetic score zero. The y-axis is logarithmic.
- `plot_stat_curves(all_stats, outfile)` when `cf.plot_stat_curves=True`. It writes `{fold}_{mode}_stat_curves_roc` and `_prc` using the curve tuples in patient-level stats. ROI stats have `None` curves and are skipped.

Source caveat: when patient AUC/PRC cannot be computed, `return_metrics` stores `np.nan` rather than `None`. `plot_stat_curves` only checks `is not None` and may try to index a scalar NaN. Disable curve plotting or sanitize unavailable curve values when the evaluated class has only one patient label or no positives.

## Training monitoring

`utils.exp_utils.prepare_monitoring` creates train/validation histories and a `TrainingPlot_2Panel`. `TrainingPlot_2Panel.update_and_save(metrics, epoch)` writes `plot_dir/monitor_{fold}_{figure_index}` (matplotlib chooses format from configuration/default behavior) and calls `detection_monitoring_plot`. The first figure plots unassigned monitoring keys; `cf.assign_values_to_extra_figure` routes selected values to additional figures. Train lines are dashed and validation lines are solid.

In `exec.train`, each epoch:

1. collects `results_dict['monitor_values']` for train batches;
2. evaluates train detections and, if enabled, validation detections;
3. updates model selection from configured monitoring criteria;
4. saves monitoring figures;
5. draws a sampled validation prediction plot.

For patient validation, `Predictor(mode='val')` performs patch WBC/optional 2D-to-3D merge before evaluator matching. For `val_sampling`, `net.train_forward` outputs are evaluated directly. These modes do not measure identical data units; document `cf.val_mode` when comparing metrics.

## Analysis flow

`python exec.py --mode analysis --exp_source ... --exp_dir ...` loads stored experiment settings and raw prediction pickles. For ordinary CV folds it WBC-consolidates, optionally merges 2D-to-3D, evaluates, and writes dataframe/text outputs. For a hold-out test set it aggregates selected `--folds`, WBC-consolidates, and calls the CSV writer rather than `Evaluator`.

Safe practice:

1. Copy or hash raw pickles before analysis.
2. Record stored config provenance and fold list.
3. Validate WBC input metadata and evaluation records with the bundled scripts.
4. Write derived outputs to an explicitly versioned experiment directory; source functions append some outputs.
5. Never present image plots or CSV coordinates as clinical validation. The repository provides engineering outputs, not verified clinical performance.
