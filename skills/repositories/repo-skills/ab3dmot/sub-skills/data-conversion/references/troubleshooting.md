# Data-conversion troubleshooting

Use this page when AB3DMOT cannot find data or detections, when converted detector files fail validation, or when nuScenes conversion commands fail before tracking.

## Detection files exist but tracking still fails

Symptoms:

- `main.py` finds files under `data/<dataset>/detection/...` but fails in initialization.
- Errors mention missing calibration, image, oxts, or tracking folders.

Likely cause: detector text files are present but the full tracking dataset tree is absent. AB3DMOT needs both detections and dataset tracking data for calibration, ego-motion compensation, frame lists, and visualization/debug paths.

Recovery:

1. Confirm the dataset-specific tracking root exists:
   - KITTI: `data/KITTI/tracking/<training|testing>/calib`, `image_02`, `oxts`.
   - nuScenes: `data/nuScenes/nuKITTI/tracking/<train|val|test>/calib`, `image_02`, `oxts`.
2. If only detection files are available, use API-level synthetic smoke checks instead of full tracking.
3. Do not patch detection folders to stand in for tracking data.

## Wrong split or subfolder

Symptoms:

- KITTI validation command searches `training` while the user expected `val` folders.
- nuScenes command searches `val` or `test` under `nuKITTI/tracking`.

AB3DMOT maps splits differently by dataset:

- KITTI `val` uses the external KITTI `training` subfolder and a validation sequence list.
- KITTI `test` uses the external KITTI `testing` subfolder.
- nuScenes uses the split name directly as the KITTI-like subfolder (`train`, `val`, or `test`).

Recovery: preserve this mapping; do not rename dataset folders to match the CLI split mechanically.

## Category/detector folder mismatch

Symptoms:

- Tracking skips a category or reports no detections.
- A folder such as `pointrcnn_all_val` exists, but category folders are absent.

AB3DMOT constructs category-specific detection roots from the detector, category, and split. For KITTI PointRCNN validation, all of these are needed:

```text
data/KITTI/detection/pointrcnn_Car_val/
data/KITTI/detection/pointrcnn_Pedestrian_val/
data/KITTI/detection/pointrcnn_Cyclist_val/
```

Recovery:

1. Check `cat_list` in the dataset config.
2. Check tracker parameter branches for supported detector/category combinations.
3. Convert or split detections into per-category folders, not only an `_all_` folder.

## Detection validator reports wrong column count

Symptoms:

- The bundled validator reports rows with fewer or more than 15 fields.
- Rows start with strings such as `Car` or are space-separated.

Likely cause: the file is still in KITTI object-detection format, not AB3DMOT tracker-input format.

Recovery:

1. Convert raw KITTI object rows into AB3DMOT rows using the conversion workflow.
2. Confirm rows are comma-separated and start with integer `frame,type_id`.
3. Re-run the validator on a small representative subset before converting every split.
4. If a sequence file is genuinely empty, add `--allow-empty` to the validator instead of treating the file as malformed.

## Detection validator reports invalid dimensions or box ordering

Symptoms:

- `h`, `w`, or `l` is zero/negative.
- `x2 < x1` or `y2 < y1`.

Recovery:

- Positive 3D dimensions are required; fix the detector conversion if these fail.
- Box-order warnings may indicate swapped columns or off-camera placeholders. Inspect whether the file came from a raw object label, a nuScenes conversion, or a custom detector exporter.
- Do not silently reorder columns unless you know which exporter produced them.

## nuScenes optional dependency import errors

Symptoms:

- `ModuleNotFoundError: nuscenes`, `fire`, `pyquaternion`, `motmetrics`, or `pandas`.
- `scripts/nuScenes/export_kitti.py --help` fails before showing Fire help.

Recovery:

1. Install the nuScenes optional requirements in the active AB3DMOT runtime environment.
2. Verify with a help-only command before writing data:
   ```bash
   python scripts/nuScenes/export_kitti.py --help
   ```
3. If the task only validates existing AB3DMOT detection files, skip optional nuScenes conversion dependencies.

## Raw nuScenes result JSON not found

Symptoms:

- `nuscenes_obj_result2kitti` cannot open `results_<split>.json`.

The converter expects this layout:

```text
data/nuScenes/data/produced/results/detection/<result_name>/results_<split>.json
```

Recovery: either move/symlink the detector JSON to that layout or pass the correct `--result_name` and `--split`. Keep the raw detector name stable because it becomes the AB3DMOT `det_name` folder prefix.
