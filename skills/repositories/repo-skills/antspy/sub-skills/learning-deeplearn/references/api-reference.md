# ANTsPy Learning and Deeplearn API Reference

This reference describes public `ants` APIs verified from the `antspyx` package inspection and distilled source/test evidence. Import with `import ants`. These helpers prepare images and arrays for learning workflows; they do not train neural-network models.

## Statistical Learning Helpers

| Function | Verified signature | Return contract | Key shape/usage notes |
|---|---|---|---|
| `ants.eig_seg` | `(mask, img_list, apply_segmentation_to_images=False, cthresh=0, smooth=1)` | `ANTsImage` segmentation with labels based on the image/component that has maximum absolute value at each mask voxel. | `mask` is a D-dimensional `ANTsImage` where voxels `> 0` are segmented. `img_list` can be a list/tuple of images or an already-built NumPy matrix. When images are supplied, rows correspond to images and columns to masked voxels. `smooth > 0` smooths per-image values before label assignment. |
| `ants.sparse_decom2` | `(inmatrix, inmask=(None, None), sparseness=(0.01, 0.01), nvecs=3, its=20, cthresh=(0, 0), statdir=None, perms=0, uselong=0, z=0, smooth=0, robust=0, mycoption=0, initialization_list=[], initialization_list2=[], ell1=10, prior_weight=0, verbose=False, rejector=0, max_based=False, version=1)` | `dict` with `projections`, `projections2`, `eig1`, `eig2`, and `summary` DataFrame with `corrs` and `pvalues`. | `inmatrix=(x, y)` must have equal row counts: `x.shape[0] == y.shape[0]`. Columns are variables/features. ANTsPy does not scale inputs internally. Optional masks can be `ANTsImage` objects or NumPy arrays. `robust > 0` raises `NotImplementedError`. `perms > 0` adds random permutation work. |
| `ants.initialize_eigenanatomy` | `(initmat, mask=None, initlabels=None, nreps=1, smoothing=0)` | `dict` with `initlist`, `mask`, and `enames`. | `initmat` can be a NumPy matrix whose rows are initial vectors, or a labeled `ANTsImage`. With image input, positive labels define initial components unless `initlabels` is supplied. Use its `initlist` and `mask` as initialization evidence for sparse decomposition workflows. |

## Patch Helpers

| Function | Verified signature | Return contract | Key shape/usage notes |
|---|---|---|---|
| `ants.extract_image_patches` | `(image, patch_size, max_number_of_patches='all', stride_length=1, mask_image=None, random_seed=None, return_as_array=False, randomize=True)` | List of NumPy patch arrays by default, or one NumPy patch batch when `return_as_array=True`. | Supports 2-D and 3-D images. `len(patch_size)` must equal `image.dimension`; every patch dimension must be no larger than the image. For scalar images with `return_as_array=True`, output shape is `(n_patches, *patch_size)`. For component images, output shape is `(n_patches, *patch_size, image.components)`. |
| `ants.reconstruct_image_from_patches` | `(patches, domain_image, stride_length=1, domain_image_is_mask=False)` | Reconstructed `ANTsImage` using `domain_image` geometry. | `patches` must have the same format as `extract_image_patches`. For stride-based full coverage, pass the same `stride_length` used during extraction. When `domain_image_is_mask=True`, patch placement is limited to mask-centered locations. Multi-component patches are reassembled as component images. |

### Patch Counting Rules

For `max_number_of_patches='all'`, ANTsPy iterates starts along each axis:

```python
range(0, image.shape[d] - patch_size[d] + 1, stride_length[d])
```

The full patch count is the product of those per-axis range lengths. Use this formula before extracting dense patches from large 3-D volumes.

For random extraction, `max_number_of_patches` must be an integer. With `mask_image`, patches are centered on non-zero mask voxels after pruning centers too close to the image edge. `random_seed` seeds Python's `random` module for patch start selection, not every NumPy-random helper elsewhere.

## Augmentation and Random Transform Helpers

| Function | Verified signature | Return contract | Key shape/usage notes |
|---|---|---|---|
| `ants.randomly_transform_image_data` | `(reference_image, input_image_list, segmentation_image_list=None, number_of_simulations=10, transform_type='affine', sd_affine=0.02, deformation_transform_type='bspline', number_of_random_points=1000, sd_noise=10.0, number_of_fitting_levels=4, mesh_size=1, sd_smoothing=4.0, input_image_interpolator='linear', segmentation_image_interpolator='nearestNeighbor')` | Dict with `simulated_images`, `simulated_transforms`, and `which_subject`; adds `simulated_segmentation_images` when segmentation input is supplied. | `input_image_list` is list-of-subjects, each subject is list-of-modalities. Returned `simulated_images[i][j]` is simulation `i`, modality `j`. `which_subject[i]` records the sampled subject index. Transform options are `translation`, `rotation`, `rigid`, `scaleShear`, `affine`, `deformation`, and `affineAndDeformation`. |
| `ants.data_augmentation` | `(input_image_list, segmentation_image_list=None, pointset_list=None, number_of_simulations=10, reference_image=None, transform_type='affineAndDeformation', noise_model='additivegaussian', noise_parameters=(0.0, 0.05), sd_simulated_bias_field=1.0, sd_histogram_warping=0.05, sd_affine=0.05, sd_deformation=0.2, output_numpy_file_prefix=None, verbose=False)` | Dict with `simulated_images`; optionally `simulated_segmentation_images` and/or `simulated_pointset_list`. Can also write NumPy arrays when `output_numpy_file_prefix` is supplied. | Wraps random spatial transforms, noise, simulated bias fields, histogram warping, and range rescaling. `reference_image` defaults to `input_image_list[0][0]`. Pointsets require invertible transform workflows and are returned as arrays in reference-image dimension. |

### Augmentation List Contracts

- Outer list axis: subject/case.
- Inner list axis: modality/channel image for that subject.
- Every inner image list should have the same modality count.
- Modalities within a subject should be co-registered in physical space.
- `segmentation_image_list[k]`, if supplied, corresponds to `input_image_list[k]` and is resampled/transformed with nearest-neighbor interpolation.
- If an input image does not match `reference_image` physical space, `randomly_transform_image_data` attempts to resample it to the reference domain before augmentation.

## One-Hot Segmentation Helpers

| Function | Verified signature | Return contract | Key shape/usage notes |
|---|---|---|---|
| `ants.segmentation_to_one_hot` | `(segmentations_array, segmentation_labels=None, channel_first_ordering=False)` | NumPy one-hot array. | Supports 2-D and 3-D segmentation arrays. If labels are omitted, `np.unique(segmentations_array)` defines channel order. Include background label, typically `0`, when specifying `segmentation_labels`. Channel-last output is `(*seg_shape, n_labels)`; channel-first output is `(n_labels, *seg_shape)`. |
| `ants.one_hot_to_segmentation` | `(one_hot_array, domain_image, channel_first_ordering=False)` | List of probability `ANTsImage` objects, one per label channel. | Uses `domain_image` geometry for each returned image. This function does not collapse probabilities to a single argmax label image; use downstream NumPy or segmentation logic if a hard label map is required. |

## Intensity Simulation and Matching Helpers

| Function | Verified signature | Return contract | Key shape/usage notes |
|---|---|---|---|
| `ants.histogram_warp_image_intensities` | `(image, break_points=(0.25, 0.5, 0.75), displacements=None, clamp_end_points=(False, False), sd_displacements=0.05, transform_domain_size=20)` | `ANTsImage` with warped intensities and original image geometry. | Normalizes intensities internally, fits a 1-D B-spline displacement curve, then rescales to original min/max. `break_points` as a tuple/list must lie in `[0, 1]`; as an integer it defines an evenly-spaced point count. `len(displacements)` must match the effective break-point count after clamping endpoints. |
| `ants.simulate_bias_field` | `(domain_image, number_of_points=10, sd_bias_field=1.0, number_of_fitting_levels=4, mesh_size=1)` | `ANTsImage` log-bias field in the domain image space. | Samples random spatial points and fits a low-frequency B-spline field. Use `np.exp(log_field.numpy())` or a power of that field to multiply intensities when simulating multiplicative bias. `mesh_size` can be scalar or one value per dimension. |
| `ants.regression_match_image` | `(source_image, reference_image, mask=None, poly_order=1, truncate=True)` | Matched `ANTsImage` copied into `source_image` geometry. | `source_image.shape` must equal `reference_image.shape`. Optional `mask` selects voxels for fitting. Uses scikit-learn `PolynomialFeatures` and `LinearRegression`; `poly_order=1` is linear matching. With `truncate=True`, matched values are clipped to the reference fit range. |

## Crop and Pad Utilities for Learning Shapes

| Function | Verified signature | Return contract | Key shape/usage notes |
|---|---|---|---|
| `ants.crop_image_center` | `(image, crop_size)` | Center-cropped `ANTsImage`. | `len(crop_size)` must match image dimension and every requested size must be <= the image size. |
| `ants.pad_image_by_factor` | `(image, factor)` | `ANTsImage` padded/cropped to dimensions divisible by `factor`. | `factor` can be scalar or one value per image dimension. Useful before patch or external CNN pipelines that require sizes divisible by pooling/downsampling factors. |
| `ants.pad_or_crop_image_to_size` | `(image, size)` | Center padded or cropped `ANTsImage` with the requested size. | Pads symmetrically when needed, then center-crops to the final `size`. Use for fixed-size learning inputs after deciding how to handle physical-space metadata. |

## Public-Export Caveat

`crop_image_from_center_point(image, center_point, patch_size)` appears in source helper code but was not present as public `ants.crop_image_from_center_point` in the verified `antspyx` 0.6.3 inspection. If a user needs this behavior, first check `hasattr(ants, "crop_image_from_center_point")` in the active environment. Otherwise use exported crop/pad helpers or implement a task-local helper with `ants.transform_physical_point_to_index`, `ants.crop_indices`, and `ants.resample_image_to_target`.

## Dependency Notes

- `sparse_decom2` and `initialize_eigenanatomy` rely on NumPy/Pandas/Statsmodels/SciPy-backed workflows plus ANTs compiled wrappers.
- `regression_match_image` requires scikit-learn, which is a declared `antspyx` dependency.
- Augmentation helpers call ANTs transform, displacement-field, noise, `iMath`, and B-spline utilities; keep simulations small for smoke tests.
