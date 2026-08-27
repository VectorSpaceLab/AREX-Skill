# Segmentation and Label Troubleshooting

## Atropos Returns No Probability Images

Symptoms:

- Exception similar to `No Atropos output probability images found`.
- Nonzero Atropos status.
- `kmeans_segmentation` fails because it wraps Atropos.

Checks and fixes:

- Ensure the mask is nonempty: `int(mask.sum()) > 0`.
- Ensure mask and image share dimension, shape, spacing, origin, and direction.
- Use a dimension-correct MRF string: `"[0.2,1x1]"` for 2-D and `"[0.2,1x1x1]"` for 3-D.
- Use a feasible class count for the number of distinct intensities inside the mask.
- If using prior images, provide one prior per class and validate each prior matches the image domain.
- Retry with a tiny iteration count and verbose backend options only for diagnosis; do not turn verbose logs into a runtime dependency.

## Mask/Image Mismatch

Symptoms:

- Indexing errors from `image[mask > 0]`.
- Empty segmentation or all-background labels.
- Label matrices with unexpected voxel counts.
- Overlap values that look impossible.

Checks and fixes:

- Check `ants.image_physical_space_consistency(image, mask)` before segmentation, statistics, or matrices.
- Confirm `image.shape == mask.shape` as a quick voxel-domain check.
- Convert masks to binary after any arithmetic: `mask = (mask > 0).clone("unsigned int")`.
- Resample masks to the target domain with nearest-neighbor or label-safe interpolation; route transform mechanics to `registration-transforms`.
- Disable aggressive cleanup for very small synthetic images: `ants.get_mask(image, cleanup=0)`.

## Class Ordering Is Not What You Expected

Symptoms:

- Gray matter and white matter are swapped.
- `kelly_kapowski` receives the wrong posterior image.
- Prior-based segmentation produces valid labels with unexpected semantics.

Checks and fixes:

- K-means/Atropos classes initialized with `Kmeans[N]` are ordered by intensity of the first input image.
- Prior-based classes follow the order of the prior probability image list.
- Otsu can include background as label `0`, so `k=3` may produce four values: `0`, `1`, `2`, `3`.
- Compute `ants.label_stats(image, segmentation)` and inspect per-label means before assigning anatomical names.
- Relabel deliberately if downstream code expects fixed label numbers.

## Label Dtype or Value Errors

Symptoms:

- `Input label values must be representable as uint32`.
- Geometry output has invalid labels.
- Fractional transformed labels create too many classes.

Checks and fixes:

- Validate that label values are discrete before calling label measures.
- Avoid linear interpolation for labels; use nearest-neighbor or label-safe interpolation when applying transforms.
- Keep labels nonnegative and within `uint32` range.
- For `multi_label_morphology`, confirm background is `0` and labels are positive integers.
- If more than 200 labels are intentionally present, pass `force=True`; otherwise treat this as evidence that a continuous image was passed by mistake.

## Label Statistics or Geometry Looks Wrong

Symptoms:

- Counts/volumes do not match expectations.
- Centroids are shifted.
- Geometry rows are missing labels.

Checks and fixes:

- Confirm intensity image and label image occupy the same physical space.
- Check that labels exist inside the target mask or intensity-image domain.
- For `label_geometry_measures`, pass the intensity image only when intensity summaries are meaningful in the label domain.
- Remember `VolumeInMillimeters` equals voxel count times spacing product when the backend does not provide it directly.
- `label_image_centroids` returns voxel-space vertices and requires a 3-D image; use image-core coordinate transforms if physical points are needed.

## Overlap Measures Before Alignment

Symptoms:

- Dice/mean overlap is unexpectedly low.
- Row `Label == 'All'` looks plausible but per-label rows are nonsensical.
- Comparing labels from different subjects or spaces gives misleading metrics.

Checks and fixes:

- Validate physical-space consistency before overlap.
- If one label image comes from registration, inspect the transform direction and interpolation in `registration-transforms`.
- Confirm source and target label values mean the same structures.
- Crop or mask both labels only after they are aligned; do not compare labels from different voxel grids directly.

## Joint Label Fusion Is Too Slow or Returns Unexpected Shape

Symptoms:

- `joint_label_fusion` takes much longer than expected.
- Output is an `ANTsImage` when a dictionary was expected.
- Probability image count does not match label assumptions.

Checks and fixes:

- Passing no `label_list` requests intensity fusion and returns an `ANTsImage`; pass aligned label images to get segmentation probabilities.
- Reduce atlas count, `rad`, and `r_search` for debugging.
- Set thread counts outside the skill workflow if needed; do not bake machine-specific settings into reusable skill content.
- Validate every atlas image and label image is already in target space.
- Use `rad=[r] * target.dimension` to avoid dimensionality errors.
- Avoid `max_lab_plus_one=True` unless intended because it can modify label images and changes background handling.

## KellyKapowski Fails or Produces All Zeros

Symptoms:

- Runtime error that KellyKapowski failed to compute thickness.
- Thickness image is all zeros.

Checks and fixes:

- Ensure segmentation labels include the configured `gm_label` and `wm_label`.
- Ensure gray and white probability images correspond to those labels and match the segmentation domain.
- Use realistic 3-D tissue-like inputs; tiny synthetic images are often not suitable.
- Lower iterations only for smoke/debugging; do not interpret a bounded debug run as scientifically meaningful thickness.

## Functional Lung Segmentation Boundaries

Symptoms:

- Error that function only works for 3-D images.
- Error that mask is missing.
- Unexpected class count or slow runtime.

Checks and fixes:

- Use only 3-D images with a nonempty binary mask.
- Set low `number_of_iterations` and `number_of_atropos_iterations` for bounded checks.
- Provide `cluster_centers` with exactly `number_of_clusters` values when using custom centers.
- Route generic 2-D or non-lung segmentation tasks to k-means, Atropos, or Otsu.

## Missing Labels in `labels_to_matrix`

Symptoms:

- Rows are filled with `nan` or `missing_val`.
- Matrix has fewer rows than expected.

Checks and fixes:

- Pass explicit `target_labels` when row order matters.
- Confirm the requested label exists within `mask > 0`, not merely somewhere in the image.
- Use `missing_val=0.0` when downstream code cannot handle `nan`.
- Validate mask alignment before interpreting row sums.

## Point Images and Centroids Are Misplaced

Symptoms:

- `make_points_image` silently omits points.
- Point labels are shifted relative to anatomy.
- Centroids are in voxel coordinates when physical coordinates were expected.

Checks and fixes:

- `make_points_image` expects physical-space coordinates and ignores points outside the target image.
- `pts.shape[1]` must equal `target.dimension`.
- Use image-core coordinate transforms to convert voxel indices to physical points before making a points image.
- `label_image_centroids(..., physical=True)` currently returns voxel-space vertices; transform them explicitly if physical points are required.
