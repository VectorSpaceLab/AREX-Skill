# BEVFormer nuScenes data formats

This reference covers the files and metadata that the BEVFormer dataset-preparation flow hands to the camera-only dataset classes.

## Temporal info pkl structure

The generated `nuscenes_infos_temporal_*.pkl` files are the main contract between raw nuScenes data and the BEVFormer datasets.

Typical root keys:

| Key | Meaning |
| --- | --- |
| `infos` | List of per-sample dictionaries used by the dataset classes. |
| `metadata.version` | nuScenes split identifier such as `v1.0-trainval` or `v1.0-test`. |

Typical per-sample keys written by the converter:

| Key | Meaning |
| --- | --- |
| `lidar_path` | Top LiDAR sample path used to anchor the scene and sweep chain. |
| `token` | nuScenes sample token. |
| `prev` / `next` | Temporal neighbor tokens or empty strings at scene boundaries. |
| `scene_token` | Scene token used to keep temporal queues scene-local. |
| `frame_idx` | Monotonic index within the scene. |
| `timestamp` | Sample timestamp in microseconds. |
| `sweeps` | Previous LiDAR sweep records, truncated by the chosen sweep limit. |
| `cams` | Six camera records with paths and extrinsics/intrinsics. |
| `can_bus` | Expanded CAN-bus pose vector consumed by the temporal queue logic. |
| `lidar2ego_translation` / `lidar2ego_rotation` | LiDAR-to-ego transform. |
| `ego2global_translation` / `ego2global_rotation` | Ego-to-global transform. |
| `gt_boxes` / `gt_names` / `gt_velocity` / `num_lidar_pts` / `num_radar_pts` / `valid_flag` | Training-only annotation fields. |

## Camera record fields

Each camera entry in `cams` provides the fields the dataset classes need to build image transforms:

| Key | Meaning |
| --- | --- |
| `data_path` | Image path. |
| `sensor2ego_translation` / `sensor2ego_rotation` | Camera-to-ego extrinsics. |
| `ego2global_translation` / `ego2global_rotation` | Scene pose at the sample timestamp. |
| `sensor2lidar_translation` / `sensor2lidar_rotation` | Camera-to-top-LiDAR transform derived by the converter. |
| `cam_intrinsic` | Camera intrinsics in the converter output. |

## CustomNuScenesDataset metadata keys

`CustomNuScenesDataset` is the camera-only BEVFormer dataset used by the base BEVFormer configs.

Expected keys from `get_data_info` and `union2one`:

- `sample_idx`
- `pts_filename`
- `sweeps`
- `ego2global_translation`
- `ego2global_rotation`
- `prev_idx`
- `next_idx`
- `scene_token`
- `can_bus`
- `frame_idx`
- `timestamp`
- optional camera keys when `use_camera=True`: `img_filename`, `lidar2img`, `cam_intrinsic`, `lidar2cam`
- `ann_info` in training mode
- `prev_bev_exists` inside the merged temporal metadata map

Notes:

- `use_camera=True` and `use_lidar=False` are config-level modality settings for the BEVFormer camera-only route.
- Even in camera-only mode, the raw nuScenes LiDAR folders remain required because the converter and metadata builder still read LiDAR sample data.

## CustomNuScenesDatasetV2 metadata keys

`CustomNuScenesDatasetV2` extends the temporal queue logic for BEVFormerV2.

Expected keys from `prepare_input_dict`, `get_data_info`, and `union2one`:

- `sample_idx`
- `pts_filename`
- `sweeps`
- `ego2global_translation`
- `ego2global_rotation`
- `lidar2ego_translation`
- `lidar2ego_rotation`
- `prev`
- `next`
- `scene_token`
- `frame_idx`
- `timestamp`
- optional camera keys when `use_camera=True`: `img_filename`, `lidar2img`, `cam2img`, `lidar2cam`
- `mono_input_dict` and `mono_ann_idx` when a `mono_cfg` is active during training
- `lidaradj2lidarcurr` inside the merged temporal metadata map
- `aug_param` and per-frame `timestamp` in the merged queue

Important distinctions:

- `frames` is a temporal dataset field, not a model architecture knob. The anchor frame should include `0`, and extra offsets must stay within the same scene.
- `cam2img` appears in V2 instead of the older `cam_intrinsic` key used by `CustomNuScenesDataset`.
- `mono_cfg` is only used to build the auxiliary monocular branch during training; if it is missing or malformed, the V2 dataset will not be able to populate `mono_input_dict`.

## Data-root and ann-file wiring

For both dataset classes, the config should point `data_root` at the directory that contains:

- the raw nuScenes folders
- the temporal info pkls
- the version folders that match the split used during generation

Then set `ann_file` to the exact temporal pkl for the split you want to load.

If `data_root` and `ann_file` disagree, the dataset will usually fail before any model code runs.
