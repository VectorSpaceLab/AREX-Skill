# Geometry Vision API Reference

This reference summarizes stable Kornia 0.9.0rc1 geometry/tracking entry points
for Researcher runtime use. It focuses on shapes, matrix direction, and safe
minimal dependencies.

## Import map

```python
import torch
import kornia
from kornia import geometry as KG
from kornia.geometry import transform as KGT
from kornia.geometry import camera as KGC
from kornia.geometry import epipolar as KGE
from kornia.geometry import calibration as KCal
from kornia.geometry import depth as KDepth
from kornia.geometry import liegroup as KLie
```

Many functions are re-exported at `kornia.geometry`, so both
`KG.warp_perspective(...)` and `KGT.warp_perspective(...)` are commonly valid.
Use submodule imports when you want the owner of a call to be obvious.

## Image transforms and warps

| API | Primary inputs | Output / notes |
|---|---|---|
| `resize(input, size, interpolation="bilinear", align_corners=None, side="short", antialias=False)` | `input` shape `(..., H, W)`; `size` int or `(h, w)` | Keeps leading dims; int size preserves aspect ratio by `side`. `align_corners=None` follows PyTorch interpolate defaults. |
| `resize_to_be_divisible(input, divisible_factor, interpolation="bilinear", align_corners=None, side="short", antialias=False)` | `C,H,W` or `B,C,H,W` | Rounds spatial size to nearest multiple, then resizes. |
| `rescale(input, factor, interpolation="bilinear", align_corners=None, antialias=False)` | Factor float or `(fy, fx)` | Convenience wrapper around `resize`. |
| `warp_affine(src, M, dsize, mode="bilinear", padding_mode="zeros", align_corners=True, fill_value=None)` | `src: (B,C,H,W)`, `M: (B,2,3)`, `dsize: (h,w)` | Applies a source→destination pixel affine matrix; output `(B,C,h,w)`. |
| `warp_perspective(src, M, dsize, mode="bilinear", padding_mode="zeros", align_corners=True, fill_value=None)` | `src: (B,C,H,W)`, `M: (B,3,3)`, `dsize: (h,w)` | Applies a source→destination pixel homography; output `(B,C,h,w)`. |
| `homography_warp(patch_src, src_homo_dst, dsize, mode="bilinear", padding_mode="zeros", align_corners=False, normalized_coordinates=True, normalized_homography=True)` | `patch_src: (N,C,H,W)`, homography `(N,3,3)` | Default consumes destination→source normalized homography. With `normalized_homography=False`, consumes source→destination pixel homography and delegates to `warp_perspective`. |
| `remap(src, map_x, map_y, mode="bilinear", padding_mode="zeros", align_corners=True)` | Explicit sampling maps | Use when the sampling grid is already known. |

`padding_mode` is usually one of `"zeros"`, `"border"`, or `"reflection"`.
`warp_affine` and `warp_perspective` also support `"fill"`; ensure `fill_value`
has a compatible channel shape. For MPS, avoid 2D `grid_sample` border padding
unless you have verified the backend path.

## Matrix builders and point transforms

| API | Primary inputs | Output / notes |
|---|---|---|
| `get_perspective_transform(points_src, points_dst)` | `points_src, points_dst: (B,4,2)` float tensors | Returns source→destination pixel homography `(B,3,3)`. Four points must form a non-degenerate quadrilateral. |
| `get_rotation_matrix2d(center, angle, scale)` | `center: (B,2)` as `(x,y)`, `angle: (B)` degrees, `scale: (B,2)` | Returns source→destination pixel affine `(B,2,3)`. Positive angles rotate counter-clockwise in displayed image coordinates. |
| `get_affine_matrix2d`, `get_translation_matrix2d`, `get_shear_matrix2d` | Batched transform parameters | Build affine or homogeneous matrices for later warping. |
| `invert_affine_transform(M)` | `M: (B,2,3)` | Invert an affine transform. |
| `convert_affinematrix_to_homography(M)` | `M: (B,2,3)` | Promote to `(B,3,3)`. |
| `transform_points(trans_01, points_1)` | Transform `(...,D+1,D+1)` and points `(...,N,D)` | Applies homogeneous transform to Euclidean points. |
| `compose_transformations`, `inverse_transformation`, `relative_transformation` | Rigid homogeneous transforms | Compose, invert, or compare frame transforms. |
| `normalize_pixel_coordinates`, `denormalize_pixel_coordinates`, `normalize_homography`, `denormalize_homography` | Pixel/normalized image coordinates plus sizes | Use to bridge pixel-space math and normalized grid-sample coordinates. |

For 3D volumes, analogous APIs include `warp_affine3d`, `warp_perspective3d`,
`homography_warp3d`, `get_perspective_transform3d`, and `normalize_homography3d`.
Volume sizes are ordered `(depth, height, width)`.

## Homography estimation and robust fitting

| API | Use |
|---|---|
| `find_homography_dlt(points1, points2, weights=None, solver="lu")` | Estimate homography from many corresponding point pairs when all points are trusted. |
| `find_homography_dlt_iterated(points1, points2, weights, soft_inl_th=3.0, n_iter=5)` | Iteratively reweight homography fit. |
| `RANSAC(model_type="homography", inl_th=2.0, batch_size=2048, max_iter=10, confidence=0.99, max_lo_iters=5, score_type="ransac", prosac_sampling=False, seed=None)` | Robustly estimate `"homography"`, `"fundamental"`, `"fundamental_7pt"`, `"essential"`, or `"homography_from_linesegments"` from outlier-contaminated correspondences. |
| `oneway_transfer_error`, `symmetric_transfer_error`, `sampson_epipolar_distance` | Error functions for fitted geometry. |

Use feature/matcher sub-skills to obtain correspondences. Once you have point
pairs, this sub-skill owns the geometry solve and validation.

## Camera, calibration, and projection

| API | Primary inputs | Output / notes |
|---|---|---|
| `PinholeCamera(intrinsics, extrinsics, height, width)` | `intrinsics, extrinsics: (B,4,4)`; `height,width: (B)` tensors | Stores camera matrix, `rt_matrix`, rotation, translation, `fx/fy/cx/cy`, and image size. |
| `project_points(point_3d, camera_matrix)` | `point_3d: (*,3)`, `camera_matrix: (*,3,3)` | Returns pixel `(u,v)` / `(x,y)` coordinates `(*,2)`. Keep depth away from zero. |
| `unproject_points(point_2d, depth, camera_matrix, normalize=False)` | `point_2d: (*,2)`, `depth: (*,1)`, `camera_matrix: (*,3,3)` | Returns camera-frame `(*,3)` points. Set `normalize=True` only when depth is Euclidean ray length. |
| `project_points_z1`, `unproject_points_z1` | Points on the normalized image plane | Convert between normalized camera rays and image-plane coordinates. |
| `project_points_orthographic`, `unproject_points_orthographic` | Orthographic camera points and extensions | Use when perspective projection is not appropriate. |
| `distort_points_affine`, `undistort_points_affine`, `distort_points_kannala_brandt`, `undistort_points_kannala_brandt` | Distortion parameters and points | Useful for calibration workflows with affine or fisheye-style distortion models. |
| `cam2pixel(cam_coords_src, dst_proj_src, eps=1e-12)` | Dense camera coordinates `(B,H,W,3)` plus projection `(B,4,4)` | Returns dense pixel coordinates `(B,H,W,2)`. |
| `pixel2cam(depth, intrinsics_inv, pixel_coords)` | `depth: (B,1,H,W)`, inverse intrinsics `(B,4,4)`, pixel coords `(B,H,W,3)` | Returns camera coordinates `(B,H,W,3)`. |
| `solve_pnp_dlt(world_points, img_points, intrinsics, weights=None, svd_eps=1e-4)` | `world_points: (B,N,3)`, `img_points: (B,N,2)`, `intrinsics: (B,3,3)`, `N>=6` | Returns world→camera extrinsics `(B,3,4)`. Requires float32/float64 and non-collinear, non-coplanar 3D points. |
| `undistort_image`, `undistort_points`, `distort_points`, `tilt_projection` | Pinhole/distortion parameters | Use for camera calibration and lens distortion correction. |

`PinholeCamera` uses 4x4 intrinsic and extrinsic matrices. Standalone projection
functions use 3x3 intrinsics and broadcast over point dimensions; repeat or
unsqueeze intrinsics to match point batches when broadcasting is ambiguous.

## Epipolar, pose, and triangulation

| API | Primary inputs | Output / notes |
|---|---|---|
| `find_fundamental(points1, points2, weights=None, method="8POINT")` | Correspondences `(B,N,2)`, `N>=8` for 8-point or `N>=7` for 7-point | Returns `(B,3*m,3)`; 7-point can return multiple candidates. |
| `find_essential(points1, points2, weights=None)` | Normalized correspondences `(B,N,2)`, `N>=5` | Returns all 5-point candidates `(B,10,3,3)`. Pick with an error metric or motion disambiguation. |
| `essential_from_fundamental`, `fundamental_from_essential`, `essential_from_Rt`, `fundamental_from_projections` | Convert between camera models and epipolar matrices | Keep intrinsics and projection matrices realistic and well-conditioned. |
| `decompose_essential_matrix`, `motion_from_essential`, `motion_from_essential_choose_solution`, `relative_camera_motion` | Pose decomposition and solution selection | Use positive-depth/cheirality checks to pick a valid solution. |
| `compute_correspond_epilines`, `sampson_epipolar_distance`, `symmetrical_epipolar_distance` | Epipolar diagnostics | Distances are useful for candidate ranking and inlier checks. |
| `triangulate_points(P1, P2, points1, points2, solver="dlt")` | Projection matrices and corresponding 2D points | Returns 3D points; prefer well-spaced views and float64 for sensitive scenes. |

Many epipolar algorithms use SVD internally. Kornia casts where needed for
stability, but ill-conditioned points, huge coordinates, or TF32 CUDA matmuls
can still dominate error.

## Depth, stereo, and point clouds

| API | Primary inputs | Output / notes |
|---|---|---|
| `depth_from_disparity(disparity, baseline, focal)` | Disparity, camera baseline, focal length | Converts disparity to depth. Guard near-zero disparity. |
| `depth_to_3d(depth, camera_matrix, normalize_points=False)` | `depth: (B,1,H,W)`, `camera_matrix: (B,3,3)` | Returns point cloud image `(B,3,H,W)`. |
| `depth_to_3d_v2(depth, camera_matrix, normalize_points=False, xyz_grid=None)` | `depth: (*,H,W)`, `camera_matrix: (*,3,3)` | Returns `(*,H,W,3)`; avoids some meshgrid overhead. |
| `unproject_meshgrid(height, width, camera_matrix, normalize_points=False, device=None, dtype=None)` | Camera intrinsics and image size | Precompute rays for repeated depth unprojection. |
| `depth_to_normals(depth, camera_matrix, normalize_points=False)` | `depth: (B,1,H,W)` | Returns normal map `(B,3,H,W)`. |
| `warp_frame_depth(image_src, depth_dst, src_trans_dst, camera_matrix, normalize_points=False)` | Source image, destination depth, destination→source transform, intrinsics | Warps source into destination geometry; depth must be positive and valid. |
| `StereoCamera(left_camera_matrix, right_camera_matrix)` and `reproject_disparity_to_3D` | Rectified stereo projection matrices or disparity/Q matrix | Convert disparity to 3D points in a rectified stereo setup. |
| `save_pointcloud_ply`, `load_pointcloud_ply`, binary variants | Point tensors and user-supplied PLY file paths | Use for simple point-cloud interchange; validate shape and file permissions. |

## Lie groups and rotation representations

| API | Use |
|---|---|
| `So2`, `So3`, `Se2`, `Se3` | Group elements for 2D/3D rotation and rigid transforms. |
| `exp`, `log`, `inverse`, `matrix`, `adjoint`, `hat`, `vee` | Move between tangent vectors, matrices, and group operations. |
| `Quaternion`, `Vector2`, `Vector3` helpers | Typed wrappers used by Lie group classes. |
| `axis_angle_to_rotation_matrix`, `rotation_matrix_to_quaternion`, `quaternion_to_rotation_matrix`, `Rt_to_matrix4x4` | Conversion utilities when interoperating with plain tensors. |

Use Lie group APIs when state lives on a manifold and repeated composition or
inverse operations must preserve group structure. Use plain tensor transforms
for simple one-off point/image warps.

## Tracking

`kornia.tracking.HomographyTracker` estimates and tracks a planar target across
frames. It stores a target image, cached matcher representations, a previous
homography, keypoint counts, and inlier counts. The default constructor builds
feature matchers and a RANSAC estimator; default feature matchers can involve
pretrained models or heavyweight feature code, so do not instantiate the default
tracker in no-download or minimal-runtime checks. Provide explicit matchers and
RANSAC modules when downloads and caches are acceptable.

Important methods:

- `set_target(target)`: cache a new reference image and any matcher features.
- `reset_tracking()`: clear `previous_homography`.
- `match_initial(x)`: estimate target-to-frame homography with initial matcher.
- `track_next_frame(x)`: prewarp by previous homography, then match and refine.
- `forward(x)`: calls `match_initial` first, then `track_next_frame` on later frames.

