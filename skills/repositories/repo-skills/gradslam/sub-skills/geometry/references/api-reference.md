# Geometry API reference

This reference records the implementation-level contracts used by the
geometry sub-skill. Unless noted otherwise, inputs are `torch.Tensor`s and
outputs preserve dtype/device through the tensor operations. The verified
inspection environment used Python 3.8, CPU PyTorch 2.0.0, and GradSLAM 0.1.0;
CUDA was not selected for this inspection.

## Public projective API

These functions are exported by `gradslam.geometry` and re-exported at the
package root through the geometry package initializer. The documented module
for them is `gradslam.geometry.projutils`.

### `homogenize_points(pts)`

- Requires `pts.dim() >= 2`.
- Appends a last coordinate of `1.0` with `torch.nn.functional.pad`.
- For input `(..., K)`, returns `(..., K+1)`; common point input is `(N, 3)`
or `(B, N, 3)`.
- Rejects non-tensors with `TypeError` and rank-1 tensors with `ValueError`.

### `unhomogenize_points(pts, eps=1e-6)`

- Divides all coordinates except the last by the last coordinate `w`.
- For `abs(w) <= eps`, uses scale `1` rather than `1/w`; this is a finite
  fallback for points at infinity, not a geometric normalization.
- `(..., K)` becomes `(..., K-1)` and rank must be at least 2.
- The same named helper exists in `geometryutils`; use the module-specific
  import when the surrounding code is using that module.

### `project_points(cam_coords, proj_mat, eps=1e-6)`

- `cam_coords` must have rank at least 2 and last dimension 3 or 4.
- `proj_mat` must be `(4, 4)`, or have the same rank as the point tensor with
  matching first batch size, e.g. `(B, 4, 4)` for `(B, N, 3)` points.
- 3D points are homogenized automatically. Homogeneous 4D points are used as
  supplied.
- Matrix multiplication is followed by `x/z, y/z`; exact `z == 0` uses a
  denominator of one. The `eps` argument is present in the public signature
  but the implementation's division guard checks exact zero.
- Output is `(..., 2)`, retaining point leading dimensions.
- A projection matrix is broadcast when it is rank 2. Rank-3 matrices do not
  broadcast over arbitrary additional point dimensions; satisfy the explicit
  batching contract.

For ordinary pinhole projection, construct a 4x4 matrix with the focal and
principal-point values in its top-left 3x3 camera block and homogeneous bottom
row/column matching the library's 4x4 convention. A zero or negative camera
`z` is not rejected; the caller must mask invalid depths if required.

### `unproject_points(pixel_coords, intrinsics_inv, depths)`

- Pixel coordinates end in 2 (Euclidean `(u,v)`) or 3 (homogeneous pixels).
- `intrinsics_inv` must end in `(3, 3)`, either unbatched or with the same rank
  as pixel coordinates and matching leading batch size.
- `depths.shape` must equal `pixel_coords.shape[:-1]` exactly.
- 2D pixels are homogenized; the inverse intrinsics matrix is multiplied by
  each pixel ray, then the result is multiplied by `depths[..., None]`.
- Output ends in 3 and preserves leading dimensions.
- Rejects wrong types/ranks/shapes with `TypeError` or `ValueError`.

### `inverse_intrinsics(K, eps=1e-6)`

- Supports `(..., 3, 3)` and `(..., 4, 4)` only.
- Assumes a pinhole layout: `fx=K[...,0,0]`, `fy=K[...,1,1]`,
  `cx=K[...,0,2]`, `cy=K[...,1,2]`.
- Returns a zero-like tensor populated with `1/(fx+eps)`, `1/(fy+eps)`,
  `-cx/(fx+eps)`, `-cy/(fy+eps)`, `Kinv[...,2,2]=1`, and, for 4x4, the last
  diagonal element `1`. It is not a general inverse and does not preserve
  arbitrary skew or off-layout entries.
- The `eps` addition is used to avoid division by zero. The fast inverse is
  differentiable with respect to the read intrinsics values, subject to the
  output assembly and normal autograd caveats.

## Direct `geometryutils` API

`gradslam.geometry.__init__` imports only `projutils` with a wildcard. The
following are **not guaranteed package exports**; import them from
`gradslam.geometry.geometryutils`.

### Homogeneous and transform primitives

- `homogenize_points`, `unhomogenize_points`: same broad contracts as the
  public functions, implemented separately.
- `inverse_transfom_3d(trans)`: spelling is intentionally `transfom` in the
  code. Accepts a 4x4 or `(N,4,4)` tensor by intended contract and uses
  `R.T` and `-R.T @ t`, assuming an orthogonal 3x3 rotation. The bottom-right
  element is set to one. Verify the input shape before relying on errors; the
  source has a weak shape guard.
- `compose_transforms_3d(trans1, trans2)`: equal-shaped 4x4 or `(N,4,4)`
  tensors; computes `R1@R2` and `R1@t2+t1`, returning the same shape. It uses
  an assignment-based output assembly, so avoid mutating participating leaf
  tensors in a gradient-sensitive caller.
- `transform_pts_3d(pts_b, t_ab)`: `t_ab` must be exactly 4x4 and points must
  have rank at least 2. Points whose last dimension is 3 are homogenized;
  other last dimensions are treated as already homogeneous. Intended output
  is points in frame `a`, with the same leading point dimensions and final 3.
- `transform_pts_nd_KF(pts, tform)`: batch-first points `(B,N,D)` and transforms
  `(B,D+1,D+1)` with equal batch size. Homogenizes and unhomogenizes through
  batched matrix multiplication. This is a direct helper, not a package
  export.
- `relative_transform_3d(trans_01, trans_02)`: computes
  `inverse_transfom_3d(trans_01) @ trans_02` for equal-shaped rigid tensors.
- `relative_transformation(trans_01, trans_02, orthogonal_rotations=False)`:
  accepts intended `(4,4)` or `(N,4,4)` pairs with equal rank and computes
  `inverse(trans_01) @ trans_02` using Kornia composition. With
  `orthogonal_rotations=True`, it uses Kornia's rigid inverse, which assumes
  orthogonal rotations. The non-orthogonal default is more general.

### Pixel and camera helpers

- `normalize_pixel_coords(pixel_coords, height, width)` and
  `unnormalize_pixel_coords(pixel_coords_norm, height, width)` require last
  dimension 2 and Python `int` dimensions. Intended mapping is coordinate
  endpoints `[0, height-1]` and `[0, width-1]` to `[-1,1]` and back. The
  implementation currently builds a two-axis factor but indexes the first
  factor in both return expressions; preserve this known behavior unless a
  source change explicitly changes it.
- `create_meshgrid(height, width, normalized_coords=True)` returns a grid of
  shape `(1, H, W, 2)`. With normalization it uses `linspace(-1,1,...)`; with
  `False`, it uses pixel coordinates from zero through `height-1` and
  `width-1`. It uses a meshgrid call without an explicit indexing keyword.
- `cam2pixel(cam_coords_src, dst_proj_src, eps=1e-6)`: expects camera points
  ending in 3 and a 4x4 projection transform; calls `transform_pts_3d` and
  divides x/y by z, using one for exact zero. The docstring says normalized
  output, but the implementation returns raw ratios.
- `pixel2cam(depth, intrinsics_inv, pixel_coords)`: legacy helper expecting a
  4x4 inverse transform and homogeneous pixel grid; calls `transform_pts_3d`
  then multiplies by a depth tensor after `depth.permute(0,2,3,1)`. Prefer
  public `unproject_points` for a clean `( ..., 3x3)` contract.
- `cam2pixel_KF(cam_coords_src, P, eps=1e-6)`: batch-first helper using
  `transform_pts_nd_KF`; point last dimension is 3 and transform last two
  dimensions are 4x4. It returns raw x/z and y/z ratios.
- `transform_pointcloud(pointcloud, transform)`: strictly `(N,3)` points and
  a transform whose final dimensions are 4x4; applies `R @ points.T + t` and
  returns `(N,3)`. It does not accept batched clouds.
- `transform_normals(normals, transform)`: strictly `(N,3)` normals and a
  4x4-final-dimension transform; applies only the top-left rotation `R`, never
  translation. For non-rigid transforms, the mathematically correct normal
  operation may require inverse-transpose, which this helper does not do.

## Direct `se3utils` API

Import these from `gradslam.geometry.se3utils`; in particular, do not write
`gradslam.geometry.se3_exp` unless a caller has explicitly installed an alias.

- `so3_hat(omega)`: a tensor 3-vector to a skew-symmetric 3x3 matrix.
- `se3_hat(xi)`: a tensor 6-vector in `(v_x,v_y,v_z,omega_x,omega_y,omega_z)` order
to a 4x4 matrix with `so3_hat(omega)` in the rotation block and `v` in the
translation column.
- `so3_exp(omega)`: Rodrigues exponential to a 3x3 rotation. For norm below
  `1e-6`, uses first-order `I + hat(omega)`; otherwise uses sine/cosine
  coefficients.
- `se3_exp(xi)`: exponential of a six-vector in translation-then-rotation
  order. It computes `R` and the SE(3) V matrix, then `t=V@v`, returning a
  4x4 matrix with bottom row `[0,0,0,1]`. Inputs are single six-vectors, not
  documented batches. Small rotations use first-order `I+hat` branches.

The SE(3) helpers use assertions for tensor type and scalar norm branches, and
construct outputs on the input dtype/device. Their small-angle branch is
piecewise, so test gradients at nonzero and near-zero rotations separately.
