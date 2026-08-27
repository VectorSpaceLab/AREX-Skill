# RGB-D and point-cloud workflows

## Construct a frame sequence

Use PyTorch tensors, not NumPy arrays, at the package boundary:

```python
import torch
from gradslam.structures import RGBDImages

B, L, H, W = 1, 2, 8, 10
colors = torch.zeros(B, L, H, W, 3, dtype=torch.float32)
depths = torch.ones(B, L, H, W, 1, dtype=torch.float32)
K = torch.eye(4).repeat(B, 1, 1)
K[:, 0, 0] = K[:, 1, 1] = 20.0
K[:, 0, 2] = (W - 1) / 2
K[:, 1, 2] = (H - 1) / 2
poses = torch.eye(4).repeat(B, L, 1, 1)
frames = RGBDImages(colors, depths, K[:, None], poses)
```

The usual channels-last layout is `(B,L,H,W,C)`: RGB has `C=3` and depth has
`C=1`. For channels-first, pass `(B,L,C,H,W)` and `channels_first=True`.
The object does not normalize RGB or depth; normalize colors with
`gradslam.datasets.datautils.normalize_image` at the input boundary when
needed. Depth values must already use the units expected by the rest of the
pipeline.

Check `frames.valid_depth_mask`, `frames.vertex_map`, and
`frames.normal_map` before localization. Derived maps are cached. Zero or
negative depth is invalid and produces zero-valued geometry at those pixels.
A missing `poses` argument is valid, but global maps then cannot represent a
true world transform.

## Convert one frame to a cloud

`pointclouds_from_rgbdimages` expects a one-frame slice (`L == 1`):

```python
from gradslam.structures.utils import pointclouds_from_rgbdimages

frame = frames[:, 0]
cloud = pointclouds_from_rgbdimages(
    frame, global_coordinates=True, filter_missing_depths=True
)
print(cloud.points_list[0].shape, cloud.has_normals, cloud.has_colors)
```

Use `filter_missing_depths=False` only when a dense flattened cloud with zero
rows is required. `global_coordinates=False` uses camera coordinates;
`global_coordinates=True` uses poses when present and otherwise has the same
coordinates as the local map.

## Work with ragged point clouds

```python
from gradslam import Pointclouds

cloud = Pointclouds(
    points=[torch.rand(12, 3), torch.rand(7, 3)],
    colors=[torch.rand(12, 3), torch.rand(7, 3)],
)
print(cloud.num_points_per_pointcloud())
cloud2 = cloud.transform(torch.eye(4))
```

Use `points_list` for per-cloud lengths and `points_padded` for batched tensor
operations. `nonpad_mask` identifies real rows in padded storage. Normals and
colors must use the same list-versus-padded representation and point counts.
Use `clone()` before destructive edits and the underscore methods only when
in-place mutation is intentional.

## Device and visualization checks

Keep all operands on one device. `to(device, copy=False)`, `.cpu()`, and
`.cuda()` transfer internal tensors; `.cuda()` requires a CUDA-capable PyTorch
installation and device. For headless validation, call `open3d(index)` or
`plotly(index, as_figure=False)` and inspect the returned object. Do not call
viewer functions or `.show()` in automated jobs.

Run the bundled `scripts/structures_smoke.py` for a tiny CPU fixture. It is a
shape/conversion check, not a replacement for real sensor calibration or
external dataset validation.
