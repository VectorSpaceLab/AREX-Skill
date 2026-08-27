# Model and configuration API reference

This reference records signatures and roles observed in the targeted MapTR
release. It is intended for config reasoning and diagnostics, not as a stable
public Python API guarantee.

## Registry and plugin surface

With `plugin=True`, the launcher imports the package derived from `plugin_dir`.
The package initializer imports MapTR datasets, pipelines, BEVFormer modules,
and MapTR modules. Those imports register objects into MMDetection/MMCV
registries. Typical registry names used by configs include:

| Registry type | Config name | Role |
|---|---|---|
| detector | `MapTR` | Camera feature extraction, optional LiDAR voxelization, temporal BEV state, train/test dispatch. |
| head | `MapTRHead` | Structured vector queries, transformer invocation, classification/point outputs and losses. |
| transformer | `MapTRPerceptionTransformer` | BEV encoding, optional fusion, point-query decoding. |
| transformer sequence | `MapTRDecoder` | Iterative decoder and reference-point refinement. |
| transformer sequence | `LSSTransform` | Lift-splat depth projection and BEV pooling. |
| attention | `GeometrySptialCrossAttention` | Camera-visible BEV query rebatching and camera aggregation. The spelling `Sptial` is the registered release spelling. |
| attention | `GeometryKernelAttention` | Fixed geometry-kernel sampling backed by a custom CUDA extension. |
| assigner | `MapTRAssigner` | Hungarian matching over class, box, IoU, and ordered point costs. |
| loss | `PtsL1Loss`, `PtsDirCosLoss`, `OrderedPtsL1Loss` | Point regression, direction consistency, and ordered point loss. |
| fuser | `ConvFuser` | Concatenation, convolution, batch normalization, and activation for camera/LiDAR BEV. |

A registry `KeyError` normally means the plugin was not imported, the expected
module import failed before registration, or the config type belongs to a
different code/version family. Do not respond by changing `type` to an
unrelated registered class.

## `MapTR`

Observed constructor shape:

```python
MapTR(
    use_grid_mask=False,
    pts_voxel_layer=None,
    pts_voxel_encoder=None,
    pts_middle_encoder=None,
    pts_fusion_layer=None,
    img_backbone=None,
    pts_backbone=None,
    img_neck=None,
    pts_neck=None,
    pts_bbox_head=None,
    img_roi_head=None,
    img_rpn_head=None,
    train_cfg=None,
    test_cfg=None,
    pretrained=None,
    video_test_mode=False,
    modality='vision',
    lidar_encoder=None,
)
```

Key behavior:

- Inherits `MVXTwoStageDetector` and builds the image backbone/neck/head through
  the parent detector.
- Applies grid mask only when configured.
- For `modality='fusion'`, builds either hard `Voxelization` or
  `DynamicScatter` plus a middle encoder from `lidar_encoder`.
- `forward_train` expects queued images, uses the last frame as current, and
  computes history BEV only when queue length exceeds one.
- `forward_test` resets previous BEV on scene changes and when
  `video_test_mode=False`.
- Fusion calls `extract_lidar_feat(points)`; points cannot be omitted merely
  because the image path is valid.

## `MapTRHead`

Relevant constructor parameters after `*args`:

```python
MapTRHead(
    with_box_refine=False,
    as_two_stage=False,
    transformer=None,
    bbox_coder=None,
    num_cls_fcs=2,
    code_weights=None,
    bev_h=30,
    bev_w=30,
    num_vec=20,
    num_pts_per_vec=2,
    num_pts_per_gt_vec=2,
    query_embed_type='all_pts',
    transform_method='minmax',
    gt_shift_pts_pattern='v0',
    dir_interval=1,
    loss_pts=...,
    loss_dir=...,
    **kwargs,
)
```

Important invariants:

- The effective query count is recomputed as
  `num_vec * num_pts_per_vec`; a separately supplied `num_query` does not
  override that internal relationship.
- `query_embed_type='instance_pts'` creates one embedding per vector and one
  per point, then adds and flattens them.
- A learned BEV embedding is created only if
  `transformer.encoder.type == 'BEVFormerEncoder'`; LSS receives no learned
  BEV queries.
- `bbox_coder.pc_range` becomes the head's normalization range and defines
  `real_w` and `real_h`.
- `transform_method='minmax'` turns each predicted point set into an envelope
  box. Other methods are not implemented in this release.
- `forward(mlvl_feats, lidar_feat, img_metas, prev_bev=None, only_bev=False)`
  expects each image feature level in `[B,N,C,H,W]` layout.
- Classification is per vector (point features are averaged); point regression
  is per structured point query.

The common config sets zero weight for box and IoU regression losses and a
weight of five for point L1 loss. Assignment nevertheless contains class,
box, IoU, and ordered point cost entries; the configured zero weights make the
corresponding terms inert.

## `MapTRPerceptionTransformer`

Observed constructor parameters:

```python
MapTRPerceptionTransformer(
    num_feature_levels=4,
    num_cams=6,
    two_stage_num_proposals=300,
    fuser=None,
    encoder=None,
    decoder=None,
    embed_dims=256,
    rotate_prev_bev=True,
    use_shift=True,
    use_can_bus=True,
    len_can_bus=18,
    can_bus_norm=True,
    use_cams_embeds=True,
    rotate_center=[100, 100],
    modality='vision',
    **kwargs,
)
```

The constructor treats `encoder['type'] == 'BEVFormerEncoder'` as the switch
for attention BEV encoding. Any other encoder follows `lss_bev_encode`, so an
unknown type is not a harmless variant. Fusion builds `fuser` only when
`modality='fusion'`.

`get_bev_features(...)` chooses attention or LSS, then interpolates and fuses a
non-null LiDAR feature. `forward(...)` creates 2-D reference points, decodes
structured object queries against one BEV feature level, and returns BEV
features, decoder states, and initial/intermediate references.

CAN bus length is explicit. The temporal `*_t4` configs use a shorter length
than the common default; changing `len_can_bus` requires image metadata with at
least that many fields and semantics matching the transformer's slicing.

## `MapTRDecoder`

Observed call shape:

```python
MapTRDecoder.forward(
    query,
    *args,
    reference_points=None,
    reg_branches=None,
    key_padding_mask=None,
    **kwargs,
)
```

Each layer receives normalized 2-D reference points. If regression branches are
provided, each layer adds a predicted offset in inverse-sigmoid space, applies
sigmoid, and detaches the new reference for the next layer. With
`return_intermediate=True`, it stacks per-layer outputs and references.

## Assigner and point losses

Observed assigner constructor:

```python
MapTRAssigner(
    cls_cost={'type': 'ClassificationCost', 'weight': 1.0},
    reg_cost={'type': 'BBoxL1Cost', 'weight': 1.0},
    iou_cost={'type': 'IoUCost', 'weight': 0.0},
    pts_cost={...},
    pc_range=None,
)
```

`assign(bbox_pred, cls_pred, pts_pred, gt_bboxes, gt_labels, gt_pts,
gt_bboxes_ignore=None, eps=1e-7)` normalizes GT boxes and points using
`pc_range`, interpolates predicted point sequences when counts differ, selects
the lowest cost among equivalent GT point orders, and runs SciPy's Hungarian
assignment on CPU. It supports only `gt_bboxes_ignore=None` and 4-D predicted
boxes.

`PtsL1Loss` requires prediction/target shapes to match.
`PtsDirCosLoss` computes cosine embedding loss over direction segments.
`OrderedPtsL1Loss` and `OrderedPtsSmoothL1Loss` compare against all permitted
orders and use a custom reduction requiring `avg_factor` for mean reduction.

## Geometry attention path

`GeometrySptialCrossAttention` constructor parameters include `embed_dims`,
`num_cams`, `pc_range`, `dropout`, `batch_first`, and a nested `attention`
config. It determines which BEV queries are visible in each camera, rebatches
queries/reference points, calls the nested attention, then averages camera
contributions and applies an output projection.

`GeometryKernelAttention` constructor parameters include:

```python
GeometryKernelAttention(
    embed_dims=256,
    num_heads=8,
    num_levels=4,
    num_points=4,       # overwritten by kernel_size area
    kernel_size=(3, 3),
    dilation=1,
    im2col_step=64,
    dropout=0.1,
    batch_first=True,
    norm_cfg=None,
    init_cfg=None,
)
```

`embed_dims` must be divisible by `num_heads`; power-of-two channels per head
are recommended by the implementation. The effective point count is
`kernel_size[0] * kernel_size[1]`. Reference points must end in 2-D coordinates;
the 4-D path asserts false. The forward path calls
`GeometricKernelAttentionFunc.apply`; the Python fallback present as a method
is not selected by the active forward path.

## BEV pool / LSS path

`LSSTransform` accepts `in_channels`, `out_channels`, `feat_down_sample`,
`pc_range`, `voxel_size`, `dbound`, and optional `downsample`. `BaseTransform`
derives grid step/offset/size, creates a depth frustum from image shape, uses
camera calibration transforms to project into the LiDAR frame, filters points
to configured bounds, and calls `mmdet3d.ops.bev_pool`.

The active code requires one image feature level. `feat_down_sample` must agree
with actual image and feature heights. A downsample value greater than one is
accepted only when it equals two.

## Configuration-only confidence boundary

All signatures above were checked against source for the targeted release.
They do not prove registry import, a successful extension build, compatible
binary ops, dataset metadata, or an end-to-end forward. The bundled checker
intentionally stops before those operations.
