---
name: geometry
description: "Use GradSLAM's tensor geometry utilities for camera projection,
  homogeneous coordinates, pixel grids, rigid transforms, quaternions, SE(3)
  exponential maps, and point or normal frame changes."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Geometry

Use this skill when a GradSLAM operation needs camera-coordinate projection,
depth unprojection, intrinsics handling, pixel-grid conversion, rigid-body
transforms, quaternion rotation, or Lie-group SE(3) updates. The functions are
PyTorch tensor operations: preserve the input dtype/device and keep tensors in
the expected trailing-dimension layout.

Read the focused contracts in [api-reference.md](references/api-reference.md)
before selecting a function. Use [workflows.md](references/workflows.md) for
projection/unprojection and transform pipelines, and
[troubleshooting.md](references/troubleshooting.md) when a shape, frame, dtype,
or gradient check fails.

## Module and export boundary

`gradslam.geometry` exports the projective functions from `projutils`:

- `homogenize_points`
- `unhomogenize_points`
- `project_points`
- `unproject_points`
- `inverse_intrinsics`

The package root also re-exports these projective names. Do not assume that
other geometry helpers are attributes of `gradslam.geometry`; import them from
their implementation modules explicitly:

```python
from gradslam.geometry import project_points, unproject_points
from gradslam.geometry.geometryutils import (
    cam2pixel,
    compose_transforms_3d,
    create_meshgrid,
    relative_transformation,
    transform_normals,
    transform_pointcloud,
    transform_pts_3d,
)
from gradslam.geometry.se3utils import se3_exp, so3_exp
```

`se3_exp` is specifically a direct `se3utils` import. The same is true of
`so3_hat`, `se3_hat`, and `so3_exp`. `geometryutils` also contains a second
implementation of homogeneous conversion plus transform and pixel-grid
helpers; importing from that module is intentional when using those helpers,
not an alternate package-level export.

## Operating rules

1. **Name frames before multiplying.** A transform `t_ab` in
   `transform_pts_3d(pts_b, t_ab)` maps coordinates expressed in frame `b` to
   frame `a`. Matrix composition `compose_transforms_3d(t1, t2)` computes
   `t1 @ t2`, so `t2` is applied first.
2. **Keep points in the last dimension.** Projective points end in 3 or 4,
   pixels in 2 or homogeneous 3, and normals/Euclidean points in 3.
   Batched projective tensors retain all leading dimensions when the batching
   contract is satisfied.
3. **Use true camera intrinsics for unprojection.** `unproject_points` takes
   an inverse 3x3 matrix and a depth tensor with shape exactly equal to the
   pixel tensor without its last coordinate. `inverse_intrinsics` is a fast
   pinhole inverse for the supported 3x3/4x4 layout, not a general matrix
   inverse.
4. **Treat zero denominators deliberately.** Homogeneous weights within
   `eps` are left unscaled by `unhomogenize_points`; projected depth exactly
   equal to zero is divided by one. These guards avoid infinities but do not
   provide a physically meaningful point at infinity.
5. **Do not detach geometry tensors.** The routines are intended to remain in
   the autograd graph. Avoid `.numpy()`, `.item()` in the computational path,
   or in-place edits to leaf tensors requiring gradients.
6. **Use rigid transforms for rigid helpers.** The custom inverse in
   `inverse_transfom_3d` assumes an orthogonal rotation. Use
   `relative_transformation(..., orthogonal_rotations=False)` when the input
   may be a general invertible homogeneous matrix.
7. **Respect implementation quirks.** `quaternion_to_rotation_matrix` expects
   `(x, y, z, w)` and flattens leading batch dimensions beyond one batch axis;
   `normalize_pixel_coords` currently applies the first image-size factor to
   both coordinates. See the API and troubleshooting references rather than
   silently correcting these behaviors in a caller.

## Minimal decision tree

- Euclidean or homogeneous point conversion: use the exported `projutils`
  functions for public camera code; use the `geometryutils` versions only when
  a transform helper in that module is also required.
- 3D camera points to pixels: use `project_points` with a 4x4 projection
  matrix; it accepts `(..., 3)` or `(..., 4)` points.
- Pixels and depth to camera points: use `unproject_points` with a 3x3
  inverse intrinsics matrix and matching depth shape.
- Intrinsics inverse: use `inverse_intrinsics` for the library's pinhole K
  layout, including the 4x4 form used by RGB-D structures.
- Point/normal frame change: use `transform_pts_3d` or
  `transform_pointcloud`; rotate normals without translation using
  `transform_normals`.
- Relative poses: use `relative_transformation` for batched or general
  invertible poses; use `relative_transform_3d` for matching rigid tensors.
- Optimization update: use `se3_exp` on a six-vector ordered as
  `(translation, rotation)`; it returns a 4x4 transform.

The bundled CPU smoke check is
`scripts/geometry_smoke.py`. It uses only deterministic in-memory tensors and
has no network, display, dataset, or GPU path.
