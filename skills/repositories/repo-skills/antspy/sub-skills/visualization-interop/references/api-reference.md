# ANTsPy Visualization and Interop API Reference

This reference covers plotting, non-interactive rendering, channels/RGB/vector images, image-matrix conversion, n-dimensional image lists, and optional nibabel/SimpleITK bridges. It assumes the public distribution `antspyx` is installed and imported as `ants`.

## Verified Public Signatures

Live inspection of `antspyx` verified these visualization and interop signatures:

| API | Signature |
| --- | --- |
| `ants.plot` | `(image, overlay=None, blend=False, alpha=1, cmap='Greys_r', overlay_cmap='turbo', overlay_alpha=0.9, vminol=None, vmaxol=None, cbar=False, cbar_length=0.8, cbar_dx=0.0, cbar_vertical=True, axis=0, nslices=12, slices=None, ncol=None, slice_buffer=None, black_bg=True, bg_thresh_quant=0.01, bg_val_quant=0.99, domain_image_map=None, crop=False, scale=False, reverse=False, title=None, title_fontsize=20, title_dx=0.0, title_dy=0.0, filename=None, dpi=500, figsize=1.5, reorient=True, resample=True)` |
| `ants.plot_ortho` | `(image, overlay=None, reorient=True, blend=False, xyz=None, xyz_lines=True, xyz_color='red', xyz_alpha=0.6, xyz_linewidth=2, xyz_pad=5, orient_labels=True, alpha=1, cmap='Greys_r', overlay_cmap='jet', overlay_alpha=0.9, cbar=False, cbar_length=0.8, cbar_dx=0.0, cbar_vertical=True, black_bg=True, bg_thresh_quant=0.01, bg_val_quant=0.99, crop=False, scale=False, domain_image_map=None, title=None, titlefontsize=24, title_dx=0, title_dy=0, text=None, textfontsize=24, textfontcolor='white', text_dx=0, text_dy=0, filename=None, dpi=500, figsize=1.0, flat=False, transparent=True, resample=False, allow_xyz_change=True)` |
| `ants.plot_ortho_stack` | `(images, overlays=None, reorient=True, xyz=None, xyz_lines=False, xyz_color='red', xyz_alpha=0.6, xyz_linewidth=2, xyz_pad=5, cmap='Greys_r', alpha=1, overlay_cmap='jet', overlay_alpha=0.9, black_bg=True, bg_thresh_quant=0.01, bg_val_quant=0.99, crop=False, scale=False, domain_image_map=None, title=None, titlefontsize=24, title_dx=0, title_dy=0, text=None, textfontsize=24, textfontcolor='white', text_dx=0, text_dy=0, filename=None, dpi=500, figsize=1.0, colpad=0, rowpad=0, transpose=False, transparent=True, orient_labels=True)` |
| `ants.plot_grid` | `(images, slices=None, axes=2, figsize=1.0, rpad=0, cpad=0, vmin=None, vmax=None, colorbar=True, cmap='Greys_r', title=None, tfontsize=20, title_dx=0, title_dy=0, rlabels=None, rfontsize=14, rfontcolor='white', rfacecolor='black', clabels=None, cfontsize=14, cfontcolor='white', cfacecolor='black', filename=None, dpi=400, transparent=True, **kwargs)` |
| `ants.plot_hist` | `(image, threshold=0.0, fit_line=False, normfreq=True, title=None, grid=True, xlabel=None, ylabel=None, facecolor='green', alpha=0.75)` |
| `ants.movie` | `(image, filename=None, writer=None, fps=30)` |
| `ants.plot_directory` | `(directory, recursive=False, regex='*', save_prefix='', save_suffix='', axis=None, **kwargs)` |
| `ants.merge_channels` | `(image_list, channels_first=False)` |
| `ants.split_channels` | `(image)` |
| `ants.scalar_to_rgb` | `(image, mask=None, filename=None, cmap='red', custom_colormap_file=None, min_input=None, max_input=None, min_rgb_output=None, max_rgb_output=None, vtk_lookup_table=None)` |
| `ants.rgb_to_vector` | `(image)` |
| `ants.vector_to_rgb` | `(image)` |
| `ants.images_to_matrix` / `ants.image_list_to_matrix` / `ants.matrix_from_images` | `(image_list, mask=None, sigma=None, epsilon=0.5)` |
| `ants.matrix_to_images` / `ants.images_from_matrix` | `(data_matrix, mask)` |
| `ants.timeseries_to_matrix` | `(image, mask=None)` |
| `ants.matrix_to_timeseries` | `(image, matrix, mask=None)` |
| `ants.ndimage_to_list` | `(image)` |
| `ants.list_to_ndimage` | `(image, image_list)` |
| `ants.from_nibabel_nifti` | `(nib_image, deshear_threshold=1e-06, max_angle_deviation=0.5, pixeltype='float')` |
| `ants.to_nibabel_nifti` | `(ants_image, header=None)` |
| `ants.from_sitk` | `(sitk_image: 'SimpleITK.Image') -> ants.core.ants_image.ANTsImage` |
| `ants.to_sitk` | `(ants_image: ants.core.ants_image.ANTsImage) -> 'SimpleITK.Image'` |

Inspection also verified that old or guessed aliases `ants.nifti_to_ants` and `ants.ants_to_nibabel` are not present. Use `ants.from_nibabel_nifti` and `ants.to_nibabel_nifti` instead.

## Plotting APIs

| API | Best for | Important behavior |
| --- | --- | --- |
| `ants.plot` | 2D images and multi-slice 3D panels with optional scalar overlay. | Accepts `image` and `overlay` as `ANTsImage` objects or filenames. Axis aliases include `x`, `y`, and `z`. By default 3D display reorients to `LAI`. If `filename` is provided, the figure is saved and closed; otherwise Matplotlib display is invoked. Component images are rejected. |
| `ants.plot_ortho` | Three orthogonal slices through a single 3D image. | Requires a 3D scalar image. `xyz` selects the crosshair location; `flat=True` makes a one-row panel. Reorients by default to `RPI`. Mismatched overlays are resampled to the base image. |
| `ants.plot_ortho_stack` | Comparing multiple 3D images and optional overlays in one orthographic figure. | Each image must be 3D. Mismatched overlays and stack images are resampled internally. `transpose=True` switches stack orientation. |
| `ants.plot_grid` | Arbitrary 2D/3D image grids with row/column labels and colorbars. | `images` may be a list or array-like 2D grid of `ANTsImage` objects. `slices` and `axes` may be scalars or grid-shaped arrays. Saves and closes when `filename` is set. |
| `ants.plot_hist` | Quick intensity histogram from an `ANTsImage`. | Uses `plt.hist(...)` and `plt.show()`; it has no `filename` argument. For headless scripts, set `Agg` and call `matplotlib.pyplot.savefig(...)` yourself after `plot_hist`. |
| `ants.movie` | Animating 3D slices to GIF/MP4 or another Matplotlib animation writer output. | Pads the image and creates a `FuncAnimation`. If `writer` is omitted, it uses `FFMpegWriter`, which requires ffmpeg. Provide `PillowWriter` for GIFs when Pillow is installed. |
| `ants.plot_directory` | Batch PNG previews of `.nii.gz` images under a directory. | Walks a directory, loads matching `.nii.gz` files, and calls `ants.plot(..., filename=...)`. It writes plots next to the input image files, so use only on directories where that side effect is intended. |

`overlay` images must be scalar images. If a task asks for label-specific color semantics, label ordering, or segmentation metrics, route the interpretation to [segmentation-labels](../../segmentation-labels/SKILL.md) and use this sub-skill only for the final display mechanics.

## Physical-Space Validation for Display

Use `ants.image_physical_space_consistency(base, overlay)` before plotting overlays or feeding images to external display libraries. Plotting helpers may resample mismatched overlays automatically, but explicit checks make interpolation and label-vs-intensity decisions visible:

| Situation | Recommended action |
| --- | --- |
| Same image grid and scalar intensity overlay | Plot directly. |
| Overlay shape/spacing/origin/direction differs and overlay is continuous intensity | Resample with `ants.resample_image_to_target(overlay, base, interp_type="linear")`, then plot. |
| Overlay is a label/mask image | Use nearest-neighbor or label-safe interpolation before plotting; route label semantics to segmentation. |
| Only metadata differs because an array was rebuilt from the same grid | Use `ants.copy_image_info(reference, rebuilt)` only if voxel data already describes the same physical space. |
| Component or RGB image needs display | Split/select components or convert intentionally; do not pass multi-component overlays to plotting helpers. |

## Channels, RGB, and Vector Images

| API | Behavior |
| --- | --- |
| `ants.merge_channels([img1, img2, ...], channels_first=False)` | Combines scalar `ANTsImage` objects with the same pixel type into a multi-component image. `channels_first` records an attribute but ANTsPy NumPy component arrays are still conventionally handled with a trailing component axis. |
| `ants.split_channels(image)` | Returns scalar images for each component of a multi-component image. |
| `ants.from_numpy(arr, has_components=True)` | Treats the last array axis as components and returns a vector image. |
| `ants.from_numpy(arr, is_rgb=True)` | Treats the last axis as RGB components and returns an RGB image, typically from `uint8` data with three components. |
| `ants.rgb_to_vector(image)` | Converts RGB storage to vector storage; clones to `unsigned char` first if needed. |
| `ants.vector_to_rgb(image)` | Converts vector storage to RGB storage; clones to `unsigned char` first if needed. |
| `ants.scalar_to_rgb(...)` | Present but currently raises that the function is unsupported because the backend wrapper is unavailable. Do not build workflows that depend on it. |

For channel-first external arrays such as `(channels, x, y)` or `(channels, x, y, z)`, move the channel axis to the end before creating an ANTsPy component image:

```python
channel_last = np.moveaxis(channel_first, 0, -1)
vec = ants.from_numpy(channel_last.astype("float32"), has_components=True)
```

## Matrix and N-Dimensional Image APIs

| API | Use for | Key behavior |
| --- | --- | --- |
| `ants.images_to_matrix(image_list, mask=None, sigma=None, epsilon=0.5)` | Convert scalar images into a matrix with one row per image. | If `mask` is omitted, ANTsPy builds one from the first image. Voxels where `mask >= epsilon` become columns. Images with a shape mismatch are resampled to the mask grid. `sigma` smooths images before extraction. |
| `ants.matrix_to_images(data_matrix, mask)` | Convert rows back into scalar images in the mask grid. | The number of matrix columns must equal `sum(mask >= 0.5)`. Each row becomes one image with values filled into mask voxels. |
| `ants.timeseries_to_matrix(image, mask=None)` | Split an n-dimensional image into lower-dimensional sections and convert sections to matrix rows. | Internally uses `ndimage_to_list` and `images_to_matrix`. If `mask` is omitted, all voxels of the first section are included. |
| `ants.matrix_to_timeseries(image, matrix, mask=None)` | Rebuild an n-dimensional image from matrix rows. | Uses `matrix_to_images`, `list_to_ndimage`, and copies metadata from `image`. Provide the same mask used for extraction. |
| `ants.ndimage_to_list(image)` | Split an n-dimensional image along the last spatial dimension into a list of `dimension - 1` images. | The resulting images inherit origin, spacing, and direction from the leading dimensions. |
| `ants.list_to_ndimage(image, image_list)` | Merge a list of scalar images into a target n-dimensional image space. | The target image supplies output spacing, origin, direction, and shape including the merged dimension. Input images must share pixel type. |

Aliases: `ants.image_list_to_matrix` and `ants.matrix_from_images` are aliases of `ants.images_to_matrix`; `ants.images_from_matrix` is an alias of `ants.matrix_to_images`.

## Optional nibabel Interop

`ants.from_nibabel_nifti` and `ants.to_nibabel_nifti` support nibabel NIfTI objects when `nibabel` is installed.

Key behavior:

- Supported nibabel inputs are 3D, 4D time-series, and 5D multi-component images.
- Spatial units must be millimeters. 4D and 5D images also require seconds for the time dimension; unknown units are set to millimeters/seconds with warnings.
- Affines are converted between nibabel RAS+ and ITK/ANTs LPS+ conventions.
- Shear can be removed with `deshear_threshold`; excessive direction deviation raises `ValueError`.
- Supported output pixel types for conversion are `unsigned char`, `unsigned int`, `float`, and `double`.
- For component images, ANTsPy component arrays are mapped to nibabel's fifth dimension shape convention `(x, y, z, 1, components)`.
- `ants.to_nibabel_nifti(ants_image, header=header)` can reuse a header. If the header transform differs, the output transform is based on the ANTs image.

Guard optional imports in reusable scripts:

```python
try:
    import nibabel as nib
except ImportError:
    nib = None
```

## Optional SimpleITK Interop

`ants.from_sitk` and `ants.to_sitk` require `SimpleITK` to be installed. They raise an `ImportError` with an install hint when it is missing.

Key behavior:

- Supported scalar/vector image dimensions are 2, 3, and 4.
- SimpleITK arrays are exposed as `(z, y, x)` or `(z, y, x, components)` for 3D data; ANTsPy arrays use `(x, y, z)` plus trailing components. The bridge transposes axes during conversion.
- Origin, spacing, and direction are copied between the two image objects.
- Vector images preserve component count and use `GetNumberOfComponentsPerPixel() > 1` on the SimpleITK side.
- Unsupported dimensions raise `ValueError`.

