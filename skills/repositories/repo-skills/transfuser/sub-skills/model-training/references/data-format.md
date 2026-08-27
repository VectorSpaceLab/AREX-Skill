# Training Data Format

## Purpose

Use this reference to validate a TransFuser dataset before `CARLA_Data` scans it. The loader constructs samples from nested scenario/town/route directories and does not perform a friendly schema check: missing files, malformed JSON, wrong image dimensions, or an empty eligible split surface later as file, shape, or DataLoader errors.

## Directory tree

The public dataset description is abbreviated here into the loader's actual path contract:

```text
<root_dir>/
  <scenario-group>/                 # top-level directory; e.g. a scenario collection
    <town-group>/                   # directory name is used by split substring matching
      <route>/
        rgb/                       0002.png, ...
        depth/                     0002.png, ...
        semantics/                 0002.png, ...
        topdown/                   encoded_0002.png, ...
        lidar/                     0002.npy, ...
        label_raw/                 0002.json, 0003.json, ...
        measurements/              0002.json, ...
```

`GlobalConfig` lists the immediate children of `root_dir` as scenario groups, then lists each scenario group's children as town groups. `CARLA_Data` receives the resulting route directories. A flat `<root_dir>/<town>/<route>` tree does not match the `GlobalConfig` enumeration expected by this code.

The README also describes the semantic roles: RGB camera images, depth images, segmentation images, `.npy` point clouds, top-down segmentation maps, raw 3-D bounding-box labels, and measurements containing ego position, velocity, and metadata.

## Sample enumeration and frame margins

For each route, the loader computes `num_seq = len(route_dir / "lidar")` and emits current frame indices:

```text
seq = 2 ... num_seq - pred_len - seq_len - 2  (Python range upper bound exclusive)
```

With defaults `seq_len=1`, `pred_len=4`, each candidate therefore has two leading frames skipped and reserves future frames plus two trailing frames. It uses one current frame of each modality and `seq_len + pred_len` label files. Do not delete a current modality because only one of the future label files is absent; all required names must exist.

The source does not cross-check that modality directory counts match. For reliable data, make the frame stem set equal across `rgb`, `depth`, `semantics`, `topdown`, `lidar`, `measurements`, and `label_raw`, with `topdown` using the `encoded_` prefix.

## Per-modality contract

### RGB

- Loaded with OpenCV as BGR, converted to RGB, scaled by `config.scale`, then center-cropped with `crop_image_cv2`.
- Default output is channels-first `rgb` with shape `(3, 160, 704)`, normally `uint8` before the training loop casts it to CUDA `float32`.
- `config.camera_width=960`, `camera_height=480`, `camera_fov=120` describe the source camera setup; `img_resolution=(160,704)` is the network crop. With `scale=1`, the source image must be large enough for that crop.

### Depth

- Loaded as a color image and converted with `get_depth`.
- `get_depth` decodes a 24-bit packed value using weights `[65536, 256, 1]`, clips the normalized value to `[0, 0.05]`, then rescales to `[0,1]` by multiplying by 20.
- Default output is a cropped `(160,704)` float-like array. It is passed to the model as `float32` when `multitask=True`.
- Depth files are not opened when `multitask=False`, but the disk-cache path still attempts to encode depth/semantic values; avoid that combination or patch and test it first.

### Semantics

- Loaded unchanged, scaled with nearest-neighbor semantics, center-cropped, and mapped through `config.converter`.
- The converted target uses class indices `0..6`; `num_class=7`.
- The training loop calls `squeeze(1)` and sends the result as `long` to cross-entropy. With the default loader output `(H,W)` and DataLoader batch shape `(B,H,W)`, `squeeze(1)` is normally a no-op because height is 160, not a singleton. Preserve integer labels and do not apply bilinear interpolation.

### Top-down BEV

- Loaded from `topdown/encoded_%04d.png`, BGR→RGB converted, moved channel-first, decoded by `decode_pil_to_npy`, and cropped/rotated by `load_crop_bev_npy`.
- The final `bev` is an integer class map for three classes, cropped to `(160,160)` by default. The model uses a 3-class weighted cross-entropy with weights `[1,1,3]`.
- Source constants use a 256×256 BEV/LiDAR grid at 8 pixels per meter, while `load_crop_bev_npy` takes a 32-meter by 32-meter crop at 5 pixels per meter before the final class map. Preserve the implementation's conventions rather than assuming all BEV arrays have one resolution.

### LiDAR `.npy`

- Loaded with `np.load(..., allow_pickle=True)[1]` and treated as XYZI. The loader negates the second column on load to align the stored CARLA convention with the model convention.
- Voxelized/default histogram `lidar` has shape `(2,256,256)` and `float32`: one clipped occupancy histogram for points with `z>-2.3`, one for `z<=-2.3`, at 8 pixels/meter over `x∈[-16,16)` and `y∈[-32,0)`.
- If `seq_len>1` is deliberately enabled, aligned frames are concatenated in reverse temporal order into `2*lidar_seq_len` channels, but the transformer classes currently assert/use sequence length 1. Treat temporal extension as a porting task, not a supported default.
- For `geometric_fusion`, raw XYZ points are retained to build `bev_points` and `cam_points` correspondences. The correspondence tensors are model-specific and must be produced by the loader; do not fabricate them as ordinary images.

### Raw labels

Each `label_raw/%04d.json` is a list of object dictionaries. Fields consumed by the loader include:

```json
{
  "id": 17,
  "num_points": 42,
  "distance": 12.3,
  "position": [x, y, z],
  "extent": [dx, dy, dz],
  "yaw": 0.2,
  "speed": 3.1,
  "brake": 0
}
```

`ego_matrix` is also required for every object used by `get_waypoints`; it is a 4×4 transform matrix. The first object in the current label list is assumed to identify the ego vehicle (`labels[seq_len-1][0]['id']`). Ensure it exists and is consistent across the future label files.

The loader filters objects with `num_points <= 1` or centers outside the 256×256 BEV image. Remaining boxes are stored in a fixed padded target array of shape `(20,7)`, with fields `(center_x, center_y, width, height, yaw, speed, brake)` in BEV/pixel conventions. More than 20 retained objects overflows the padding and is not a supported sample.

### Measurements

The current `measurements/%04d.json` must provide at least:

- `ego_matrix` (4×4),
- `steer`, `throttle`, `brake`, `light_hazard`, `speed`, `theta`,
- `x`, `y`, `x_command`, `y_command`.

The transform fields align historical LiDAR and convert the command point into the local target-point vector. The returned training keys include:

```text
rgb, bev, depth, semantic, lidar, label, ego_waypoint,
lidar_raw, num_points, bev_points, cam_points,
target_point, target_point_image,
steer, throttle, brake, light, speed, theta, x_command, y_command
```

`depth`, `semantic` exist only for `multitask=True`; `lidar_raw`/`num_points` exist when PointPillars is enabled; `bev_points`/`cam_points` exist for `geometric_fusion`.

## Split rules and validation expectations

### `all`

Every top-level scenario group and every nested town group is scanned as training data. The config also builds `val_data` from the first enumerated top-level group, but `train.py` does not call validation for this setting. If you need an actual validation metric, use `02_05_withheld` or revise the workflow intentionally.

### `02_05_withheld`

Town matching is a substring check on nested directory names:

- any group name containing `Town02` or `Town05` is excluded from training;
- those groups are placed in validation;
- all other group names are training.

Confirm that your directory names contain exactly those case-sensitive tokens. If all groups match or none match, stop and fix the dataset/split assumption rather than interpreting an empty side.

### `eval`

`GlobalConfig(setting='eval')` leaves train and validation lists unset. This is appropriate for model-only evaluation configuration, not dataset-backed training.

## Fast safe validator

The bundled validator is intentionally conservative:

```bash
python <this-sub-skill>/scripts/validate_training_setup.py \
  --dataset-root <root_dir> \
  --setting 02_05_withheld \
  --backbone transFuser \
  --max-routes 20
```

It reports missing directories/files, split counts, route frame counts, and a bounded sample check. It does not load large arrays, decode images, mutate files, instantiate a model, or download assets. Add `--strict` in automation to return nonzero on any validation error.

## Common shape/key traps

- A `topdown/0002.png` name is wrong; the loader requests `topdown/encoded_0002.png`.
- A LiDAR file that is a plain `N×4` array is wrong for this loader unless it is wrapped so index 1 returns the expected point array.
- `label_raw` needs current plus future frames, not just one annotation file.
- `ego_matrix` is needed in labels and measurements even when only waypoint loss is desired.
- The RGB crop and LiDAR histogram are channels-first. Do not pass HWC arrays into the training model.
- Geometric fusion needs the loader-generated projected correspondence tensors; PointPillars needs fixed `(max_lidar_points,4)` raw arrays plus the actual `num_points` count.
