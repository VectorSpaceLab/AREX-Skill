# Image Operations and Math API Reference

ANTsPy is imported as `ants`; the public package distribution is `antspyx`. The signatures below were verified from the installed `antspyx` API inspection and checked against the source package. Many functions are also chainable `ANTsImage` methods because ANTsPy decorates them as image methods, so both `ants.smooth_image(img, 1)` and `img.smooth_image(1)` are valid when the method is present.

## Resampling, Smoothing, and Filtering

| Task | API | Key choices |
| --- | --- | --- |
| Gaussian smoothing | `ants.smooth_image(image, sigma, sigma_in_physical_coordinates=True, FWHM=False, max_kernel_width=32)` | `sigma` may be scalar or length `image.dimension`. Use `sigma_in_physical_coordinates=False` for voxel units. `FWHM=True` interprets `sigma` as full-width-half-max. Multi-channel images are split, smoothed, and merged. |
| Resample by spacing/count | `ants.resample_image(image, resample_params, use_voxels=False, interp_type=1)` | `use_voxels=True` means `resample_params` are output voxel counts; `False` means physical spacing. Numeric `interp_type`: `0` linear, `1` nearest neighbor, `2` gaussian, `3` windowed sinc, `4` bspline. Multi-channel images are handled channel-wise. |
| Resample to target grid | `ants.resample_image_to_target(image, target, interp_type="linear", imagetype=0, verbose=False, **kwargs)` | Uses identity `antsApplyTransforms` to match the target image grid and physical space. Accepted string interpolators include `linear`, `nearestNeighbor`, `genericLabel`, `multiLabel`, `gaussian`, `bSpline`, `cosineWindowedSinc`, `welchWindowedSinc`, `hammingWindowedSinc`, `lanczosWindowedSinc`. Set `imagetype=3` for 4D moving images resampled to a 3D target. |
| Denoise | `ants.denoise_image(image, mask=None, shrink_factor=1, p=1, r=2, noise_model="Rician", v=0)` | Adaptive non-local means. Use a mask to limit work; increase `shrink_factor` for speed. `noise_model` is typically `"Rician"` for MR or `"Gaussian"` for generic noise. |
| Anti-alias binary image | `ants.anti_alias(image)` | Applies an anti-alias filter to a binary image, cloning to unsigned char if needed. Use for binary masks before surface-like operations; route plotting of the result to visualization. |
| Add synthetic noise | `ants.add_noise_to_image(image, noise_model, noise_parameters)` | `noise_model` values: `"additivegaussian"` with `(mean, sd)`, `"saltandpepper"` with `(probability, saltValue, pepperValue)`, `"shot"` with scalar scale, or `"speckle"` with scalar standard deviation. Unknown models raise `ValueError`. |
| Weingarten curvature | `ants.weingarten_image_curvature(image, sigma=1.0, opt="mean")` | Computes curvature-like scalar image measures; use masks and downsampling for large 3D volumes if the operation becomes expensive. |

Use [registration-transforms](../../registration-transforms/) for non-identity transforms. Use `resample_image_to_target` only when the transform is intentionally identity and the goal is grid matching.

## Thresholds, Masks, Morphology, Crop, Pad, and Slice

| Task | API | Behavior and validation |
| --- | --- | --- |
| Threshold scalar image | `ants.threshold_image(image, low_thresh=None, high_thresh=None, inval=1, outval=0, binary=True)` | Voxels inside `[low_thresh, high_thresh]` receive `inval`; other voxels receive `outval`. If `binary=False`, the thresholded output is multiplied by the original image. Omitted bounds default to just outside image min/max. |
| Create mask | `ants.get_mask(image, low_thresh=None, high_thresh=None, cleanup=2)` | Defaults threshold from image mean to max. `cleanup>0` erodes, keeps a large component, dilates, closes, and fills holes. On tiny images or small targets, set `cleanup=0` and assert `mask.max() > 0`. |
| Apply mask or selected labels | `ants.mask_image(image, mask, level=1, binarize=False)` | `level` may be a scalar, tuple/list, or NumPy array of label values. With `binarize=True`, returns the intersection of nonzero image values and selected mask labels. Mask and image should share dimension and physical space. |
| Morphology wrapper | `ants.morphology(image, operation, radius, mtype="binary", value=1, shape="ball", radius_is_parametric=False, thickness=1, lines=3, include_center=False)` | `operation`: `dilate`, `erode`, `open`, `close`. `mtype`: `binary` or `grayscale`. Binary `shape`: `ball`, `box`, `cross`, `annulus`, `polygon`. Multi-channel inputs raise an error. |
| Crop by foreground/label | `ants.crop_image(image, label_image=None, label=1)` | Crops around a label image; if `label_image` is omitted, `get_mask(image)` supplies one. Multi-channel images are split and merged. |
| Crop by indices | `ants.crop_indices(image, lowerind, upperind)` | `lowerind` and `upperind` lengths must equal `image.dimension`. The result can later be restored with `decrop_image`. |
| Decrop | `ants.decrop_image(cropped_image, full_image)` | Inserts a cropped image back into a full image frame. Use after processing a crop when downstream code expects original shape and metadata. |
| Pad | `ants.pad_image(image, shape=None, pad_width=None, value=0.0, return_padvals=False)` | Pass either `shape` or `pad_width`, not both. If both are omitted, pads each dimension to the largest existing dimension. With `return_padvals=True`, returns `(new_image, lower_pad_vals, upper_pad_vals)`. |
| Slice | `ants.slice_image(image, axis, idx, collapse_strategy=0)` | `axis=-1` maps to the last axis. Valid `collapse_strategy` values are `0`, `1`, `2`. 2D scalar/vector slices return NumPy arrays; 3D slices return 2D `ANTsImage` objects. |

## Bias Correction and Intensity Normalization

| Task | API | Guidance |
| --- | --- | --- |
| N3 simple | `ants.n3_bias_field_correction(image, downsample_factor=3)` | Simple N3 correction. Larger `downsample_factor` speeds correction but loses detail. |
| N3 advanced | `ants.n3_bias_field_correction2(image, mask=None, rescale_intensities=False, shrink_factor=4, convergence={"iters": 50, "tol": 1e-7}, spline_param=None, number_of_fitting_levels=4, return_bias_field=False, verbose=False, weight_mask=None)` | Use when masks, fitting levels, convergence, weight masks, or bias field output are needed. `weight_mask` must be an `ANTsImage`. |
| N4 | `ants.n4_bias_field_correction(image, mask=None, rescale_intensities=False, shrink_factor=4, convergence={"iters": [50, 50, 50, 50], "tol": 1e-7}, spline_param=None, return_bias_field=False, verbose=False, weight_mask=None)` | Common MRI bias correction. Input is cloned to float if needed. `spline_param` must be scalar or length `image.dimension`; `weight_mask` must be an `ANTsImage`. |
| ABP N4 | `ants.abp_n4(image, intensity_truncation=(0.025, 0.975, 256), mask=None, usen3=False)` | Runs `iMath("TruncateIntensity", ...)` then N4, or N3 when `usen3=True`. `intensity_truncation` must have exactly three values. |
| Histogram match | `ants.histogram_match_image(source_image, reference_image, number_of_histogram_bins=255, number_of_match_points=64, use_threshold_at_mean_intensity=False)` | ITK-style source-to-reference matching; output keeps source pixel type. Use on scalar images in comparable physical contexts. |
| Histogram match with masks | `ants.histogram_match_image2(source_image, reference_image, source_mask=None, reference_mask=None, match_points=64, transform_domain_size=255)` | Uses quantile/B-spline intensity warping. Masks restrict foreground mapping. If `match_points` is a vector, values must be in `[0, 1]`. |
| Histogram equalize | `ants.histogram_equalize_image(image, number_of_histogram_bins=256)` | Equalizes intensities and copies image metadata back onto the result. |

## iMath and Quantitative Math

| Task | API | Notes |
| --- | --- | --- |
| Generic image math | `ants.iMath(image, operation, *args)` and alias `ants.image_math(image, operation, *args)` | `operation` must be one of ANTsPy's recognized operation names. Arguments are positional and operation-specific. See [iMath reference](imath-reference.md). |
| Common iMath wrappers | `ants.iMath_normalize`, `ants.iMath_truncate_intensity`, `ants.iMath_sharpen`, `ants.iMath_grad`, `ants.iMath_laplacian`, `ants.iMath_canny`, `ants.iMath_MD`, `ants.iMath_ME`, `ants.iMath_MO`, `ants.iMath_MC`, `ants.iMath_GD`, `ants.iMath_GE`, `ants.iMath_GO`, `ants.iMath_GC`, `ants.iMath_fill_holes`, `ants.iMath_get_largest_component`, `ants.iMath_maurer_distance`, `ants.iMath_perona_malik`, `ants.iMath_pad`, `ants.iMath_propagate_labels_through_mask` | Prefer wrappers when available because they encode the exact operation string and positional argument order. |
| Image similarity | `ants.image_similarity(fixed_image, moving_image, metric_type="MeanSquares", fixed_mask=None, moving_mask=None, sampling_strategy="regular", sampling_percentage=1.0)` | Returns an ITK/ANTs metric value, often a distance or dissimilarity. With `Correlation`, self-similarity returns `-1` by convention. Metrics include `MeanSquares`, `Correlation`, `ANTSNeighborhoodCorrelation`, `MattesMutualInformation`, `JointHistogramMutualInformation`, and `Demons`. |
| Mutual information | `ants.image_mutual_information(image1, image2)` | Both images must have float pixel type and the same dimension. Clone to float before calling. |
| Neighborhoods in mask | `ants.get_neighborhood_in_mask(image, mask, radius, physical_coordinates=False, boundary_condition=None, spatial_info=False, get_gradient=False)` | `radius` may be a scalar or length `image.dimension`. `boundary_condition` may be `None`, `"image"`, or `"mean"`. Returns an array unless `spatial_info` or `get_gradient` requests dictionaries. |
| Neighborhood at voxel | `ants.get_neighborhood_at_voxel(image, center, kernel, physical_coordinates=False)` | `center` and `kernel` must be tuple/list with length equal to `image.dimension`; `kernel` is interpreted as the full neighborhood size in each dimension. |
| Hausdorff distance | `ants.hausdorff_distance(image1, image2)` | Computes distances between non-zero pixels after cloning inputs to unsigned int. Use binary/label images in the same physical space. |
| Average images | `ants.average_images(x, normalize=True, mask=None, imagetype=0, sum_image_threshold=3, return_sum_image=False, verbose=False)` | `x` can contain filenames or `ANTsImage` objects. Images are resampled to the largest image space, but this is not registration; images should already occupy the same physical space. |
| Reflect image | `ants.reflect_image(image, axis=None, tx=None, metric="mattes")` | Without `tx`, applies a reflection transform. With `tx`, runs registration after reflection and returns a registration dictionary; route transform details to registration-transforms. |
| Symmetrize image | `ants.symmetrize_image(image)` | Expensive iterative reflection/registration workflow. Treat as a heavyweight 3D operation and validate runtime budget before using. |
| Reorientation helpers | `ants.get_orientation(image)`, `ants.get_possible_orientations()`, `ants.reorient_image2(image, orientation="RAS")`, `ants.get_center_of_mass(image)` | `reorient_image2` requires a 3D image and supports multi-channel images by splitting/merging. The live inspection may show `reorient_image` as a module, but the callable helper is `reorient_image2`. |

## Chainable Method Notes

Common chains:

```python
mask = img.get_mask(cleanup=0)
normalized = img.iMath("Normalize").smooth_image(1.0)
resampled_label = label.resample_image_to_target(target, interp_type="nearestNeighbor")
cropped = img.crop_image(mask, 1).iMath("TruncateIntensity", 0.01, 0.99, 64)
```

Avoid long chains when a step changes shape, pixel type, component count, or physical metadata. Store intermediate images and inspect `dimension`, `shape`, `spacing`, `origin`, `direction`, `pixeltype`, `components`, and `has_components` before masking, metrics, Hausdorff distance, or averaging.
