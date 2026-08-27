# Coordinate systems and box conventions

Read this before any conversion. Most silent evaluation failures are an axis,
origin, dimension-order, or yaw-sign error rather than a numerical error.

## Canonical formats

| Context | Center/box columns | Dimensions and origin | Heading |
|---|---|---|---|
| Internal lidar | `[x,y,z,w,l,h,rz]` | `[w,l,h]`; normal center origin `[0.5,0.5,0.5]` | lidar yaw about z, source `axis=2` |
| KITTI camera label | location `[x,y,z]`, dimensions `[l,h,w]` | bottom-center origin `[0.5,1.0,0.5]` | `rotation_y`, about camera y, source `axis=1` |
| KITTI text fields | `h,w,l` on disk | parser converts to `[l,h,w]` | field 15 is `rotation_y` |
| BEV rotated box | `[x,y,w,l,rz]` | 2-D center origin normally `0.5` | positive source 2-D rotation |

KITTI camera coordinates conventionally use x right, y down, z forward. The
lidar convention used by this code is x forward, y lateral, z up. The exact yaw
mapping across frames is calibration/dataset dependent; do not infer it from a
mere dimension reorder.

## KITTI conversion sequence

`box_camera_to_lidar(data, r_rect, velo2cam)` expects camera rows
`[x,y,z,l,h,w,ry]`, applies the homogeneous inverse of `r_rect @ velo2cam`
to centers, and returns `[x,y,z,w,l,h,angle]`. The inverse
`box_lidar_to_camera` transforms centers with `r_rect @ velo2cam` and returns
`[x,y,z,l,h,w,angle]`. The source functions preserve the last angle column;
they do not themselves apply a yaw sign or `pi/2` offset.

For KITTI dataset preparation, the historical path subsequently changes the
lidar box z origin from bottom-center to center using the equivalent of
`change_box3d_center_(box3d, src=[0.5,0.5,0], dst=[0.5,0.5,0.5])`. Keep this
step explicit when constructing internal `gt_boxes`; otherwise corners and
point-in-box tests are vertically shifted by `h/2`.

Use homogeneous matrices with compatible shapes:

```text
points [N,3] + ones -> [N,4]
T = r_rect @ velo2cam          # normally 4x4
lidar_to_camera: points4 @ T.T -> first 3 columns
camera_to_lidar: points4 @ inv(T.T) -> first 3 columns
```

Check a round trip with identity matrices first. Then check a known translation
and only then use calibration. A matrix with shape 3x4 must be extended to 4x4
before using these APIs; a 3x3 rotation alone cannot encode translation.

## NuScenes conversion

The internal NuScenes boxes are lidar-frame center boxes with `[w,l,h]` dimensions
and optional velocity `[vx,vy]` trailing columns. The source result conversion
performs the explicit heading transform
`rz_nusc_lidar = -rz_internal - pi/2`, creates a NuScenes `Box` with center,
`wlh`, quaternion about z, score, label, and velocity, then applies
`lidar2ego` and `ego2global` rotations/translations. It filters boxes by the
configured per-class detection range before writing results.

Do not reuse the KITTI camera conversion for NuScenes. For each result, preserve
its `metadata.token`, map integer labels to the configured class list, and keep
velocity as `[vx,vy]` (or NaN when no sweep velocity is available). The evaluator
expects global-frame `translation`, `size` in `wlh` order, quaternion `rotation`
(elements list), `velocity`, `detection_name`, `detection_score`, and
`attribute_name`; see [evaluation.md](evaluation.md).

## Angles and periods

`limit_period(val, offset=0.5, period=np.pi)` computes
`val - floor(val/period + offset)*period`. Therefore the default representative
interval is approximately `[-pi/2, pi/2)`, useful for pi-periodic box headings.
For a full-turn lidar heading use `period=2*pi`, which gives approximately
`[-pi,pi)`. Use the same period on both sides of a comparison; angular residuals
are not ordinary absolute differences near a wrap boundary.

A robust equivalence check is:

```python
wrapped = limit_period(pred_angle - target_angle, offset=0.5, period=2*np.pi)
assert abs(wrapped) < tolerance
```

For a directionless rectangle, compare modulo `pi`; for NuScenes quaternion
conversion, compare the resulting quaternion or transformed corners rather than
only the raw yaw scalar.

## Voxel/grid and visualization order

`coors_range` is `[xmin,ymin,zmin,xmax,ymax,zmax]`; `voxel_size` is xyz. Grid
sizes are computed from `(max-min)/voxel_size`, while BEV maps are returned in
`[height,width]` / DHW order. Anchor feature sizes are `[D,H,W]`, although
3-D anchor construction internally meshes x/y/z before transposing to that
output order. `simplevis` maps xy to image width/height and draws the same
center-format lidar boxes; it is a visual sanity check, not an evaluator.
