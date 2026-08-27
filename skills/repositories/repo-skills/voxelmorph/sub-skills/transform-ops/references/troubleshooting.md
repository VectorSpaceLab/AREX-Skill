# Transform operation troubleshooting

Use this guide when VoxelMorph transform code fails, produces unexpected motion, or gives inconsistent tensor shapes.

## Common errors and fixes

| Symptom | Likely cause | Fix |
|---|---|---|
| `ModuleNotFoundError: neurite` during import | VoxelMorph's PyTorch transform helpers depend on Neurite for grid generation, interpolation-mode inference, and fractal noise. | Install the base VoxelMorph dependencies in the active Python environment. Confirm `import voxelmorph, neurite, torch` works before debugging transform code. |
| `AssertionError: Provide exactly one of meshgrid or shape` from `affine_to_disp()` | Both `meshgrid` and `shape` were supplied, or neither was supplied. | Pass `shape=(H, W)` or `(D, H, W)` for simple use, or pass a precomputed `(ndim, *spatial)` meshgrid when avoiding repeated grid construction. |
| `affine dim (...D) != meshgrid dim (...D)` | Affine matrix dimensionality does not match the spatial grid, or a batched dense field shape was accidentally used as the spatial shape. | Check affine shape `(N,N+1)` or `(N+1,N+1)` and spatial shape `S`. For batched dense fields `(B,N,*S)`, the spatial shape is `field.shape[2:]`, not `field.shape[1:]`. |
| Output image moves opposite from the sign you expected | VoxelMorph performs backward warping: output samples input at `x + disp(x)`. | To move visible content right/down, use negative displacements along the corresponding axes, or reason in target-to-source sampling coordinates. |
| Warped output loses intensity near boundaries | Default `padding_mode='zeros'` samples zeros outside the image. | Use `padding_mode='border'` for validation or avoid measuring near boundaries. For real workflows, choose the padding mode that matches the desired extrapolation. |
| `coords_to_disp()` raises `NotImplementedError` | The inverse normalized-coordinate-to-displacement function is not implemented in current VoxelMorph. | Keep the original displacement field if it will be needed later. If you have normalized coords, manually invert normalization with careful axis order, or avoid workflows requiring this inverse. |
| `grid_sample` complains about grid rank/last dimension | VoxelMorph's `disp_to_coords()` returns channels-first normalized coordinates, while PyTorch `grid_sample()` expects channels-last grid order. | Prefer `vxm.spatial_transform()` or `vxf.spatial_transform()`. If calling `grid_sample()` directly, move the coordinate axis to the end and reverse from `ij` to PyTorch coordinate order. |
| `spatial_transform()` treats a transform-shaped tensor as affine when it should be dense | Dense 2D fields with shape like `(B, 2, 3)` or compact affine-like trailing dimensions are ambiguous. | Use unambiguous spatial shapes, add explicit batch/channel dimensions, or call lower-level conversion functions first. Avoid tiny dense field shapes that look like affine matrices. |
| `non_spatial_dims` confusion | Top-level functions default to unbatched dense fields, while `voxelmorph.nn.functional` defaults to neural-network layouts. | For image `(C,*S)`, pass `(0,)`; for image `(B,C,*S)`, pass `(0,1)`; for displacement `(B,N,*S)`, pass `(0,)`; for unbatched displacement `(N,*S)`, pass `None`. |
| `ValueError: align_corners option can only be set...` from `ResizeDisplacementField(..., interpolation_mode='nearest')` | The module wrapper passes `align_corners` into `torch.nn.functional.interpolate()`, but nearest mode requires `align_corners=None`. | Prefer `vxm.resize_disp(..., mode='nearest')`, or instantiate `ResizeDisplacementField(..., interpolation_mode='nearest', align_corners=None)`. |
| `compose([])` assertion | Empty transform lists are not defined. | Return identity explicitly in caller code, or call `compose()` only after at least one transform is present. |
| Mixed affine plus batched dense composition fails with a meshgrid/affine dimension assertion | Current composition shape inference can use `(N,*S)` instead of `S` when the current dense transform is batched. | Loop over batch elements, or convert each affine to a dense field with the correct `shape` and then compose dense fields. |
| Random transform tests are not reproducible after `torch.manual_seed()` only | VoxelMorph random helpers use NumPy RNG for affine parameters and transform selection. | Call both `numpy.random.seed(seed)` and `torch.manual_seed(seed)`. |
| CPU works but CUDA errors with device mismatch | Some helper-created tensors or cached meshgrids can remain on a previous device if tensors are moved after module construction. | Keep image, field, affine, and meshgrid tensors on the same device. Recreate `SpatialTransformer` after changing device/dtype with the same spatial shape, or delete the cached `meshgrid` attribute. |
| Label maps become floating or blurred | Linear interpolation is inappropriate for labels and may cast integer tensors to float. | Use `mode='nearest'` / `method='nearest'` for labels and masks. Use linear interpolation only for continuous images or vector fields. |
| Integration is slow or produces unexpectedly large deformations | `steps` controls the number of scaling-and-squaring loops, and large velocities can fold or sample outside the field. | Start with small velocity magnitudes and `steps` around 5 to 7 for tests. Use smaller synthetic tensors for debugging. |

## Axis sanity checks

For a 2D field shaped `(2, H, W)` with `ij` indexing:

- `field[0]` is displacement along the first spatial axis (rows / height).
- `field[1]` is displacement along the second spatial axis (columns / width).
- A positive `field[0]` samples from larger row indices, so visible content moves upward.
- A positive `field[1]` samples from larger column indices, so visible content moves left.

Minimal check:

```python
import torch
import voxelmorph as vxm

image = torch.zeros(1, 8, 16)
image[0, 4, 8] = 1.0
field = torch.zeros(2, 8, 16)
field[0] = 2.0
warped = vxm.spatial_transform(image, field, non_spatial_dims=(0,), mode="nearest")
assert warped[0, 2, 8] > 0.5  # content moved up by two rows
```

## Affine-origin checks

`affine_to_disp(..., origin_at_center=True)` rotates/scales around the image center. With `origin_at_center=False`, the origin is the corner coordinate `0` along each axis. If a rotation or scale appears to pivot around the wrong point, inspect this flag first.

```python
import torch
import voxelmorph as vxm

scale = torch.tensor([[2., 0., 0.], [0., 2., 0.]])
centered = vxm.affine_to_disp(scale, shape=(5, 5), origin_at_center=True)
corner = vxm.affine_to_disp(scale, shape=(5, 5), origin_at_center=False)
assert torch.allclose(centered[:, 2, 2], torch.zeros(2))
assert torch.allclose(corner[:, 0, 0], torch.zeros(2))
```

## When to use the smoke script

Run `scripts/transform_ops_smoke.py` after changing transform-operation guidance, when validating a new Python environment, or when debugging a suspected axis/sign/magnitude regression. The smoke script is synthetic and fast; it is not a substitute for downstream model or data-pipeline tests.
