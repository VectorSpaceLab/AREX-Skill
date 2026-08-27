# MapTR data and vector formats

## nuScenes temporal info files

The modified nuScenes converter writes a dictionary with `infos` and `metadata`.
The names used by MapTR are:

```text
nuscenes_infos_temporal_train.pkl
nuscenes_infos_temporal_val.pkl
nuscenes_infos_temporal_test.pkl
```

Each `infos` record is expected to provide at least:

- `token`, `timestamp`, `scene_token`, `frame_idx`, `prev`, and `next`;
- `lidar_path`, `sweeps`, and lidar-to-ego translation/rotation;
- ego-to-global translation/rotation and `can_bus`;
- `map_location` matching one of `boston-seaport`,
  `singapore-hollandvillage`, `singapore-onenorth`, or
  `singapore-queenstown`;
- `cams`, when the camera modality is enabled. Each camera record supplies a
  data path, sensor-to-lidar transforms, sensor-to-ego transforms, and
  `cam_intrinsic`.

`ann_file` points at one of these pkl files. `data_root` is the directory used
by the custom dataset and the vectorizer to find the raw `maps/` expansion.
Keep pkl and raw paths consistent: a pkl generated against one raw root can
contain paths that are not valid under another root.

The conversion command's `--out-dir` controls pkl placement; the documented
MapTR command uses the same directory as `--root-path`. `map_ann_file` is a
separate JSON path, normally `nuscenes_map_anns_val.json`, created when map
ground truth or prediction formatting is requested. It is not the converter's
input and it does not replace `maps/`.

## Argoverse2 converter pkl

The AV2 converter writes a dictionary:

```python
{
    "samples": [
        {
            "sample_idx": 0,
            "e2g_translation": ...,       # city-frame pose translation
            "e2g_rotation": ...,           # rotation matrix/object
            "cams": {
                "ring_front_center": {
                    "img_fpath": "...",
                    "intrinsics": ..., "extrinsics": ...
                },
                # six other configured ring cameras
            },
            "lidar_fpath": "...",
            "timestamp": "...",
            "log_id": "...",
            "token": "<log-id>_<timestamp>"
        }
    ],
    "id2map": {
        "<log-id>": {
            "divider": [array-like polylines],
            "ped_crossing": [array-like polygon coordinates],
            "boundary": [array-like polygon coordinates]
        }
    }
}
```

The exact serialized numpy/AV2 object types are produced by the converter;
do not hand-author a production pkl with JSON-like substitutes. The checker
only verifies the expected filename and does not deserialize pkl files. The
custom loader sorts `samples` by `timestamp`, stores `id2map`, and looks up
`id2map[log_id]` for vectorization.

The AV2 raw root is the directory containing `train`, `val`, and `test`; the
converter receives that root, not a single split. For each log it searches
`<split>/<log-id>/map/log_map_archive_*.json` and requires exactly one match.
A malformed or duplicate archive is a stop condition, not a recoverable
sample skip.

## Map classes and labels

The standard MapTR map config uses this ordered class list:

| class | label | source geometry | local representation |
|---|---:|---|---|
| `divider` | 0 | nuScenes road/lane divider; AV2 lane boundary marks | open `LineString` instances |
| `ped_crossing` | 1 | pedestrian-crossing polygons | polygon exterior/interior lines |
| `boundary` | 2 | nuScenes road/lane contours; AV2 drivable areas | polygon boundary lines |

nuScenes `VectorizedLocalMap.CLASS2LABEL` additionally knows source layer
names `road_divider` and `lane_divider` as label 0, `contours` as label 2,
and `others` as -1. AV2 maps source divider, crossing, and boundary directly.
Unknown configured `vec_class` values raise an error in both vectorizers.

The vectorizer clips geometries to a local patch derived from `pc_range`,
rotates/transforms them into local lidar/ego coordinates, and creates a
`LiDARInstanceLines` object. A configured positive `fixed_ptsnum_per_line`
causes `fixed_num_sampled_points` to produce a float32 tensor shaped
`[N, fixed_num, 2]`; the standard configs set `fixed_num=20`. For each line,
points are interpolated from distance 0 to line length and x/y are clamped to
half patch width/height. The first and last point of a closed line are equal.

Shift targets have an additional shift dimension. Depending on the selected
implementation pattern, a closed polygon may expose cyclic shifts and an open
line forward/reverse shifts. Non-applicable shifts are filled with
`padding_value=-10000`. `gt_vecs_label` is a tensor/list of integer class
labels aligned one-to-one with vector instances. A vector count of zero is
valid; an empty result must not be replaced with a fake class or point.

## Config consistency checks

For the common nuScenes config:

```text
point_cloud_range = [-15, -30, -2, 15, 30, 2]
patch height = 60  (y max - y min)
patch width  = 30  (x max - x min)
map classes  = divider, ped_crossing, boundary
GT points    = 20
pred points  = 20
```

The AV2 config uses `[-30, -15, -2, 30, 15, 2]`, so its planar patch is
height 30 and width 60. A config change must keep model, coder, assigner, and
dataset `pc_range`/point counts coherent; the layout checker cannot verify
that. Route that decision to the model-configuration sibling skill.

## Minimal schema checklist

Before handing off a generated file, assert:

1. filename split and dataset agree;
2. pkl is at the configured `data_root` and readable by the configured
   `ann_file` path;
3. nuScenes temporal records include map location and temporal links;
4. AV2 pkl has top-level `samples` and `id2map`, every sample log id has a map
   entry, and each map entry has all three class keys;
5. every vector has numeric coordinate pairs, at least two points for an open
   line, and a closed polygon for a boundary/crossing source;
6. labels use exactly 0/1/2 for the three configured classes;
7. fixed-point count and padding value match the chosen config.

Only items 1–2 are intentionally automated by the bundled filesystem checker;
the remaining items require a dependency-aware, read-only pkl/schema inspection
that is not bundled because it would import legacy libraries and deserialize
user data.