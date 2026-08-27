# Data formats and layout contracts

This reference distills the repository's README, NUSCENES-GUIDE, dataset
readers, info builders, and protobuf declarations. Source code is the authority
when prose and implementation differ.

## KITTI tree

The preparation code expects a root with both splits. It uses the fixed image
id lists bundled with the data package (`train.txt`, `val.txt`, and `test.txt`)
and therefore does not discover arbitrary filenames by itself.

| Path relative to `<KITTI_ROOT>` | Required for | Format/role | Validation notes |
|---|---|---|---|
| `training/image_2/<id>.png` | train/val info generation | Camera image; shape is stored in info | IDs are six-digit names such as `000000.png`; source reads image shape. |
| `training/calib/<id>.txt` | train/val/reduced clouds | KITTI calibration text | The reader consumes P0–P3 (3x4), R0_rect (3x3), and Tr_velo_to_cam/Tr_imu_to_velo (3x4); malformed or missing lines fail generation. |
| `training/velodyne/<id>.bin` | train/val/reduced clouds | little-endian float32 rows `[x,y,z,reflectivity]` | The source reshapes to `[-1, 4]`; byte length must be divisible by 16. |
| `training/label_2/<id>.txt` | train/val info generation | KITTI camera annotations | Testing has no labels in the normal layout. `DontCare` is retained in infos then removed for model targets. |
| `training/velodyne_reduced/<id>.bin` | normal runtime after reduction | camera-frustum-filtered float32 rows `[x,y,z,reflectivity]` | The reader prefers this path when it exists. An empty directory is a valid pre-generation state. |
| `testing/image_2/<id>.png` | test info generation | Camera image | Needed because the info builder reads image shape even for test infos. |
| `testing/calib/<id>.txt` | test info/reduction | KITTI calibration text | Required by the source info builder. |
| `testing/velodyne/<id>.bin` | test info/reduction | float32 `[x,y,z,reflectivity]` | Must match image/calibration stems. |
| `testing/velodyne_reduced/<id>.bin` | normal test runtime after reduction | Reduced float32 cloud | Empty directory is accepted before generation. |

The validator intentionally checks a flexible, nonempty subset rather than
hard-coding the canonical 7,481/7,518 counts. The historical directory checker
used fixed counts, but a small or custom split can be prepared if the image-set
IDs and all referenced files agree. For training, image, calibration, lidar,
and label stems must agree. For testing, image, calibration, and lidar stems
must agree.

## KITTI info schema

`kitti_infos_train.pkl`, `kitti_infos_val.pkl`, `kitti_infos_trainval.pkl`, and
`kitti_infos_test.pkl` are lists of dictionaries. A normal entry contains:

```text
image:
  image_idx: integer
  image_path: relative or absolute image path
  image_shape: [height, width]
point_cloud:
  num_features: 4
  velodyne_path: relative or absolute lidar path
calib:
  P0, P1, P2, P3: 4x4 (or source-compatible 3x4) camera matrices
  R0_rect: 4x4 (or source-compatible 3x3) rectification matrix
  Tr_velo_to_cam: 4x4 (or source-compatible 3x4) transform
  Tr_imu_to_velo: 4x4 (or source-compatible 3x4) transform
annos:  # omitted for test infos
  name: [N] strings
  bbox: [N, 4]
  location: [N, 3] camera coordinates
  dimensions: [N, 3] camera [l, h, w]
  rotation_y: [N]
  difficulty: [N] (added by the reader)
  num_points_in_gt: [N] (computed for training/validation infos)
```

The builder uses relative paths by default. The runtime joins relative paths
to the configured root. Do not move the root or generated database without
updating the config and relative database paths.

## NuScenes tree and metadata

For a prepared NuScenes root, the expected shape is:

| Path | Role |
|---|---|
| `samples/` | Key-frame sensor files; the source also expects the front-camera path to exist in generated infos. |
| `sweeps/` | Historical lidar frames used to build a multi-sweep sample. The code asserts key-frame availability and reads up to `max_sweeps` previous frames. |
| `maps/` | Dataset payload directory retained by the published layout; it is not used by the lidar preparation path. |
| `v1.0-trainval/` | NuScenes train/validation JSON tables. |
| `v1.0-test/` | NuScenes test JSON tables. |
| `v1.0-mini/` | Mini metadata/data version if using the mini split. |

The exact metadata tables are owned by the installed NuScenes devkit. At
minimum, the requested version directory must exist and be readable by
`NuScenes(version=<VERSION>, dataroot=<ROOT>)`; a directory with only
`samples/` and `sweeps/` is not a prepared root. Validate the version before
running the writer. Supported versions in the source are exactly
`v1.0-trainval`, `v1.0-test`, and `v1.0-mini`.

## NuScenes info schema and class choice

The generator writes:

- `infos_train.pkl` and `infos_val.pkl` for `v1.0-trainval` or `v1.0-mini`;
- `infos_test.pkl` for `v1.0-test`.

Each file is a dictionary with `metadata.version` and an `infos` list. An info
entry carries `lidar_path`, `cam_front_path`, `token`, `sweeps`, lidar-to-ego
and ego-to-global transforms, and `timestamp`. Train/mini entries also carry
`gt_boxes`, `gt_names`, `gt_velocity`, `num_lidar_pts`, and `num_radar_pts`.

NuScenes raw lidar rows are five float32 values. The reader scales intensity by
`1/255`, replaces the key-frame time channel with zero, transforms each sweep
into the key lidar frame, and returns four features `[x, y, z, time_delta]`.
`NumPointFeatures` is therefore 4 in all built-in NuScenes classes.

The generated base box is `[x, y, z, w, l, h, yaw]` in the lidar frame. The
source changes the NuScenes yaw to SECOND's convention with `-yaw - pi/2`.
`NuScenesDatasetVelo` and `NuScenesDatasetD2Velo` append two lidar-frame
velocity components, producing nine-dimensional ground-truth boxes while point
features remain four. Missing/NaN velocities are replaced by zero when read.
Do not mix a Velo class with a non-velocity database/config or vice versa.

The source maps NuScenes names as follows: `vehicle.car`→`car`, both bus forms
→`bus`, `vehicle.truck`→`truck`, `vehicle.trailer`→`trailer`,
`vehicle.bicycle`→`bicycle`, `vehicle.motorcycle`→`motorcycle`, pedestrian
variants→`pedestrian`, `movable_object.barrier`→`barrier`, and
`movable_object.trafficcone`→`traffic_cone`.

## Ground-truth database schema

The writer creates `<ROOT>/gt_database/` and a pickle, normally
`<ROOT>/kitti_dbinfos_train.pkl`. For each annotated object it writes a binary
file named `<image-or-index>_<class>_<object-index>.bin`; the points are copied
from the object and translated so the object's box center is the origin. The
pickle is a dictionary keyed by class name. Each entry includes:

```text
name, path, image_idx, gt_idx, box3d_lidar, num_points_in_gt,
difficulty, group_id
```

`path` is normally relative, for example `gt_database/000123_Car_0.bin`.
`database_info_path` must point to this pickle and `root_path` must resolve its
relative paths. The default writer name is historical and is also used for
NuScenes; do not rename it in config without updating the sampler path.
