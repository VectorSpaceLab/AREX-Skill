# Troubleshooting

## 1. Missing analyzed outputs
- **Symptom:** `filterpredictions`, `create_labeled_video`, `plot_trajectories`, or `analyzeskeleton` cannot find the analyzed file.
- **Likely cause:** the analysis step was not run, or `destfolder`, `shuffle`, `trainingsetindex`, `modelprefix`, or `track_method` does not match the analysis step that produced the file.
- **Fix:** point every downstream step at the same analysis folder and reuse the same routing parameters.

## 2. Filtered vs unfiltered confusion
- **Symptom:** a filtered plot or labeled video still appears to use raw predictions.
- **Likely cause:** the filtered file was never created, or the follow-up step was not told to read filtered outputs.
- **Fix:** run `filterpredictions(...)` in the correct analysis folder and then pass `filtered=True` to the renderer or plotter.

## 3. Multi-animal detections are not tracklets yet
- **Symptom:** plotting or rendering fails because the data are only raw detections.
- **Likely cause:** the multi-animal conversion and stitching steps were not completed.
- **Fix:** hand off to the multi-animal-tracking skill for `convert_detections2tracklets(...)` and `stitch_tracklets(...)` before coming back here.

## 4. Raw outlier helper rejects the file pair
- **Symptom:** `find_outliers_in_raw_data(...)` raises an error about the pickle or the matching video.
- **Likely cause:** the pickle is not one of the supported raw-detection suffixes, or its stem does not match the video stem.
- **Fix:** pair the correct `_full.pickle` or `_assemblies.pickle` with its source video.

## 5. Corrupt or unreadable videos
- **Symptom:** `check_video_integrity(...)` warns, a video helper fails, or the generated output truncates early.
- **Likely cause:** codec/container mismatch or corrupted metadata.
- **Fix:** inspect the integrity log, then re-encode the source video to a supported codec/container before rerunning downstream steps.

## 6. Cropping looks shifted
- **Symptom:** the cropped video or overlaid labels are offset in the wrong place.
- **Likely cause:** the crop box was supplied in the wrong order.
- **Fix:** use `x1, x2, y1, y2` ordering, not width/height ordering.

## 7. Outlier extraction is too strict or too loose
- **Symptom:** `extract_outlier_frames(...)` returns too many or too few frames.
- **Likely cause:** the heuristic does not match the failure mode, or the thresholds are too aggressive.
- **Fix:** use `jump` for abrupt motion, `uncertain` for low confidence, `fitting` for trajectory deviation, and `manual` or `list` when heuristics are not enough.

## 8. Merge does not advance the iteration
- **Symptom:** `merge_datasets(...)` says some folders were not refined.
- **Likely cause:** at least one `labeled-data/*` folder still lacks corrected labels.
- **Fix:** finish the missing folders, then rerun `merge_datasets(...)`. The iteration only increases when every required folder is ready.

## 9. Calibration or undistortion looks wrong
- **Symptom:** `calibrate_cameras(...)` or `check_undistortion(...)` shows bad checkerboard corners or wrong ordering.
- **Likely cause:** the camera names in the filenames do not match the 3D config, or some image pairs are bad.
- **Fix:** keep the camera names stable, remove the bad pairs, rerun once with `calibrate=False`, then rerun with `calibrate=True`.

## 10. Triangulation cannot pair the videos
- **Symptom:** `triangulate(...)` cannot find the paired views or the output looks mismatched.
- **Likely cause:** the two files do not share the same prefix/suffix around the camera names, the camera names differ between views, or the 2D outputs were written to a different analysis folder.
- **Fix:** make the filename pairing unambiguous, keep the camera names identical across views, and reuse the same analysis location for the 2D inputs.

## 11. Triangulation or 3D rendering cannot find the videos
- **Symptom:** the 3D renderer cannot locate the camera videos.
- **Likely cause:** the triangulated file and camera videos live in different folders.
- **Fix:** pass `videofolder` explicitly to `create_labeled_video_3d(...)`.

## 12. Export problems
- **Symptom:** `export_model(...)` cannot find snapshots, or the export is not portable.
- **Likely cause:** the wrong shuffle or snapshot was selected, a top-down model is missing a detector snapshot, or local project paths were kept in the bundle.
- **Fix:** choose a snapshot that exists, add the detector snapshot or use `without_detector=True`, use `overwrite=True` only when replacing an old export, and use `wipe_paths=True` for a portable export.

## 13. 3D frame counts differ
- **Symptom:** the two camera views do not cover the same number of frames.
- **Likely cause:** one recording is shorter or was re-encoded differently.
- **Fix:** trim or re-encode the views before triangulation so the camera pair is aligned as closely as possible.
