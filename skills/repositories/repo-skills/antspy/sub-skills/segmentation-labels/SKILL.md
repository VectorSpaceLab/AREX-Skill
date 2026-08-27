---
name: segmentation-labels
description: "Use ANTsPy segmentation and label workflows for Atropos, k-means,
  Otsu, priors, joint label fusion, label statistics, overlap, geometry,
  matrices, centroids, points, and multi-label morphology."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# ANTsPy Segmentation and Labels

Use this sub-skill when a task asks for ANTsPy segmentation, label images, connected components, label statistics, overlap/geometry measures, label matrices, centroid or point-image workflows, multi-label morphology, or segmentation-to-mask/registration handoffs.

## Start Here

1. Import the public package as `import ants`; the package distribution is `antspyx`.
2. Check verified signatures and return contracts in [API reference](references/api-reference.md).
3. Pick a recipe from [workflows](references/workflows.md): k-means, Atropos, Otsu, prior-based segmentation, joint label fusion, label stats/overlap/matrix, point images, or mask alignment validation.
4. Use [troubleshooting](references/troubleshooting.md) before changing class counts, masks, priors, label dtypes, or physical metadata.
5. Run [scripts/antspy_segmentation_smoke.py](scripts/antspy_segmentation_smoke.py) for a tiny deterministic in-memory check in an environment with `antspyx` installed.

## Core Contracts

- `ants.atropos(...)`, `ants.kmeans_segmentation(...)`, and `ants.prior_based_segmentation(...)` return dictionaries with `segmentation` and `probabilityimages`; `ants.otsu_segmentation(...)` returns only an `ANTsImage` label image.
- `ants.joint_label_fusion(...)` returns an `ANTsImage` for intensity-only fusion when no labels are supplied, and a dictionary with `segmentation`, `intensity`, `probabilityimages`, and `segmentation_numbers` when `label_list` is supplied.
- `ants.fuzzy_spatial_cmeans_segmentation(...)` and `ants.functional_lung_segmentation(...)` use snake_case keys `segmentation_image` and `probability_images`; lung segmentation also returns `processed_image`.
- Label-measure helpers generally clone labels to `unsigned int`; non-integer or out-of-range labels can fail or silently collapse if not validated first.
- Overlap, statistics, matrices, and label/image interactions assume matching dimension, shape, origin, spacing, and direction; validate with image-core helpers before computing metrics.
- Register intensity images with registration-transforms, apply transforms to labels with nearest-neighbor or label-safe interpolation, then return here for label statistics and overlap.

## Route Elsewhere

- Image creation, IO, cloning, metadata repair, dtype conversion, `image_physical_space_consistency`, and coordinate transforms: [image-core](../image-core/SKILL.md).
- Generic masks, thresholding, binary/grayscale morphology, smoothing, resampling, bias correction, and `iMath`: [image-ops-math](../image-ops-math/SKILL.md).
- Registration mechanics, transform lists, and label-safe transform application: [registration-transforms](../registration-transforms/SKILL.md).
- Plotting label overlays or exporting images for visualization: [visualization-interop](../visualization-interop/SKILL.md).
- Learning one-hot segmentation, patch extraction, and augmentation workflows: [learning-deeplearn](../learning-deeplearn/SKILL.md).

## References

- [API reference](references/api-reference.md): verified public signatures, return keys, label dataframe contracts, dtype rules, and expensive-function caveats.
- [Workflows](references/workflows.md): self-contained recipes for segmentation, priors, labels, overlap/statistics, label matrices, centroids, points, and registration/mask interactions.
- [Troubleshooting](references/troubleshooting.md): Atropos probability failures, mask/image mismatch, class ordering, label dtype handling, joint label fusion/KellyKapowski costs, and physical-space consistency before overlap.
