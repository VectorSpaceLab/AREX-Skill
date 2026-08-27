# Mapping/localization troubleshooting

Start with the safe validator before rerunning expensive pycolmap operations:

```bash
python sub-skills/mapping-localization/scripts/validate_hloc_inputs.py --help
```

## pycolmap or COLMAP model errors

Symptoms:

- `ModuleNotFoundError: No module named 'pycolmap'`.
- `pycolmap.Reconstruction(...)` fails to load a model folder.
- Pair generation from covisibility/poses finds no useful pairs.
- Localization logs warn that retrieved images are not in the database/model.

Checks and fixes:

1. Confirm the runtime environment imports `hloc` and `pycolmap`.
2. Confirm model folders contain `cameras.bin`, `images.bin`, and `points3D.bin`. Newer models may also contain `frames.bin` and `rigs.bin`.
3. Confirm image names in pair/retrieval files exactly match model image names. Directory prefixes and case must match.
4. Covisibility pairs require 3D point tracks; a pose-only model may work for `pairs_from_poses` but not for useful covisibility.
5. If a reconstructed model is empty, reduce pair/match filtering, verify image import, or try a more connected pair graph.

## Option parsing failures

Symptoms:

- `Options format: key1=value1 key2=value2 etc.`
- `Unknown option ... allowed options ...`
- `Incorrect type for option ...`
- A triangulation CLI run fails when mapper options are needed.

Checks and fixes:

1. Pass pycolmap options as separate `key=value` arguments, for example `--mapper_options min_num_matches=15 ba_refine_focal_length=True`.
2. Values are parsed as Python literals. Numbers and booleans can be written directly; strings need quotes that survive shell parsing, for example `camera_model='"PINHOLE"'`.
3. Keys must exist on the corresponding pycolmap options object. If uncertain, run the command with `--help` or inspect pycolmap option summaries in a short Python snippet.
4. The reconstruction CLI exposes `--image_options` and `--mapper_options`; the triangulation Python API exposes `mapper_options`. Prefer the Python API when the CLI does not expose an option required by the run.

## Missing pairs, features, or matches

Symptoms:

- Assertion failures on `features`, `pairs`, or `matches` paths.
- `Could not find pair (...) Maybe you matched with a different list of pairs?`
- HDF5 `KeyError` for an image name or dataset.
- Reconstruction imports images but fails while importing keypoints or matches.

Checks and fixes:

1. Run the validator with the workflow that matches the command:

   ```bash
   python sub-skills/mapping-localization/scripts/validate_hloc_inputs.py \
     --workflow reconstruction \
     --pairs pairs.txt \
     --features features.h5 \
     --matches matches.h5 \
     --image-dir images
   ```

2. Pair/retrieval files must have exactly two tokens per non-empty line. Do not include comments in pair files.
3. Feature HDF5 image groups must use the original image names. If names include `/`, they appear as nested HDF5 paths.
4. Match group names replace `/` inside image names with `-` and join the two names with `/`. Reverse groups and older underscore groups can be read by hloc, but consistent forward naming is easier to debug.
5. If `min_match_score` is set too high, too few matches may survive import or PnP. Retry without it or with a lower threshold.
6. For localization, ensure the retrieval file used to create matches is the same retrieval file passed to `localize_sfm` or `localize_inloc`.

## Reconstruction does not produce a usable model

Symptoms:

- `Could not reconstruct any model!`
- Very few registered images.
- COLMAP logs show repeated failed initial pairs or no verified matches.

Checks and fixes:

1. Confirm `image_dir` contains the referenced images and that any `image_list` subset names are relative to that directory.
2. Check pair graph connectivity. Retrieval pairs with too small `num_matched` may isolate images; exhaustive pairs can be safer for small datasets.
3. Confirm features and matches are for the same image resolution/name set used by reconstruction.
4. Keep geometric verification enabled unless matches are already trusted and verified elsewhere.
5. Try `--camera_mode SINGLE` only when images genuinely share intrinsics. Wrong camera sharing can prevent stable mapping.
6. If using `--skip_geometric_verification`, understand that bad matches will be imported as inliers and may degrade or break reconstruction.

## Triangulation from known poses fails

Symptoms:

- `reference_model` assertion or load errors.
- Model-aware geometric verification has no inliers.
- `pycolmap.triangulate_points` returns few or no points.

Checks and fixes:

1. The reference model must contain cameras and registered images with names matching pair and feature files.
2. Use `pairs_from_poses` for pose-neighbor pairs or `pairs_from_covisibility` only when the model already has useful 3D tracks.
3. If reference poses are good but two-view geometry estimation is needed instead of model-aware checks, use the Python API with `estimate_two_view_geometries=True`.
4. Check that keypoints were extracted from the same images and coordinate frame used to create the known poses.
5. Reduce or remove `min_match_score` if too few matches remain.

## SfM localization PnP failures

Symptoms:

- Warnings: `No images retrieved for query image ...`.
- Warnings: `Image ... was retrieved but not in database`.
- Query lines are absent from the result file.
- Result pose exists but has low inlier count in logs.

Checks and fixes:

1. Query names in the intrinsics list must exactly match the left column of the retrieval file and the query feature HDF5 groups.
2. Database names in the retrieval file must exactly match image names registered in the reference model.
3. Match HDF5 must contain query-reference groups for the same retrieval file.
4. Intrinsics must use a correct camera model, image size, and parameter order. Bad intrinsics can make PnP fail even with good matches.
5. Increase retrieval `num_matched` when the correct reference image may not be among the candidates.
6. Enable `--covisibility_clustering` when retrieval returns images from multiple disconnected scene components.
7. Inspect `<results>_logs.pkl`; use `PnP_ret`, inlier counts, and `num_matches` to distinguish true localization from fallback/weak poses.

## InLoc scan and alignment failures

Symptoms:

- Missing `.mat` scan files.
- Missing alignment transform files.
- Interpolation assertions or all-NaN scan points.
- Very low InLoc PnP inlier count.

Checks and fixes:

1. Dataset-specific file layout belongs in `../dataset-pipelines/`; confirm the InLoc-style tree is present before calling the low-level localizer.
2. Each retrieved database image path `r` must have a corresponding scan file at `dataset_dir / (r + ".mat")` containing `XYZcut`.
3. Database image path segments must encode floor, scan, and building names in the layout expected by the localizer.
4. Feature HDF5 must contain keypoints for both query and retrieved database names.
5. Match groups must use the same retrieval pairs passed to `localize_inloc`.
6. Use `--skip_matches` to skip retrieved images with too few tentative matches, but avoid setting it so high that all candidates are skipped.

## Pose output interpretation

Symptoms:

- Pose file has fewer lines than queries.
- Pose file contains a line for a query that actually failed strong PnP.
- Downstream evaluator expects a different query name format.

Checks and fixes:

1. Pose lines are `name qw qx qy qz tx ty tz`; quaternion order is scalar first.
2. `localize_sfm` writes only the image basename by default. Use `--prepend_camera_name` if downstream tooling needs `parent/name.jpg`.
3. The translation is the pycolmap `cam_from_world` translation.
4. Always pair pose files with `<results>_logs.pkl` for quality checks.
5. If a downstream evaluator uses dataset-specific naming, route to `../dataset-pipelines/` for the benchmark adapter.
