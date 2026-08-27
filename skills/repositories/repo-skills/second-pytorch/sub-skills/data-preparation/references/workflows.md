# Preparation workflows

These plans describe the historical write-producing argument contracts
without copying the writer. Inspect and validate first; run a separately
supplied writer only against a disposable or backed-up data root. The bundled
validator is the only runnable command here. No step proves detector execution.

## KITTI: validate → infos → reduced clouds → database

1. Validate the root without mutation:

```bash
python <skill-root>/scripts/validate_dataset_layout.py kitti --root <KITTI_ROOT>
```

Expected output ends with `OK: KITTI layout is valid ...`. For a partial/custom
split, use `--allow-empty-split` only when the split is intentionally absent;
the source writer still needs every image-set ID it reads.

2. `second/create_data.py` exposes the Fire operation
   `kitti_data_prep(root_path)`. Its implementation invokes
   `create_kitti_info_file(root_path)`, `create_reduced_point_cloud(root_path)`,
   then `create_groundtruth_database("KittiDataset", root_path,
   root_path / "kitti_infos_train.pkl")`. The historical argument shape is documentation only; this skill bundles no
writer:

```text
kitti_data_prep --root_path=<KITTI_ROOT>
```

The public README shows `--data_path`; the actual function parameter is
`root_path`, so prefer the source signature and verify the local Fire parser
with `--help` before running. The operation writes:

```text
<KITTI_ROOT>/kitti_infos_train.pkl
<KITTI_ROOT>/kitti_infos_val.pkl
<KITTI_ROOT>/kitti_infos_trainval.pkl
<KITTI_ROOT>/kitti_infos_test.pkl
<KITTI_ROOT>/training/velodyne_reduced/*.bin
<KITTI_ROOT>/testing/velodyne_reduced/*.bin
<KITTI_ROOT>/gt_database/*.bin
<KITTI_ROOT>/kitti_dbinfos_train.pkl
```

The source opens reduced-output files in write mode and does not create the
reduced directories explicitly. Create `training/velodyne_reduced` and
`testing/velodyne_reduced` before invoking it if they are missing. Re-running
can overwrite generated files. The source also computes `num_points_in_gt`
using calibration and image bounds while creating infos.

For explicit stages, the source functions have these contracts:

```text
create_kitti_info_file(data_path, save_path=None, relative_path=True)
create_reduced_point_cloud(data_path, train_info_path=None,
  val_info_path=None, test_info_path=None, save_path=None, with_back=False)
create_groundtruth_database(dataset_class_name, data_path, info_path=None,
  used_classes=None, database_save_path=None, db_info_save_path=None,
  relative_path=True, add_rgb=False, lidar_only=False, bev_only=False,
  coors_range=None)
```

Use the explicit stages if the default output location is unsuitable. The
reduction pass reads all three info files by default, so missing any one is a
failure rather than an optional branch.

3. Configure both readers with matching paths. For train use
`kitti_infos_train.pkl` and for validation use `kitti_infos_val.pkl`; set
`dataset_class_name: "KittiDataset"`, `kitti_root_path: "<KITTI_ROOT>"`, and
point feature width 4. Keep database sampler paths relative to that same root
unless `relative_path: false` was used when generating the database.

## NuScenes: version and sweeps are part of the contract

1. Validate metadata and the requested run contract:

```bash
python <skill-root>/scripts/validate_dataset_layout.py nuscenes \
  --root <NUSC_ROOT> --version v1.0-trainval --max-sweeps 10
```

Expected output reports the version directory, `samples`, `sweeps`, and
`max_sweeps`. The checker can detect a wrong version directory or a missing
payload, but it cannot replace the devkit's table/schema validation.

2. `second/create_data.py` exposes
`nuscenes_data_prep(root_path, version, dataset_name, max_sweeps=10)`. It calls
`create_nuscenes_infos(root_path, version=version, max_sweeps=max_sweeps)` and
then writes a ground-truth database from `infos_train.pkl` (or
`infos_test.pkl` for `v1.0-test`). Historical argument shapes are documentation only; this skill bundles no
writer:

```text
nuscenes_data_prep --root_path=<NUSC_ROOT> --version=v1.0-trainval \
  --dataset_name=NuScenesDataset --max_sweeps=10
nuscenes_data_prep --root_path=<NUSC_TEST_ROOT> --version=v1.0-test \
  --dataset_name=NuScenesDataset --max_sweeps=10
```

The repository README labels the root option `data_path`, but the source
signature is authoritative. `dataset_name` must match the intended database
box dimensionality: use `NuScenesDatasetVelo` (or a matching D-class Velo
variant) when velocity is intended. The writer creates:

```text
<NUSC_ROOT>/infos_train.pkl and infos_val.pkl   # trainval/mini
<NUSC_ROOT>/infos_test.pkl                      # test
<NUSC_ROOT>/gt_database/*.bin
<NUSC_ROOT>/kitti_dbinfos_train.pkl             # historical filename
```

3. Set the config's `dataset_class_name`, `kitti_info_path`, and
`kitti_root_path` consistently. Use `NuScenesDatasetD2`–`D8` only as deliberate
sample-count reductions for development. A Velo class requires nine-dimensional
box anchors/coders (typically `custom_values: [0, 0]`) and a database generated
from the matching class; otherwise use the seven-dimensional base class.

4. Use ten sweeps as the historical quality baseline. `max_sweeps=0` is
syntactically possible in the generator but contradicts the guide's key-frame
warning and should be an explicit reduced-quality experiment, not an accidental
mismatch. The generator walks previous lidar frames and asserts key-frame paths
exist; incomplete sweep downloads fail during info generation.

## Preprocessing and sampling order

`second/builder/dataset_builder.py` maps the protobuf input-reader fields to
`second.data.preprocess.prep_pointcloud`. In training, the effective order is:

1. load points/annotations;
2. optionally remove environment and unknown/DontCare objects;
3. optionally filter by minimum lidar points;
4. database-sample objects and prepend their points;
5. remove original points colliding with sampled boxes when
   `remove_points_after_sample` is true;
6. object noise/collision filtering, random flips, global rotation, scaling,
   translation, and range filtering;
7. shuffle points if enabled;
8. voxelize and create anchors/targets.

Start with the dataset guide's conservative NuScenes settings (zero object/global
noise and disabled database sampler while debugging). For KITTI, the checked-in
config demonstrates moderate object/global rotation and scaling, `random_flip_y`
true, and a Car sampler. Tune one class/range field at a time; route model
anchor/NMS questions to the model or geometry sub-skills.

## Custom dataset adaptation

Implement the public `Dataset` surface: `__len__`, `__getitem__`,
`get_sensor_data`, and `evaluation`. A sensor result must provide
`{"lidar": {"points": [N, 3+], "annotations": {"boxes": [N, 7(+),],
"names": [...] }}, "metadata": {...}}` for training; `calib` and camera data
are optional unless a KITTI conversion/evaluator is used. Boxes must be center
format in the lidar frame and use `[x, y, z, w, l, h, yaw]`; use z-center
0.5 for ordinary lidar boxes. Point feature count must agree with the class's
`NumPointFeatures` and model `num_point_features` in this legacy builder.

Registration steps:

1. Add the class to the registry via `@register_dataset` in a module imported by
   the package's data initializer, or explicitly import that module before
   `get_dataset_class` is called.
2. Ensure `all_dataset.py` can resolve the class name (the registry is
   `REGISTERED_DATASET_CLASSES`; duplicate names assert).
3. Generate an info file whose paths and arrays your class reads.
4. Set `dataset_class_name`, info path, root path, class names, and feature width
   in config; verify with a static fixture before enabling sampling.
5. Use a visual check or geometry test for box z-axis/center and yaw. Native
   custom-data support was explicitly marked untested in the release notes.

Do not reuse KITTI camera calibration for a custom lidar box unless the
coordinate transforms are actually valid. Route custom evaluation transforms
to geometry-and-evaluation.
