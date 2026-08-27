# Analysis workflows

This reference covers the stable scikit-image analysis route: feature extraction, descriptor matching, region measurement, contour/surface extraction, and metrics. It assumes images are already loaded as NumPy arrays and that any nontrivial preprocessing or segmentation has been done by the sibling routes.

## Choose the workflow

| User intent | Primary APIs | Output |
| --- | --- | --- |
| Detect points, blobs, templates, textures, or dense appearance descriptors | `skimage.feature` detectors/descriptors | keypoints, descriptor arrays, response images, feature vectors |
| Match two feature sets | `match_descriptors`, `plot_matched_features` | match index pairs and point correspondences |
| Quantify existing labels | `regionprops`, `regionprops_table`, moments, perimeters | object properties or table columns |
| Trace boundaries or surfaces | `find_contours`, `approximate_polygon`, `profile_line`, `marching_cubes` | contour arrays, line profiles, meshes |
| Compare images or label maps | `skimage.metrics` | scalar scores or small metric tuples |

## Feature extraction and descriptors

### Point and local-feature workflow

Use this path when the user asks for corners, local keypoints, descriptors, or later matching.

1. Work from a prepared grayscale image unless the selected descriptor explicitly supports channels.
2. Pick the detector/descriptor family:
   - Corners: `corner_harris`, `corner_shi_tomasi`, `corner_fast`, `corner_peaks`, and `corner_subpix`.
   - Binary descriptors: `BRIEF`, `ORB`; `ORB.detect_and_extract(image)` is the compact route, while `BRIEF.extract(image, keypoints)` starts from supplied keypoints.
   - Float descriptors: `SIFT`, `daisy`, HOG-style features.
   - Blobs or local extrema: `blob_log`, `blob_dog`, `blob_doh`, `peak_local_max`.
   - Templates/textures: `match_template`, `graycomatrix`, `graycoprops`, `local_binary_pattern`, `multiblock_lbp`, Haar-like features, and `multiscale_basic_features`.
3. Keep keypoint and descriptor row ordering synchronized.
4. If the task asks for alignment or warp parameters after feature extraction, stop at corresponding point arrays and load `../transform-registration/SKILL.md`.

Example skeleton for corner coordinates:

```python
from skimage.feature import corner_harris, corner_peaks, corner_subpix

response = corner_harris(gray, sigma=1)
keypoints = corner_peaks(response, min_distance=5, threshold_rel=0.02)
keypoints_subpix = corner_subpix(gray, keypoints, window_size=13)
```

Example skeleton for an ORB descriptor set:

```python
from skimage.feature import ORB

extractor = ORB(n_keypoints=200)
extractor.detect_and_extract(gray)
keypoints = extractor.keypoints
descriptors = extractor.descriptors
```

### Dense or window-level feature vectors

Use `hog` when the user needs a fixed descriptor vector or a visual diagnostic of oriented gradients. For color images, set `channel_axis`; for grayscale images, leave `channel_axis=None`.

```python
from skimage.feature import hog

features, hog_image = hog(
    image,
    orientations=8,
    pixels_per_cell=(16, 16),
    cells_per_block=(1, 1),
    visualize=True,
    channel_axis=-1,  # omit or set None for grayscale
)
```

Tune `pixels_per_cell` and `cells_per_block` to the object scale. Very small images fail when the requested HOG cell/block geometry does not fit.

## Descriptor matching workflow

Use this path when two images already have comparable descriptor arrays.

```python
from skimage.feature import match_descriptors

matches = match_descriptors(descriptors0, descriptors1, cross_check=True)
points0 = keypoints0[matches[:, 0]]
points1 = keypoints1[matches[:, 1]]
```

Matching rules to preserve:

- Descriptor arrays must have the same descriptor length: `(M, P)` and `(N, P)`.
- With `metric=None`, scikit-image chooses Hamming distance for boolean/binary descriptors and Euclidean distance for numeric float-like descriptors.
- `cross_check=True` keeps only mutual best matches and is a good default for robust correspondences.
- Use `max_distance` to reject distant matches and `max_ratio < 1.0` to reject ambiguous matches; SIFT-like workflows commonly try a ratio near `0.8` and validate visually.
- `plot_matched_features` is useful for visual diagnostics, but the runtime output that downstream transform workflows need is the matched point arrays.

Boundary: this sub-skill owns descriptor extraction and matching. Estimating `AffineTransform`, `ProjectiveTransform`, `SimilarityTransform`, applying `warp`, or running registration belongs to `../transform-registration/SKILL.md`.

## Geometric model fitting

Use `ransac` with geometric model classes when you already have measured points, contours, or keypoint coordinates and want a robust fit that still belongs to analysis.

```python
import numpy as np
from skimage.measure import ransac, LineModelND, CircleModel, EllipseModel

points = np.array([[0, 0], [10, 1], [20, 2], [30, 4]], dtype=float)
model, inliers = ransac(
    points,
    LineModelND,
    min_samples=2,
    residual_threshold=1.0,
    rng=0,
)
```

Model choices:
- `LineModelND` for robust line fits in 2-D or higher dimensions.
- `CircleModel` for circular fits.
- `EllipseModel` for ellipses in 2-D.
- Use the fitted model as an analysis result; only hand off to transform-registration if the fitted geometry will become an image warp or alignment step.

## Region measurement workflow

Use this path when the user already has a label image and wants object-level quantities.

```python
from skimage.measure import regionprops, regionprops_table

regions = regionprops(label_image, intensity_image=image, spacing=spacing)
for region in regions:
    label = region.label
    area = region.area
    centroid = region.centroid

columns = regionprops_table(
    label_image,
    intensity_image=image,
    properties=(
        "label",
        "area",
        "bbox",
        "centroid",
        "axis_major_length",
        "axis_minor_length",
        "orientation",
        "eccentricity",
        "perimeter",
        "intensity_mean",
    ),
    spacing=spacing,
)
```

Operational choices:

- Use `regionprops` for interactive/lazy access to many properties on a few regions.
- Use `regionprops_table` when the next step is pandas, CSV, plotting, or model input.
- Include `intensity_image` only when intensity-derived properties are needed.
- Pass `spacing=(row_spacing, col_spacing, ...)` for physical units; otherwise area, axis lengths, and moments are in pixel units.
- Use `regionprops(..., offset=offset)` for cropped labels when reported coordinates need the original image frame. `regionprops_table` supports `spacing` but not `offset` in the stable signature.
- For custom object measurements, use `extra_properties` with `regionprops` or `regionprops_table`, keeping functions deterministic and shape-aware.

Do not use this route to decide how to partition objects. If a user needs markers, watershed, morphology cleanup, SLIC, or label creation from an image, load `../segmentation-and-shapes/SKILL.md` first.

## Contours, profiles, moments, and surfaces

### 2D contours and polygons

Use `find_contours` for iso-valued boundaries in a 2D scalar image or mask.

```python
from skimage.measure import find_contours, approximate_polygon

contours = find_contours(image, level=0.5)
main = max(contours, key=len)
simplified = approximate_polygon(main, tolerance=2.0)
```

Remember that contour arrays are in image coordinate order. For Matplotlib plotting, use `contour[:, 1]` on the x-axis and `contour[:, 0]` on the y-axis. Contours that touch an image edge can be open; internal contours are typically closed.

Use `subdivide_polygon` when a simplified polygon needs smoother interpolation instead of fewer points.

### Shape measurements and moments

Use the moment/perimeter helpers when the user asks for scalar geometric descriptors without a full `RegionProperties` object:

- `perimeter`, `perimeter_crofton`, `euler_number` for binary or labeled region geometry.
- `moments`, `moments_central`, `moments_normalized`, `moments_hu`, `centroid`, `inertia_tensor`, and `inertia_tensor_eigvals` for shape descriptors.
- Carry `spacing` into moment functions that accept it when measurements must be in physical coordinates.

### Line profiles

Use `profile_line` to sample intensities along a line segment.

```python
from skimage.measure import profile_line

profile = profile_line(
    image,
    src=(row0, col0),
    dst=(row1, col1),
    linewidth=3,
    order=1,
    mode="reflect",
    reduce_func=None,  # keep the full cross-line samples instead of reducing
)
```

Use a reduction such as `reduce_func=np.mean`, `np.max`, or `np.sum` when a wide line should collapse to one value per step.

### 3D surfaces

Use `marching_cubes` for an isosurface mesh from a 3D volume.

```python
from skimage.measure import marching_cubes, mesh_surface_area

verts, faces, normals, values = marching_cubes(volume, level=level, spacing=spacing)
area = mesh_surface_area(verts, faces)
```

Pass `spacing` for anisotropic voxels. Use a boolean `mask` only when it has the same shape as the volume and genuinely limits the domain.

## Metrics workflow

### Image similarity or restoration quality

Use pixel-level metrics when both arrays represent the same field and have compatible shapes:

```python
from skimage.metrics import (
    mean_squared_error,
    normalized_root_mse,
    peak_signal_noise_ratio,
    structural_similarity,
)

mse = mean_squared_error(reference, candidate)
nrmse = normalized_root_mse(reference, candidate)
psnr = peak_signal_noise_ratio(reference, candidate, data_range=data_range)
ssim = structural_similarity(
    reference,
    candidate,
    data_range=data_range,
    channel_axis=-1,  # omit or set None for grayscale
)
```

For float images, always compute and pass the intended `data_range` such as `1.0`, `candidate.max() - candidate.min()` only when that is scientifically meaningful, or a known physical range.

Use `normalized_mutual_information(image0, image1, bins=...)` when comparing statistical dependence between images, including registration-style diagnostics where absolute intensity agreement is not the goal.

### Segmentation and shape agreement

Use label metrics when arrays are label images rather than intensities:

```python
from skimage.metrics import adapted_rand_error, variation_of_information

error, precision, recall = adapted_rand_error(labels_true, labels_test)
false_splits, false_merges = variation_of_information(
    labels_true,
    labels_test,
    ignore_labels=[0],
)
```

- `adapted_rand_error` reports an error plus precision and recall; lower error is better.
- `variation_of_information` separates oversegmentation (`false_splits`) from undersegmentation (`false_merges`).
- `contingency_table` is useful when implementing or debugging a custom label-overlap analysis.
- `hausdorff_distance` and `hausdorff_pair` compare foreground point sets or binary masks when boundary/shape discrepancy is more relevant than pixelwise intensity.

Do not use SSIM or PSNR to score semantic label maps unless the user explicitly wants a pixelwise numeric comparison and understands that label identities are arbitrary.

## Cross-link: matched features to transform estimation

Feature matching often feeds transform estimation, but analysis should stop at the analysis contract:

```python
matches = match_descriptors(descriptors0, descriptors1, cross_check=True)
source_points = keypoints0[matches[:, 0]]
destination_points = keypoints1[matches[:, 1]]
```

Hand `source_points`, `destination_points`, the source/target images, and any metric checks to `../transform-registration/SKILL.md` for transform class selection, RANSAC transform estimation, inverse-map/coordinate convention handling, warping, registration, and alignment scoring.
