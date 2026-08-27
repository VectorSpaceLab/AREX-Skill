# Image Operations and Math Workflows

These recipes assume images are already `ants.ANTsImage` objects. For creation, IO, pixel types, and metadata repair, use [image-core](../../image-core/). For non-identity transforms, registration outputs, or point transforms, use [registration-transforms](../../registration-transforms/).

## Validate Before Combining Images

Before masking, multiplying, computing metrics, Hausdorff distance, averaging, or matching a target grid, inspect both array geometry and physical space:

```python
def space_tuple(image):
    return (image.dimension, image.shape, image.spacing, image.origin, image.direction)

print(space_tuple(image))
print(space_tuple(mask_or_target))
```

Use this decision tree:

1. If dimensions differ, rebuild the input or choose a slice/volume workflow; do not broadcast arrays manually.
2. If shape differs but the images should occupy the same anatomical space, resample the moving image to a trusted target.
3. If shape matches but spacing, origin, or direction differ, decide whether metadata was lost, the images are actually different spaces, or a true resampling step is required.
4. For labels and masks, use nearest-neighbor-style interpolation and verify unique values after resampling.

## Resample Scalar and Label Images Safely

Match another image's grid:

```python
scalar_on_target = ants.resample_image_to_target(
    scalar_image,
    target_image,
    interp_type="linear",
)
label_on_target = ants.resample_image_to_target(
    label_image,
    target_image,
    interp_type="nearestNeighbor",
)
```

Change output voxel count directly:

```python
scalar_small = ants.resample_image(scalar_image, (64, 64), use_voxels=True, interp_type=0)
label_small = ants.resample_image(label_image, (64, 64), use_voxels=True, interp_type=1)
```

Change physical spacing directly:

```python
one_mm = ants.resample_image(scalar_image, (1.0, 1.0, 1.0), use_voxels=False, interp_type=0)
```

Validation checklist:

- Use `resample_image_to_target` when the user names a reference/target image.
- Use `resample_image(..., use_voxels=True)` only when `resample_params` are output voxel counts.
- Use `resample_image(..., use_voxels=False)` only when `resample_params` are new physical spacing values.
- Use `linear` or numeric `0` for scalar intensities.
- Use `nearestNeighbor`, `genericLabel`, or numeric `1` for masks and labels.
- After label resampling, check that `set(np.unique(out.numpy()))` is a subset of expected labels.

## Build, Clean, and Apply Masks

Create a normal foreground mask:

```python
mask = ants.get_mask(image, low_thresh=None, high_thresh=None, cleanup=2)
if mask.max() == 0:
    raise ValueError("empty mask")
masked = ants.mask_image(image, mask, level=1)
```

Create a tiny or synthetic mask without cleanup erosion:

```python
mask = ants.get_mask(image, low_thresh=1.0, high_thresh=image.max(), cleanup=0)
if mask.max() == 0:
    raise ValueError("thresholds or cleanup removed the target")
```

Select labels from a multi-label mask:

```python
selected_values = ants.mask_image(image, label_image, level=(2, 3))
selected_binary = ants.mask_image(image, label_image, level=(2, 3), binarize=True)
```

Mask validation steps:

- Confirm `ants.is_image(mask)` and `mask.dimension == image.dimension`.
- Confirm `mask.shape`, `mask.spacing`, `mask.origin`, and `mask.direction` match the image, or resample with nearest-neighbor interpolation.
- Confirm `mask.max() > 0` before denoising, bias correction, metrics, histogram matching, or cropping.
- Route label statistics or label-region summaries to [segmentation-labels](../../segmentation-labels/).

## Crop, Process, and Restore an Image

Crop around a mask, process the crop, then restore the original frame:

```python
mask = ants.get_mask(image, cleanup=0)
cropped = ants.crop_image(image, mask, label=1)
processed_crop = cropped.smooth_image(1.0)
restored = ants.decrop_image(processed_crop, image)
assert restored.shape == image.shape
```

Use deterministic index cropping when the bounds are known:

```python
patch = ants.crop_indices(image, lowerind=(10, 10), upperind=(80, 80))
restored_patch = ants.decrop_image(patch, image)
```

Pad to a shape or explicit widths:

```python
padded = ants.pad_image(image, shape=(160, 160, 160))
padded2, lower, upper = ants.pad_image(image, pad_width=[(0, 4), (0, 8), (0, 12)], return_padvals=True)
```

Notes:

- `pad_image` rejects calls that specify both `shape` and `pad_width`.
- `pad_width=(10, 10)` in 2D means total padding split across lower/upper sides for each axis; list-of-pairs gives asymmetric padding.
- Use `slice_image(image, axis=-1, idx=...)` for the last axis. In 2D, output is a NumPy array; in 3D, output is a 2D `ANTsImage`.

## Denoise and Correct Bias Field

A conservative MRI preprocessing pattern:

```python
mask = ants.get_mask(image, cleanup=1)
truncated = ants.iMath(image, "TruncateIntensity", 0.01, 0.99, 64)
denoised = ants.denoise_image(truncated, mask=mask, shrink_factor=2, noise_model="Rician")
corrected = ants.n4_bias_field_correction(
    denoised,
    mask=mask,
    shrink_factor=4,
    convergence={"iters": [50, 50, 30, 20], "tol": 1e-7},
)
normalized = ants.iMath(corrected, "Normalize")
```

When speed matters:

- Increase `shrink_factor` for `denoise_image` or N4.
- Crop to a foreground mask first, process the crop, then `decrop_image` back.
- Use a smaller convergence schedule for exploratory runs and a full schedule for final outputs.

Validation:

- Check no empty mask: `mask.max() > 0`.
- For N4/N3 `spline_param`, use either a scalar or one value per image dimension.
- `weight_mask` must be an `ANTsImage`; scalar weights raise an error.
- `abp_n4` requires `intensity_truncation=(lower_q, upper_q, bins)` with exactly three entries.

## Histogram Alignment and Equalization

Use full-image ITK matching when foreground/background differences are acceptable:

```python
matched = ants.histogram_match_image(source_image, reference_image)
```

Use masked matching for foreground-only intensity alignment:

```python
source_mask = ants.get_mask(source_image, cleanup=1)
reference_mask = ants.get_mask(reference_image, cleanup=1)
matched = ants.histogram_match_image2(
    source_image,
    reference_image,
    source_mask=source_mask,
    reference_mask=reference_mask,
    match_points=64,
)
```

Use equalization for contrast enhancement rather than cross-image standardization:

```python
equalized = ants.histogram_equalize_image(image, number_of_histogram_bins=256)
```

Validation:

- Keep source and reference as scalar images.
- Ensure masks are non-empty and match their respective image spaces.
- Use `ants.iMath(image, "Normalize")` for simple normalization; use histogram matching only when a reference image defines the target distribution.

## Morphology and iMath Operations

Prefer `ants.morphology` when the task is generic binary/grayscale morphology:

```python
closed = ants.morphology(mask, operation="close", radius=2, mtype="binary", shape="ball")
gray_open = ants.morphology(image, operation="open", radius=1, mtype="grayscale")
```

Use iMath wrappers or direct operation names when the task asks for an ANTs ImageMath operation:

```python
largest = ants.iMath_get_largest_component(mask, min_size=50)
distance = ants.iMath_maurer_distance(mask, foreground=1)
edges = ants.iMath_canny(image, sigma=1.0, lower=0.1, upper=0.9)
normalized = ants.iMath(image, "Normalize")
```

Validation:

- `ants.morphology` rejects multi-channel images; split channels or convert to scalar first.
- Operation names are case-sensitive. `ants.iMath(image, "normalize")` fails; use `"Normalize"`.
- Use [iMath reference](imath-reference.md) for the ANTsPy-recognized operation subset. The CLI ImageMath tutorial lists more operations than this wrapper accepts.

## Metrics, Neighborhoods, and Quantitative Checks

Mean-squares or registration-style metric:

```python
metric = ants.image_similarity(
    fixed_image.clone("float"),
    moving_image.clone("float"),
    metric_type="MeanSquares",
)
```

Mutual information:

```python
mi = ants.image_mutual_information(fixed_image.clone("float"), moving_image.clone("float"))
```

Neighborhood matrix inside a mask:

```python
mask = ants.get_mask(image, cleanup=0)
values = ants.get_neighborhood_in_mask(image, mask, radius=1, boundary_condition="mean")
with_space = ants.get_neighborhood_in_mask(image, mask, radius=(1, 1), spatial_info=True)
```

Specific voxel neighborhood:

```python
neighborhood = ants.get_neighborhood_at_voxel(image, center=(5, 5), kernel=(3, 3))
```

Hausdorff distance between binary/label images:

```python
stats = ants.hausdorff_distance(mask1, mask2)
```

Averaging images:

```python
avg = ants.average_images(images, normalize=True, mask=None)
```

Validation:

- `image_mutual_information` requires both images to be float and have the same dimension.
- `image_similarity` returns metric values using ITK/ANTs conventions; values may be distances rather than intuitive similarities.
- `get_neighborhood_in_mask` requires `image` and `mask` to be `ANTsImage` objects. Scalar `radius` expands to all dimensions; tuple/list radius length must equal `image.dimension`.
- `get_neighborhood_at_voxel` requires `center` and `kernel` lengths to equal image dimension.
- `average_images` resamples to the largest image space; it is not registration. Only average images already in the same physical space.

## Reorientation, Reflection, and Symmetrization

Orientation inspection and reorientation:

```python
orientation = ants.get_orientation(image)
valid_orientations = ants.get_possible_orientations()
ras = ants.reorient_image2(image, orientation="RAS")
```

Reflection and symmetrization:

```python
reflected = ants.reflect_image(image, axis=0)
# Heavy: runs repeated registration internally
# symmetric = ants.symmetrize_image(image)
```

Guidance:

- `reorient_image2` is for 3D images; it raises for non-3D images.
- `reflect_image(tx=None)` applies a reflection transform; `tx="Affine"` or another transform type triggers registration and returns a registration dictionary.
- `symmetrize_image` runs iterative reflection and registration; confirm runtime budget and route transform interpretation to [registration-transforms](../../registration-transforms/).
