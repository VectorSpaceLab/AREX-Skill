# Geometry troubleshooting

## `gradslam.geometry.se3_exp` or a transform helper is missing

`gradslam.geometry.__init__` exports the `projutils` wildcard only. Import
`se3_exp`, `so3_exp`, `so3_hat`, and `se3_hat` from
`gradslam.geometry.se3utils`. Import `create_meshgrid`, transform helpers,
quaternion helpers, and legacy camera helpers from
`gradslam.geometry.geometryutils`. The public projective names can be
imported from `gradslam.geometry` or the package root.

## Wrong point or pixel rank

**Signals:** `Input tensor must have at least 2 dimensions`, `cam_coords must
have shape (*,3), or (*,4)`, or a final-dimension error.

Keep coordinates in the last dimension. Typical valid forms are `(N,3)` or
`(B,N,3)` for points, `(N,4)` for homogeneous points, `(N,2)` or `(B,N,2)`
for pixels, and `(B,N,D)` for `transform_pts_nd_KF`. A single point shaped
`(3,)` is rejected by the projective conversion helpers; use `(1,3)` if a
one-point batch is intended.

## Projection matrix batch mismatch

**Signal:** `proj_mat must either have 2 dimensions...` or a batch-size error.

Use one `(4,4)` matrix to broadcast across a supported point batch, or use a
matching `(B,4,4)` matrix for `(B,N,3/4)` points. A rank-3 matrix must have the
same rank as the point tensor and the same first dimension. A `(1,4,4)` matrix
is not a universal broadcast substitute for an arbitrary `(B,...,3)` shape.

## Unprojection depth mismatch

**Signal:** `pixel_coords and depths must have the same shape`.

For `pixel_coords.shape == (...,2)` or `(...,3)`, require
`depths.shape == pixel_coords.shape[:-1]`. The inverse intrinsics matrix must
be `(3,3)` or a matching batch form such as `(B,3,3)`. Select the top-left
3x3 from a GradSLAM `(4,4)` intrinsics tensor before calling the public
unprojector.

## Intrinsics inverse is inaccurate or surprising

`inverse_intrinsics` is a specialized pinhole-layout inverse. It reads only
`fx`, `fy`, `cx`, and `cy`, adds `eps` to both focal denominators, and writes a
small set of output entries. It does not invert arbitrary skew, distortion,
or a general dense matrix. Ensure focal values are nonzero and that the 4x4
matrix has the expected homogeneous diagonal. If a fully general inverse is
required, use a suitable PyTorch linear algebra operation outside this helper
and validate conditioning yourself.

## NaN/Inf around zero depth or homogeneous weight

`unhomogenize_points` uses scale one when `abs(w) <= eps`, and
`project_points`/legacy camera helpers use denominator one only for exact
`z == 0`. A very small nonzero z is still divided. These guards are not
visibility tests. Mask nonpositive or invalid depth before projection, and
choose an application-specific threshold instead of relying on a finite
fallback to signal invalid geometry.

## Projection round-trip has a coordinate offset

Check all of the following:

1. pixel convention is `(u,v)` with the intended x/column and y/row meaning;
2. `K` and `inverse_intrinsics(K)` use the same 3x3 pinhole block;
3. the projection matrix has the same focal/principal-point entries as `K`;
4. depth is camera z and has shape `pixels.shape[:-1]`;
5. homogeneous points have their final coordinate in the expected position.

Do not mix `normalize_pixel_coords` output with raw pixel coordinates without
converting one representation. `cam2pixel` returns raw ratios despite a
stale docstring describing normalized output.

## Non-square pixel normalization is wrong

The implementation of `normalize_pixel_coords` and
`unnormalize_pixel_coords` currently uses the first computed normalization
factor in both coordinate arithmetic. This is observable for different
height/width. If a caller requires exact non-square endpoint behavior, either
apply an explicit caller-side two-axis formula or gate the behavior on a
version/source change; do not document the current helper as a general
correctness guarantee.

## Wrong frame or transform order

Write the frame labels beside every matrix. `transform_pts_3d(pts_b, t_ab)`
means `b -> a`. `compose_transforms_3d(t1,t2)` computes `t1 @ t2` and applies
`t2` first. For poses against a common reference, the relative transform is
`inverse(T_01) @ T_02`. Test with a pure translation and one asymmetric point
before using rotation-plus-translation data.

`inverse_transfom_3d` (including its misspelling) uses transpose-based inversion
and therefore requires an orthogonal rotation. For imperfect or general
invertible matrices, use `relative_transformation(...,
orthogonal_rotations=False)` or a general inverse.

## Normals moved unexpectedly

`transform_normals` applies only the 3x3 rotation block. It intentionally does
not translate normals. It also does not apply inverse-transpose for scale or
shear. Use it only for rigid transforms or implement the correct normal
mapping for a non-rigid transform at the caller boundary.

## Quaternion rotation looks mirrored

The expected quaternion order is `(x,y,z,w)`. Normalize before comparing
results, remember that `q` and `-q` represent the same rotation, and verify
the active transform convention with a basis vector. `quaternion_to_axisangle`
uses the vector part and scalar part in that same order. A zero quaternion is
degenerate; do not depend on a meaningful axis-angle result for it.

## `se3_exp` gives unexpected translation

`se3_exp` takes `[v_x,v_y,v_z,omega_x,omega_y,omega_z]`, not rotation first.
Translation is `V @ v`, so it is coupled to the rotation in the exponential
map; it is not simply copied into the last column for a nonzero `omega`.
For a pure translation, the result should be identity rotation and `v` in
its translation column. For a tiny rotation, the implementation uses a
first-order branch at norm `< 1e-6`.

## Gradient is absent or non-finite

Keep all differentiable values as tensors. Do not call `.item()`, `.numpy()`,
or detach a transform/update before applying it. Confirm the loss depends on
the intended tensor, then check `requires_grad`, `grad is not None`, and
finite values. Use float64 for diagnosis. Avoid in-place writes on leaf tensors
with `requires_grad=True`, especially when assembling a 4x4 transform around a
learned rotation. Check zero-depth, zero-weight, zero-quaternion, and the
small-angle SE(3) branch separately; these are piecewise or degenerate cases.

## CPU smoke check fails at import

Run `python scripts/geometry_smoke.py --help` first; help should not require a
GPU or execute geometry. Then run the script from any current working
 directory with the repository environment active. If importing GradSLAM fails,
verify the package installation and the compatible CPU PyTorch/Kornia pair
before diagnosing geometry. The inspection baseline was CPU-only; CUDA
parameterized native tests were not part of drafting.
