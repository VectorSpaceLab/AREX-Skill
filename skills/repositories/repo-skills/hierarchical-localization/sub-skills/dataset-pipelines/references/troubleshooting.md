# Troubleshooting

This guide focuses on planning-stage failures for dataset-specific hloc workflows: missing downloads, pair files, calibration files, benchmark outputs, and filesystem scale.

## 1. Missing downloads or partial extraction

Typical symptoms:

- The dataset root does not exist.
- A pipeline asserts that `images`, `queries`, `sparse`, or a benchmark-specific model folder is missing.
- A challenge archive was unpacked only partially.

What to check:

- Aachen v1.0: `images_upright/`, `3D-models/aachen_cvpr2018_db.nvm`, `3D-models/database_intrinsics.txt`, `aachen.db`, `queries/`.
- Aachen v1.1: `images_upright/`, `3D-models/aachen_v_1_1`, `queries/`.
- InLoc: dataset images and metadata for the benchmark root, plus a precomputed retrieval pair file.
- SfM demo: a small local mapping image folder under `datasets/sacre_coeur/`.
- 4Seasons: `reference/undistorted_images`, `reference/poses.txt`, `reference/Calibration/undistorted_calib_0.txt`, `reference/Calibration/undistorted_calib_1.txt`, `reference/Calibration/undistorted_calib_stereo.txt`, and the sequence folders under `training`, `validation`, `test0`, or `test1`.
- 7Scenes: scene folders, triangulated SIFT models, DenseVLAD pair files, and optional rendered depth.
- CMU: root `intrinsics.txt` and per-slice `database`, `query`, `sparse`, and `test-images-sliceN.txt` files.
- Cambridge: the scene folders plus `CambridgeLandmarks_Colmap_Retriangulated_1024px/<scene>/`.
- RobotCar: unpacked condition folders, the three intrinsics files, and the NVM / reference database pair.

Plan-only fix:

- Report the missing folder names and the expected output root.
- Do not start `wget`, `gdown`, unzip, or benchmark evaluation automatically.

## 2. Pair files or query lists are missing

Typical symptoms:

- `pairs-db-covis{N}.txt`, `pairs-query-netvlad{N}.txt`, or sequence-specific pair files are absent.
- A localization step cannot find `*_queries_with_intrinsics.txt`, `query_list_with_intrinsics.txt`, or `results*.txt`.
- InLoc has the benchmark images but no retrieval pair file.

What to check:

- The pair file must be created under the same output root as the rest of the run.
- Query-list files and retrieval pairs must agree on the same dataset root and scene or sequence naming.
- InLoc expects a precomputed retrieval pair file before localization.

Plan-only fix:

- State which pair file is missing and which route should create it.
- If the request is only to plan, stop before calling the pipeline.

## 3. Calibration or intrinsics mismatch

Typical symptoms:

- The query list generator fails or localization reports camera issues.
- The wrong scene or sequence is paired with the wrong intrinsics file.
- Dense-depth mode is requested but the depth folder is absent.

What to check:

- Aachen, Cambridge, CMU, RobotCar, 7Scenes, and 4Seasons all rely on per-image or per-sequence intrinsics data.
- 4Seasons requires the reference poses, calibration files, and the relocalization-file layout to agree with the chosen sequence.
- 7Scenes dense mode requires the rendered-depth directory for the selected scene.
- RobotCar needs all three camera-side intrinsics files.

Plan-only fix:

- Confirm the camera model and the exact intrinsics path before any run.
- If the calibration file is missing, keep the response at the planning stage.

## 4. Benchmark output or submission file not found

Typical symptoms:

- The run completed but the expected result file is missing.
- A user asks where to find the submission artifact or per-scene report.

Expected locations:

- Aachen: `./outputs/aachen/Aachen_hloc_superpoint+superglue_netvlad50.txt`
- Aachen v1.1: `./outputs/aachen_v1.1/Aachen-v1.1_hloc_superpoint+superglue_netvlad50.txt`
- InLoc: `./outputs/inloc/InLoc_hloc_superpoint+superglue_netvlad40.txt`
- 4Seasons: `./outputs/4Seasons/localization_<sequence>_hloc+superglue.txt` and `submission_hloc+superglue/`
- 7Scenes: per-scene `results_sparse.txt` or `results_dense.txt`
- CMU: per-slice `CMU_hloc_superpoint+superglue_netvlad10.txt`
- Cambridge: per-scene `results.txt`
- RobotCar: `./outputs/robotcar/RobotCar_hloc_superpoint+superglue_netvlad20.txt`
- SfM demo: `./outputs/demo/sfm/`, `features.h5`, and `matches.h5`

Plan-only fix:

- Restate the exact output path before any run.
- If the user only wants a route, do not imply that evaluation or submission packaging has already happened.

## 5. Filesystem scale and dataset mutation

Typical symptoms:

- The run is slow on a network mount or shared filesystem.
- A dataset directory has unexpectedly fewer images after a 4Seasons prep step.
- Large HDF5 or SfM outputs fill the filesystem quickly.

What to do:

- Prefer a local SSD or fast scratch space for `outputs/`.
- Keep large benchmark runs out of the planning path.
- Reduce only the planning scope, not the correctness requirements, when the user asks for a dry run.
- Treat 4Seasons as potentially destructive: the prep step may delete unused images to speed up feature extraction, so work on a copy if you need to preserve the original files.

## 6. When to reroute

- Feature/retrieval/HDF5 questions should go to `feature-retrieval`.
- SfM, pair generation, and localization logic should go to `mapping-localization`.
- New extractor, matcher, or model implementation should go to `custom-interop`.

## Planning rule

If the user asks only for a safe plan, give the missing prerequisites, the output root, and the command skeleton, then stop. Do not start a benchmark-scale run unless the user explicitly asks for execution.
