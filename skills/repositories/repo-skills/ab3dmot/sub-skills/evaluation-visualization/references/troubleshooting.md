# Evaluation and visualization troubleshooting

This guide assumes tracking already ran and a `results/<dataset>/<result_sha>/` folder should exist.

## Result SHA mismatch

Symptoms:

- Evaluation says the uploaded results could not be evaluated.
- Thresholding or visualization cannot find the result folder.
- nuScenes export fails because a result directory or `data_0` file is missing.

Checks:

```bash
find results/KITTI -maxdepth 2 -type d | sort
find results/nuScenes -maxdepth 2 -type d | sort
```

Fixes:

- Use the folder basename only as `result_sha`, for example `pointrcnn_val_H1`, not `results/KITTI/pointrcnn_val_H1`.
- Distinguish combined folders from category folders. `pointrcnn_val_H1` is combined; `pointrcnn_Car_val_H1` is Car-only.
- Preserve the split segment. Validation and test folders are different: `pointrcnn_val_H1` versus `pointrcnn_test_H1`.
- Preserve `_thres` when visualizing or submitting thresholded results.

## Missing `data_0`

Symptoms:

- KITTI or nuScenes quick evaluation finds no tracker data.
- nuScenes KITTI-to-JSON export cannot load sequence result files.
- Server submission folder is empty or missing sequence files.

Checks:

```bash
test -d results/<dataset>/<result_sha>/data_0
find results/<dataset>/<result_sha>/data_0 -maxdepth 1 -type f | head
```

Fixes:

- If only category folders exist, the category-combination step did not complete. Re-run tracking or run the category combiner in the repository runtime so that the combined folder is created.
- If `data_1` exists but `data_0` does not, confirm the `num_hypo` setting and evaluator argument. AB3DMOT examples expect one hypothesis and `data_0`.
- If sequence files are missing for a split, rerun tracking with the intended `--dataset`, `--split`, and `--det_name` rather than evaluating a different split's folder.

## Missing `trk_withid_0`

Symptoms:

- Confidence thresholding fails while reading `trk_withid_0`.
- Visualization produces no boxes or cannot find per-frame result files.

Checks:

```bash
test -d results/<dataset>/<result_sha>/trk_withid_0
find results/<dataset>/<result_sha>/trk_withid_0 -maxdepth 2 -type f | head
```

Fixes:

- Rerun tracking or category combination; `trk_withid_0` is created alongside `data_0`.
- Do not use a pure server-submission `data_0` folder as a visualization result unless `trk_withid_0` is also present.
- For thresholded visualization, run `trk_conf_threshold.py` before `visualization.py` so the thresholded folder contains both `data_0` and `trk_withid_0`.

## Wrong threshold type

Symptoms:

- KITTI numbers do not match expected 3D or 2D reports.
- A test submission unexpectedly contains many false-positive tracks.
- Thresholding crashes for an unsupported detector name.

Fixes:

- Keep KITTI metric IoU thresholds separate from confidence thresholds:
  - KITTI 3D MOT validation commonly uses `3D 0.25` or `3D 0.5`; Car-only strict reporting uses `3D 0.7`.
  - KITTI 2D MOT validation uses `2D 0.5`.
  - Confidence thresholding uses detector/category score thresholds from AB3DMOT's threshold table and writes `<result_sha>_thres`.
- The threshold script infers `det_name` as the first underscore-delimited part of `result_sha`. `pointrcnn_test_H1` works for KITTI; a custom detector name needs a supported threshold entry in the running code.
- For official nuScenes evaluation, use the raw result folder unless the experiment explicitly evaluates thresholded tracks.

## nuScenes converted JSON missing

Symptoms:

- Official nuScenes evaluation reports that the result file does not exist.
- `results/nuScenes/<result_sha>/results_val.json` or `results_test.json` is absent.

Checks:

```bash
test -f results/nuScenes/<result_sha>/results_<split>.json
test -d results/nuScenes/<result_sha>/data_0
test -d data/nuScenes/nuKITTI/tracking/produced/correspondence/<split>
```

Fixes:

- Run the KITTI-to-nuScenes export first:

```bash
python3 scripts/nuScenes/export_kitti.py kitti_trk_result2nuscenes --result_name <result_sha> --split <split>
```

- If the export cannot find correspondence, raw nuScenes-to-KITTI conversion is incomplete. Route back to data-conversion.
- Use `v1.0-trainval` for train/val local official evaluation and `v1.0-test` for test export/server submission.

## Visualization image or calibration missing

Symptoms:

- Visualization logs that the full dataset is missing and then fails.
- Output folders are created but contain blank/no-image results.
- nuScenes visualization fails even though KITTI mini visualization worked.

Checks:

```bash
test -d results/<dataset>/<result_sha>/trk_withid_0
test -d data/KITTI/tracking/training/image_02 || test -d data/KITTI/mini/training/image_02
test -d data/nuScenes/nuKITTI/tracking/val/image_02
```

Fixes:

- For KITTI validation quick demos, the repository can fall back to KITTI mini image/calibration data for selected sequences, but matching tracking results are still required.
- For nuScenes, prepare the converted nuKITTI tracking image/calibration tree for the target split before visualization.
- Pass the same split used to create the result folder:

```bash
python3 scripts/post_processing/visualization.py --dataset KITTI --result_sha pointrcnn_val_H1_thres --split val
python3 scripts/post_processing/visualization.py --dataset nuScenes --result_sha megvii_val_H1_thres --split val
```

- If using a highlight file, ensure each line follows the expected `seq_id, frame_id, ID, error_type` comma-space format.

## nuScenes command typo

The intended nuScenes thresholding command includes a space before `--result_sha`:

```bash
python3 scripts/post_processing/trk_conf_threshold.py --dataset nuScenes --result_sha megvii_val_H1
```

If a copied command looks like `--dataset nuScenes-- result_sha`, fix it before running.
