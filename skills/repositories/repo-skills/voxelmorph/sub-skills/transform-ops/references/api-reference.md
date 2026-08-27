# Transform operations API reference

This reference describes VoxelMorph's PyTorch transform primitives as exposed through `voxelmorph`, `voxelmorph.functional`, `voxelmorph.nn.functional`, and `voxelmorph.nn.modules`. It is self-contained runtime guidance for agents using an installed VoxelMorph package.

## Version and dependency assumptions

The API was distilled from VoxelMorph `0.3.3` behavior with PyTorch tensor operations and Neurite grid/noise helpers available. The minimum verified backend for these operations is CPU; CUDA is optional for users who install a CUDA-capable PyTorch build and keep all tensors on the same device.

## Shape and coordinate conventions

| Symbol | Meaning |
|---|---|
| `ndim` or `N` | Number of spatial dimensions. Dense warps work for 2D and 3D in normal VoxelMorph use; affine helpers assert `N in {2, 3}`. |
| `S` | Spatial shape, such as `(H, W)` or `(D, H, W)`. |
| `B` | Batch size. |
| `C` | Image channel count. |
| `meshgrid` | Identity grid with shape `(N, *S)`, usually from Neurite's `volshape_to_ndgrid(..., stack=True)` with `ij` indexing. |
| `disp` | Dense displacement in voxel units, channels-first: `(N, *S)` or `(B, N, *S)`. Component `disp[d]` corresponds to spatial axis `d` in `ij` order. |
| `trf` | Either an affine matrix, a dense displacement, absolute coordinates, or `None` depending on the API argument. |
| `coords` | Normalized grid-sample coordinates in `[-1, 1]`; VoxelMorph stores them channels-first before internally moving coordinate channels to the last dimension and reversing to PyTorch grid order. |

Affine matrix shapes:

- Compact 2D/3D affine: `(N, N + 1)`.
- Square homogeneous affine: `(N + 1, N + 1)`.
- Batched affine: `(B, N, N + 1)` or `(B, N + 1, N + 1)`.
- Composition utilities also accept additional leading batch dimensions for all-affine matrix multiplication.

Warping semantics:

- VoxelMorph uses backward sampling: output at coordinate `x` samples the input at `x + disp(x)`.
- Positive displacement along a spatial axis therefore makes image content appear to move in the negative direction along that axis.
- `padding_mode='zeros'` is the default, so boundaries can lose energy. Use `padding_mode='border'` when validating exact shifts away from boundary artifacts.

## Top-level `voxelmorph` / `voxelmorph.functional` functions

The package root imports `voxelmorph.functional` symbols, so `voxelmorph.affine_to_disp` and `voxelmorph.functional.affine_to_disp` refer to the same public operation.

| Function | Signature | Output and notes |
|---|---|---|
| `angles_to_rotation_matrix` | `angles_to_rotation_matrix(rotation, degrees=True)` | Returns a float64 `(2, 2)` or `(3, 3)` rotation matrix. `rotation` must contain one angle for 2D or three angles for 3D. 2D positive 90 degrees returns `[[0, -1], [1, 0]]`; the 3D implementation composes `Rx @ Ry @ Rz` with its documented test convention. |
| `params_to_affine` | `params_to_affine(ndim, translation=None, rotation=None, scale=None, shear=None, degrees=True, device=None)` | Returns a float32 square affine `(N + 1, N + 1)`. Parameters compose as `Translation @ Rotation @ Scale @ Shear`. `translation` length is `N`; `rotation` and `shear` length is 1 for 2D and 3 for 3D; scalar `scale` broadcasts to every axis. |
| `random_affine` | `random_affine(ndim, max_translation=0, max_rotation=0, max_scaling=1, device=None, sampling=True)` | Returns a float32 square affine. With `sampling=True`, translation and rotation use NumPy uniform RNG; scales are sampled in `[1/max_scaling, max_scaling]` and require `max_scaling >= 1`. With `sampling=False`, max values are used directly. |
| `affine_to_disp` | `affine_to_disp(affine, meshgrid=None, origin_at_center=True, shape=None, warp_right=None)` | Converts a compact/square affine to a displacement field. Provide exactly one of `meshgrid` or `shape`. Output is `(N, *S)` for one affine or `(B, N, *S)` for a batched affine. `origin_at_center=True` treats the image center as the affine origin. `warp_right` right-composes a dense field: it computes `affine(x + warp_right(x)) - x`. |
| `disp_to_trf` | `disp_to_trf(disp, grid=None, non_spatial_dims=None)` | Adds an identity grid to a displacement, returning absolute coordinates with the same shape. Use `non_spatial_dims=None` for `(N, *S)` and `(0,)` for `(B, N, *S)`. |
| `trf_to_disp` | `trf_to_disp(trf, grid=None, non_spatial_dims=None)` | Subtracts an identity grid from absolute coordinates, returning displacement with the same shape. `disp_to_trf()` and `trf_to_disp()` round-trip dense fields when the same shape/grid convention is used. |
| `disp_to_coords` | `disp_to_coords(disp, meshgrid=None, non_spatial_dims=None)` | Adds the identity grid and normalizes each axis to `[-1, 1]`. Output shape remains channels-first, matching `disp`. Use `(0,)` for batched displacement input. |
| `coords_to_disp` | `coords_to_disp(coords, meshgrid=None, non_spatial_dims=None)` | Present but not implemented. It raises `NotImplementedError`; do not rely on it for inverse conversion. |
| `spatial_transform` | `spatial_transform(image, trf, mode='linear', isdisp=True, meshgrid=None, origin_at_center=True, non_spatial_dims=None, align_corners=True, padding_mode='zeros')` | Warps `image`. `trf=None` returns `image`. `trf` can be affine, batched affine, dense displacement, or already-normalized coordinates if `isdisp=False`. `non_spatial_dims` tells the function which leading image dimensions are non-spatial: `None` for `(*S)`, `(0,)` for `(C, *S)`, `(0, 1)` for `(B, C, *S)`. `mode='linear'` infers bilinear/trilinear as appropriate; `mode='nearest'` is appropriate for labels. |
| `integrate_disp` | `integrate_disp(disp, steps, meshgrid=None, non_spatial_dims=None)` | Scaling-and-squaring integration of a stationary velocity field. `steps=0` returns the input. Use `None` for unbatched `(N, *S)` or `(0,)` for batched `(B, N, *S)`. Runtime cost grows linearly with `steps`. |
| `resize_disp` | `resize_disp(disp, scale_factor=None, shape=None, mode='linear', non_spatial_dims=None)` | Spatially resizes a displacement field and scales vector magnitudes by the same per-axis factors. Provide exactly one of `scale_factor` or `shape`. Supports scalar or per-axis sequence `scale_factor`, target `shape`, and unbatched/batched dense fields. Unlike `ResizeDisplacementField`, it handles `mode='nearest'` by passing `align_corners=None`. |
| `compose` | `compose(transforms, interpolation_mode='linear', origin_at_center=True, shape=None)` | Composes transforms so `compose([A, B, C])` means `A(B(C(x)))`: the rightmost transform is applied first. Returns a compact affine if every input is affine; otherwise returns a displacement field. For mixed affine/dense composition, provide `shape` when the rightmost transform is affine and no dense field appears to its right. See the batched mixed-composition limitation below. |
| `constant_shift_field` | `constant_shift_field(spatial_shape, shift_size=1, normalize=False, device='cpu')` | Builds a constant displacement field `(N, *S)`. `shift_size` may be scalar, length-`N` sequence, or tensor. `normalize=True` only divides the first component by `spatial_shape[0] - 1`; it does not normalize every axis. |
| `is_affine_shape` | `is_affine_shape(shape)` | Returns `True` for compact or square 2D/3D affine matrix shapes, including leading batch dimensions. |
| `make_square_affine` | `make_square_affine(mat)` | Converts compact `(..., N, N + 1)` to square homogeneous `(..., N + 1, N + 1)` by appending the bottom row. Square inputs are returned unchanged. |
| `random_disp` | `random_disp(shape, scales=10, magnitude=10, integrations=0, voxsize=1, meshgrid=None, non_spatial_dims=None, device=None, fractal_mode='upsample')` | Generates fractal-noise displacement. With `non_spatial_dims=None`, `shape` is spatial and output is `(N, *S)`. With `(0,)`, `shape` starts with batch and output is `(B, N, *S)`. `scales` and `magnitude` are divided by `voxsize`; `integrations > 0` applies `integrate_disp()`. |
| `random_transform` | `random_transform(shape, affine_probability=1.0, max_translation=5.0, max_rotation=5.0, max_scaling=1.1, warp_probability=1.0, warp_integrations=5, warp_scales_range=(10, 20), warp_magnitude_range=(1, 2), voxsize=1, non_spatial_dims=None, device=None, fractal_mode='upsample', sampling=True)` | Generates a displacement field that may combine random affine and nonlinear warp parts. Top-level default treats `shape` as spatial. If both probabilities are zero, current behavior returns a zero field rather than `None`. Seed both NumPy and PyTorch for reproducibility. |

## `voxelmorph.nn.functional` functions

Use this layer when working with neural-network tensor layouts. The affine helpers in this module are underscored implementation helpers; prefer the top-level public names for constructing affine matrices.

| Function | Signature | Output and notes |
|---|---|---|
| `spatial_transform` | `spatial_transform(image, trf, method='linear', isdisp=True, meshgrid=None, origin_at_center=True, non_spatial_dims=(0, 1), align_corners=True, padding_mode='zeros')` | Canonical batched/channel image warp for `image` shaped `(B, C, *S)`. Dense fields are `(N, *S)` or `(B, N, *S)`. Affines are inverted internally before conversion to displacement because PyTorch grid sampling is backward. |
| `disp_to_coords` | `disp_to_coords(disp, meshgrid=None, non_spatial_dims=(0,))` | Converts `(B, N, *S)` by default to normalized channels-first coordinates with the same shape. Use `non_spatial_dims=None` for unbatched `(N, *S)`. |
| `coords_to_disp` | `coords_to_disp(coords, meshgrid=None, non_spatial_dims=(0,))` | Always raises `NotImplementedError` in this version. |
| `integrate_disp` | `integrate_disp(disp, steps, meshgrid=None, non_spatial_dims=(0,))` | Scaling-and-squaring integration for `(B, N, *S)` by default. For unbatched fields, pass `non_spatial_dims=None`. |
| `compose` | `compose(transforms, interpolation_mode='linear', origin_at_center=True, shape=None)` | Same composition order as top-level `compose()`. It can compose all-affine sequences, unbatched dense fields, batched dense fields, and many affine/dense mixes. Current behavior can misinfer shape for `[affine, batched_disp]`; use a per-batch loop or convert the affine per sample as a workaround. |
| `random_disp` | `random_disp(shape, scales=10, magnitude=10, integrations=0, voxsize=1, meshgrid=None, non_spatial_dims=(0, 1), device=None, fractal_mode='upsample')` | Default `shape` is image-like `(B, C, *S)`; channel count is ignored and output is `(B, N, *S)`. Pass `non_spatial_dims=None` if `shape` is only spatial. |
| `random_transform` | `random_transform(shape, affine_probability=1.0, max_translation=5.0, max_rotation=5.0, max_scaling=1.1, warp_probability=1.0, warp_integrations=5, warp_scales_range=(10, 20), warp_magnitude_range=(1, 2), voxsize=1, non_spatial_dims=(0, 1), device=None, fractal_mode='upsample', sampling=True)` | Default `shape` is image-like `(B, C, *S)` and output is `(B, N, *S)`. Use top-level `random_transform()` or pass `non_spatial_dims=None` for spatial-only input. |

## Module wrappers in `voxelmorph.nn.modules`

| Module | Constructor / forward | Use and caveats |
|---|---|---|
| `SpatialTransformer` | `SpatialTransformer(interpolation_mode='linear', align_corners=True, device=None)`; `forward(moving_image, deformation_field)` | Wraps `voxelmorph.nn.functional.spatial_transform()`. Expects `moving_image` `(B, C, *S)` and `deformation_field` `(B, N, *S)` with the same tensor rank. The `device` constructor argument is deprecated and ignored. The module caches a meshgrid by spatial shape; if you reuse the same instance across devices or dtypes with the same shape, instantiate a new module or clear the cached `meshgrid`. |
| `IntegrateVelocityField` | `IntegrateVelocityField(shape=None, steps=1, interpolation_mode='linear', align_corners=True, device=None)`; `forward(velocity_field)` | Module form of scaling and squaring. Expects `(B, N, *S)`. `steps` must be nonnegative. The deprecated `shape` and `device` arguments are kept for compatibility and are not needed. |
| `ResizeDisplacementField` | `ResizeDisplacementField(scale_factor=1.0, interpolation_mode='linear', align_corners=True)`; `forward(disp)` | Resizes `(B, N, *S)` by scalar `scale_factor`, multiplying displacement magnitudes by the same scalar before interpolation. Use top-level `resize_disp()` for per-axis scale factors or target shapes. With `interpolation_mode='nearest'`, pass `align_corners=None` if using this wrapper, or prefer top-level `resize_disp(..., mode='nearest')`. |

## Known edge cases to plan around

- `coords_to_disp()` is intentionally unavailable and raises `NotImplementedError` in both API layers.
- Mixed affine plus batched dense composition has a shape-inference pitfall when the affine is left of the batched displacement. Work around it by looping over batch elements, composing unbatched fields, or converting each affine to a dense field with the correct `shape` before composing dense fields.
- `random_affine()`, `random_disp()`, and `random_transform()` use NumPy randomness in addition to any PyTorch randomness; seed both libraries for deterministic tests.
- `SpatialTransformer` and `voxelmorph.nn.functional.spatial_transform()` are designed around `(B, C, *S)` images. If you pass channel-only or spatial-only images, use the top-level wrapper and set `non_spatial_dims` explicitly.
