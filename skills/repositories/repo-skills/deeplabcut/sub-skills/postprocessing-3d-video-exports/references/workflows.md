# Workflows

## 1. Clean up analyzed 2D predictions

1. Confirm that the video was already analyzed and that the analysis folder is the same folder you will use for downstream steps.
2. If you want smoothed or inspectable predictions, run `filterpredictions(...)`.
3. Use `create_labeled_video(..., filtered=True)` when you want the overlay to use the filtered output.
4. Use `plot_trajectories(..., filtered=True)` to inspect position, likelihood, and displacement behavior.
5. If the project config already has skeleton links, run `analyzeskeleton(...)` to quantify bone length and orientation.

### Typical decision points
- Use `median` filtering for a light cleanup pass.
- Use `arima` or `spline` only when you need the stronger model-based behavior.
- Keep `destfolder` aligned with the analysis location, or the later steps will not find the outputs.

## 2. Extract and refine outliers

1. Start with `extract_outlier_frames(...)` when pose predictions look wrong.
2. Choose the selection heuristic that matches the failure mode:
   - `jump` for abrupt motion
   - `uncertain` for low-confidence detections
   - `fitting` for model-fit deviations
   - `manual` for direct human selection
   - `list` when you already know the frame numbers
3. Correct the labels in the extracted frames.
4. Merge the corrections back into the dataset with `merge_datasets(...)`.
5. Hand the expanded dataset back to the training skill for new training-data generation or retraining.

### Raw-detection branch
- When the outlier source is a raw detection pickle such as `_full.pickle` or `_assemblies.pickle`, use `find_outliers_in_raw_data(...)` instead of the h5-based path.

## 3. Prepare or repair videos

1. If a video fails to open, begin with `check_video_integrity(...)`.
2. Use `CropVideo(...)`, `DownSampleVideo(...)`, or `ShortenVideo(...)` to create a new, smaller video when the downstream task does not need the original file.
3. Re-run analysis on the derived video; do not reuse the old analyzed outputs after changing the pixels or frame range.
4. Use the bundled inventory helper to preview which files in a folder will be considered inputs.

### Practical reminder
- Cropping coordinates are `x1, x2, y1, y2` in DeepLabCut-style video helpers.
- `DownSampleVideo` keeps aspect ratio when one dimension is `-1`.

## 4. Calibrate and triangulate 3D data

1. Make sure the 3D project already knows the exact camera names and the linked 2D project configs.
2. Put 20-60 calibration image pairs into the calibration-image folder.
3. Run `calibrate_cameras(..., calibrate=False)` first and inspect the detected corners.
4. Remove bad pairs, then rerun `calibrate_cameras(..., calibrate=True)`.
5. Run `check_undistortion(...)` to verify the rectification.
6. Run `triangulate(...)` on either a directory of paired videos or an explicit list of video pairs.
7. Create a subset 3D visualization with `create_labeled_video_3d(...)`.

### Pairing rules
- Each video filename must contain the exact camera name used in the 3D config.
- The pair must share the same prefix/suffix around the camera name so the views can be matched unambiguously.
- If trained 2D models do not exist, route upstream first; if the models exist but pose files are absent, `triangulate(...)` can run the 2D analysis/filtering substep internally.
- If the videos are stored away from the triangulated file, pass `videofolder` to the 3D renderer.

## 5. Export portable model bundles

1. Choose the correct shuffle and snapshot for the trained model.
2. For top-down models, either include a detector snapshot or choose `without_detector=True` when that is the intended export.
3. Run `export_model(...)` to create the portable bundle.
4. Use `overwrite=False` when you want to keep an existing export, and `wipe_paths=True` when the bundle must not contain local project paths.

### Export expectations
- The PyTorch export path writes under `exported-models-pytorch/`.
- If no snapshots exist for the selected shuffle, the export must be fixed upstream in the training skill.
