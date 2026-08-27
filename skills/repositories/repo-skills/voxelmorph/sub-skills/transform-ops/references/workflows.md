# Transform operation workflows

The examples below assume `torch`, `numpy`, and `voxelmorph` are importable. They use synthetic tensors only and do not require datasets, checkpoints, downloads, or repository-local files.

## 1. Build an affine, convert it to displacement, then warp an image

Use the top-level API when you need affine construction or shape-agnostic image layouts.

```python
import torch
import voxelmorph as vxm

# Channel-only 2D image: (C, H, W)
image = torch.zeros(1, 9, 11)
image[0, 4, 5] = 1.0

# Translation, rotation, scale, and shear compose as T @ R @ Z @ S.
affine = vxm.params_to_affine(
    ndim=2,
    translation=(1.0, 0.0),
    rotation=0.0,
    scale=1.0,
)

disp = vxm.affine_to_disp(affine, shape=image.shape[1:], origin_at_center=True)
warped = vxm.spatial_transform(image, disp, non_spatial_dims=(0,), mode="linear")
assert warped.shape == image.shape
```

Notes:

- Dense fields are `(ndim, *spatial)` for unbatched data.
- `spatial_transform()` performs backward sampling: positive row displacement samples from lower rows and makes visible content move upward.
- For label images, prefer `mode="nearest"`.

## 2. Use neural-network layouts directly

For tensors already shaped `(B, C, *spatial)`, use `voxelmorph.nn.functional` or `SpatialTransformer`.

```python
import torch
import voxelmorph as vxm
import voxelmorph.nn.functional as vxf

moving = torch.randn(2, 1, 16, 20)      # (B, C, H, W)
field = torch.zeros(2, 2, 16, 20)       # (B, ndim, H, W)
field[:, 0] = 0.25                      # row-axis displacement in voxel units

warped_fn = vxf.spatial_transform(moving, field, method="linear")
warped_mod = vxm.nn.modules.SpatialTransformer()(moving, field)
assert warped_fn.shape == moving.shape
assert warped_mod.shape == moving.shape
```

When using a channel-only image `(C, *spatial)` or a pure spatial tensor `(*spatial)`, use the top-level `vxm.spatial_transform()` and set `non_spatial_dims` explicitly.

## 3. Convert displacement to absolute coordinates and normalized coordinates

```python
import torch
import voxelmorph as vxm

field = torch.randn(2, 8, 12) * 0.05
absolute = vxm.disp_to_trf(field)
round_trip = vxm.trf_to_disp(absolute)
assert torch.allclose(field, round_trip, atol=1e-5)

coords = vxm.disp_to_coords(field)
assert coords.shape == field.shape
assert coords.min() >= -1.5 and coords.max() <= 1.5  # small field around normalized grid

try:
    vxm.coords_to_disp(coords)
except NotImplementedError:
    pass  # expected in current VoxelMorph
```

`disp_to_coords()` returns normalized coordinates in channels-first VoxelMorph layout. Do not feed that tensor directly to `torch.nn.functional.grid_sample()` unless you also move the coordinate axis to the end and reverse coordinate order as VoxelMorph does internally.

## 4. Integrate a stationary velocity field

Functional form:

```python
import torch
import voxelmorph as vxm

velocity = torch.randn(1, 2, 32, 32) * 0.1  # (B, ndim, H, W)
disp = vxm.integrate_disp(velocity, steps=5, non_spatial_dims=(0,))
assert disp.shape == velocity.shape
```

Module form:

```python
import voxelmorph as vxm

integrator = vxm.nn.modules.IntegrateVelocityField(steps=5)
disp_from_module = integrator(velocity)
assert disp_from_module.shape == velocity.shape
```

Use small to moderate `steps` for tests and interactive work. Runtime grows with the number of squaring iterations.

## 5. Resize displacement fields without losing physical meaning

Displacement magnitudes must scale with the spatial resize factor. The top-level helper handles scalar, per-axis, and target-shape resizing.

```python
import torch
import voxelmorph as vxm

field = torch.ones(2, 8, 10)  # constant one-voxel shift in both axes
larger = vxm.resize_disp(field, scale_factor=(2.0, 3.0), mode="linear")
assert larger.shape == (2, 16, 30)
assert torch.isclose(larger[0, 0, 0], torch.tensor(2.0))
assert torch.isclose(larger[1, 0, 0], torch.tensor(3.0))

batched = field.unsqueeze(0).repeat(4, 1, 1, 1)  # (B, ndim, H, W)
smaller = vxm.resize_disp(batched, shape=(4, 5), non_spatial_dims=(0,))
assert smaller.shape == (4, 2, 4, 5)
```

Module wrapper for scalar scale factors:

```python
resizer = vxm.nn.modules.ResizeDisplacementField(scale_factor=2.0, interpolation_mode="linear")
resized = resizer(torch.ones(1, 2, 8, 10))
assert resized.shape == (1, 2, 16, 20)
```

Prefer `vxm.resize_disp(..., mode="nearest")` for nearest-neighbor displacement resizing; the module wrapper needs `align_corners=None` for nearest mode.

## 6. Compose transforms in the correct order

`compose([A, B, C])` represents `A(B(C(x)))`: the rightmost transform acts first.

```python
import torch
import voxelmorph as vxm

translate = torch.tensor([[1., 0., 5.], [0., 1., 3.]])
scale = torch.tensor([[2., 0., 0.], [0., 2., 0.]])
combined_affine = vxm.compose([translate, scale])
assert combined_affine.shape == (2, 3)

field_a = torch.zeros(2, 16, 16)
field_b = torch.zeros(2, 16, 16)
field_a[0] = 1.0
field_b[1] = 2.0
combined_field = vxm.compose([field_a, field_b])
assert combined_field.shape == field_a.shape
```

For mixed affine and batched displacement fields, avoid the current shape-inference pitfall by composing per sample:

```python
batched_field = torch.zeros(3, 2, 16, 16)
batched_affine = torch.eye(3).repeat(3, 1, 1)
per_sample = [vxm.compose([batched_affine[i], batched_field[i]]) for i in range(3)]
combined = torch.stack(per_sample, dim=0)
assert combined.shape == batched_field.shape
```

## 7. Generate deterministic synthetic transforms

Seed both NumPy and PyTorch because VoxelMorph random transform helpers use NumPy sampling and PyTorch tensors.

```python
import numpy as np
import torch
import voxelmorph as vxm

np.random.seed(17)
torch.manual_seed(17)

affine = vxm.random_affine(
    ndim=2,
    max_translation=2.0,
    max_rotation=5.0,
    max_scaling=1.1,
)
assert affine.shape == (3, 3)

# Affine-only random_transform is fast and deterministic with probabilities fixed.
trf = vxm.random_transform(
    shape=(16, 20),
    affine_probability=1.0,
    warp_probability=0.0,
    max_translation=1.0,
    max_rotation=0.0,
    max_scaling=1.0,
    sampling=False,
)
assert trf.shape == (2, 16, 20)
```

For nonlinear synthetic warps, enable `warp_probability`, choose small spatial shapes for smoke tests, and keep `warp_integrations` modest.

## 8. Run the bundled smoke script

From this sub-skill directory:

```bash
python scripts/transform_ops_smoke.py --help
python scripts/transform_ops_smoke.py --dim 2
```

The script checks core affine, displacement, warping, integration, resizing, composition, random-transform, and module-wrapper behavior on tiny synthetic tensors.
