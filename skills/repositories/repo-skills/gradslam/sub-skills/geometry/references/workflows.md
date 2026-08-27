# Geometry workflows

These workflows are CPU-safe patterns built from deterministic tensors. They
assume `torch` is available and use no datasets, network access, display, or
GPU. Keep the frame convention and tensor layout explicit in the caller.

## 1. Project a camera point and round-trip through depth

For a pinhole camera represented by a 4x4 matrix `P` and a 3x3 inverse
intrinsics matrix `K_inv`:

```python
import torch
from gradslam.geometry import inverse_intrinsics, project_points, unproject_points

K = torch.eye(3, dtype=torch.float32)
K[0, 0], K[1, 1] = 100.0, 100.0
K[0, 2], K[1, 2] = 32.0, 24.0
K_inv = inverse_intrinsics(K)

cam = torch.tensor([[0.0, 0.0, 2.0], [0.5, -0.25, 4.0]])
P = torch.eye(4, dtype=cam.dtype)
P[:3, :3] = K
pixels = project_points(cam, P)
recovered = unproject_points(pixels, K_inv, cam[:, 2])
assert torch.allclose(recovered, cam, atol=1e-5)
```

`project_points` accepts `(N,3)`, `(N,4)`, `(B,N,3)`, or `(B,N,4)` patterns
with either one `(4,4)` matrix or a matching `(B,4,4)` matrix. For a batched
matrix, make the matrix batch dimension agree rather than expecting arbitrary
broadcasting. `unproject_points` follows the same batch pattern, but requires
`depths.shape == pixels.shape[:-1]`.

For a depth image, make the pixel grid's final dimension 2 or 3 and make the
depth tensor exactly the grid shape without that final coordinate. Use a
3x3 inverse intrinsics matrix for `unproject_points`; do not pass a 4x4
RGB-D structure intrinsics tensor without first selecting the top-left 3x3
camera block.

## 2. Homogeneous normalization with an explicit infinity policy

```python
import torch
from gradslam.geometry import homogenize_points, unhomogenize_points

xy = torch.tensor([[2.0, 4.0], [1.0, -3.0]])
h = homogenize_points(xy)
assert h.shape == (2, 3) and torch.equal(h[:, -1], torch.ones(2))

# The zero-weight row is returned with scale one by the implementation.
h2 = torch.tensor([[4.0, 2.0, 2.0], [7.0, 8.0, 0.0]])
xy2 = unhomogenize_points(h2, eps=1e-6)
assert torch.allclose(xy2[0], torch.tensor([2.0, 4.0]))
assert torch.allclose(xy2[1], torch.tensor([7.0, 8.0]))
```

Use `eps` to choose when a weight is considered too small. This is a finite
fallback, not a validity mask. If points with invalid depth must be excluded,
create and apply an explicit mask outside the helper.

## 3. Normalize image coordinates and create a grid

```python
import torch
from gradslam.geometry.geometryutils import (
    create_meshgrid,
    normalize_pixel_coords,
    unnormalize_pixel_coords,
)

height, width = 6, 8
grid = create_meshgrid(height, width, normalized_coords=False)
# grid is (1, H, W, 2); its first coordinate follows height, second width.
normalized = normalize_pixel_coords(grid, height, width)
restored = unnormalize_pixel_coords(normalized, height, width)
```

The intended endpoint convention is `0..height-1` and `0..width-1` to
`-1..1`. Check the current implementation when non-square images matter: both
normalization helpers currently index the first factor in their arithmetic.
Use `create_meshgrid(..., normalized_coords=True)` when a `grid_sample`-style
normalized grid is the desired input and no pixel-to-normalized conversion is
needed.

## 4. Apply, compose, and compare frame transforms

```python
import torch
from gradslam.geometry.geometryutils import (
    compose_transforms_3d,
    inverse_transfom_3d,
    relative_transformation,
    transform_normals,
    transform_pointcloud,
    transform_pts_3d,
)

T_ab = torch.eye(4)
T_ab[:3, 3] = torch.tensor([1.0, 0.0, 0.0])
points_b = torch.tensor([[0.0, 2.0, 3.0], [1.0, 2.0, 3.0]])
points_a = transform_pts_3d(points_b, T_ab)
points_a_legacy = transform_pointcloud(points_b, T_ab)
assert torch.allclose(points_a, points_a_legacy)

T_bc = torch.eye(4)
T_bc[:3, 3] = torch.tensor([0.0, 2.0, 0.0])
T_ac = compose_transforms_3d(T_ab, T_bc)
assert torch.allclose(transform_pts_3d(points_b, T_ac),
                       transform_pts_3d(transform_pts_3d(points_b, T_bc), T_ab))

T_ba = inverse_transfom_3d(T_ab)
assert torch.allclose(compose_transforms_3d(T_ab, T_ba), torch.eye(4))
T_rel = relative_transformation(T_ab, T_ac)
```

Read `T_ab` as coordinates from `b` into `a`. `relative_transformation(T_ab,
T_ac)` computes a transform from the `b` pose to the `c` pose when both are
expressed against the same reference. Use `orthogonal_rotations=False` for
general invertible matrices; use `True` only when the 3x3 blocks are truly
orthogonal.

For normals, use:

```python
normals_a = transform_normals(normals_b, T_ab)
```

This applies only `T_ab[:3,:3]`; translation is intentionally ignored. The
helper is for rigid rotations. A caller handling a general scale/shear must
choose the mathematically appropriate inverse-transpose operation itself.

## 5. Quaternion to rotation and differentiable point transform

```python
import torch
from gradslam.geometry.geometryutils import (
    normalize_quaternion,
    quaternion_to_axisangle,
    quaternion_to_rotation_matrix,
    transform_pointcloud,
)

q = torch.tensor([0.0, 0.0, 0.0, 1.0], requires_grad=True)
q_unit = normalize_quaternion(q)
axisangle = quaternion_to_axisangle(q_unit)
R = quaternion_to_rotation_matrix(q_unit)
T = torch.eye(4, dtype=q.dtype)
T[:3, :3] = R
points = torch.tensor([[1.0, 2.0, 3.0]], dtype=q.dtype)
loss = transform_pointcloud(points, T).square().sum()
loss.backward()
assert q.grad is not None and torch.isfinite(q.grad).all()
```

Quaternion order is `(x,y,z,w)`, not `(w,x,y,z)`. The conversion normalizes
its input before building `R`; `normalize_quaternion` uses an epsilon of
`1e-12` by default. The axis-angle result has final dimension 3. Keep
quaternions away from the zero vector in optimization or define a policy for
that degenerate input.

## 6. SE(3) optimization update

```python
import torch
from gradslam.geometry.se3utils import se3_exp
from gradslam.geometry.geometryutils import transform_pointcloud

xi = torch.tensor([0.1, 0.0, 0.0, 0.0, 0.0, 0.05], requires_grad=True)
update = se3_exp(xi)
cloud = torch.tensor([[0.0, 0.0, 1.0], [0.2, 0.0, 1.0]])
objective = transform_pointcloud(cloud, update).sum()
objective.backward()
assert xi.grad is not None and torch.isfinite(xi.grad).all()
```

`xi[:3]` is translation `v` and `xi[3:]` is rotation `omega`. `se3_exp`
returns a single `(4,4)` transform. The implementation branches at a small
rotation norm, so evaluate finite gradients both near zero and at ordinary
nonzero rotations if this is used in a solver. The odometry code uses this
direct module import for residual updates.

## 7. Batch and differentiability checks

For `(B,N,D)` points and `(B,D+1,D+1)` transforms, use the direct
`transform_pts_nd_KF` helper:

```python
from gradslam.geometry.geometryutils import transform_pts_nd_KF
out = transform_pts_nd_KF(points_batched, transforms_batched)
assert out.shape == points_batched.shape
```

Its batch size must match exactly. For public projection, compare a single
matrix `(4,4)` against a per-batch matrix `(B,4,4)` deliberately; do not infer
that a `(1,4,4)` matrix broadcasts to every arbitrary point rank.

For a gradient-sensitive path:

1. create inputs with `dtype=torch.float64` when numerical diagnosis matters;
2. set `requires_grad=True` only on the intended optimization tensor;
3. run the geometry operation without converting to Python/NumPy values;
4. backpropagate a finite scalar loss;
5. assert `grad is not None` and `torch.isfinite(grad).all()`;
6. check the zero-depth/zero-weight branch separately because its guarded
   division is piecewise.

Assignment-based output assembly appears in several legacy helpers. Avoid
in-place writes to tensors that are leaf variables requiring gradients; build
transforms from differentiable blocks or use the helper as an output boundary.
