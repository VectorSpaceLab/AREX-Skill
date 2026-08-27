# ANTsPy Learning and Deeplearn Workflows

These recipes assume inputs are already `ants.ANTsImage` objects or NumPy arrays. For image construction and physical-space repair, use [image-core](../../image-core/SKILL.md). For registration outside random augmentation helpers, use [registration-transforms](../../registration-transforms/SKILL.md).

## Extract and Reconstruct Dense Patches

Use dense patch extraction when every sliding-window patch is needed and the count is bounded:

```python
patch_size = (4, 4)
stride = (2, 2)
patches = ants.extract_image_patches(
    image,
    patch_size=patch_size,
    max_number_of_patches="all",
    stride_length=stride,
    return_as_array=True,
)
reconstructed = ants.reconstruct_image_from_patches(
    patches,
    domain_image=image,
    stride_length=stride,
)
assert reconstructed.shape == image.shape
```

Before extraction, estimate count:

```python
import math
count = math.prod(
    len(range(0, image.shape[d] - patch_size[d] + 1, stride[d]))
    for d in range(image.dimension)
)
```

Validation checklist:

- `len(patch_size) == image.dimension`.
- `patch_size[d] <= image.shape[d]` for every axis.
- Use the same `stride_length` for reconstruction that was used for dense extraction.
- For component images, expect a trailing component axis in the patch array.
- For large 3-D images, calculate patch count first to avoid unbounded memory use.

## Random or Masked Patch Sampling

Use random sampling for small training batches or masked foreground sampling:

```python
mask = ants.get_mask(image, cleanup=0)
patches = ants.extract_image_patches(
    image,
    patch_size=(16, 16),
    max_number_of_patches=32,
    mask_image=mask,
    random_seed=11,
    return_as_array=True,
)
```

Rules:

- Random extraction requires integer `max_number_of_patches`.
- With `mask_image`, each patch is chosen so its center is a non-zero mask voxel after edge pruning.
- `random_seed` controls Python `random` sampling inside patch extraction. It does not seed all other ANTsPy augmentation helpers.
- If `randomize=False` with a mask, ANTsPy returns pruned mask-centered locations in mask index order and may return fewer than requested patches.

## Track Randomly Transformed Paired Images

Use `randomly_transform_image_data` when spatial augmentation must keep modalities and labels paired:

```python
import numpy as np
np.random.seed(7)

result = ants.randomly_transform_image_data(
    reference_image=reference,
    input_image_list=[[modality_a, modality_b]],
    segmentation_image_list=[label_image],
    number_of_simulations=2,
    transform_type="affine",
    sd_affine=0.01,
    input_image_interpolator="linear",
    segmentation_image_interpolator="nearestNeighbor",
)

sim0_mod0 = result["simulated_images"][0][0]
sim0_mod1 = result["simulated_images"][0][1]
sim0_label = result["simulated_segmentation_images"][0]
sim0_transform = result["simulated_transforms"][0]
which_subject = int(result["which_subject"][0])
```

Validation checklist:

- `len(result["simulated_images"]) == number_of_simulations`.
- Each simulation contains the same number of modalities as the selected subject.
- `which_subject[i]` is the source subject index for simulation `i`.
- Use nearest-neighbor interpolation for segmentation images.
- Keep `simulated_transforms` with the generated images if points, labels, or external annotations must be audited later.
- If input images differ from `reference_image` physical space, ANTsPy may resample them internally; explicitly check and resample beforehand when this would be surprising.

## Apply Full Data Augmentation Without Training

Use `data_augmentation` for a bundled helper pipeline that combines spatial transforms, noise, bias-field simulation, histogram warping, and intensity rescaling:

```python
aug = ants.data_augmentation(
    input_image_list=[[image]],
    segmentation_image_list=[label_image],
    number_of_simulations=2,
    reference_image=image,
    transform_type="affine",
    noise_model="additivegaussian",
    noise_parameters=(0.0, 0.02),
    sd_simulated_bias_field=0.1,
    sd_histogram_warping=0.02,
    sd_affine=0.01,
)

simulated_images = aug["simulated_images"]
simulated_labels = aug.get("simulated_segmentation_images")
```

Use bounded parameters in tests:

- Reduce `number_of_simulations` to `1` or `2`.
- Prefer `transform_type="affine"` for fast checks.
- Set `sd_simulated_bias_field=0` and `sd_histogram_warping=0` if a spatial-only check is sufficient.
- Avoid `noise_model="speckle"` in smoke tests; it is documented as slower.
- Use `output_numpy_file_prefix` only when the task explicitly needs `.npy` artifacts in a task-owned output directory.

## Convert Segmentations to One-Hot Arrays

Channel-last is the default and is often easier for NumPy-first pipelines:

```python
labels = [0, 1, 2]
seg_array = segmentation.numpy().astype("int32")
one_hot = ants.segmentation_to_one_hot(
    seg_array,
    segmentation_labels=labels,
    channel_first_ordering=False,
)
assert one_hot.shape == (*seg_array.shape, len(labels))
probability_images = ants.one_hot_to_segmentation(one_hot, segmentation)
```

Use channel-first only when the downstream framework expects it:

```python
one_hot_cf = ants.segmentation_to_one_hot(
    seg_array,
    segmentation_labels=labels,
    channel_first_ordering=True,
)
assert one_hot_cf.shape == (len(labels), *seg_array.shape)
probability_images_cf = ants.one_hot_to_segmentation(
    one_hot_cf,
    segmentation,
    channel_first_ordering=True,
)
```

Validation checklist:

- Include background in `segmentation_labels` when background is meaningful.
- Preserve label ordering explicitly; relying on `np.unique` may reorder channels numerically.
- `one_hot_to_segmentation` returns one probability image per channel, not an argmax segmentation.
- To build a hard segmentation, compute `np.argmax(one_hot, axis=channel_axis)` and map indices back to label values before creating an `ANTsImage`.

## Simulate Bias Fields and Histogram Warps

Use these helpers for intensity perturbation experiments, not for scanner-validated harmonization:

```python
import numpy as np

np.random.seed(13)
log_bias = ants.simulate_bias_field(
    image,
    number_of_points=4,
    sd_bias_field=0.2,
    number_of_fitting_levels=2,
    mesh_size=2,
)
bias = np.exp(log_bias.numpy())
biased = image * ants.from_numpy_like(bias, image)

warped = ants.histogram_warp_image_intensities(
    image,
    break_points=(0.25, 0.5, 0.75),
    displacements=(0.02, -0.01, 0.015),
    clamp_end_points=(True, True),
    transform_domain_size=8,
)
```

Rules:

- `simulate_bias_field` returns a log field; exponentiate before multiplicative intensity simulation.
- Keep `number_of_points`, fitting levels, and domain size small in tests.
- For deterministic histogram warping, pass explicit `displacements`; otherwise ANTsPy samples random displacements.
- `break_points` must be in `[0, 1]`; clamped endpoints add zero-displacement endpoint constraints.

## Match Source Intensities to a Reference

Use polynomial regression matching when source and reference have the same voxel shape:

```python
mask = ants.get_mask(reference_image, cleanup=0)
matched = ants.regression_match_image(
    source_image,
    reference_image,
    mask=mask,
    poly_order=1,
    truncate=True,
)
```

Validation checklist:

- `source_image.shape == reference_image.shape` is required.
- Ensure `mask` is non-empty and in the same physical space as both images.
- `poly_order=1` is usually the safest first pass; higher orders can overfit tiny or narrow-intensity masks.
- With `truncate=True`, output intensities are clipped to the reference fit range.

## Prepare Fixed Learning Shapes With Crop and Pad Helpers

Use exported crop/pad helpers for shape constraints before patch extraction or external model input:

```python
fixed = ants.pad_or_crop_image_to_size(image, (128, 128))
multiple_of_16 = ants.pad_image_by_factor(fixed, 16)
center = ants.crop_image_center(multiple_of_16, (96, 96))
```

Rules:

- `crop_size`, `size`, and vector `factor` lengths must match image dimension.
- `crop_image_center` rejects crop sizes larger than the image.
- `pad_image_by_factor` pads up to the next size divisible by the factor.
- For general crop/pad/mask/resample preprocessing details, route to [image-ops-math](../../image-ops-math/SKILL.md).

## Segment by Eigenimage Maximum

Use `eig_seg` when a list of images or component matrix already represents competing component strengths:

```python
mask = ants.get_mask(image0, cleanup=0)
seg = ants.eig_seg(mask, [component0, component1, component2], smooth=0, cthresh=0)
```

Notes:

- Labels are one-based indices of the component with largest absolute value at each mask voxel.
- `cthresh > 0` removes small connected clusters after assignment.
- `apply_segmentation_to_images=True` mutates the supplied image list by zeroing values outside each assigned component; only enable it when mutation is intended.
- If supplying a NumPy matrix, rows should correspond to component images and columns to masked voxels.

## Run Sparse CCA Decomposition

Use `sparse_decom2` for paired matrix decomposition, not image registration or neural-network training:

```python
x = np.asarray(x, dtype="float64")
y = np.asarray(y, dtype="float64")
if x.shape[0] != y.shape[0]:
    raise ValueError("sparse_decom2 requires equal sample rows")

result = ants.sparse_decom2(
    inmatrix=(x, y),
    sparseness=(0.1, 0.2),
    nvecs=2,
    its=5,
    perms=0,
)
summary = result["summary"]
```

Validation checklist:

- Center/scale matrices before calling if the analysis requires it; ANTsPy does not scale internally.
- Start with small `nvecs`, low `its`, and `perms=0` for smoke checks.
- Use `initialize_eigenanatomy` output only when masks/vectors match the decomposition feature layout.
- `perms > 0` increases runtime and introduces additional randomness.
