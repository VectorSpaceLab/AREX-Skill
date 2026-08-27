# Data and preprocessing API reference

The following names and defaults are distilled from the source modules. Use
these as contracts, not as a promise that every legacy dependency imports in a
modern environment.

## Dataset registry and constructors

`second.data.dataset` owns:

```python
REGISTERED_DATASET_CLASSES = {}
register_dataset(cls, name=None)
get_dataset_class(name)
```

Registration defaults to `cls.__name__` and rejects duplicate names. The package
initializer imports the built-in KITTI and NuScenes modules. The built-ins have
constructors:

```python
KittiDataset(root_path, info_path, class_names=None,
             prep_func=None, num_point_features=None)
NuScenesDataset(root_path, info_path, class_names=None,
               prep_func=None, num_point_features=None)
```

They load pickle infos, expose `__len__`, `get_sensor_data(query)`, `__getitem__`,
and `evaluation`. The builder supplies `prep_func`; direct constructor use
without a preprocessing function is only useful for raw sensor inspection.

Built-in registry names include:

```text
KittiDataset
NuScenesDataset
NuScenesDatasetVelo
NuScenesDatasetD2, D3, D4, D5, D6, D7, D8
NuScenesDatasetD2Velo, NuScenesDatasetD8Velo
```

The source also defines the other D-class variants. `Dk` subsamples a full
train set by taking sorted infos `[::k]` when the info count exceeds 28,000;
it does not change the generated file's metadata.

## Writer signatures

`second/create_data.py` is a thin Fire wrapper:

```python
def kitti_data_prep(root_path): ...
def nuscenes_data_prep(root_path, version, dataset_name, max_sweeps=10): ...
```

The underlying writers are:

```python
create_kitti_info_file(data_path, save_path=None, relative_path=True)
create_reduced_point_cloud(data_path, train_info_path=None,
    val_info_path=None, test_info_path=None, save_path=None,
    with_back=False)
create_nuscenes_infos(root_path, version="v1.0-trainval", max_sweeps=10)
create_groundtruth_database(dataset_class_name, data_path, info_path=None,
    used_classes=None, database_save_path=None, db_info_save_path=None,
    relative_path=True, add_rgb=False, lidar_only=False, bev_only=False,
    coors_range=None)
```

`kitti_data_prep` invokes all three KITTI stages and uses
`kitti_infos_train.pkl` as database input. `nuscenes_data_prep` chooses
`infos_test.pkl` only when `version == "v1.0-test"`, otherwise
`infos_train.pkl`.

## Source-authoritative path behavior

`kitti_common.get_*_path` functions form six-digit names and use:

```text
training/{image_2,label_2,velodyne,calib}/<id>.<png|txt|bin>
testing/{image_2,label_2,velodyne,calib}/<id>.<png|txt|bin>
```

`get_kitti_image_info` reads image shape with scikit-image, parses calibration,
loads labels, and records relative paths by default. `_calculate_num_points_in_gt`
projects/removes points outside the image and counts points in lidar boxes.
`create_reduced_point_cloud` uses the same calibration/image bounds and writes
filtered four-feature clouds. It does not create missing reduced directories.

`KittiDataset.get_sensor_data` prefers a sibling `velodyne_reduced` file when it
exists, loads four float32 columns, removes `DontCare` only when constructing
training annotations, converts camera boxes to lidar boxes, and shifts the
KITTI bottom-centered box to center format. `NuScenesDataset.get_sensor_data`
concatenates key lidar plus transformed previous sweeps and returns four
features; it filters annotations to boxes with `num_lidar_pts > 0`.

## `prep_pointcloud` contract

```python
prep_pointcloud(input_dict, root_path, voxel_generator, target_assigner,
    db_sampler=None, max_voxels=20000, remove_outside_points=False,
    training=True, create_targets=True, shuffle_points=False,
    remove_unknown=False, gt_rotation_noise=(-pi/3, pi/3),
    gt_loc_noise_std=(1,1,1), global_rotation_noise=(-pi/4, pi/4),
    global_scaling_noise=(.95,1.05), global_random_rot_range=(.78,2.35),
    global_translate_noise_std=(0,0,0), num_point_features=4,
    anchor_area_threshold=1, gt_points_drop=0., gt_drop_max_keep=10,
    remove_points_after_sample=True, anchor_cache=None,
    remove_environment=False, random_crop=False,
    reference_detections=None, out_size_factor=2, use_group_id=False,
    multi_gpu=False, min_points_in_gt=-1, random_flip_x=True,
    random_flip_y=True, sample_importance=1., out_dtype=np.float32)
```

The builder overrides these from `InputReader.Preprocess`. Some arguments are
legacy or currently inert in the shown path (`remove_outside_points` is passed
false by the builder; point-drop fields are accepted but not the primary
normal route). Do not infer behavior solely from a config field: inspect the
effective builder call and preparation order.

## Protobuf fields

`InputReader.Dataset`:

| Field | Meaning |
|---|---|
| `kitti_info_path` | Info pickle for either dataset. |
| `kitti_root_path` | Root used to resolve relative point/database paths. |
| `dataset_class_name` | Registry key. |

`InputReader.Preprocess`:

| Field | Effective role |
|---|---|
| `shuffle_points` | Shuffle raw points before voxelization. |
| `max_number_of_voxels` | Per-sample voxel cap. |
| `groundtruth_localization_noise_std` | Object translation noise standard deviations. |
| `groundtruth_rotation_uniform_noise` | Object yaw noise range. |
| `global_rotation_uniform_noise` | Global yaw range. |
| `global_scaling_uniform_noise` | Global scale range. |
| `global_translate_noise_std` | Global translation standard deviations. |
| `remove_unknown_examples` | Drop difficulty `-1` entries. |
| `num_workers` | Reader workers. |
| `anchor_area_threshold` | Anchor occupancy threshold; negative disables mask generation. |
| `remove_points_after_sample` | Remove original points inside sampled boxes. |
| `groundtruth_points_drop_percentage`, `groundtruth_drop_max_keep_points` | Legacy point-drop controls passed through. |
| `remove_environment` | Keep points associated with selected classes during training. |
| `global_random_rotation_range_per_object` | Per-sampled-object rotation range. |
| `database_prep_steps` | Filters applied to DB infos. |
| `database_sampler` | DB info path, groups, rate, and per-object rotation range. |
| `use_group_id` | Apply grouped-object sampling/noise when group ids exist. |
| `min_num_of_points_in_gt` | Ignore GT boxes below this point count. |
| `random_flip_x`, `random_flip_y` | Independent flip controls, probability 0.5. |
| `sample_importance` | Importance assigned to sampled GT targets. |

The sampler message has `database_info_path`, repeated `sample_groups`,
`database_prep_steps`, `global_random_rotation_range_per_object`, and `rate`.
A group maps class name to maximum number. The two preprocessing oneofs are
`filter_by_difficulty.removed_difficulties` and
`filter_by_min_num_points.min_num_point_pairs`.

## Velocity and anchors

All standard dataset classes declare four point features. A Velo NuScenes class
appends two velocity values to each ground-truth box. If using velocity, add two
anchor `custom_values` (typically zeros) so anchor/target dimensionality becomes
9, and use a matching box coder/config. This is separate from the four point
features. A common failure is selecting `NuScenesDatasetVelo` while retaining
seven-dimensional anchors or a database made by `NuScenesDataset`.

`NuScenesDataset.NameMapping` and `DefaultAttribute` define canonical names and
submission attributes. Keep config class names exactly equal to mapped names.
For KITTI, labels use `Car`, `Pedestrian`, `Cyclist`, and other KITTI spellings;
class filtering is string-based.

## Database sampler behavior

`DataBasePreprocessor` applies configured filters in order. The default writer
stores localized object points and `group_id`; the sampler reads its pickle,
filters difficulty/minimum points, samples requested class counts at `rate`,
rotates sampled objects if configured, and can remove collisions from original
points. A missing path, missing class key, or feature-width mismatch fails at
sampler construction or sample time. Keep `database_info_path`, root, and
relative `path` fields aligned.
