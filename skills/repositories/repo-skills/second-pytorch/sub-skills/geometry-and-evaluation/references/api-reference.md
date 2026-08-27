# Geometry and assignment API reference

Read this for source-faithful signatures and shapes. The generated route is
self-contained; these are distilled contracts, not instructions to reopen the
source checkout.

## Box arrays and corners

The primary internal lidar representation is `[N, 7]` or `[N, 7+C]`:
`[x, y, z, w, l, h, rz, custom...]`. `center_to_corner_box3d(centers,
dims, angles=None, origin=(0.5,0.5,0.5), axis=2)` accepts `centers [N,3]`,
`dims [N,3]`, and `angles [N]`, returning `[N,8,3]`. For camera KITTI geometry,
the source contract uses `dims=[l,h,w]`, `origin=[0.5,1.0,0.5]`, and `axis=1`.
For internal lidar center boxes use dimensions `[w,l,h]`, `origin=[0.5,0.5,0.5]`,
and `axis=2`.

- `corners_nd(dims, origin=0.5)` returns `[N, 2**ndim, ndim]`; 2-D corners
  are reordered clockwise and 3-D corners use the source's fixed eight-corner
  ordering.
- `center_to_corner_box2d(centers, dims, angles=None, origin=0.5)` maps
  `[N,2] + [N,2] + [N]` to `[N,4,2]`. Positive angles follow the source's
  2-D rotation convention; do not mix it with an external clockwise convention.
- `rbbox3d_to_corners(rbboxes, origin=[0.5,0.5,0.5], axis=2)` slices the first
  seven columns and returns `[N,8,3]`.
- `rbbox3d_to_bev_corners(rbboxes, origin=0.5)` uses `[x,y,w,l,rz]` and returns
  `[N,4,2]`.
- `corner_to_standup_nd(boxes_corner)` requires a 3-D array `[N,K,D]` and
  returns `[N,2D]` as min coordinates followed by max coordinates.
- `corner_to_surfaces_3d(corners)` maps `[N,8,3]` to `[N,6,4,3]`; the surface
  winding is significant because point-in-convex-polygon expects inward normals.

`points_in_rbbox(points, rbbox, z_axis=2, origin=(0.5,0.5,0.5))` returns a
boolean `[num_points,num_boxes]` matrix. `points_count_rbbox` returns
`[num_boxes]`. The underlying 3-D convex-polygon functions likewise accept
points `[P,3]`, surfaces `[B,6,4,3]`, and return `[P,B]`; all surface normals
must point inward. `points_in_convex_polygon(points, polygon, clockwise=True)`
accepts points `[P,2]` and polygons `[B,K,2]`, returning `[P,B]`.

Preprocessing helpers use the same geometry contracts. `assign_label_to_voxel`
takes `gt_boxes [G,7]`, voxel coordinates `[V,3]` in zyx order, `voxel_size [3]`
xyz, and `coors_range [6]` xyzxyz; it returns integer `[V]` labels based on
voxel-center inclusion. `assign_label_to_voxel_v3` tests voxel corners and also
returns `[V]`. `get_anchor_bv_in_feature(anchors_bv, voxel_size, coors_range,
grid_size)` maps BEV `[N,4]` minmax coordinates to clipped integer feature
coordinates `[N,4]`; it mutates the passed array's y coordinates, so pass a copy
when retaining physical coordinates. `image_box_region_area(img_cumsum,bbox)`
uses `[M,H,W]` cumulative maps and integer `[N,4]` xyxy boxes, returning `[N,M]`.

## Encoding and decoding

`second_box_encode(boxes, anchors, encode_angle_to_vector=False,
smooth_dim=False, cylindrical=False)` accepts paired arrays `[N,7+C]` and
`[N,7+C]`. The regular output is `[N,7+C]`, ordered
`[xt,yt,zt,wt,lt,ht,rt,custom...]`; with `encode_angle_to_vector=True` it is
`[N,8+C]` and replaces `rt` by `[rtx,rty]`. The implementation uses
`d=sqrt(la**2+wa**2)`, `xt=(xg-xa)/d`, `yt=(yg-ya)/d`, `zt=(zg-za)/ha`,
log dimension ratios unless `smooth_dim=True`, and angle residual `rg-ra`.
The `cylindrical` parameter exists in the NumPy signature but is not used in
its arithmetic.

`second_box_decode(box_encodings, anchors, encode_angle_to_vector=False,
smooth_dim=False)` reverses the same contract and returns `[N,7+C]`. Vector-angle
decoding adds the anchor cosine/sine pair and uses `arctan2`; compare angles
modulo a period rather than requiring equal representatives.

`bev_box_encode(boxes, anchors, encode_angle_to_vector=False,
smooth_dim=False)` takes five-column BEV boxes/anchors `[x,y,w,l,rz]` and returns
`[N,5]` or `[N,6]`. `BevBoxCoder` accepts full seven-column boxes/anchors,
slices columns `[0,1,3,4,6]`, and decodes to seven columns by inserting fixed
`z_fixed` (default `-1.0`) and `h_fixed` (default `2.0`). `GroundBox3dCoder.code_size`
is 7 or 8 plus custom columns; `BevBoxCoder.code_size` is 5 or 6 and does not
accept custom columns.

The Torch counterparts in `second.pytorch.core.box_torch_ops` have the same
math and shape contracts but require Torch tensors. `GroundBox3dCoderTorch`
and `BevBoxCoderTorch` expose `encode_torch`/`decode_torch`. Use the NumPy
helper for safe validation before trying Torch or detector imports.

## Anchors and targets

`create_anchors_3d_stride(feature_size, sizes, anchor_strides, anchor_offsets,
rotations, dtype)` and `create_anchors_3d_range(feature_size, anchor_range,
sizes, rotations, dtype)` use `feature_size=[D,H,W]` (documented as zyx) and
return `[D,H,W,num_sizes,num_rotations,7]`. `sizes` are xyz dimension triplets
in the generated tensor's `[w,l,h]` convention. `AnchorGeneratorStride` and
`AnchorGeneratorRange` add optional custom columns and report `ndim=7+C` and
`num_anchors_per_localization=num_sizes*num_rotations`.

Configuration intent is expressed through `point_cloud_range` as xyzxyz,
`voxel_size` as xyz, per-class anchor generator sizes/ranges/rotations, and
per-class NMS score/IoU limits. Treat those values as dataset/model intent:
validate the resulting array shapes and coordinate frame instead of copying a
threshold from one config to another.

`TargetAssigner(box_coder, anchor_generators, classes, feature_map_sizes,
positive_fraction=None, region_similarity_calculators=None, sample_size=512,
assign_per_class=True)` provides:

- `generate_anchors(feature_map_size)` -> dict with flattened `anchors [A,ndim]`,
  `matched_thresholds [A]`, and `unmatched_thresholds [A]`.
- `generate_anchors_dict(feature_map_size)` -> class-keyed dict; each value has
  the same three arrays for that class.
- `assign_all(anchors, gt_boxes, anchors_mask=None, gt_classes=None,
  matched_thresholds=None, unmatched_thresholds=None, importance=None)` and
  `assign_per_class(...)` -> labels, bbox targets, outside weights, positive GT
  ids, and importance. `create_target_np` uses positive labels `1+`, negative
  `0`, and ignore `-1`; forced best-anchor matches can be positive even when a
  threshold is not met. `bbox_targets` has `[A,box_code_size]`.

`RotateIouSimilarity.compare(boxes1,boxes2)` expects `[N,5]` and `[M,5]`
`[x,y,w,l,rz]`, returning `[N,M]`; it delegates to legacy rotated IoU. The
`NearestIouSimilarity` path first makes near axis-aligned boxes; the
`DistanceSimilarity` path compares `[x,y,rz]` with a configured distance norm.

## IoU, NMS, and preprocessing math

- `iou_jit(boxes, query_boxes, eps=1.0)` accepts axis-aligned `[N,4]` and
  `[K,4]` xyxy arrays and returns `[N,K]`. `eps=0.0` is used for geometric
  overlap gates; `eps=1.0` preserves KITTI-style inclusive pixel boxes.
- `riou_cc(rbboxes,qrbboxes,standup_thresh=0.0)` and `rinter_cc(...)` use
  `[x,y,w,l,rz]`, first reject non-overlapping standup boxes, then call legacy
  spconv rotated geometry.
- `nms_jit(dets, thresh, eps=0.0)` expects `[N,5]=[x1,y1,x2,y2,score]` and
  returns kept integer indices in descending score order. It is a Numba CPU
  implementation. `soft_nms_jit` mutates its input and should be copied first.
- `nms_cc`, `rotate_nms_cc`, `nms_gpu`, `rotate_nms_gpu`, and `rotate_iou_gpu`
  depend on legacy spconv or Numba CUDA interfaces. The source GPU rotated NMS
  itself warns that performance was not tested. None of these backend kernels
  are verified by this skill. Current spconv is known not to expose the legacy
  `non_max_suppression`/`VoxelGeneratorV2` names; report that as a compatibility
  block instead of substituting modern APIs silently.

`simplevis.draw_box_in_bev(img, coors_range, boxes, color, thickness=1,
labels=None, label_color=None)` expects center-format lidar boxes, uses columns
`[0,1,3,4,6]`, maps the xy range to image width/height, and returns the image.
`points_to_bev(points, voxel_size, coors_range, with_reflectivity=False,
density_norm_num=16, max_voxels=40000)` returns `[channels,H,W]` in DHW order;
its final channel is a count map, not a normalized density map. For a point
`p`, the source grid index is `floor((p - coors_range[:3]) / voxel_size)`;
reject indices outside `[0, grid_size)` before indexing.
