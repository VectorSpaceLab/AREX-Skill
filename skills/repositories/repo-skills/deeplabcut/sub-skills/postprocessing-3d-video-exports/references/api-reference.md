# API reference

This page maps the public DeepLabCut APIs owned by this sub-skill.

## Prediction cleanup and refinement

- `filterpredictions(config, video, video_extensions=None, shuffle=1, trainingsetindex=0, filtertype='median', windowlength=5, p_bound=0.001, ARdegree=3, MAdegree=1, alpha=0.01, save_as_csv=True, destfolder=None, modelprefix='', track_method='', return_data=False, **kwargs)`
  - Use after the video has already been analyzed.
  - Filters frame-by-frame pose predictions with `median`, `arima`, or `spline`.
  - Writes `*_filtered.h5` next to the analyzed output and can also write CSV.
  - Return data mode yields filtered data keyed by video path.

- `extract_outlier_frames(config, videos, video_extensions=None, shuffle=1, trainingsetindex=0, outlieralgorithm='jump', frames2use=None, comparisonbodyparts='all', epsilon=20, p_bound=0.01, ARdegree=3, MAdegree=1, alpha=0.01, extractionalgorithm='kmeans', automatic=False, cluster_resizewidth=30, cluster_color=False, opencv=True, savelabeled=False, copy_videos=False, destfolder=None, modelprefix='', track_method='', **kwargs)`
  - Selects frames for manual correction.
  - `outlieralgorithm`: `jump`, `uncertain`, `fitting`, `manual`, or `list`.
  - `extractionalgorithm`: `kmeans` or `uniform`.
  - Can save labeled frames and can add the video to the project when needed.

- `find_outliers_in_raw_data(config, pickle_file, video_file, pcutoff=0.1, percentiles=(5, 95), with_annotations=True, extraction_algo='kmeans', copy_videos=False)`
  - For raw detection pickles such as `_full.pickle` or `_assemblies.pickle`.
  - Useful when refinement starts from raw detections rather than analyzed `.h5` pose outputs.

- `merge_datasets(config, forceiterate=None)`
  - Merges corrected labels back into the training set.
  - Advances `iteration` only after all required labeled-data folders are complete.

## Video inspection and labeled outputs

- `create_labeled_video(config, videos, video_extensions=None, shuffle=1, trainingsetindex=0, filtered=False, fastmode=True, save_frames=False, keypoints_only=False, Frames2plot=None, displayedbodyparts='all', displayedindividuals='all', codec='mp4v', outputframerate=None, destfolder=None, draw_skeleton=False, trailpoints=0, displaycropped=False, color_by='bodypart', modelprefix='', init_weights='', track_method='', superanimal_name='', pcutoff=None, skeleton=None, skeleton_color='white', dotsize=8, colormap='rainbow', alphavalue=0.5, overwrite=False, confidence_to_alpha=False, plot_bboxes=True, bboxes_pcutoff=None, max_workers=None, **kwargs)`
  - Renders labels on analyzed videos.
  - Use `filtered=True` to read `*_filtered.h5` outputs.
  - `draw_skeleton`, `trailpoints`, `keypoints_only`, `displaycropped`, and `color_by` control appearance.
  - Output videos are written as labeled mp4s near the analyzed file or in `destfolder`; filtered renders use a filtered-labeled suffix.

- `plot_trajectories(config, videos, video_extensions=None, shuffle=1, trainingsetindex=0, filtered=False, displayedbodyparts='all', displayedindividuals='all', showfigures=False, destfolder=None, modelprefix='', imagetype='.png', resolution=100, linewidth=1.0, track_method='', pcutoff=None, **kwargs)`
  - Creates bodypart-vs-time, x/y, likelihood, and histogram plots.
  - Use `filtered=True` to inspect the filtered predictions.
  - Output folder is `plot-poses/<video-stem>/`.

- `analyzeskeleton(config, videos, video_extensions=None, shuffle=1, trainingsetindex=0, filtered=False, save_as_csv=False, destfolder=None, modelprefix='', track_method='', return_data=False, **kwargs)`
  - Computes length and orientation for each skeleton edge.
  - Requires a non-empty skeleton definition in the project config.
  - Writes `*_skeleton.h5` and, if requested, CSV.

## Video utilities

- `check_video_integrity(video_path)`
  - Verifies that a video can be opened and read reliably.
  - Writes a `.log` file next to the video when ffmpeg reports errors.

- `CropVideo(vname, width=256, height=256, origin_x=0, origin_y=0, outsuffix='cropped', outpath=None, useGUI=False)`
  - Crops to a fixed rectangle.
  - Coordinates are `origin_x`, `origin_y`, `width`, `height`.

- `DownSampleVideo(vname, width=-1, height=200, outsuffix='downsampled', outpath=None, rotatecw='No', angle=0.0)`
  - Rescales the video while preserving aspect ratio when one dimension is `-1`.
  - Optional rotation is supported.

- `ShortenVideo(vname, start='00:00:01', stop='00:01:00', outsuffix='short', outpath=None)`
  - Trims the video between two timestamps.

## 3D stereo workflow

- `calibrate_cameras(config, cbrow=8, cbcol=6, calibrate=False, alpha=0.4, search_window_size=(11, 11))`
  - Extracts checkerboard corners and calibrates a stereo pair.
  - Use 20-60 calibration image pairs.
  - Camera names in filenames must match the names listed in the 3D config.
  - First inspect with `calibrate=False`, then rerun with `calibrate=True` after curation.
  - Writes per-camera intrinsic pickles and `stereo_params.pickle` for later triangulation and undistortion.

- `check_undistortion(config, cbrow=8, cbcol=6, plot=True)`
  - Generates undistorted calibration images and visual checks.

- `triangulate(config, video_path, videotype='', filterpredictions=True, filtertype='median', gputouse=None, destfolder=None, save_as_csv=False, track_method='')`
  - Triangulates paired camera outputs into 3D predictions.
  - Accepts a directory of videos or explicit video pairs.
  - Prefers filtered 2D data when it exists and `filterpredictions=True`.
  - Camera names and filename prefix/suffix pairing must be consistent across views.
  - Writes 3D `.h5`, optional `.csv`, and metadata pickle files.

- `create_labeled_video_3d(config, path, videofolder=None, start=0, end=None, trailpoints=0, videotype='', view=(-113, -270), xlim=None, ylim=None, zlim=None, draw_skeleton=True, color_by='bodypart', figsize=(20, 8), fps=30, dpi=300)`
  - Builds a combined 2D/3D visualization from triangulated outputs and writes a labeled mp4 alongside the triangulated file.
  - Use `videofolder` when the camera videos are not stored next to the triangulated file.
  - `color_by` supports `bodypart` or `individual`.

## Model export

- `export_model(config, shuffle=1, trainingsetindex=0, snapshotindex=None, detector_snapshot_index=None, iteration=None, overwrite=False, wipe_paths=False, without_detector=False, modelprefix=None)`
  - Public export router for trained models.
  - For the current PyTorch engine, exports portable `.pt` bundles under `exported-models-pytorch/`.
  - Top-down models need a detector snapshot unless `without_detector=True`.
  - `wipe_paths=True` removes local project-path references from the exported config payload.

## Practical notes

- Keep the same `destfolder`, `shuffle`, `trainingsetindex`, `modelprefix`, and `track_method` when moving from analysis to filtering, plotting, labeled videos, and skeleton analysis.
- Use `filtered=True` only when the matching filtered file exists.
- The helper script in `scripts/collect_video_inventory.py` mirrors the safe video-selection style used by this sub-skill.
