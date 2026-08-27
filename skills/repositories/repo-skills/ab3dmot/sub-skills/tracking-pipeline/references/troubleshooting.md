# Tracking Troubleshooting

Use this page when `main.py` tracking or direct `AB3DMOT.track` usage fails. For conversion-specific failures, use the data-conversion sub-skill. For metrics, thresholding, exports, and visualization failures, use the evaluation-visualization sub-skill.

## Import or PYTHONPATH failures

Symptoms:

- `ModuleNotFoundError: No module named 'AB3DMOT_libs'`
- `ModuleNotFoundError: No module named 'xinshuo_io'`
- missing `filterpy`, `easydict`, `numba`, `scipy`, `yaml`, `cv2`, or similar dependencies

Fixes:

1. Run from the AB3DMOT repository root for command-level tracking.
2. Ensure the repository root is on `PYTHONPATH` for direct API use.
3. Ensure the Xinshuo toolbox dependency is installed or on `PYTHONPATH`.
4. Install the Python packages listed by the project requirements. Older pinned versions can be difficult on newer Python; a compatible environment that imports the required modules is acceptable for smoke checks.
5. Run the bundled no-dataset smoke for a focused report:

```bash
python sub-skills/tracking-pipeline/scripts/smoke_track_synthetic.py
```

## `main.py` uses nuScenes when KITTI was intended

Cause: parser default for `--dataset` is `nuScenes`.

Fix: always pass the full command explicitly:

```bash
python main.py --dataset KITTI --split val --det_name pointrcnn
```

Use [../scripts/build_tracking_command.py](../scripts/build_tracking_command.py) before running a command:

```bash
python sub-skills/tracking-pipeline/scripts/build_tracking_command.py --dataset KITTI --split val --det_name pointrcnn
```

## Dataset or sequence files missing

Symptoms:

- missing calibration, OXTS/ego-motion, image, or sequence files;
- assertions from `get_subfolder_seq`, `initialize`, `load_oxts`, or calibration loading;
- no result folder appears even though detections exist.

Causes and fixes:

- Detection files alone are not enough for full `main.py` tracking. The initializer also needs tracking data roots with calibration, ego-motion, and images.
- KITTI tracking expects `./data/KITTI/tracking/training/...` for `val` and `./data/KITTI/tracking/testing/...` for `test`.
- nuScenes tracking expects converted KITTI-like tracking data under `./data/nuScenes/nuKITTI/tracking/<split>/...`.
- If raw data or detector conversion is incomplete, switch to the data-conversion sub-skill before retrying tracking.

## Detection folder mismatch

`main.py` looks for category-specific detection roots with this exact formula:

```text
./data/<dataset>/detection/<det_name>_<cat>_<split>/<seq>.txt
```

Examples:

```text
./data/KITTI/detection/pointrcnn_Car_val/0001.txt
./data/nuScenes/detection/megvii_Pedestrian_val/<seq>.txt
```

If a folder is named with a different split, detector, category spelling, capitalization, or all-category suffix, tracking can skip detections or fail later. Use the data-conversion validator for detection row schema and folder naming.

## Config and detector mismatch

Symptoms:

- `AssertionError: error` from tracker parameter selection;
- no branch for a detector/category combination;
- confusing behavior after editing config comments only.

Fixes:

- KITTI tuned detector names: `pointrcnn`, `pvrcnn`.
- nuScenes tuned detector names: `megvii`, `centerpoint`.
- Do not use nuScenes `mapillary` or `pointpillar` directly unless tracker parameters are added and verified.
- Keep category names exactly as expected: `Car`, `Pedestrian`, `Cyclist` for KITTI; `Car`, `Pedestrian`, `Bicycle`, `Motorcycle`, `Bus`, `Trailer`, `Truck` for nuScenes.

## KITTI `train` split confusion

A utility has a stale KITTI train sequence list, but the split dispatch for KITTI tracking accepts `val` and `test`. Treat `--dataset KITTI --split train` as unsupported unless the code is modified and verified.

## Numba deprecation and Python syntax warnings

Common non-fatal warnings include:

- Numba deprecation warnings about implicit object mode;
- syntax warnings from string comparisons such as `is not ''`;
- dependency-version warnings when running outside the originally tested Python version.

If `main.py --help` and the synthetic smoke still exit successfully, record the warnings but do not treat them as tracking failures. If warnings become exceptions under a newer Python, use a compatible Python environment or patch and verify the code.

## No combined result folder

The combined all-category folder, such as `pointrcnn_val_H1`, is created only after every category loop finishes and `combine_trk_cat` runs.

Check:

1. Did per-category folders exist for every configured category?
2. Did `combine_log.txt` appear in the combined folder?
3. Did a category fail early because its detection folder or sequence data was missing?
4. Is `save_root` pointing somewhere different from the expected `./results/<dataset>`?

## Score threshold surprises

`score_threshold` in the YAML affects rows written to `data_0` during tracking. It does not prevent `trk_withid_0` rows from being written. The default `-10000` is intentionally permissive; post-processing thresholding is usually applied after tracking for evaluation or visualization.

If evaluation sees too many or too few objects, check both:

- `score_threshold` used during tracking;
- any later confidence-thresholding result folder with `_thres` suffix.

## Direct API shape errors

`AB3DMOT.track` expects:

```python
dets_all = {
    "dets": ndarray_with_shape_N_by_7,
    "info": ndarray_with_shape_N_by_7,
}
```

Common mistakes:

- Passing full 15-column detection rows as `dets` instead of slicing to `[h,w,l,x,y,z,theta]`.
- Passing internal `[x,y,z,theta,l,w,h]` order as raw detection order.
- Omitting `info`, using the wrong `info` shape, or putting category names where numeric type IDs are expected.
- Passing an empty Python list instead of `(0, 7)` arrays for empty frames.
- Recreating `AB3DMOT` every frame, which resets IDs and track state.
- Skipping frames with no detections, which prevents aging/deletion and corrupts affinity continuity.

Run [../scripts/smoke_track_synthetic.py](../scripts/smoke_track_synthetic.py) to compare expected one-frame behavior.

## Ego-motion and visualization misuse in API mode

If constructing `AB3DMOT` directly:

- Use `ego_com=False` unless you have valid calibration and OXTS/ego poses for every frame.
- Use `vis=False` unless `img_dir`, `vis_dir`, `hw`, calibration, and image files are all valid.
- The command-level initializer handles these paths for full dataset runs; direct API callers must supply them deliberately.

## Affinity shape confusion

With `affi_pro: true`, the returned matrix is post-processed into past-active-output by current-active-output order. A first frame with one new detection normally has shape `(0, 1)`, not `(1, 0)` or `(1, 1)`. With `affi_pro: false`, the matrix follows raw detection-by-predicted-track shape.
