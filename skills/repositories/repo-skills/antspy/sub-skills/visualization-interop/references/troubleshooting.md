# ANTsPy Visualization and Interop Troubleshooting

Use this guide when plots do not render, saved outputs are missing or blank, overlays are misplaced, channel/RGB images are confusing, matrix round trips lose ordering, or optional nibabel/SimpleITK conversions fail.

## Quick Triage

1. Confirm imports: `import ants`, `import numpy as np`, and for plotting `import matplotlib`.
2. In scripts and CI, set `matplotlib.use("Agg")` before importing `ants` or `matplotlib.pyplot`.
3. Print `image.dimension`, `image.shape`, `image.spacing`, `image.origin`, `image.direction`, `image.components`, and `image.is_rgb`.
4. For overlays or matrix masks, check `ants.image_physical_space_consistency(base, other)` before combining images.
5. Use `filename=` for `ants.plot`, `ants.plot_ortho`, `ants.plot_ortho_stack`, and `ants.plot_grid`; use `plt.savefig(...)` for `ants.plot_hist`.
6. Guard optional imports for `nibabel` and `SimpleITK` and choose a fallback when they are unavailable.

## Display Backend Failures

### Symptom: `ImportError`, `TclError`, Qt errors, or no display named

Likely cause: Matplotlib selected an interactive backend in a headless environment.

Fix:

```python
import matplotlib
matplotlib.use("Agg")
import ants
```

Then save plots with `filename=` or `plt.savefig(...)` instead of relying on an interactive window.

### Symptom: saved figure is empty or later plots overlap

Likely cause: Manual Matplotlib figure state was not saved or closed correctly.

Fix:

- For `ants.plot`, `ants.plot_ortho`, `ants.plot_ortho_stack`, and `ants.plot_grid`, pass `filename=` so ANTsPy saves and closes the figure.
- For `ants.plot_hist`, call `plt.savefig(...)` immediately after the plot, then `plt.close()`.
- Avoid mixing multiple plotting APIs in one global figure unless you manage Matplotlib figure objects explicitly.

### Symptom: `plot_hist(..., fit_line=True)` fails in Matplotlib

Likely cause: the implementation uses legacy `matplotlib.mlab.normpdf`, which may be unavailable in newer Matplotlib versions.

Fix: omit `fit_line=True`, or compute the normal curve yourself with NumPy/SciPy and plot it after `ants.plot_hist`.

## Missing Optional Dependencies

### Symptom: `ImportError: No module named 'nibabel'`

`ants.from_nibabel_nifti` and `ants.to_nibabel_nifti` require nibabel for object creation or downstream use.

Fix:

- Guard `import nibabel as nib` and skip nibabel-specific conversion when unavailable.
- If the task only needs file IO, use `ants.image_read` and `ants.image_write` for NIfTI files instead of nibabel object conversion.
- Do not use absent aliases such as `ants.nifti_to_ants` or `ants.ants_to_nibabel`; use `ants.from_nibabel_nifti` and `ants.to_nibabel_nifti`.

### Symptom: `ImportError: SimpleITK is required...`

`ants.from_sitk` and `ants.to_sitk` import `SimpleITK` at call time.

Fix:

- Guard `import SimpleITK as sitk` and branch when it is unavailable.
- Use ANTsPy image IO directly if the workflow does not truly require a SimpleITK object.
- If SimpleITK is installed but conversion still fails, check supported dimension and component count.

## Overlay Dimension or Physical-Space Mismatch

### Symptom: overlay is shifted, stretched, flipped, or silently interpolated

Likely cause: the base image and overlay differ in shape, spacing, origin, direction, or orientation.

Fix:

```python
if not ants.image_physical_space_consistency(base, overlay):
    overlay = ants.resample_image_to_target(overlay, base, interp_type="linear")
```

For labels or masks:

```python
overlay = ants.resample_image_to_target(overlay, base, interp_type="nearestNeighbor")
```

Notes:

- `ants.plot`, `ants.plot_ortho`, and `ants.plot_ortho_stack` can resample mismatched overlays internally, but explicit resampling documents interpolation choice.
- Use [segmentation-labels](../../segmentation-labels/SKILL.md) when label IDs, colormaps, or overlap interpretation matter.
- Use [image-ops-math](../../image-ops-math/SKILL.md) when resampling, cropping, padding, or thresholding choices are the task.

### Symptom: `ValueError: Overlay image must have 3 dimensions!`

Likely cause: `plot_ortho` and `plot_ortho_stack` only support 3D scalar base and overlay images.

Fix: use `ants.plot` for 2D images or convert/select a 3D scalar volume before calling orthographic plotting APIs.

### Symptom: `overlay cannot have more than one voxel component`

Likely cause: a vector/RGB/component image was passed as an overlay.

Fix:

```python
component = ants.split_channels(vector_image)[0]
ants.plot(base, overlay=component, filename="component_overlay.png")
```

## Channel Axis and RGB Confusion

### Symptom: expected a 2D RGB image but got a 3D scalar image

Likely cause: `ants.from_numpy(arr)` treated shape `(x, y, 3)` as a 3D scalar image because component intent was not specified.

Fix:

```python
rgb = ants.from_numpy(arr.astype("uint8"), is_rgb=True)
vec = ants.from_numpy(arr.astype("float32"), has_components=True)
```

### Symptom: channel-first arrays are scrambled after conversion

Likely cause: ANTsPy component arrays use the last axis for components.

Fix:

```python
channel_last = np.moveaxis(channel_first, 0, -1)
vec = ants.from_numpy(channel_last, has_components=True)
```

### Symptom: precision changes during RGB/vector conversion

Likely cause: `rgb_to_vector` and `vector_to_rgb` clone to `unsigned char` when the input pixel type is not already byte-valued.

Fix: keep float vector images for numeric computation and reserve RGB conversion for display/export. Use [image-core](../../image-core/SKILL.md) for pixel type and component storage diagnostics.

### Symptom: `ants.scalar_to_rgb` raises an unsupported-function exception

Current ANTsPy exposes `scalar_to_rgb` but the function raises because the backend wrapper is not supported.

Fix: use scalar plotting with Matplotlib colormaps, or construct an explicit RGB array and call `ants.from_numpy(..., is_rgb=True)`.

## Matrix and Mask Ordering Problems

### Symptom: `ValueError: Num masked voxels ... must match data matrix ...`

Likely cause: the matrix column count does not match `sum(mask >= 0.5)` in `matrix_to_images`.

Fix:

- Reuse the exact mask used to create the matrix.
- Keep mask thresholding binary or consistent across extraction and reconstruction.
- Check `matrix.shape[1] == int((mask.numpy() >= 0.5).sum())` before `matrix_to_images`.

### Symptom: rows are assigned to the wrong image after reconstruction

Likely cause: row order was changed outside ANTsPy.

Fix: maintain an explicit list of image IDs alongside matrix rows. `images_to_matrix([a, b, c], mask)` returns rows in `[a, b, c]` order; ANTsPy does not store labels in the matrix.

### Symptom: columns do not line up with expected voxels

Likely cause: mask or `epsilon` changed, or the image was resampled to a different grid before matrix extraction.

Fix:

- Persist the mask image or reconstruct it exactly from metadata and array values.
- Use the same `epsilon` in `images_to_matrix` and remember `matrix_to_images` fills voxels where `mask >= 0.5`.
- Validate physical space of all images against the mask before extraction.

### Symptom: matrix extraction changes image values unexpectedly

Likely cause: `sigma` was set in `images_to_matrix`, or an image shape mismatch triggered resampling to the mask grid.

Fix: set `sigma=None` unless smoothing is intended, and pre-resample images explicitly when needed so interpolation choice is clear.

## nibabel Conversion Failures

### Symptom: unsupported dimension error

`from_nibabel_nifti` supports only 3D, 4D, and 5D NIfTI images. `to_nibabel_nifti` supports ANTsPy images with dimension 3 through 5.

Fix: select or reshape the data into a supported image dimensionality before conversion.

### Symptom: spatial/time unit error

Likely cause: NIfTI units are not millimeters and seconds.

Fix:

```python
nib_img.header.set_xyzt_units("mm", "sec")
```

Use millimeters for spatial axes. Use seconds for the time axis in 4D or 5D images.

### Symptom: affine, origin, or direction sign looks flipped

Likely cause: nibabel uses RAS+ affine conventions while ANTs/ITK use LPS+ physical metadata.

Fix: use ANTsPy's conversion helpers rather than manually copying affine elements. Validate with round-trip tests on known origin, spacing, and direction.

### Symptom: shear or direction deviation error

Likely cause: a sheared affine exceeded the configured deshearing tolerance.

Fix: inspect the source NIfTI affine. Adjust `deshear_threshold` or `max_angle_deviation` only when the downstream workflow can tolerate the resulting direction approximation.

## SimpleITK Conversion Failures

### Symptom: unsupported dimension error

`ants.from_sitk` and `ants.to_sitk` support 2D, 3D, and 4D images.

Fix: slice, stack, or reshape unsupported images into supported dimensions before conversion.

### Symptom: array axes appear reversed after conversion

Likely cause: SimpleITK and ANTsPy expose arrays in different axis orders. SimpleITK uses z-y-x style for 3D array views; ANTsPy uses x-y-z style with trailing components.

Fix: compare image metadata and physical-space behavior, not only raw array shape. When comparing arrays directly, account for the axis transpose performed by the bridge.

### Symptom: vector image component count changes

Likely cause: the input object was not actually a SimpleITK vector image, or the ANTs image was constructed as scalar with an extra spatial dimension instead of `has_components=True`.

Fix:

- In SimpleITK, check `sitk_image.GetNumberOfComponentsPerPixel()`.
- In ANTsPy, check `ants_image.components`, `ants_image.has_components`, and `ants_image.numpy().shape`.
- For NumPy construction, pass `has_components=True` with channel-last arrays.

## Plot Directory Side Effects

### Symptom: unexpected PNG files appear beside input images

`ants.plot_directory` writes previews into the walked directory tree.

Fix: if previews should go elsewhere, write a custom loop that reads each file with `ants.image_read` and calls `ants.plot(..., filename=output_path)` in a separate output directory.

## Movie Writer Problems

### Symptom: ffmpeg writer is unavailable

`ants.movie` defaults to Matplotlib `FFMpegWriter` when `writer=None`.

Fix: install/provide ffmpeg, or use another installed writer such as `animation.PillowWriter` for GIF output.

### Symptom: movie generation is slow or huge

Likely cause: high-resolution volume or high frame rate.

Fix: resample/crop the image intentionally first, lower `fps`, or use static orthographic figures for quick QA.
