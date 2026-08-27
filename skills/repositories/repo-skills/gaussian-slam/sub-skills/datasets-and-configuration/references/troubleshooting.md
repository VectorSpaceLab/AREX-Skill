# Configuration and data troubleshooting

## Config fails before data inspection

- **`inherit_from` not found:** run from the intended repository/working root or
  change the child to a path relative to the child file. The validator prefers
  the file-relative interpretation and only accepts the repository's legacy
  root-relative form as a reported fallback. Check for cycles and YAML
  indentation.
- **Wrong dataset alias:** use exactly `replica`, `tum_rgbd`, `scan_net`, or
  `scannetpp`, matching `src/entities/datasets.py`. `scannet` is a common but
  invalid spelling for this codebase.
- **Missing effective section/key:** validate the merged scene config, not just
  the default. A scene override can replace a mapping accidentally, or omit
  `data` entirely. Restore `project_name`, `dataset_name`, `mapping`,
  `tracking`, `cam`, and `data` at the effective top level.
- **Bad camera geometry:** ensure positive `H`, `W`, `fx`, `fy`, and
  `depth_scale`; ensure `crop_edge * 2 < H` and `< W`. Crop changes principal
  points and output dimensions; it is not a depth-only trim.

## Data records are rejected

- **Replica count mismatch or missing pose:** compare `results/frame*.jpg`,
  `results/depth*.png`, and lines in `traj.txt`. Numeric IDs must correspond;
  never pad poses with identity matrices.
- **ScanNet missing pose:** every selected color/depth numeric ID needs a
  `pose/<id>.txt` 4x4 matrix. Check zero-padded names by numeric stem and remove
  stale files from a partial extraction.
- **TUM malformed timestamps:** list files need timestamp plus relative path;
  pose rows need timestamp, three translations, and four quaternion values.
  Remove non-comment prose from the data rows and keep timestamps finite. A
  missing `groundtruth.txt` is acceptable only when valid `pose.txt` exists.
- **TUM frame mismatch:** independent list lengths may differ, but the loader
  drops records without a nearest depth and pose within `0.08` seconds. Fix
  timestamp units/order or use the correct sequence calibration; do not simply
  zip the lists.
- **ScanNet++ split/camera mismatch:** verify that `use_train_split` selects
  the intended list and metadata array, that every split name exactly matches a
  metadata `file_path`, and that the name has the `.JPG` suffix expected by the
  depth replacement. Check the selected frame's 4x4 transform and scene
  intrinsics. A test split ignores `frame_limit` in the current loader.

## Run starts but images look wrong

- Check RGB/BGR conversion is expected and that color/depth resolutions match
  the configured camera after resize/crop.
- Check `depth_scale` against the encoded PNG units. A factor-of-1000 error is
  common between datasets.
- Check TUM distortion coefficients and crop are from the same sequence. An
  incorrect principal point after crop shifts all projections.
- Confirm poses are camera-to-world in the format expected by the loader:
  Replica and ScanNet read matrices directly; TUM normalizes from the first
  associated pose; ScanNet++ applies its fixed coordinate conversion.

## Relative input/output paths

The source `load_config` merges YAML but does not rebase `data.input_path` or
`data.output_path`. The CLI process therefore interprets relative paths from
its current working directory. Use one of:

```bash
python .../validate_config.py --path-base /work/Gaussian-SLAM --require-data \
  configs/TUM_RGBD/rgbd_dataset_freiburg1_desk.yaml
python run_slam.py configs/Replica/office0.yaml \
  --input_path /datasets/Replica/office0 --output_path /runs/office0
```

The second command is still a GPU/long-running operation; the validator only
checks the preconditions. If an output path already contains a checkpoint,
stop and decide explicitly whether this is a continuation or a new run rather
than overwriting results.

## What this sub-skill does not diagnose

A passing data/config check cannot prove CUDA availability, custom rasterizer
or k-nearest-neighbor extension imports, GPU memory sufficiency, mapping
convergence, or metric correctness. Route those issues to the runtime and
evaluation skills rather than weakening dataset validation.
