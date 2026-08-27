# Configuration guide

This reference is a static editing guide for the release's Python/MMCV
configuration system. It records observed keys and relationships, not a
promise that every optional combination is runnable.

## 1. Inheritance and `mmcv.Config`

A MapTR config normally starts with:

```python
_base_ = [
    '../datasets/custom_nus-3d.py',
    '../_base_/default_runtime.py'
]
plugin = True
plugin_dir = 'projects/mmdet3d_plugin/'
```

`Config.fromfile(path)` loads the Python config, resolves `_base_` files, and
merges dictionaries in the MMCV 1.x style. Names such as `_dim_`,
`num_map_classes`, and `point_cloud_range` are ordinary Python variables while
the file is evaluated; they are not registry entries. A child dictionary can
override a nested base value, but a list is not a safe place to expect a
semantic merge. Inspect the fully resolved config before editing an inherited
pipeline or dataset.

The training and test entry points then apply optional `--cfg-options`
overrides. Those overrides are useful for a temporary experiment, but they do
not update the checked-in relationships. Make durable architecture changes in
the copied config and rerun the static checker.

The checker in this skill uses `mmcv.Config` when installed. If MMCV is absent,
it uses a conservative AST fallback that checks assignments and syntax but may
not resolve `_base_` inheritance or dynamic expressions. It never imports
plugin modules, builds a detector, opens a dataset, or executes a forward pass.

## 2. Family map

| Config family | Dataset intent | Encoder signature | Distinguishing values |
|---|---|---|---|
| `maptr_tiny_r50_24e` | nuScenes local map | `BEVFormerEncoder` → `GeometrySptialCrossAttention` → `GeometryKernelAttention` | R50, BEV 200×100, queue 1, 900 queries, 50 vectors, 20 points. |
| `maptr_tiny_r50_110e` | nuScenes local map | same GKT path | R50 and same common geometry, 110 epochs. |
| `maptr_nano_r18_110e` | nuScenes local map | same GKT path | R18, BEV 80×40, 100 vectors, two decoder layers, `im2col_step=192`. |
| `maptr_tiny_r50_24e_bevformer` | nuScenes local map | `BEVFormerEncoder` → `SpatialCrossAttention` → `MSDeformableAttention3D` | No `GeometryKernelAttention`; camera calibration remains required. |
| `maptr_tiny_r50_24e_bevpool` | nuScenes local map | `LSSTransform` → `mmdet3d.ops.bev_pool` | `pc_range` z −10…10, voxel z 20, `dbound=[1,35,0.5]`. |
| `maptr_tiny_fusion_24e` | nuScenes camera + LiDAR | GKT plus `lidar_encoder` and `ConvFuser` | `model.modality='fusion'`, point loaders, sparse encoder, fuser channels. |
| `maptr_tiny_r50_av2_24e` | Argoverse2 | GKT camera path | AV2 dataset class, seven-camera transformer setting, BEV 100×200. |
| `*_t4` | same dataset as stem | GKT or BEVFormer as named | Reduced `im2col_step`/memory settings; retain the stem's encoder. |

The common GKT R50 camera baseline has:

```text
point_cloud_range = [-15, -30, -2, 15, 30, 2]
voxel_size        = [0.15, 0.15, 4]
map_classes       = ['divider', 'ped_crossing', 'boundary']
bev_h, bev_w      = 200, 100
num_query         = 900  # num_vec * num_pts_per_vec = 50 * 20
num_vec           = 50
num_pts_per_*     = 20
embed_dims        = 256
queue_length      = 1
```

The AV2 and nano values are intentionally different. Select a family first;
then change values by contract rather than copying this baseline.

## 3. Required top-level sections

A normal MapTR config has these sections or inherited equivalents:

- `plugin=True` and a valid `plugin_dir` for registry population.
- `point_cloud_range`, `voxel_size`, `map_classes`, `num_map_classes`, and
  `input_modality`.
- `model.type='MapTR'` with `img_backbone`, `img_neck`, and
  `pts_bbox_head.type='MapTRHead'`.
- A head `transformer`, `bbox_coder`, positional encoding, classification and
  point losses, and `num_classes`.
- `train_cfg.pts.assigner` with the same geometric range.
- `data.train`, `data.val`, and `data.test` with local map dataset settings,
  map classes, BEV size, point range, fixed point count, and pipelines.

Some of these may be inherited. The checker reports unresolved inherited
values in fallback mode rather than inventing defaults.

## 4. Coordinated geometry edits

### Point range

The six values are `[xmin, ymin, zmin, xmax, ymax, zmax]`. The MapTR head
normalizes x/y point and box targets using x/y extents; z is relevant to
projection, voxel/LSS bounds, and LiDAR filtering. After changing it, update
all of the following:

```text
point_cloud_range                       # canonical variable
model.pts_bbox_head.bbox_coder.pc_range
model.pts_bbox_head.transformer.encoder.pc_range
model.pts_bbox_head.train_cfg?          # usually train_cfg is outside head
train_cfg.pts.point_cloud_range
train_cfg.pts.assigner.pc_range
bbox coder post_center_range            # review explicitly
all data.*.pc_range
ObjectRangeFilter.point_cloud_range     # every affected pipeline step
CustomPointsRangeFilter.point_cloud_range for fusion
```

In the observed MapTR files, `train_cfg=dict(pts=...)` is nested inside the
`model` dictionary, so the resolved path is `cfg.model.train_cfg.pts` (the
launcher still separately accepts a top-level `train_cfg` if a different config
uses one). A checker warning about one stale range is actionable.
`post_center_range` is a list of four xy boxes in the common config, not a
copy of the six-number `pc_range`; choose it deliberately.

### Voxel and BEV dimensions

For a BEVFormer/GKT camera model, `bev_h` and `bev_w` feed the learned BEV
embedding, positional encoding (`row_num_embed` and `col_num_embed`), dataset
`bev_size`, grid length, and transformer spatial shapes. The head's learned
embedding exists only when the encoder type is `BEVFormerEncoder`.

For fusion, the LiDAR voxel layer additionally uses `lidar_point_cloud_range`,
`voxel_size`, `max_voxels`, and sparse encoder shape. `voxel_size` in the
baseline is `[0.1,0.1,0.2]` for LiDAR, while the map BEV range uses a separate
camera range. Do not replace one with the other.

For LSS/BEV pool, `LSSTransform` derives x/y/z bounds from `pc_range` and
`voxel_size`. `dbound=[d_min,d_max,d_step]` controls depth bins and must have a
positive, coherent step. The code asserts a single feature level and expects
camera calibration fields in each image meta.

### Classes and fixed points

The release's map labels are `divider`, `ped_crossing`, and `boundary`.
`num_map_classes` is the length of `map_classes`; the head, coder, and dataset
split configs must agree. `num_pts_per_vec` sets predicted point count and
`num_pts_per_gt_vec` sets GT count. `MapTRAssigner` interpolates predictions to
the GT count before point matching, but the dataset's fixed-point annotation
format still must be intentional.

## 5. Input and pipeline contracts

Camera-only pipelines collect `img` and include image loading, normalization,
scaling, padding, formatting, and annotation loading in training. Evaluation
usually collects only `img`. The local-map dataset receives `bev_size`,
`pc_range`, `fixed_ptsnum_per_line`, `map_classes`, `queue_length`, and
`modality`.

Fusion pipelines additionally load points, load sweeps, filter by
`lidar_point_cloud_range`, and collect `points`. The model sets
`model.modality='fusion'`, owns `lidar_encoder`, and creates a `ConvFuser` with
input channels matching camera and LiDAR BEV features. Leaving `use_lidar=False`
or omitting `points` while retaining `modality='fusion'` is a hard mismatch.

LSS/BEV pool evaluation/training image metadata must contain the calibration
arrays consumed by `BaseTransform`: camera/ego transforms, intrinsics,
augmentation matrices, LiDAR/ego transforms, and a usable `img_shape`. These
are data-preparation/runtime inputs, not values to fabricate in a model config.

Temporal configs use nested image queues. `MapTR.forward_train` takes the last
frame as current input and obtains history BEV only when the queue length is
greater than one. A queue setting alone does not enable temporal inference;
`video_test_mode` controls whether previous BEV is retained at test time.

## 6. Safe editing recipes

### Change map extent

1. Copy the selected config.
2. Change the canonical range and voxel values, if needed.
3. Search the resolved config for every `pc_range` and range-filter value.
4. Update BEV dimensions if the physical cell size should stay constant.
5. Recheck the coder's `post_center_range` and assigner range.
6. Run the checker and stop on any stale-range diagnostic.

### Change classes

Update `map_classes`, the derived class count, head/coder class count, and all
three dataset splits. Do not substitute the 10 object `class_names` list for
map classes; the former belongs to the inherited 3-D dataset interface.

### Choose an encoder

- Choose GKT only when its custom extension can be built and tested for the
  exact environment. Keep the attention dict nested under
  `GeometrySptialCrossAttention` and retain `kernel_size`, `num_heads`, and
  `num_levels`.
- Choose BEVFormer when the desired path is MMCV 3-D deformable attention.
  Replace the cross-attention structure as a unit; do not just rename the
  attention type.
- Choose BEV pool when camera calibration and `dbound` are available. Keep a
  single feature level and its LSS-specific voxel geometry.
- Choose fusion only with a LiDAR data contract and sparse backend plan.

## 7. Checker examples

From a runtime package root, a normal static check is:

```bash
python <skill-root>/sub-skills/model-configuration/scripts/check_maptr_config.py \
  projects/configs/maptr/maptr_tiny_r50_24e.py
```

Expected healthy shape (exact wording can vary):

```text
parser: mmcv.Config
family: GKT camera / BEVFormerEncoder
plugin: enabled; plugin_dir: ... (exists)
geometry: range=[-15.0, -30.0, -2.0, 15.0, 30.0, 2.0], bev=200x100, classes=3, points=20
PASS: required MapTR configuration checks
WARN: GKT extension import/CUDA ABI was not tested
```

A config with a changed canonical range but an old coder/assigner range should
exit non-zero and identify the inconsistent paths. A BEV pool config retaining
`modality='fusion'` or a fusion config lacking `lidar_encoder` should also
exit non-zero.
