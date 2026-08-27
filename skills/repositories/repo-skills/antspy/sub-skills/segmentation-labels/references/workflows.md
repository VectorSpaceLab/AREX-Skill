# Segmentation and Label Workflows

These recipes are self-contained patterns for agents using `antspyx` through `import ants`. They intentionally avoid runtime dependence on repository files.

## Before Any Segmentation or Label Metric

1. Ensure every image is an `ANTsImage`; route image creation and IO to `image-core`.
2. Match physical domains before combining images: dimension, shape, spacing, origin, and direction must agree.
3. Use a binary mask in the same domain as the image for Atropos/k-means/prior workflows.
4. Keep labels discrete. If labels were transformed, use nearest-neighbor or label-safe interpolation in `registration-transforms`.
5. For label statistics and geometry, validate labels are nonnegative integers representable as `uint32`.

```python
import ants

if not ants.image_physical_space_consistency(image, mask):
    raise ValueError("image and mask are not in the same physical space")
mask = (mask > 0).clone("unsigned int")
```

## Fast K-Means Segmentation

Use k-means when you need quick tissue-like classes plus posterior probability images.

```python
mask = ants.get_mask(image, cleanup=0)
seg = ants.kmeans_segmentation(image, k=3, kmask=mask, mrf=0.1)
labels = seg["segmentation"]
posteriors = seg["probabilityimages"]
```

Practical notes:

- `k` is the number of classes inside the mask.
- Class labels are ordered by intensity of the first image because the wrapper initializes Atropos with `kmeans[k]`.
- `posteriors` is a list with one probability image per class. Use the list order consistently when passing priors to `prior_based_segmentation` or `kelly_kapowski`.
- The wrapper creates a mask when `kmask=None`, but explicit masks are safer for small images or non-brain domains.

## Direct Atropos Workflow

Use direct Atropos for multivariate features, explicit convergence, MRF neighborhoods, or prior probability images.

```python
features = [image, ants.iMath(image, "Grad")]
mask = ants.get_mask(image, cleanup=0)
seg = ants.atropos(
    a=features,
    x=mask,
    i="Kmeans[3]",
    m="[0.2,1x1]",
    c="[5,0]",
    priorweight=0.25,
)
labels = seg["segmentation"]
posteriors = seg["probabilityimages"]
```

Rules:

- For 2-D images, MRF neighborhoods look like `1x1`; for 3-D images, use `1x1x1`.
- For multivariate segmentation, each feature image must already match the first image's domain.
- If using `i=prior_images`, provide exactly one prior probability image per class. The output class order follows the prior-list order.
- If Atropos exits nonzero or returns no probability images, run with verbose backend options only in a debugging environment, then check mask extent and initialization.

## Otsu Threshold Segmentation

Use Otsu for quick threshold labels when probability maps are not required.

```python
labels = ants.otsu_segmentation(image, k=3, mask=mask)
```

Notes:

- `k` threshold classes can produce labels `0..k` because background is included.
- If `mask` is supplied, the image is masked before thresholding.
- Route generic thresholding and mask cleanup to `image-ops-math`; return here for label stats/overlap.

## Prior-Based Refinement

Use this when existing posterior maps should initialize or constrain segmentation.

```python
initial = ants.kmeans_segmentation(image, k=3, kmask=mask)
priors = initial["probabilityimages"]
refined = ants.prior_based_segmentation(
    image=image,
    priors=priors,
    mask=mask,
    priorweight=0.25,
    mrf=0.1,
    iterations=10,
)
```

Checklist:

- Priors must match the image/mask domain and class count.
- Keep the list order stable; downstream class labels correspond to the prior order.
- Use `priorweight=0` for initialization-only behavior, or higher values such as `0.25`/`0.5` when priors should constrain the result.

## Fuzzy Spatial C-Means

Use fuzzy spatial c-means for a Python-level fuzzy segmentation with spatial neighborhood smoothing.

```python
fuzzy = ants.fuzzy_spatial_cmeans_segmentation(
    image,
    mask=mask,
    number_of_clusters=3,
    radius=1,
    max_number_of_iterations=10,
)
labels = fuzzy["segmentation_image"]
posteriors = fuzzy["probability_images"]
```

Remember the key names differ from Atropos. `radius` can be a scalar or dimension-length tuple.

## Joint Label Fusion

Use joint label fusion only after atlas intensity images and atlas label images are already in the target image domain.

```python
fusion = ants.joint_label_fusion(
    target_image=target,
    target_image_mask=target_mask,
    atlas_list=warped_atlas_images,
    label_list=warped_atlas_labels,
    rad=[1] * target.dimension,
    r_search=2,
    verbose=False,
)
labels = fusion["segmentation"]
probability_images = fusion["probabilityimages"]
label_numbers = fusion["segmentation_numbers"]
```

Safety and routing:

- Perform atlas registration and transform application in `registration-transforms`.
- Apply transforms to label images with nearest-neighbor or label-safe interpolation.
- Keep `rad`, `r_search`, atlas count, and registration iterations small for tests.
- If `label_list=None`, `joint_label_fusion` returns an intensity-fusion `ANTsImage`, not a label dictionary.
- Avoid `max_lab_plus_one=True` unless you can tolerate mutation of the input label images.

## KellyKapowski Cortical Thickness Boundary

`kelly_kapowski` is label/probability dependent and computationally heavier than simple label metrics.

```python
seg = ants.kmeans_segmentation(image, k=3, kmask=mask)
thickness = ants.kelly_kapowski(
    s=seg["segmentation"],
    g=seg["probabilityimages"][1],
    w=seg["probabilityimages"][2],
    its=20,
    r=0.5,
    m=1.0,
    gm_label=2,
    wm_label=3,
)
```

Confirm that the gray/white probability images correspond to `gm_label` and `wm_label`. If class ordering is unclear, inspect intensity means or relabel deliberately before thickness estimation.

## Functional Lung Segmentation Boundary

Use `functional_lung_segmentation` only for 3-D masked ventilation-style lung segmentation.

```python
lung = ants.functional_lung_segmentation(
    image,
    mask=mask,
    number_of_iterations=1,
    number_of_atropos_iterations=1,
    number_of_clusters=3,
    bias_correction="n4",
    verbose=False,
)
labels = lung["segmentation_image"]
posteriors = lung["probability_images"]
processed = lung["processed_image"]
```

For 2-D images, missing masks, or generic threshold tasks, choose k-means, Atropos, or Otsu instead.

## Label Statistics and Geometry

Use `label_stats` when you need intensities by label; use `label_geometry_measures` when you need shape/volume descriptors.

```python
stats = ants.label_stats(image, labels)
geom = ants.label_geometry_measures(labels, image)
```

Expect pandas DataFrames. For geometry, important columns include `Label`, `VolumeInVoxels`, `VolumeInMillimeters`, centroids, bounding boxes, and intensity summaries when an intensity image is provided. For statistics, sort order follows `LabelValue`.

## Label Overlap and Physical-Space Validation

Use overlap metrics only after label images are in the same physical domain.

```python
if not ants.image_physical_space_consistency(source_labels, target_labels):
    raise ValueError("resample/apply transforms before overlap")
overlap = ants.label_overlap_measures(source_labels, target_labels)
all_row = overlap.loc[overlap["Label"] == "All"]
```

Do not use overlap to compare labels with different class semantics. Align label value conventions first.

## Labels to Matrix

Use `labels_to_matrix` when downstream code needs one binary row per label inside a mask.

```python
matrix = ants.labels_to_matrix(labels, mask, target_labels=[0, 1, 2, 3], missing_val=0.0)
```

The output shape is `(len(target_labels), number_of_mask_voxels)` when `target_labels` is provided. Without `target_labels`, rows correspond to sorted unique values found in `labels[mask > 0]`, including background when present.

## Connected Components and Multi-Label Morphology

```python
clusters = ants.label_clusters(stat_image, min_cluster_size=10, min_thresh=2.5, max_thresh=1e15)
cluster_images = ants.image_to_cluster_images(stat_image, min_cluster_size=10, min_thresh=2.5, max_thresh=1e15)
dilated = ants.multi_label_morphology(labels, "MD", radius=1, dilation_mask=mask)
```

Use `label_clusters` for component IDs, `image_to_cluster_images` for separate component images, and `multi_label_morphology` when each label should be morphed independently. For generic binary or grayscale morphology, route to `image-ops-math`.

## Centroids and Point Images

```python
centroids = ants.get_centroids(clusters, clustparam=0)
label_centroids = ants.label_image_centroids(label_image_3d, convex=True)
points_image = ants.make_points_image(points_array, target=image, radius=3)
point_stats = ants.label_stats(image, points_image)
```

- `make_points_image` expects physical-space coordinates with one coordinate column per image dimension.
- `label_image_centroids` is 3-D only and returns voxel-space vertices in the current implementation.
- Use image-core coordinate helpers when converting between indices and physical points.

## Aligning Labels with Registration and Masks

When labels come from another image domain:

1. Use `registration-transforms` to register intensity images and apply transforms.
2. Apply transforms to label images with nearest-neighbor or label-safe interpolation.
3. Validate physical-space consistency between transformed labels, target image, and mask.
4. Clone/cast labels to `unsigned int` only after confirming values are discrete and nonnegative.
5. Compute label statistics, overlap, or matrices in this sub-skill.

```python
warped_labels = ants.apply_transforms(
    fixed=target,
    moving=moving_labels,
    transformlist=tx["fwdtransforms"],
    interpolator="nearestNeighbor",
)
if not ants.image_physical_space_consistency(warped_labels, target):
    raise ValueError("warped labels are not aligned to target")
stats = ants.label_stats(target, warped_labels)
```
