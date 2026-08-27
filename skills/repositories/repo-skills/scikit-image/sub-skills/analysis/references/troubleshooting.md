# Analysis troubleshooting

Use this guide when scikit-image analysis code fails or returns implausible descriptors, measurements, contours, or metrics.

## Fast triage

1. Confirm the task belongs here: existing image arrays, existing labels, feature/descriptor outputs, contours, or metric scores. If the failure is caused by loading, dtype conversion, enhancement, segmentation, or warping, use the sibling route that owns that step.
2. Print `image.shape`, `image.dtype`, value range, and whether a channel axis is present.
3. For labels, print `label_image.dtype`, `label_image.shape`, `label_image.min()`, `label_image.max()`, and the number of nonzero labels.
4. For metrics, check that images have compatible shapes and that float arrays have an explicit `data_range`.
5. For descriptor matching, check descriptor shapes, dtypes, empty descriptor arrays, and whether keypoint rows still align with descriptor rows.

## Feature extraction and descriptor matching

### No keypoints, too many keypoints, or empty descriptors

Likely causes:

- The image is low contrast or has already been over-smoothed.
- A detector threshold is too strict (`threshold_rel`, `threshold_abs`, `min_distance`, `n_keypoints`, etc.).
- A detector that expects 2D grayscale data received a color image without conversion.
- The image is too small for the selected descriptor geometry, especially HOG `pixels_per_cell` and `cells_per_block`.

Fixes:

- Route nontrivial contrast/filtering fixes to `../enhancement/SKILL.md`, then rerun the detector.
- Relax thresholds or reduce `min_distance` in small images.
- Use `channel_axis` only for APIs that support it, such as HOG; otherwise use a prepared grayscale image.
- For HOG, reduce `pixels_per_cell` or `cells_per_block` so the block grid fits inside the image.

### `match_descriptors` raises a descriptor-length error

`match_descriptors` requires inputs shaped like `(M, P)` and `(N, P)` with the same descriptor length `P`. Do not mix descriptors from incompatible extractors or from different settings such as different BRIEF/SIFT descriptor sizes.

Checklist:

```python
print(descriptors0.shape, descriptors0.dtype)
print(descriptors1.shape, descriptors1.dtype)
assert descriptors0.ndim == descriptors1.ndim == 2
assert descriptors0.shape[1] == descriptors1.shape[1]
```

### Matches are noisy or too sparse

- `cross_check=True` keeps mutual best matches and usually reduces false matches.
- `max_distance` rejects pairs whose descriptor distance is too large.
- `max_ratio < 1.0` rejects ambiguous nearest-neighbor matches; SIFT-like descriptors often start around `0.8`, then validate on the actual images.
- With `metric=None`, boolean descriptors use Hamming distance and non-boolean numeric descriptors use Euclidean distance. Set `metric` explicitly only when the descriptor type justifies it.
- Visualize a sample with `plot_matched_features` before handing matches to transform estimation.

If the next requested step is RANSAC transform estimation, warping, or registration, switch to `../transform-registration/SKILL.md` after producing matched point arrays.

## Robust geometric fitting returns unstable models

Symptoms:
- `ransac` returns too few inliers or a model that changes a lot between runs
- a line, circle, or ellipse fit looks plausible visually but fails on cropped or noisy points
- the code starts using fitted geometry to estimate an image warp instead of a pure analysis result

Fixes:
- Normalize or re-center the point coordinates before fitting when the geometry is large or badly scaled
- Choose the model class that matches the actual geometry: `LineModelND`, `CircleModel`, or `EllipseModel`
- Increase `residual_threshold` only enough to absorb the expected measurement noise
- Use `rng=` for reproducible fits and inspect the inlier mask before trusting the model
- If the fitted result will be used to align or warp images, hand it off to `../transform-registration/SKILL.md` instead of keeping it in analysis

Quick check:

```python
import numpy as np
from skimage.measure import ransac, LineModelND

points = np.array([[0, 0], [1, 1], [2, 2], [3, 4]], dtype=float)
model, inliers = ransac(points, LineModelND, min_samples=2, residual_threshold=1.0, rng=0)
assert inliers.any()
```

## Labeled-region measurement

### `regionprops` rejects the label image

`regionprops` expects an integer label image. Float and boolean arrays are not valid label images for region measurement. Label `0` is background and is ignored; an all-background image returns no regions.

Fixes:

- If the input is a raw image or binary mask and the task asks how to create labels, route to `../segmentation-and-shapes/SKILL.md`.
- If labels already exist but are stored as float values, convert only when they are truly integer-coded labels:

```python
if (label_image == label_image.astype(int)).all():
    label_image = label_image.astype(int)
```

Do not cast probability maps or continuous intensity images to labels just to satisfy `regionprops`; create labels first.

### Intensity-derived properties are missing or implausible

Properties such as `intensity_mean`, `intensity_min`, `intensity_max`, and `intensity_std` need an `intensity_image`. Its spatial dimensions must match the label image, and it must represent the original intensity field that should be summarized.

Use `regionprops(label_image, intensity_image=image)` or include `intensity_image=image` in `regionprops_table`. If the measurements should use a filtered or exposure-adjusted image, make that preprocessing decision explicit.

### Areas, centroids, axes, or Feret diameters are in the wrong units

Pixel units are the default. For physical units, pass a `spacing` sequence with one value per spatial dimension:

```python
regions = regionprops(label_image, intensity_image=image, spacing=(row_um, col_um))
```

Effects to remember:

- Area-like properties scale by the product of spacings.
- Length/axis/Feret-like properties scale per dimension and can change under anisotropic spacing.
- `coords_scaled` reflects spacing; `coords` remains pixel coordinates.
- `spacing` values must be numeric, finite, and match the number of spatial dimensions.

### Cropped-label coordinates are not in the original image frame

Use `regionprops(..., offset=offset)` when measuring a cropped label image but reporting centroids or coordinates in the original image frame. `offset` belongs to `regionprops`; the stable `regionprops_table` signature supports `spacing` but not `offset`.

### `regionprops_table` columns look split or unexpected

Vector-valued properties such as `bbox` or `centroid` become multiple columns using the configured separator, e.g. `centroid-0`, `centroid-1`. Select a small explicit `properties` tuple and document expected columns before passing the table to pandas or a model.

## Contours, profiles, and 3D surfaces

### `find_contours` fails or returns unexpected open contours

Common causes and fixes:

- Input must be a 2D scalar array. A color image or `(rows, cols, 1)` array fails; select one channel or squeeze only when that is semantically correct.
- `mask` must be boolean and have the same shape as the image.
- Contours crossing an image edge are open. Pad/crop intentionally if a closed contour is required.
- The `level` value controls the iso-boundary. For binary masks, `level=0.5` is the usual boundary between `0` and `1`; for scalar images, choose a meaningful threshold or let the default midpoint only when that matches the analysis.
- NaNs or masked-out regions interrupt contours. Use the `mask` argument to make missing data explicit.

Plot contour coordinates as `(x, y) = (contour[:, 1], contour[:, 0])`; the array itself is in image coordinate order.

### `profile_line` values do not match expectations

- `src` and `dst` are image coordinates, not Cartesian plot coordinates.
- `order` controls interpolation; use `order=0` for nearest-neighbor sampling on labels/masks and a higher order only for intensity images.
- `mode` and `cval` control out-of-bounds behavior.
- With `linewidth > 1`, `reduce_func=None` keeps cross-line samples, while `np.mean`, `np.max`, or another reducer collapses each cross-section to one value.

### `marching_cubes` fails on a volume

Check these before changing algorithms:

- The input must be a 3D volume, not a 2D image.
- The requested `level` must cross values in the volume.
- `spacing` must have exactly one value per spatial dimension.
- `mask`, when supplied, must be boolean and match the volume shape.
- Very small volumes or invalid method names raise errors rather than returning empty meshes.

For anisotropic voxels, always pass `spacing`; otherwise surface area and mesh coordinates are in voxel index units.

## Metrics

### SSIM or PSNR fails on float images

For float arrays, pass `data_range` explicitly. `structural_similarity` raises on floats without `data_range`, and PSNR can warn or infer a range that is not the intended scientific range.

```python
ssim = structural_similarity(reference, candidate, data_range=1.0)
psnr = peak_signal_noise_ratio(reference, candidate, data_range=1.0)
```

For color SSIM, also set `channel_axis` correctly. If `win_size` exceeds an image dimension, set a smaller odd `win_size` or compare a larger crop.

### Metric inputs have incompatible shapes or meanings

- `mean_squared_error`, `normalized_root_mse`, `peak_signal_noise_ratio`, and `structural_similarity` require compatible image shapes.
- Do not compare arbitrary label IDs with PSNR or SSIM as if they were intensities; label IDs are categorical and often arbitrary.
- Use `adapted_rand_error`, `variation_of_information`, or `contingency_table` for segmentation label agreement.
- Use `hausdorff_distance` or `hausdorff_pair` for foreground set or boundary disagreement.
- Use `normalized_mutual_information` when statistical dependence matters more than exact intensity equality.

### Segmentation metric interpretation is backwards

- `adapted_rand_error(labels_true, labels_test)` returns `(error, precision, recall)`; lower error is better.
- `variation_of_information(labels_true, labels_test)` returns `(false_splits, false_merges)`; split-heavy results indicate oversegmentation, while merge-heavy results indicate undersegmentation.
- `ignore_labels` differs by metric defaults. Set it explicitly, commonly `[0]`, when background should not contribute.
- `adapted_rand_error` accepts `alpha` in `[0, 1]` to weight precision and recall; values outside this range are invalid.

## Boundary failures

If a debugging session starts asking how to compute a transform from matches, align images, choose an inverse map, or warp an image back, stop treating it as analysis and load `../transform-registration/SKILL.md`. This analysis route may provide the feature matches and metrics used to judge alignment, but it does not own transform estimation or registration execution.
