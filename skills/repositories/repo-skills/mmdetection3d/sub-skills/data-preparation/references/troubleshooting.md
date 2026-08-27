# Data Preparation Troubleshooting

Use this when dataset conversion, layout validation, or info migration is blocked. The bundled helpers in [`../scripts/`](../scripts/) are non-mutating; use them to inspect before running native conversion commands.

## Root and layout mistakes

| Symptom | Likely cause | Action |
| --- | --- | --- |
| Converter cannot find `ImageSets`, `samples`, `sequences`, or metadata files. | `--root-path` points one level too high or too low; dataset was not symlinked or config `data_root` differs from the conversion root. | Run `check_dataset_layout.py <dataset> --root <root> --stage preconvert`. Fix the root or adjust config `data_root`/`data_prefix`. |
| Training later cannot find point or image paths though conversion succeeded. | `--out-dir` differs from `--root-path`, but configs still expect outputs under the dataset root. | Link/copy the converted output back, or update config `data_root`, `ann_file`, and `data_prefix`. |
| Ready-made annotation pickles load, but `ObjectSample` fails. | Ground-truth database files were not generated. | Render an `--only-gt-database` command for KITTI, NuScenes, or Waymo when supported, then run it only after confirming the input info pickle exists. |
| Layout checker fails on indoor datasets before `create_data.py`. | S3DIS/ScanNet/SUN RGB-D require dataset-specific export or MATLAB extraction before MMDetection3D conversion. | Check `source` stage first, perform the dataset-provided export outside the safe helper, then check `preconvert` or `converted` stage. |

## Unsupported or mismatched custom conversion

- MMDetection3D v1.4.0 source dispatch does not implement a verified `create_data.py custom` branch even though the customization guide shows a custom command shape.
- Do not promise that a custom conversion command will work unless the user's checkout has added a custom branch.
- Prefer one of these paths:
  1. reorganize to a supported dataset format such as KITTI-style data;
  2. write a converter that emits v2 `metainfo`/`data_list` pickles;
  3. register a custom dataset class and config.
- Use [`custom-dataset.md`](custom-dataset.md) to validate raw folder structure and info-pickle expectations.

## Dataset-specific blockers

### KITTI

- Missing split files under `ImageSets/` blocks info generation.
- `--with-plane` requires `training/planes/`; omit it if road planes were not prepared.
- Reduced point clouds are generated under `training/velodyne_reduced/` and `testing/velodyne_reduced/`; configs often point to those directories for testing.
- KITTI info boxes in the documented v2 format differ from old database-info coordinate conventions; use the migration helpers only for the matching old files.

### Waymo

- Full Waymo conversion is CPU/storage intensive and may appear stuck. Reduce `--workers`; set it to `0` when diagnosing multiprocessing hangs.
- Use the command builder's `--quiet-tf` flag to render `TF_CPP_MIN_LOG_LEVEL=3` when TensorFlow logging obscures conversion output.
- Install the Waymo Open Dataset TensorFlow package appropriate for the environment before full conversion.
- `--out-dir` writes `kitti_format/` under that output root. If the output root is a large external disk, link `kitti_format/` back or update configs.
- `--skip-saving-sensor-data` can reduce sensor-output writes only when existing sensor data is already usable for the intended workflow; do not use it blindly for first conversion.
- Waymo evaluation/submission binaries are a training/evaluation concern; route that part to `training-evaluation`.

### NuScenes

- Full `v1.0` expects both trainval and test metadata; `v1.0-mini` expects mini metadata and normally lacks full test outputs.
- Lidarseg preparation can replace category metadata in the dataset metadata folder. Confirm the user wants semantic segmentation before modifying a shared NuScenes root.
- Multi-sweep configs depend on sweeps paths and timestamps. If paths are missing, inspect `samples/`, `sweeps/`, and the generated info pickle.
- LiDAR boxes and camera boxes have different dimension/yaw conventions. Route projection or yaw debugging to `structures-visualization`.

### Lyft

- Keep the original `v1.01-train` and `v1.01-test` folder names; renamed Kaggle folders are a common source of missing metadata.
- Run the Lyft data fixer after conversion when preparing the standard v1.01 data; it handles a known corrupted lidar file.
- Lyft does not rely on the same generated ground-truth database flow as NuScenes in v1.4.0 guidance.

### SemanticKITTI

- Train/val/test sequence ranges are fixed by convention: training 00-07 and 09-10, validation 08, testing 11-22.
- Label files encode instance and semantic ids in one integer. If semantic masks look wrong, verify bit handling before blaming the model.
- Test sequences may not have labels; do not require labels for online test data.

### S3DIS

- Run the S3DIS collection/export step before `create_data.py`; the raw Stanford room folders alone are not the converted input.
- Check that `points/`, `instance_mask/`, `semantic_mask/`, `seg_info/`, and all area info pickles exist after conversion.
- Area split changes are config decisions; route train/validation split config changes to `configuration-model-zoo` if model configs are involved.

### ScanNet

- Run the ScanNet batch export first; `create_data.py` expects exported scene arrays, not only raw `scans/`.
- Optional RGB export can create a very large `posed_images/` tree; prepare it only for workflows that actually need multi-view image data.
- Detection stores unaligned points plus an axis-alignment matrix. If boxes appear rotated or shifted, route coordinate debugging to `structures-visualization`.

### SUN RGB-D

- MATLAB extraction must create `sunrgbd_trainval/` before `create_data.py sunrgbd` can produce info pickles.
- MMDetection3D v1.4.0 uses v1 labels for training/testing even though v2 labels may also be extracted.
- Depth-coordinate yaw migrations should be applied only to the old coordinate format and preferably into a separate output directory.

## Info migration and stale pickles

| Situation | Use | Safety note |
| --- | --- | --- |
| Info pickle was generated by early v1.0.0 release candidates and lacks current `metainfo`/`data_list` layout. | `build_create_data_command.py update-infos --dataset <name> --pkl-path <file> --out-dir <new_dir>` | Use a new output directory first; inspect one migrated sample before replacing files. |
| Old coordinate-refactor files must be updated. | `build_create_data_command.py update-coords --dataset <name> --root-dir <root> --out-dir <new_dir>` | The native coordinate-update helper can overwrite when output equals input; back up first. |
| Info pickle has old `infos` key instead of `data_list`. | Likely stale pre-v2 format. | Use `update-infos` if the dataset is supported; otherwise write a custom migration. |
| Paths inside pickle are absolute or point to another machine. | Converter or custom migration stored non-portable paths. | Regenerate or rewrite paths relative to `data_root`; avoid putting machine-specific paths in public artifacts. |

## Dependency and runtime issues

- Dataset conversion runs on CPU but imports the MMDetection3D/OpenMMLab stack and dataset SDKs.
- NuScenes and Lyft conversion require their dataset SDK packages.
- Waymo conversion requires the Waymo Open Dataset TensorFlow package and substantial storage.
- SUN RGB-D extraction requires MATLAB before MMDetection3D conversion.
- Optional sparse convolution packages are not needed just to render commands or check layouts.
- Full conversion can be expensive; do not run it as a quick verification unless the user explicitly asks and the dataset root is ready.

## What the bundled checker cannot prove

`check_dataset_layout.py` only verifies path existence for documented required and recommended entries. It does not validate:

- whether point files have the correct dtype, dimension, endianness, or point count;
- whether calibration matrices are numerically correct;
- whether label ids match class names;
- whether box dimensions/yaw follow the declared coordinate system;
- whether info pickles deserialize or match the installed package schema;
- whether a full conversion will fit disk, memory, or time limits.

For those checks, inspect representative files, load a small sample in the installed environment, or route to the relevant configuration/geometry/training sub-skill.
