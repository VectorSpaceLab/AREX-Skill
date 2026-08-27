# Coordinate Conventions

Most Kornia geometry mistakes are convention mistakes. Check this page before
changing tolerances or rewriting a transform.

## Image tensor and size ordering

- Images and image-like tensors are normally channel-first: `B,C,H,W` for
  batches and `C,H,W` for single images. Some lower-level utilities also accept
  `H,W` or arbitrary leading dimensions ending in `H,W`.
- Kornia geometry sizes are ordered `(height, width)`. Examples: `dsize=(h,w)`,
  `resize(input, (h,w))`, 2D warp output `(B,C,h,w)`, and 3D volume output
  `(B,C,d,h,w)`.
- OpenCV often asks for `(width, height)`. Convert explicitly when porting:
  `opencv_size=(w,h)` becomes `kornia_dsize=(h,w)`.

## Pixel point ordering

- Pixel coordinate points are `(x, y)`, not `(row, col)`.
- `x` moves across width/columns; `y` moves down height/rows.
- The pixel origin is the top-left image pixel center.
- A rotation center for `get_rotation_matrix2d` is also `(x, y)`. For an image
  with shape `B,C,H,W`, a center at the middle is commonly
  `[(W - 1) / 2, (H - 1) / 2]` when using corner-aligned warps.

## Matrix direction by API

### `warp_affine` and `warp_perspective`

`warp_affine(src, M, dsize, ...)` and `warp_perspective(src, M, dsize, ...)`
accept source→destination pixel transforms.

Conceptually, `M` maps source pixel points to destination pixel points:

```python
dst_points = transform_points(M, src_points)
```

During sampling, Kornia internally uses the inverse mapping so each destination
pixel samples from the source. This is why a positive translation in `M` moves
visible image content down/right while the new top/left area is filled by the
padding policy.

### `get_perspective_transform`

`get_perspective_transform(points_src, points_dst)` returns the same kind of
source→destination pixel homography expected by `warp_perspective`.

Use non-degenerate quadrilateral points ordered consistently, e.g. top-left,
top-right, bottom-right, bottom-left:

```python
points_src = torch.tensor([[[0., 0.], [W - 1., 0.], [W - 1., H - 1.], [0., H - 1.]]])
```

### `homography_warp`

`homography_warp` has a different default contract. With
`normalized_homography=True` (the default), it expects a destination→source
homography in normalized grid coordinates. This is convenient when operating
inside `HomographyWarper`/registration code, but it is not the same input
convention as `warp_perspective`.

If you have a source→destination pixel homography and want behavior like
`warp_perspective`, call:

```python
out = homography_warp(img, H_src_to_dst, (h, w), normalized_homography=False)
```

When mixing pixel and normalized homographies manually, use the normalization
helpers and verify with an asymmetric image size; square inputs can hide swapped
size and inverse-order bugs.

## `align_corners` defaults

Kornia exposes PyTorch's grid/interpolation convention. Defaults differ by API:

| API family | Default |
|---|---|
| `resize`, `rescale`, `resize_to_be_divisible` | `align_corners=None`, following `torch.nn.functional.interpolate` defaults; for bilinear-like modes this behaves like the modern non-corner-aligned convention. |
| `warp_affine`, `warp_perspective`, `rotate`, `translate`, `scale`, many module wrappers | `align_corners=True` |
| `homography_warp`, `HomographyWarper` normalized path | `align_corners=False` |
| `warp_frame_depth` | uses grid sampling with `align_corners=True` |

Always pass `align_corners` explicitly if outputs are compared numerically,
combined with augmentation matrices, exported, or expected to match another
library.

## Normalized versus pixel coordinates

- Pixel coordinates use image units: `x in [0, W-1]`, `y in [0, H-1]` for pixel
  centers.
- Normalized grid coordinates usually use `[-1, 1]` in the order `(x, y)`.
- Use `normalize_pixel_coordinates` / `denormalize_pixel_coordinates` and
  `normalize_homography` / `denormalize_homography` rather than ad-hoc formulas.
- Make source and destination sizes explicit when normalizing homographies.

## Camera coordinates

- `project_points` takes 3D camera-frame points `(...,3)` and 3x3 intrinsics;
  it returns pixel `(u,v)` coordinates, equivalent to `(x,y)`.
- `unproject_points` takes pixel points, depth `(...,1)`, and intrinsics; it
  returns 3D camera-frame points.
- `PinholeCamera` stores 4x4 intrinsics and 4x4 extrinsics. The extrinsic matrix
  is the world→camera pose used to transform world points into the camera frame.
- Keep focal lengths and principal points realistic. Fully random intrinsics are
  rarely meaningful and often numerically unstable.
- Depth and disparity denominators must be bounded away from zero.

## Batching and broadcasting

- Most solvers are batched. Keep batch dimensions aligned and prefer explicit
  expansion for intrinsics when points have an extra `N` dimension, e.g.
  `K[:, None].expand(-1, N, -1, -1)`.
- Correspondence tensors for epipolar/PnP workflows are generally `(B,N,2)` for
  image points and `(B,N,3)` for world or camera points.
- Transform matrices should live on the same device and dtype as the points or
  images they transform.

