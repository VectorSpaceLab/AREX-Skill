---
name: analysis
description: "Extract features, match descriptors, measure labeled regions,
  trace contours, and compare images or segmentations with metrics."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Analysis

Use this sub-skill when a task asks scikit-image to turn already-loaded or preprocessed images into quantitative outputs: keypoints, descriptors, descriptor matches, labeled-region measurements, contour or surface geometry, line/profile measurements, or image/segmentation quality scores.

This route covers the stable `skimage.feature`, `skimage.measure`, and `skimage.metrics` analysis surface. Keep it focused on analysis results. When the task moves from matched features into geometric transform estimation, warping, or registration, hand off to `../transform-registration/SKILL.md`.

## Route here

- Detect or describe image features with APIs such as `hog`, `corner_harris`/`corner_peaks`, `corner_subpix`, `ORB`, `SIFT`, `BRIEF`, `CENSURE`, `daisy`, `match_template`, blob detectors, texture descriptors, or related `skimage.feature` helpers.
- Match descriptor arrays with `match_descriptors` and inspect correspondence arrays or `plot_matched_features` visualizations.
- Fit robust geometric models on measured point sets with `ransac`, `LineModelND`, `CircleModel`, or `EllipseModel` when the output is still an analysis result.
- Measure already-labeled objects with `regionprops`, `regionprops_table`, moments, perimeter measurements, intensity summaries, table-style outputs, `spacing`, and `offset` handling.
- Extract contours, simplified polygons, line intensity profiles, or 3D surfaces with `find_contours`, `approximate_polygon`, `subdivide_polygon`, `profile_line`, `marching_cubes`, and `mesh_surface_area`.
- Compare images, masks, point sets, or label maps with `structural_similarity`, `peak_signal_noise_ratio`, `mean_squared_error`, `normalized_root_mse`, `normalized_mutual_information`, `adapted_rand_error`, `variation_of_information`, and Hausdorff metrics.

## Reroute

- Loading/saving images, sample datasets, dtype/range conversion, or NumPy image conventions: use `../data-io/SKILL.md`.
- Color conversion, contrast/exposure adjustment, filtering, denoising, threshold selection, or restoration before analysis: use `../enhancement/SKILL.md`.
- Creating masks, drawing synthetic shapes, morphology cleanup, watershed/random-walker/SLIC/snake methods, or other object partitioning: use `../segmentation-and-shapes/SKILL.md`.
- Estimating or applying affine/projective/similarity transforms, warps, pyramids, phase cross-correlation, optical flow, or registration: use `../transform-registration/SKILL.md` after this route has produced or validated correspondences.
- Maintainer commands, repository tests, benchmarks, or build tooling are outside the runtime analysis route.

## Start fast

1. Identify the requested output: descriptor vector, keypoint coordinates, match index pairs, per-object table, contour coordinates, mesh, line profile, or scalar metric.
2. Confirm inputs are already arrays with the expected shape and range. Most feature detectors expect 2D grayscale data; HOG and SSIM can use color data when `channel_axis` is set.
3. For labeled-object measurement, require an integer label image where `0` is background. If the user only has a raw image or binary mask and asks how to create labels, route to segmentation first.
4. For physical measurements, carry `spacing` through `regionprops`, `regionprops_table`, moments, and `marching_cubes`; use `offset` with `regionprops` when measurements come from cropped label images.
5. For image metrics on float arrays, pass an explicit `data_range`; for color SSIM, pass the correct `channel_axis`.
6. For feature matching, return descriptor matches and corresponding point arrays. Do not own transform estimation; cross-link to `transform-registration` for RANSAC transform fitting, warp application, and alignment evaluation.

## Output contracts to preserve

- Feature keypoints are coordinate arrays associated with the detector; descriptor arrays must keep the same row order as their keypoints.
- `match_descriptors` returns a `(Q, 2)` integer array of descriptor indices: column `0` indexes the first descriptor set and column `1` indexes the second.
- `regionprops` returns lazy `RegionProperties` objects; `regionprops_table` returns a pandas-compatible dictionary of columns.
- `find_contours` returns a list of `(N, 2)` arrays in image coordinate order; contours that hit an image edge can be open.
- `marching_cubes` returns `(verts, faces, normals, values)`; `mesh_surface_area(verts, faces)` consumes the first two outputs.
- Metrics return scalar scores or small tuples. Preserve tuple ordering for segmentation metrics: `adapted_rand_error` returns `(error, precision, recall)` and `variation_of_information` returns `(false_splits, false_merges)`.

## References

- `references/workflows.md` gives copyable analysis workflows for feature extraction, descriptor matching, region measurement, contours/surfaces, and metrics.
- `references/troubleshooting.md` maps label-image dtype, descriptor matching, contour, `spacing`/`offset`, and `data_range` failures to fixes.
