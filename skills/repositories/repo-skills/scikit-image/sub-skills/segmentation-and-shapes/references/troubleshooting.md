# Segmentation and Shapes Troubleshooting

## `channel_axis` errors or wrong shape assumptions

**Symptom:** `ValueError` about `channel_axis=-1`, unexpected output shape, or grayscale images being treated as multichannel.

**Likely cause:** The image shape does not match the API default.

**Fix:**

- Use `channel_axis=None` for 2D grayscale images.
- Keep the channel axis explicit for RGB or multispectral inputs.
- For `slic` and `random_walker`, remember that labels/markers are spatial only and should not include the channel dimension.

## Markers do not behave like segmentation seeds

**Symptom:** Watershed or random walker returns a single region, labels leak everywhere, or the result looks unrelated to the markers.

**Likely cause:** The marker array is malformed.

**Fix:**

- Keep the marker array the same spatial shape as the image.
- Use positive integers for seed regions.
- Keep `0` for unlabeled pixels.
- For random walker, negative labels are inactive pixels and are excluded from the graph.
- If you need markers from a mask, use `ndi.label`, thresholded blobs, or explicit seeds rather than a noisy probability map.

## Watershed leaves holes or fails to split objects

**Symptom:** Touching objects stay merged, or a contour-fill attempt leaves gaps.

**Likely cause:** The contour is open or the elevation map/markers are too weak.

**Fix:**

- Prefer marker-based watershed over raw contour filling.
- Use a distance transform for touching blobs.
- Use a gradient image for intensity-based separation.
- Increase `compactness` if you want more regular regions.
- Clean the mask first with `remove_small_objects`, `remove_small_holes`, or binary opening/closing.

## SLIC errors on grayscale or unusual channel layouts

**Symptom:** SLIC complains about multichannel input, or the segmentation looks banded or unstable.

**Likely cause:** The channel axis or intensity scaling is wrong.

**Fix:**

- Set `channel_axis=None` for grayscale.
- Use the correct channel axis for multispectral arrays.
- Keep multichannel inputs normalized consistently across channels.
- Adjust `compactness` rather than forcing `n_segments` too high.
- Use `mask=` for ROI segmentation instead of cropping if you want a shape-aware superpixel pass.

## Felzenszwalb or quickshift oversegment the image

**Symptom:** Too many tiny regions, huge merged regions, or results that change more than expected when parameters change.

**Likely cause:** The region-merging parameters are off for the image scale or color statistics.

**Fix:**

- For `felzenszwalb`, tune `scale`, `sigma`, and `min_size` together.
- For `quickshift`, tune `ratio`, `kernel_size`, `max_dist`, and `convert2lab`.
- Keep `rng` fixed when you want reproducible quickshift output.
- Inspect boundaries with `find_boundaries` or `mark_boundaries` before adding graph-merging steps.

## Felzenszwalb or quickshift oversegment the image

**Symptom:** Too many tiny regions, huge merged regions, or results that change more than expected when parameters change.

**Likely cause:** The region-merging parameters are off for the image scale or color statistics.

**Fix:**

- For `felzenszwalb`, tune `scale`, `sigma`, and `min_size` together.
- For `quickshift`, tune `ratio`, `kernel_size`, `max_dist`, and `convert2lab`.
- Keep `rng` fixed when you want reproducible quickshift output.
- Inspect boundaries with `find_boundaries` or `mark_boundaries` before adding graph-merging steps.

## Random walker is slow or needs extra packages

**Symptom:** `cg_mg` is unavailable, or the solve is much slower than expected.

**Likely cause:** The chosen linear-solver mode needs optional dependencies or is not a good fit for the image size.

**Fix:**

- Use `mode='bf'` for small images.
- Use `mode='cg'` or `mode='cg_j'` for larger images.
- Install `pyamg` only if you specifically need `cg_mg`.
- If multichannel input behaves oddly, normalize each channel before calling `random_walker`.
- For anisotropic data, pass `spacing` so the diffusion metric matches the voxel geometry.

## Flood fill or flood mask fails on color images

**Symptom:** `flood` or `flood_fill` does not give the expected region on an RGB array.

**Likely cause:** These helpers operate on scalar images.

**Fix:**

- Pick one channel, or convert the image to a scalar representation such as grayscale or HSV hue.
- Use `tolerance` only when the values near the seed are approximately equal.
- Use `connectivity` or `footprint` to control neighborhood growth.

## `random_shapes` returns fewer shapes than requested

**Symptom:** The output contains fewer shapes than `min_shapes` / `max_shapes`, or the image is just white.

**Likely cause:** The requested shapes do not fit the image, or the intensity range is invalid.

**Fix:**

- Increase the canvas size or reduce `min_size` / `max_size`.
- Keep `intensity_range` within `0..255`.
- Use a fixed `rng` to make failures reproducible.
- Expect a warning when no shape can fit.

## Boundary overlays look wrong

**Symptom:** `mark_boundaries` seems to change dtype, or boundaries appear thicker than expected.

**Likely cause:** Visualization mode or background choice is wrong.

**Fix:**

- Use `find_boundaries` when you need a boolean boundary mask.
- Use `mark_boundaries` when you want an overlay image.
- Verify `mode='thick'`, `'inner'`, `'outer'`, or `'subpixel'` matches the visualization goal.
- Expect floating-point output from `mark_boundaries`.

## Graph cuts or merges produce unexpected label IDs

**Symptom:** `cut_threshold`, `cut_normalized`, or `merge_hierarchical` returns sparse or shifted labels.

**Likely cause:** The algorithm preserves graph structure rather than compact label numbering.

**Fix:**

- Run `relabel_sequential` after the graph operation.
- Use `join_segmentations` only when the two inputs have the same shape.
- Reuse the same `rng` or avoid assertions on exact label numbers when a graph cut is known to be version-sensitive.

## `clear_border` removes more than expected

**Symptom:** Border cleanup zeroes nearly everything.

**Likely cause:** `buffer_size` is too large, or the mask marks too much of the image as outside.

**Fix:**

- Start with `buffer_size=0`.
- If you provide `mask=`, make sure it is boolean and the same shape as the labels.
- Use `bgval` only when you want a nonzero background fill value.

## `expand_labels` tie pixels look inconsistent

**Symptom:** The exact ownership of equidistant pixels changes across versions or transposed inputs.

**Likely cause:** Tie-breaking depends on the distance transform implementation.

**Fix:**

- Avoid writing exact assertions for tie pixels.
- Test coarse invariants instead: label coverage, maximum growth distance, and absence of overlap.
- Use `spacing` when anisotropic geometry matters.

## Legacy `skimage.future` helpers warn or block

**Symptom:** Warnings mentioning `skimage.future`, or a segmentation notebook opens a GUI and waits forever.

**Likely cause:** You are using legacy or interactive helpers.

**Fix:**

- Treat `fit_segmenter`, `predict_segmenter`, and `TrainableSegmenter` as compatibility shims only.
- Expect `manual_polygon_segmentation` and `manual_lasso_segmentation` to block until the GUI interaction is complete.
- Keep these out of headless smoke tests unless you intentionally mock or skip the GUI.

## Active contour methods do not converge

**Symptom:** `chan_vese`, `active_contour`, or the morphological snake methods stay stuck or collapse.

**Likely cause:** The initialization or image type is unsuitable.

**Fix:**

- Match the init shape to the API: a polyline for `active_contour`, a level-set array for Chan-Vese and morphological snakes.
- Use grayscale input for `chan_vese` and `morphological_chan_vese`.
- For geodesic snakes, preprocess with `inverse_gaussian_gradient` or another edge-enhancing scalar image.
- Start from a simple `disk_level_set` or `checkerboard_level_set` before tuning parameters.
