# Data preparation troubleshooting

Use the smallest static check first. Do not repair by silently changing dataset
versions, class names, point widths, or generated pickles.

## Install and import

| Symptom | Likely cause | Recovery |
|---|---|---|
| `ModuleNotFoundError` for `fire`, `scikit-image`, `numba`, `tensorboardX`, `protobuf`, or `nuscenes` | The legacy inspection/runtime dependency is absent | Prepare an isolated environment with only the needed route. Probe imports individually. NuScenes preparation needs the devkit; KITTI info generation needs image reading and numerical dependencies. |
| Import fails in sparse convolution or non-maximum suppression | The checkout uses legacy APIs; modern spconv 2.x is not proven compatible, and the inspected environment lacks legacy `VoxelGeneratorV2`/`non_max_suppression` | Keep data validation/static guidance separate from detector execution. Do not patch generated data to hide the backend failure. Record the blocked legacy runtime and use a maintained detector for new work. |
| Numba CUDA initialization error | Legacy Numba CUDA variables or driver assumptions are missing | Treat as an optional detector/runtime issue. Validate files and pickle paths on CPU; do not claim CUDA detector support from a device smoke test. |
| No `setup.py`, `pyproject.toml`, or package metadata | This checkout has no setup metadata | Use an explicit package path/PYTHONPATH only in a private execution context. Do not put local environment names or absolute checkout paths into a generated config. |

## Optional dependencies

| Feature | Dependency/condition | Safe response |
|---|---|---|
| KITTI image shape and reduced clouds | image reader (`scikit-image`) plus NumPy | Install/probe before info generation; a directory-only pass cannot prove image readability. |
| NuScenes infos/database | NuScenes devkit and its metadata tables | Confirm `--version` and devkit version against the downloaded dataset. Missing tables or partial sweeps are data failures, not sampler failures. |
| Detector voxelization/legacy NMS | legacy spconv and Numba-compatible APIs | Keep guarded. Current spconv 2.3.8 does not provide the inspected legacy symbols, so no detector execution is accepted as verified. |
| Visualization | image/OpenCV/plotting stack | Optional for static preparation. Prefer a small format/transform check before adding visualization dependencies. |

## Data and config validation

### KITTI

- `validate_dataset_layout.py kitti --root <ROOT>` must pass before writers.
- Missing `training/calib` or a calibration file with fewer than the expected
  seven numeric rows causes `get_kitti_image_info` or reduction to fail. Check
  P0–P3, R0_rect, Tr_velo_to_cam, and Tr_imu_to_velo ordering.
- Missing `training/velodyne_reduced` or `testing/velodyne_reduced` is a
  preparation-layout failure in the validator. Create the directories before
  the writer; they may be empty before reduction.
- The source uses six-digit ids and fixed ImageSets lists. A nonempty directory
  with nonmatching stems is not usable. Compare image, calib, lidar, and (for
  training) label stem sets.
- A `.bin` whose byte count is not divisible by 16 cannot be reshaped into four
  float32 features.
- If a runtime unexpectedly reads raw lidar, check whether the reduced file
  exists at the sibling `velodyne_reduced` path. The reader silently prefers it
  when present; compare raw/reduced counts intentionally.
- A stale `kitti_infos_*.pkl` can reference moved files or old calibration. Rerun
  info/reduction/database generation together after source, split, calibration,
  or path-layout changes.

### NuScenes

- The requested version must be one of `v1.0-trainval`, `v1.0-test`, or
  `v1.0-mini`, and the corresponding metadata directory must exist below the
  root. A valid `samples/` directory does not make another version valid.
- `v1.0-trainval` generates train/val infos; `v1.0-test` generates only
  `infos_test.pkl`; `v1.0-mini` uses mini train/val splits. Do not point a
  validation reader at `infos_test.pkl` and expect annotations.
- `max_sweeps` is written into each info's `sweeps` list. The guide recommends
  10 for quality; zero/key-frame-only is a deliberate quality tradeoff. If the
  info was generated with another count, regenerate or make that choice
  explicit rather than changing only the config.
- The generator asserts key lidar files and reads previous sweeps. A partial
  download produces missing-file errors while building infos. Confirm file paths
  in the metadata and that the previous-frame chain is available.
- The reader returns points `[x,y,z,time_delta]`, not raw five-column NuScenes
  records. Do not set model or dataset point features to 5 for the built-in
  reader.

## CLI/API misuse

- `create_data.py` functions use `root_path`, not `data_path`, in their source
  signatures. README examples show `--data_path`; if Fire rejects that option,
  retry only after checking the separately supplied writer's `--help` output
  and use `--root_path`.
- `nuscenes_data_prep` requires all of `root_path`, `version`, and
  `dataset_name`; `max_sweeps` defaults to 10. Omitting `dataset_name` is not a
  request to infer it.
- `create_reduced_point_cloud` defaults to all three info paths, so a missing
  test info can fail an otherwise complete train reduction. Pass explicit info
  paths only when a deliberate partial route is supported.
- `kitti_info_path` and `kitti_root_path` are historical names but are consumed
  for NuScenes too. Fill them with the NuScenes info/root, not KITTI paths.
- Registry errors (`available class: ...`) mean the class module was not
  imported, the name is misspelled, or a duplicate registration was attempted.
  Import the custom module before building the reader and use the exact class
  name.
- `assert dataset_cls.NumPointFeatures == model_config.num_point_features`
  means changing only one side of the config is invalid. Built-in KITTI and
  NuScenes readers both use four point features.

## Workflow-specific failures

### Ground-truth database

- `FileNotFoundError` for `kitti_infos_train.pkl` means the info stage did not
  finish or the database command used the wrong root. Do not create an empty
  placeholder pickle; regenerate from real annotations.
- `gt_database` files are object-localized point clouds. If the sampler reports
  missing relative paths, check that the database pickle's `path` is resolved
  under the configured root and that the directory was not moved.
- Empty class entries or no sampled objects can be caused by class spelling,
  `filter_by_difficulty`, `filter_by_min_num_points`, or `sample_groups`. Log
  counts before changing thresholds. `DontCare` and unmapped NuScenes names
  should not be added to target classes accidentally.
- `NuScenesDatasetVelo` with a database made by the non-Velo class is a schema
  mismatch. Regenerate the database with the same dataset class used by the
  input reader and configure nine-dimensional anchors/coders. Conversely, do
  not enable Velo custom values when using base seven-dimensional boxes.

### Preprocessing and augmentation

- Boxes disappearing after preprocessing usually means their centers fall
  outside the voxel point-cloud range, `min_num_of_points_in_gt` removed them,
  `remove_unknown_examples` removed difficulty `-1`, or database collision/noise
  filtering rejected them. Disable one option at a time and inspect counts.
- Point/box misalignment after a custom transform indicates a coordinate-frame
  or z-center error. For ordinary lidar boxes use center format and z center
  0.5; KITTI camera boxes use camera `[l,h,w]`, bottom-center conventions until
  converted. Route transform debugging to geometry-and-evaluation.
- Large NuScenes global rotation or enabled database sampler can degrade results;
  the guide recommends zero noise and disabling sampling while developing.
  Re-enable one change at a time and record `max_sweeps`, class, and sample rate.
- `groundtruth_points_drop_percentage` and `groundtruth_drop_max_keep_points`
  are accepted by the current preparation signature but are not the main active
  point-drop path in the inspected implementation. Do not claim they changed
  data unless a targeted runtime probe confirms it.
- A voxel cap truncating examples is a config/data-volume issue, not evidence of
  malformed files. Compare `max_number_of_voxels`, point-cloud range, voxel
  size, and per-sample point counts before changing class labels.

### Custom dataset

- `get_sensor_data` must return a lidar dictionary with points and, during
  training, annotations with equal-length boxes/names. Return boxes in the
  lidar frame; do not return camera boxes under a lidar key.
- Evaluation may require complete KITTI-style fields and explicit z-axis/z-center
  semantics. A fake 2D box or omitted field can make metrics meaningless even
  if serialization succeeds. Route evaluation behavior to geometry-and-evaluation.
- Add a stable info schema and a small fixture before database generation. The
  historical release notes explicitly called custom-data support untested;
  preserve that uncertainty in the handoff.
