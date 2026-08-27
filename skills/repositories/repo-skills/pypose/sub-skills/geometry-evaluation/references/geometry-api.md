# Geometry and point-cloud API

## Coordinate and shape contract

The functions in `pypose/function/geometry.py` use the final dimensions for
points and coordinates:

| API | Input shape | Output shape | Contract |
| --- | --- | --- | --- |
| `cart2homo` | `(..., D)` | `(..., D+1)` | Appends a one in the final coordinate. |
| `homo2cart` | `(..., D+1)` | `(..., D)` | Divides all but the final coordinate by the final homogeneous value. |
| `point2pixel` | points `(..., N, 3)`, `K (..., 3, 3)` | `(..., N, 2)` | Projects 3-D points through intrinsics. |
| `pixel2point` | pixels `(..., N, 2)`, depth `(..., N)`, `K (..., 3, 3)` | `(..., N, 3)` | Back-projects into the camera frame. |
| `reprojerr` | points `(..., N, 3)`, pixels `(..., N, 2)`, `K` | `(..., N, 2)` or `(..., N)` | Residual from `point2pixel`; reduction is explicit. |

`cart2homo` preserves the input dtype/device. `homo2cart` clamps the magnitude
of the final denominator to `torch.finfo(dtype).tiny` and preserves its sign;
zero and near-zero homogeneous coordinates therefore need explicit handling by
the caller if they are not meaningful projective points.

The standard pinhole equations used by `pixel2point` are:

```text
z = depth
x = (u - cx) * z / fx
y = (v - cy) * z / fy
```

Only `fx`, `fy`, `cx`, and `cy` are read from `K`; `fx` and `fy` cannot be zero.
Depth is with respect to the sensor plane and the returned point is in the
camera coordinate frame. Negative or zero depth is not filtered by the helper;
reject it when the application requires points in front of the camera.

`point2pixel` treats points as camera-frame when `extrinsics=None`. When an
`extrinsics` LieTensor is supplied, points are treated as world-frame and PyPose
applies that pose to each point before multiplying by `K`. The source checks for
an SE3-sized LieTensor (`shape[-1] == 7`) and broadcasts batch dimensions. Do
not infer a camera-to-world/world-to-camera convention from a variable name:
state which direction the supplied pose maps and validate one known point. A
common reprojection pipeline in the repository back-projects pixels to camera
points, then supplies the inverse relative pose to `point2pixel` when projecting
into the second view (`examples/module/reprojpgo`).

## Reprojection residuals

```python
residual = pp.reprojerr(points, observed_uv, K, extrinsics=None,
                        reduction='none')
```

Allowed reductions are:

- `'none'`: signed `(u, v)` residual, shape `(..., N, 2)`;
- `'norm'`: Euclidean norm per point, shape `(..., N)`;
- `'sum'`: the implementation's signed sum of the two residual components per
  point, shape `(..., N)`.

Use `'norm'` for the usual nonnegative pixel-distance objective. `'sum'` is not
an L1 norm in this implementation because it does not apply `abs`; preserve that
fact when matching an existing experiment. Shape/broadcast checks happen before
projection, and invalid reduction names raise an assertion.

## Point-set estimation

`svdtf(source, target)` estimates an SE3 transform from associated points with
shape `(..., N, 3)`. It centers both sets, computes the cross-covariance, uses
SVD, corrects an improper rotation, and returns a PyPose `SE3` LieTensor. The
point order is correspondence order: it is not a correspondence search and is
not ICP. Require equal `N` and enough nondegenerate geometry; collinear or very
small/degenerate sets can make the rotation underdetermined.

`svdstf(source, target, with_scale=True)` uses Umeyama alignment and returns a
`Sim3` LieTensor. `with_scale=False` fixes the scale to one. It also requires
`(..., N, 3)` and equal point counts. Use this for an explicit similarity
alignment, not as a replacement for the excluded robotics/ICP modules. Compare
`estimated @ source` with `target` or inspect its matrix action rather than
comparing quaternion storage directly.

## Nearest-neighbor and filtering helpers

- `knn(ref, nbr, k=1, ord=2, dim=-1, largest=False, sorted=True)` returns a
  `torch.topk` named tuple `(values, indices)`. Distances are computed between
  every reference point and neighbor point; values and indices have shape
  `(..., N_ref, k)`. `largest=False` selects nearest points. The `dim` argument
  is the coordinate/distance axis used by `torch.linalg.norm` and `topk`, so keep
  the default for ordinary `(..., N, D)` point sets.
- `random_filter(points, num)` samples `num` points along the penultimate axis
  from `(..., N, D)` and returns `(..., num, D)`. It is stochastic, requires
  `num <= N`, and does not promise order. Seed the torch RNG in a test if
  reproducibility is needed.
- `voxel_filter(points, voxel, random=False)` accepts only a 2-D `(N, D)` point
  cloud. The first `len(voxel)` values define voxel coordinates; `D` may be
  larger for attached features. Voxel bins are based on the cloud minimum and
  integer division by each nonzero voxel size. The default representative is the
  centroid of all `D` channels. `random=True` selects one input point per voxel.
  Output count is the number of occupied voxels and order follows PyTorch's
  `unique` behavior, not a semantic spatial ordering.
- `nbr_filter(points, nbr, radius, pdim=None, ord=2, return_mask=False)` accepts
  only `(N, D)`. It counts *other* points within `radius` using the first `pdim`
  coordinates (all `D` by default), keeps points with count `>= nbr`, and can
  return the `(filtered_points, mask)` pair. Variable output counts mean it does
  not support batched point clouds.
- `knn_filter(points, k, pdim=None, radius=None, ord=2)` averages each point and
  its `k` nearest neighbors. Without `radius`, batched `(..., N, D)` input is
  supported and output retains the shape. With `radius`, input must be 2-D; a
  point is retained only if at least `k` other points are within the radius, and
  the variable-length result is then averaged. `pdim` restricts distance
  computation but all feature channels are averaged.

These filters are reduction/preprocessing utilities. They do not preserve input
ordering in a general contract, do not solve registration, and should not be
silently used where exact correspondences are required.

## Comparison assertions

`pypose.testing.assert_close(actual, expected, ...)` is a wrapper around
`torch.testing.assert_close`. When both operands are LieTensors it checks the
logarithm of `actual.Inv() @ expected` against zero, which is the appropriate
representation-independent comparison. For tensors it delegates directly. Use
explicit `rtol` and `atol` for float64 geometry, and compare matrix action or
LieTensor closeness rather than raw quaternion signs.

## Evidence

- `pypose/function/geometry.py`
- `docs/source/convert.rst`
- `docs/source/functions.rst`
- `tests/function/test_downsample.py`
- `examples/module/reprojpgo/dataset.py`
- `pypose/testing/comparison.py`
