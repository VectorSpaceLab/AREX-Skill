---
name: learning-deeplearn
description: "Use ANTsPy statistical learning and deep-learning helper utilities
  for decompositions, patches, augmentation, one-hot labels, and bounded
  array/image preparation without training neural networks."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# ANTsPy Learning and Deeplearn Helpers

Use this sub-skill when a task asks for ANTsPy helper utilities around statistical learning, sparse decomposition, eigenanatomy initialization, patch extraction/reconstruction, random augmentation, one-hot segmentation arrays, simulated bias fields, histogram intensity warping, regression intensity matching, or crop/pad sizing for learning pipelines.

## Start Here

1. Import the public package as `import ants`; the package distribution is `antspyx`.
2. Keep the scope clear: ANTsPy supplies helper functions for image/array preparation and statistical decomposition, not full neural-network model training.
3. Check verified public signatures, return keys, and shape contracts in [API reference](references/api-reference.md).
4. Use [workflows](references/workflows.md) for patch extraction/reconstruction, paired augmentation, one-hot conversion, intensity simulation, regression matching, and decomposition recipes.
5. Use [troubleshooting](references/troubleshooting.md) when dimensions, channel order, paired image lists, randomness, optional dependencies, or patch counts fail.
6. Run [scripts/antspy_deeplearn_smoke.py](scripts/antspy_deeplearn_smoke.py) for a tiny bounded in-memory helper check in an environment with `antspyx` installed.

## Core Contracts

- `ants.deeplearn` helpers are data-preparation utilities: they produce images, arrays, transforms, and labels that can feed external ML code; they do not define, compile, fit, or evaluate neural-network models.
- `input_image_list` for augmentation is a list of subject lists, where each inner list holds co-registered modalities for one subject: `[[subject0_mod0, subject0_mod1], [subject1_mod0, subject1_mod1]]`.
- Patch utilities support 2-D and 3-D scalar or component images. Array patches are shaped as `(n_patches, *patch_size)` for scalar images and `(n_patches, *patch_size, components)` for component images.
- One-hot conversion uses channel-last by default (`(*image_shape, n_labels)`) and channel-first only when `channel_first_ordering=True` (`(n_labels, *image_shape)`).
- Random augmentation and simulation helpers use NumPy and Python randomness internally; set seeds around calls when repeatability matters, and verify returned transform metadata before pairing outputs with labels or points.
- `ants.sparse_decom2` expects two matrices with the same row count; it does not scale matrices internally, so center/scale decisions belong to the caller.

## Route Elsewhere

- Create, read, write, inspect, clone, compare, and repair `ANTsImage` metadata: [image-core](../image-core/SKILL.md).
- Generic preprocessing, masks, smoothing, denoising, thresholding, morphology, core cropping/padding, resampling, and histogram matching: [image-ops-math](../image-ops-math/SKILL.md).
- Registration mechanics, transform files, transform application, displacement fields, and point transform semantics outside augmentation helpers: [registration-transforms](../registration-transforms/SKILL.md).
- Segmentation algorithms, label statistics, overlap, centroids, label geometry, and label matrices: [segmentation-labels](../segmentation-labels/SKILL.md).
- Full model training, ANTsPyNet architectures, loss functions, pretrained networks, and deep learning inference workflows: use ANTsPyNet or another ML framework outside this ANTsPy repo skill.

## Boundary Notes

- The module name `ants.deeplearn` is historical and helper-oriented. Do not promise model-training support from ANTsPy itself.
- `crop_image_from_center_point` exists in source helper code but was not exported as a public `ants` function in the verified `antspyx` 0.6.3 inspection; prefer exported crop/pad helpers unless runtime introspection proves availability.
- `data_augmentation` and `randomly_transform_image_data` internally use transform and preprocessing functions. Use this sub-skill for their learning-helper contract; use registration or image-ops sub-skills to debug low-level transform/preprocessing behavior.

## References

- [API reference](references/api-reference.md): verified signatures, return keys, shape/axis contracts, dependencies, and public-export caveats.
- [Workflows](references/workflows.md): practical helper recipes for patches, augmentation, one-hot arrays, intensity perturbation, regression matching, crop/pad sizing, and decomposition.
- [Troubleshooting](references/troubleshooting.md): shape/axis mismatch, paired transform tracking, randomness, memory/patch count, optional dependency, and helper-vs-training boundaries.
