# Prediction workflows

**Primary evidence:** the repository's Predictor, execution orchestration,
defaults, and README prediction-pipeline evidence. The source API was
signature-inspected in an isolated stack; no checkpoint or native detector
forward was run.

## Preconditions

Before constructing a `Predictor`, confirm:

- `cf.dim` is `2` or `3`; the model and loader agree on it.
- The configured `cf.class_dict` contains the foreground class IDs emitted by the model. Background is not consolidated/evaluated as a foreground class.
- `cf.batch_size` fits the intended patch batch, `cf.patch_size` matches loader crop dimensions, and `cf.return_masks_in_test` is intentionally selected. Mask output is returned by some models but is not evaluated by this node.
- For `mode='test'`, `cf.fold_dir/epoch_ranking.npy` exists and contains at least `cf.test_n_epochs` entries. Every selected epoch must have `cf.fold_dir/{epoch}_best_checkpoint/params.pth`; otherwise `Predictor.__init__` or `predict_test_set` fails rather than producing a meaningful ensemble.
- A test batch generator exposes `batch_gen['n_test']` and `batch_gen['test']`; each `next(batch_gen['test'])` provides `data`, `pid`, `original_img_shape`, and patient target/label fields expected by the loader. Patched batches also provide `patch_crop_coords`.
- Validation batches provide `patient_bb_target` and `patient_roi_labels` if ground truth is to be appended. `mode='val'` is for patient validation and monitoring, not a replacement for the training loop.

The neighboring [configuration-and-experiments](../../configuration-and-experiments/SKILL.md) node owns experiment paths/CLI, and [data-and-preprocessing](../../data-and-preprocessing/SKILL.md) owns the loader/patch contract.

## Mode behavior

| Mode | Constructor behavior | Main entry point | Post-processing behavior |
|---|---|---|---|
| `val` | Keeps the current `net`; `n_ens=1`. | `predict_patient(batch)` from `exec.train`. | Calls forward once, discards model-returned non-detection boxes, appends patient GT boxes, applies WBC only for patched input, and optionally merges 2D boxes to 3D. Returns `boxes`, `seg_preds`, and `monitor_values`. |
| `test` | Loads `epoch_ranking.npy` and sets `n_ens=cf.test_n_epochs*(4 if cf.test_aug else 1)`. | `predict_test_set(batch_gen, return_results=True)`. | Repeats the whole test set for each selected checkpoint; each patient is flattened across epochs/mirrors, saved raw, then WBC and optional 2D-to-3D merging are applied. |
| `analysis` | No network/checkpoint load in `__init__`. | `load_saved_predictions(apply_wbc=True)`, as used by `exec.py --mode analysis`. | Reads previously written raw pickles, optionally aggregates folds for hold-out data, applies WBC and optional 2D-to-3D merging. It is not a forward mode. |

`predict_patient` in test mode returns raw per-patient predictions so temporal ensembling can happen after all epochs have been collected. Do not call it as if it already returned consolidated test predictions.

## Patch tiling and data augmentation

`spatial_tiling_forward` calls `batch_tiling_forward` and maps patch-local detections to patient coordinates. Loader crop coordinates are `[y1, y2, x1, x2, z1, z2]`; 2D loaders commonly represent each slice as a 3D crop with `z2=z1+1`, then remove the singleton z dimension from `data`. In 3D, `original_img_shape` follows the loader's batch/channel/spatial layout and boxes use six coordinates. Treat loader-produced arrays, not this summary, as the authority for exact axis order.

For patch batches:

1. Segmentation arrays are placed into the patient canvas and divided by a uint8 overlap map, yielding an average in overlapping pixels.
2. Each box is translated by crop origin and receives `patch_id = rank_ix + '_' + n_aug + '_' + patch_index`.
3. `box_patch_center_factor` downweights boxes near patch edges using a normal-density factor over box center positions. `box_n_overlaps` records mean patch overlap at the box area.
4. In non-patch mode, both factors are set to `1` and `patch_id` is `rank_ix + '_' + n_aug`.

In test mode with `cf.test_aug=True`, `data_aug_forward` runs the original input plus three XY variants: y mirror, x mirror, and y+x mirror. It mirrors patch crops when needed, reverses predicted coordinates and segmentation back to the original frame, and does **not** mirror z. The four views contribute to `n_ens`; changing `test_aug` changes the expected count used later by WBC.

`batch_tiling_forward` processes a whole image if `img.shape[0] <= cf.batch_size`; otherwise it splits the patch batch into chunks and flattens their `boxes`/`seg_preds`. Validation invokes `net.train_forward(..., is_validation=True)` and removes returned boxes whose `box_type` is not `det`; test invokes `net.test_forward(..., return_masks=cf.return_masks_in_test)`.

## Temporal test ensemble and raw artifacts

`predict_test_set` builds checkpoint paths from `cf.fold_dir`, loads each `params.pth`, sets `self.rank_ix` to the ensemble rank, and consumes the entire test generator once per checkpoint. It stores each patient's raw box lists, retains patient targets/labels from the first rank, then appends GT entries to the flattened result. It writes:

- `cf.fold_dir/raw_pred_boxes_list.pickle` for an ordinary test fold;
- `cf.fold_dir/raw_pred_boxes_hold_out_list.pickle` when `cf.hold_out_test_set=True`.

The raw object is a list of `[boxes_by_batch_instance, pid]` entries. `return_results=False` still writes the raw pickle but returns no consolidated list. `return_results=True` maps `apply_wbc_to_patient` over patients and then, if configured, maps `merge_2D_to_3D_preds_per_patient`.

`load_saved_predictions` reconstructs this list. Non-hold-out mode reads the fold pickle and computes `n_ens = test_n_epochs * (4 if test_aug else 1)`. Hold-out mode reads each `cf.folds/fold_{fold}` raw hold-out pickle, keeps detection boxes, flattens corresponding patient entries, and multiplies `n_ens` by the number of folds. It can apply WBC or leave raw detections unchanged before optional 2D-to-3D merging. Confirm that fold files contain the same patient ordering before using hold-out aggregation.

## Minimal call shapes

```python
predictor = Predictor(cf, net, logger, mode='test')
raw_or_final = predictor.predict_test_set(batch_gen, return_results=True)

analysis_predictor = Predictor(cf, net=None, logger=logger, mode='analysis')
final = analysis_predictor.load_saved_predictions(apply_wbc=True)

evaluator = Evaluator(cf, logger, mode='test')
evaluator.evaluate_predictions(final)
evaluator.score_test_df()
```

These snippets document signatures, not a promise that an old model/custom-op import works on a current torch/CUDA host. Route detector import failures to [models-and-architectures](../../models-and-architectures/SKILL.md) and [cuda-extensions](../../cuda-extensions/SKILL.md).
