---
name: geometry-vision
description: "Use Kornia geometry and tracking for warps, cameras, epipolar
  vision, depth, registration, point clouds, and coordinate conventions."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Kornia Geometry Vision

Use this sub-skill when a task mentions Kornia 2D/3D geometry, image warping,
resizing, homographies, registration, camera projection/unprojection,
calibration, PnP, epipolar pose, triangulation, depth, point clouds, Lie groups,
or homography tracking.

## Read first

- For exact function families and stable call shapes, read
  [references/api-reference.md](references/api-reference.md).
- For the common off-by-one, axis-order, and matrix-direction traps, read
  [references/coordinate-conventions.md](references/coordinate-conventions.md).
- For task recipes, read [references/workflows.md](references/workflows.md).
- For failure diagnosis, read
  [references/troubleshooting.md](references/troubleshooting.md).
- To verify a local Kornia runtime without downloads, run
  [scripts/geometry_smoke.py](scripts/geometry_smoke.py).

## Fast routing

Choose this sub-skill for:

- `resize`, `rescale`, `warp_affine`, `warp_perspective`, `homography_warp`,
  `HomographyWarper`, `ImageRegistrator`, and geometric crop/rotate/scale/shear.
- `get_perspective_transform`, `get_rotation_matrix2d`, homography estimation,
  RANSAC geometry models, and spatial point transforms.
- `PinholeCamera`, camera intrinsics/extrinsics, `project_points`,
  `unproject_points`, `cam2pixel`, `pixel2cam`, stereo, PnP, distortion,
  epipolar matrices, relative pose, and triangulation.
- `depth_to_3d`, `depth_to_normals`, `warp_frame_depth`, disparity/depth
  conversion, point-cloud PLY I/O, and `So2`/`So3`/`Se2`/`Se3` Lie groups.
- `kornia.tracking.HomographyTracker` behavior and state transitions.

## Common workflows

- Resize or warp an image first, then compare the result with the expected geometry in the same coordinate system.
- When a user gives matched points, confirm whether they are pixel points or normalized camera points before solving anything.
- Use float64 for gradient-check or solver-sensitive work; float32 is the usual runtime default.
- Treat tracking and registration as geometry problems, not augmentation problems.

## Pitfalls

- Many geometry bugs are just `(h, w)` versus `(w, h)` or source-to-destination versus destination-to-source confusion.
- `align_corners` affects both resize and warp behavior; do not leave it implicit when reproducing a result.
- Near-zero depth, degenerate point sets, or mixed dtypes can make a correct algorithm look broken.

## Quick validation habits

- Test a non-square image and at least one known transform before trusting a warp or registration result.
- Check whether the point coordinates are pixel-space or normalized camera-space before solving.
- Use `float64` for solver-sensitive checks and `float32` for ordinary runtime warps.
- Keep every matrix and point tensor on the same device as the image tensor.

Route away when the main problem is not geometry:

- Random augmentation containers, `AugmentationSequential`, masks/boxes/keypoint
  synchronization: [augmentation-pipelines](../augmentation-pipelines/SKILL.md).
- Feature detection, learned matchers, descriptor matching, LoFTR/LightGlue
  outputs before geometry estimation: [features-and-matching](../features-and-matching/SKILL.md).
- Loss or metric choice for training/evaluation: [losses-and-metrics](../losses-and-metrics/SKILL.md).

## Operating rules

1. Keep image data as PyTorch tensors, usually `B,C,H,W`; keep all matrices and
   point tensors on the same device and dtype as the image or point data.
2. Treat image sizes passed to Kornia geometry as `(height, width)`, not OpenCV's
   `(width, height)` convention.
3. Treat pixel points as `(x, y)` with origin at the top-left; `x` indexes width
   and `y` indexes height.
4. Pass `align_corners` explicitly when combining resize, grid sampling,
   homography warping, augmentation matrices, or external geometry references.
5. Avoid half precision for solvers, camera/epipolar math, SVD-heavy paths, and
   degenerate geometry; prefer `float32` for ordinary warps and `float64` for
   precision-sensitive estimation or gradient checks.
6. Do not trigger pretrained-model downloads by default. For tracking, inject
   already-prepared matchers if model weights are acceptable; otherwise use
   deterministic low-level homography or RANSAC APIs.
