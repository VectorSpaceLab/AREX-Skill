# Image Operations and Math Troubleshooting

## Unsupported `iMath` Operation

Symptoms:

- `ants.iMath(image, operation, *args)` raises `ValueError: Operation not recognized`.
- A user supplies an operation copied from an ANTs ImageMath CLI help page, but ANTsPy rejects it.

Likely causes and fixes:

| Cause | Fix |
| --- | --- |
| Operation name typo or wrong case. | Use exact case-sensitive names such as `"Normalize"`, `"TruncateIntensity"`, `"MaurerDistance"`, `"MD"`, or `"FillHoles"`. |
| Operation exists in CLI ImageMath but not in ANTsPy's wrapper. | Check [iMath reference](imath-reference.md) for the recognized ANTsPy subset. Use a first-class ANTsPy API when available. |
| Operation needs files, multiple images, text outputs, or transforms. | Do not force it through `ants.iMath`. Route transform tasks to [registration-transforms](../../registration-transforms/) and label/statistic tasks to [segmentation-labels](../../segmentation-labels/). |

Recovery pattern:

```python
available = sorted(ants.iMath_ops()) if hasattr(ants, "iMath_ops") else []
if operation not in available:
    raise ValueError(f"Unsupported ANTsPy iMath operation {operation!r}; available={available}")
out = ants.iMath(image, operation, *args)
```

## Interpolation Looks Wrong

Symptoms:

- Label images contain fractional values after resampling.
- Scalar images look blocky or aliased.
- `resample_image_to_target` rejects an interpolator string.

Likely causes and fixes:

| Cause | Fix |
| --- | --- |
| Linear interpolation was used for labels. | For `resample_image_to_target`, use `interp_type="nearestNeighbor"` or `"genericLabel"`. For `resample_image`, use numeric `interp_type=1`. |
| Nearest-neighbor interpolation was used for scalar intensities. | For `resample_image_to_target`, use `interp_type="linear"`; for `resample_image`, use numeric `interp_type=0`. |
| API styles were mixed. | `resample_image` documents numeric codes; `resample_image_to_target` documents string names and maps legacy integers internally. |
| Unsupported string was supplied. | Use one of `linear`, `nearestNeighbor`, `genericLabel`, `multiLabel`, `gaussian`, `bSpline`, `cosineWindowedSinc`, `welchWindowedSinc`, `hammingWindowedSinc`, or `lanczosWindowedSinc`. |

Validation:

```python
resampled_label = ants.resample_image_to_target(label, target, interp_type="nearestNeighbor")
assert set(np.unique(resampled_label.numpy())).issubset(set(np.unique(label.numpy())))
```

## Physical-Vs-Voxel Resampling Confusion

Symptoms:

- Output shape is much larger or smaller than expected.
- Spacing changes in the opposite direction from the user's intent.
- Two images have the same shape but appear shifted or scaled in physical space.

Rules:

- `ants.resample_image(image, (64, 64), use_voxels=True, ...)` means output voxel counts/shape.
- `ants.resample_image(image, (1.5, 1.5), use_voxels=False, ...)` means new physical spacing.
- `ants.resample_image_to_target(image, target, ...)` means copy the target grid and physical space.

Recovery:

```python
print("before", image.shape, image.spacing, image.origin)
out = ants.resample_image(image, params, use_voxels=use_voxels, interp_type=0)
print("after", out.shape, out.spacing, out.origin)
```

If the task describes a desired reference image, switch to `resample_image_to_target` rather than manually calculating spacing or shape.

## Wrong Mask or Image Dimensionality

Symptoms:

- Masking, multiplication, metrics, or Hausdorff results are empty or nonsensical.
- Backend errors occur when combining images.
- A mask appears shifted despite matching array shape.
- `get_neighborhood_in_mask` raises about image/mask types or radius length.

Checks:

```python
def image_space_tuple(x):
    return (x.dimension, x.shape, x.spacing, x.origin, x.direction)

print(image_space_tuple(image))
print(image_space_tuple(mask))
```

Fixes:

- If the mask is intended to match the image but has a different grid, resample with `ants.resample_image_to_target(mask, image, interp_type="nearestNeighbor")`.
- If metadata was lost during NumPy conversion, rebuild through image-core utilities using a trusted image as the metadata source.
- If the mask is 2D and the image is 3D, choose a slice workflow or rebuild a 3D mask; do not broadcast manually.
- For neighborhoods, pass `radius` as a scalar or a tuple/list whose length equals `image.dimension`.
- Confirm `mask.max() > 0` before using it for denoise, metrics, histogram matching, cropping, or Hausdorff distance.

## Empty Masks After `get_mask`

Symptoms:

- `mask.min() == mask.max()` or `mask.max() == 0`.
- Crops are empty or too small.
- Metrics or denoise run on no foreground voxels.

Likely causes and fixes:

| Cause | Fix |
| --- | --- |
| Default thresholds excluded the target. | Supply explicit `low_thresh` and `high_thresh`. |
| Cleanup morphology erased a tiny object. | Use `cleanup=0` for synthetic, patch, or small-object images. |
| Image has unexpected intensity scale. | Inspect `image.min()`, `image.max()`, `image.mean()`, and consider `ants.iMath(image, "Normalize")` or `ants.iMath(image, "TruncateIntensity", ...)`. |

## Scalar, Vector, RGB, and Component Pitfalls

Symptoms:

- Morphology raises `ValueError: multichannel images not yet supported`.
- A slice unexpectedly returns a NumPy array rather than `ANTsImage`.
- RGB or vector image operations produce component ordering confusion.

Guidance:

- Check `image.components`, `image.has_components`, and `image.is_rgb` before applying scalar operations.
- `smooth_image`, `resample_image`, `crop_image`, `crop_indices`, and `reorient_image2` have channel-splitting behavior in source code; `morphology` explicitly rejects multichannel inputs.
- For morphology on vector/RGB data, split channels or derive a scalar mask first.
- For 2D images, `slice_image` returns NumPy arrays; for 3D images it returns a 2D `ANTsImage`.
- For label images, preserve discrete labels with nearest-neighbor interpolation and avoid scalar intensity normalization.

## Bias Correction and Denoise Failures

Symptoms:

- N4/N3 raises about `spline_param` length.
- N4 raises because `weight_mask` is not an ANTsImage.
- Bias correction is slow or appears unstable.

Fixes:

- Use `spline_param=None`, a scalar, or a tuple/list whose length equals `image.dimension`.
- Build weight masks as images, e.g. `weight_mask = ants.image_clone(mask, pixeltype="float")`.
- Use a foreground `mask` to constrain correction.
- Increase `shrink_factor` for exploratory runs, then reduce it for final detail.
- Use `abp_n4(image, intensity_truncation=(0.025, 0.975, 256))` only with exactly three truncation values.

## Compiled Backend Failures

Symptoms:

- Errors mention ANTs/ITK compiled functions such as `ResampleImage`, `ThresholdImage`, `DenoiseImage`, `N4BiasFieldCorrection`, `antsApplyTransforms`, or `iMath`.
- A call works for one image but fails for another pixel type, dimension, or component layout.

Recovery checklist:

1. Confirm `ants` imports from the public `antspyx` installation and report `getattr(ants, "__version__", "unknown")`.
2. Clone scalar intensity images to float before metrics or backend-heavy math: `img_float = img.clone("float")`.
3. For masks and labels, use binary/unsigned-int-compatible images and nearest-neighbor interpolation.
4. Confirm dimensions and tuple/list parameter lengths match exactly.
5. Reduce the operation to a tiny in-memory image and run [the smoke script](../scripts/antspy_ops_smoke.py) to separate package/backend problems from data-specific problems.

## Expensive 3D Operation Cautions

High-cost operations include `denoise_image`, N4/N3 bias correction, large-radius morphology, neighborhood extraction across dense masks, `symmetrize_image`, and high-resolution 3D resampling.

Practical controls:

- Crop to foreground first and `decrop_image` after processing.
- Use masks to restrict denoise, histogram matching, and metrics.
- Downsample or increase `shrink_factor` for exploratory runs.
- Limit `get_neighborhood_in_mask` to sparse masks or smaller radii.
- Avoid running `symmetrize_image` without user approval for runtime; it performs iterative registration internally.
- For large labels, route specialized label postprocessing to [segmentation-labels](../../segmentation-labels/) rather than applying broad scalar operations.

## Average Images Produces Blurry or Misaligned Output

Symptoms:

- Averaged images are blurred or structures do not overlap.
- Output follows the largest image grid but anatomy is not aligned.

Cause and fix:

`ants.average_images` resamples inputs to the largest image space; it does not register them. Register or otherwise align images first with [registration-transforms](../../registration-transforms/), then average images that already occupy the same physical space.
