# Geometry Vision Workflows

These recipes are intentionally small and no-download. They assume tensors are
already in PyTorch format and on the desired device.

## 1. Resize or rescale an image tensor

Use `resize` when the target size is known and `rescale` when a scale factor is
known.

```python
from kornia.geometry.transform import resize, rescale

# img: B,C,H,W, float tensor
small = resize(img, (128, 192), interpolation="bilinear", align_corners=False, antialias=True)
wide = rescale(img, (1.0, 1.5), interpolation="bilinear", align_corners=False)
```

Checklist:

- Use `(height, width)` for target sizes.
- Use `antialias=True` for quality-sensitive downsampling; it has no effect for
  upsampling.
- Pass `align_corners` explicitly when matching another implementation.

## 2. Warp with an affine transform

Build a matrix in pixel coordinates, then call `warp_affine`.

```python
from kornia.geometry.transform import get_rotation_matrix2d, warp_affine

B, C, H, W = img.shape
center = img.new_tensor([[float(W - 1) / 2, float(H - 1) / 2]]).repeat(B, 1)
angle = img.new_full((B,), 15.0)
scale = img.new_ones(B, 2)
M = get_rotation_matrix2d(center, angle, scale)
out = warp_affine(img, M, (H, W), mode="bilinear", padding_mode="zeros", align_corners=True)
```

Checklist:

- `center` is `(x,y)`, not `(y,x)`.
- `M` maps source pixels to destination pixels.
- Use `invert_affine_transform` only when your matrix is destination→source.

## 3. Warp with a quadrilateral homography

Use four non-degenerate point pairs in consistent order.

```python
from kornia.geometry.transform import get_perspective_transform, warp_perspective

pts_src = img.new_tensor([[[0., 0.], [W - 1., 0.], [W - 1., H - 1.], [0., H - 1.]]])
pts_dst = img.new_tensor([[[4., 2.], [W - 5., 1.], [W - 3., H - 4.], [2., H - 2.]]])
H_src_to_dst = get_perspective_transform(pts_src, pts_dst)
warped = warp_perspective(img, H_src_to_dst, (H, W), align_corners=True)
```

Checklist:

- Do not pass integer point tensors; use float32 or float64.
- Avoid coincident points, repeated corners, collinear points, or a quadrilateral
  with near-zero area.
- If using `homography_warp`, account for its normalized destination→source
  default or set `normalized_homography=False` for pixel source→destination
  homographies.

## 4. Estimate a homography from correspondences

For exactly four trusted correspondences, `get_perspective_transform` is the
smallest tool. For many correspondences with outliers, use `RANSAC`.

```python
from kornia.geometry import RANSAC, transform_points

# pts0, pts1: (N,2) matched pixel coordinates from another pipeline
ransac = RANSAC("homography", inl_th=2.0, batch_size=2048, max_iter=10, seed=0)
H_0_to_1, inliers = ransac(pts0, pts1)
projected = transform_points(H_0_to_1[None], pts0[None])
```

Checklist:

- Feature extraction/matching belongs to the features-and-matching sub-skill;
  this workflow begins after correspondences exist.
- Tune `inl_th` in pixel units after considering image scale.
- Inspect inlier count and transfer error, not just the returned matrix shape.

## 5. Direct image registration

Use `ImageRegistrator` when you need differentiable, optimization-based
alignment of two same-modality images.

```python
from kornia.geometry.transform import ImageRegistrator

registrator = ImageRegistrator("similarity", num_iterations=200, lr=3e-4, pyramid_levels=2)
model = registrator.register(img_src, img_dst)
aligned = registrator.warp_src_into_dst(img_src)
```

Checklist:

- Supported string models are `"homography"`, `"similarity"`, `"translation"`,
  `"scale"`, and `"rotation"`.
- By default, source and destination image shapes must match. Set
  `allow_shape_mismatch=True` only when resizing the source to destination size
  is acceptable.
- Registration is iterative; use small images/pyramids for quick diagnosis and
  expect sensitivity to texture, initialization, learning rate, and loss.

## 6. Project and unproject camera points

Use 3x3 intrinsics with standalone projection functions. Use 4x4 matrices for
`PinholeCamera` objects.

```python
from kornia.geometry.camera import project_points, unproject_points

# points_cam: B,N,3 with positive z
K_points = K[:, None].expand(-1, points_cam.shape[1], -1, -1)
uv = project_points(points_cam, K_points)
points_cam_roundtrip = unproject_points(uv, points_cam[..., 2:3], K_points)
```

Checklist:

- Keep `z` positive and away from zero.
- `uv` is `(u,v)` / `(x,y)` pixel order.
- Use realistic intrinsics and explicit broadcasting.

## 7. Solve PnP from 3D/2D correspondences

Use `solve_pnp_dlt` for batched world→camera pose from at least six 3D/2D
pairs.

```python
from kornia.geometry.calibration import solve_pnp_dlt

# world_points: B,N,3; image_points: B,N,2; K: B,3,3; N >= 6
world_to_cam = solve_pnp_dlt(world_points, image_points, K)
```

Checklist:

- Use float32 or float64; prefer float64 when validating exact reprojection.
- Points must not all lie on a line or all lie on a plane.
- Verify by projecting the world points through the returned transform and
  measuring pixel reprojection error.

## 8. Estimate epipolar geometry and pose

Use fundamental matrices for pixel correspondences, essential matrices for
calibrated/normalized correspondences, and triangulation after choosing a valid
relative pose.

```python
from kornia.geometry.epipolar import find_fundamental, sampson_epipolar_distance

F = find_fundamental(points0, points1, method="8POINT")
err = sampson_epipolar_distance(points0, points1, F[:, :3])
```

Checklist:

- Use `N>=8` for the 8-point fundamental method, `N>=7` for 7-point, and `N>=5`
  for essential estimation.
- 7-point and 5-point solvers can return multiple candidate matrices.
- Use Sampson/symmetric epipolar distance and cheirality/positive-depth checks
  to select solutions.
- Prefer float64 for ill-conditioned or high-precision validations.

## 9. Convert depth to 3D and warp by depth

```python
from kornia.geometry.depth import depth_to_3d, depth_to_normals, warp_frame_depth

xyz_bchw = depth_to_3d(depth, K, normalize_points=False)      # B,3,H,W
normals = depth_to_normals(depth, K, normalize_points=False)  # B,3,H,W
warped = warp_frame_depth(image_src, depth_dst, dst_to_src, K)
```

Checklist:

- `depth` is `B,1,H,W`; keep it positive for perspective projection.
- `warp_frame_depth` expects a destination→source 4x4 transform.
- For Euclidean ray length depth, set `normalize_points=True`; for z-depth, keep
  it `False`.

## 10. Track a planar target by homography

Use `HomographyTracker` only when feature matching dependencies and potential
weights/caches are acceptable. In minimal or offline sessions, avoid default
construction and inject prepared matchers.

```python
from kornia.tracking import HomographyTracker

tracker = HomographyTracker(initial_matcher=my_initial, fast_matcher=my_fast, ransac=my_ransac)
tracker.set_target(target_img)
H, ok = tracker(next_frame)
if ok:
    # H maps target points into the current frame.
    pass
```

Checklist:

- Monitor `tracker.inliers_num`, `keypoints0_num`, and `keypoints1_num`.
- `track_next_frame` resets state when too few keypoints or inliers are found.
- Route matcher construction and learned feature model issues to the
  features-and-matching sub-skill.

## 11. Use Lie groups for pose composition

```python
from kornia.geometry.liegroup import So3, Se3

R = So3.exp(torch.zeros(3, device=device, dtype=dtype))
I = R.matrix()
R_inv = R.inverse()
```

Checklist:

- Use group operations for repeated pose composition/inversion.
- Convert to plain matrices at API boundaries that expect tensors.
- Keep tangent vectors and group objects on the same device/dtype.

