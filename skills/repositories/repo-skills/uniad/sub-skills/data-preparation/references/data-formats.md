# UniAD data formats and path conventions

This reference summarizes the runtime data artifacts that UniAD expects after nuScenes preparation. It is distilled from the data converter, dataset loaders, and public config path fields; it does not require opening the original source files.

## Raw nuScenes root

Default config path: `data/nuscenes/`.

Required core items for normal train/val workflows:

```text
data/nuscenes/
├── samples/          # key-frame camera/lidar files
├── sweeps/           # historical lidar sweeps
├── v1.0-trainval/    # metadata JSON tables for train/val
├── can_bus/          # nuScenes CAN bus extension
└── maps/             # nuScenes map extension, including expansion maps
```

Additional official-layout items:

```text
data/nuscenes/
├── v1.0-test/        # test-set metadata for submission workflows
├── v1.0-mini/        # mini metadata for quick smoke tests only
└── lidarseg/         # official nuScenes item; usually not the first UniAD data dependency
```

Expected sensor folders under `samples/` commonly include `CAM_FRONT`, `CAM_FRONT_RIGHT`, `CAM_FRONT_LEFT`, `CAM_BACK`, `CAM_BACK_LEFT`, `CAM_BACK_RIGHT`, and `LIDAR_TOP`. UniAD's pipelines read multi-view camera images and top lidar paths from the temporal info PKLs.

## Temporal info PKLs

Default config paths:

```text
data/infos/nuscenes_infos_temporal_train.pkl
data/infos/nuscenes_infos_temporal_val.pkl
```

When a real test-set conversion is generated, the converter can also produce:

```text
data/infos/nuscenes_infos_temporal_test.pkl
```

Each temporal info PKL is a pickle containing a dictionary with the general form:

```python
{
    "infos": [sample_info, ...],
    "metadata": {"version": "v1.0-trainval" or "v1.0-test" or "v1.0-mini"},
}
```

Representative `sample_info` keys used by UniAD loaders include:

| Key | Purpose |
|---|---|
| `token` | nuScenes sample token |
| `lidar_path` | path to top-lidar file |
| `prev`, `next` | temporal sample links |
| `can_bus` | ego/CAN bus array used by temporal BEV logic |
| `frame_idx` | frame index within a scene |
| `sweeps` | historical lidar sweep records |
| `cams` | per-camera paths, intrinsics, and sensor-to-lidar transforms |
| `scene_token` | scene identifier for queue/reset logic |
| `lidar2ego_translation`, `lidar2ego_rotation` | lidar-to-ego transform |
| `ego2global_translation`, `ego2global_rotation` | ego-to-global transform |
| `timestamp` | nuScenes timestamp |
| `gt_boxes`, `gt_names`, `gt_velocity`, `valid_flag` | train/val 3D detection labels |
| `gt_inds`, `gt_ins_tokens` | instance identity fields used by tracking/planning logic |
| `fut_traj`, `fut_traj_valid_mask` | future trajectory arrays produced by the converter |
| `visibility_tokens` | visibility labels for annotations |

The converter also writes camera 2D annotation JSON files beside the PKLs. Their names end in `_mono3d.coco.json`; they are generated from the temporal PKLs and raw camera data.

## CAN bus extension

Default path: `data/nuscenes/can_bus/`.

The converter uses the nuScenes CAN bus API to obtain scene pose messages. The resulting `can_bus` vector is stored in each temporal info record. UniAD datasets later update the first position/quaternion/yaw entries from nuScenes ego pose data. If CAN bus messages are missing for a scene, the converter may fall back to zeros for that sample, but a missing `can_bus/` extension is still a setup problem for reliable reproduction.

## Map extension

Default path: `data/nuscenes/maps/`.

Stage-1 track/map and stage-2/E2E datasets need map records for lane and road-divider processing. The E2E dataset constructs vector and raster map labels at runtime from nuScenes map APIs. A layout that has raw sensor files and PKLs but lacks `maps/` can still fail during dataset construction or map label generation.

The four standard nuScenes map names used by UniAD are:

- `boston-seaport`
- `singapore-hollandvillage`
- `singapore-onenorth`
- `singapore-queenstown`

## Motion anchor PKL

Default stage-2/E2E path:

```text
data/others/motion_anchor_infos_mode6.pkl
```

The stage-2 motion head reads this file through its `anchor_info_path` config value. The pickle is expected to contain an `anchors_all` entry. UniAD stacks the contained anchor arrays into a tensor with group, anchor-mode, prediction-step, and xy-coordinate dimensions; the public config uses six anchors per group and motion prediction over 12 steps.

If this file is absent, stage-2/E2E model construction can fail before any dataset iteration. BEVFormer and stage-1 track/map workflows do not use this motion-anchor file directly.

## Path-root conventions inside PKLs

Info records may store paths in one of these styles:

| Stored path style | Config implication |
|---|---|
| Relative to the process working directory, e.g. `samples/CAM_FRONT/...` | A non-empty `data_root` may be appropriate if the loader joins `data_root` and the stored path. |
| Root-prefixed relative path, e.g. `data/nuscenes/samples/CAM_FRONT/...` | Avoid prepending `data_root = "data/nuscenes/"` again; set `data_root = ""` or normalize paths. |
| Absolute local path, e.g. `/datasets/nuscenes/samples/...` | Ensure the path exists on the current machine or regenerate/normalize the PKLs; `data_root` should not duplicate the absolute root. |

When a user reports `FileNotFoundError` paths containing duplicated `data/nuscenes` segments, inspect the PKL path convention and the active config's `data_root` together.

## Split and version meanings

| Version request | Converter behavior | Typical use |
|---|---|---|
| `v1.0` | Processes `v1.0-trainval` and `v1.0-test` internally | Full dataset preparation; train/val plus optional test-set artifacts |
| `v1.0-trainval` | Underlying nuScenes split used by the converter for train and val | Conceptual split name; do not pass this directly to UniAD's wrapper-style `--version` argument |
| `v1.0-test` | Underlying nuScenes test split | Submission/test workflows; no train annotations |
| `v1.0-mini` | Processes mini train/val only | Fast parser/layout smoke tests; not representative of official UniAD metrics |

The public configs default `ann_file_test` to the validation PKL. That means ordinary validation/evaluation on the provided configs does not require a test PKL unless the user changes the config for test-set submission.
