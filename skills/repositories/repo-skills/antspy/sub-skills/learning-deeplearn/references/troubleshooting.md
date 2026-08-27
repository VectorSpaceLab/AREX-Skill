# ANTsPy Learning and Deeplearn Troubleshooting

Use this reference for helper-level failures in ANTsPy learning/deeplearn utilities. For installation/import and core `ANTsImage` metadata issues, start with the root skill and [image-core](../../image-core/SKILL.md).

## Helper vs. Training Boundary

Symptoms:

- User asks ANTsPy to define, train, compile, or evaluate a neural network.
- Task mentions ANTsPyNet architectures, pretrained deep models, TensorFlow/Keras/PyTorch losses, or GPU training.
- Agent tries to find `fit`, `model`, or network layers in `ants.deeplearn`.

Resolution:

- State that ANTsPy's `deeplearn` module contains helper utilities for patches, augmentation, one-hot labels, and intensity perturbation.
- Route full neural-network workflows to ANTsPyNet or an external ML framework.
- Use this sub-skill only to prepare images/arrays/transforms that a separate training pipeline can consume.

## Shape and Axis Mismatches

Common failures:

- `ValueError: Mismatch between the image size and the specified patch size.`
- `ValueError: Patch size is greater than the image size.`
- `ValueError: stride_length is not a scalar or vector of length dimensionality.`
- One-hot arrays appear transposed or the label channel is treated as a spatial axis.
- `ants.regression_match_image` raises because source and reference shapes differ.

Fixes:

- Check `image.dimension`, `image.shape`, `image.components`, and all requested tuple lengths before calling helpers.
- Use `patch_size` with exactly one value per spatial dimension.
- Use integer `stride_length` for isotropic strides or a tuple with one value per dimension.
- Remember patch arrays are channel-last for component images: `(n_patches, *patch_size, components)`.
- Remember one-hot arrays are channel-last by default and channel-first only when `channel_first_ordering=True`.
- Match `source_image.shape` and `reference_image.shape` before regression matching; if resampling is appropriate, route shape/space decisions to [image-ops-math](../../image-ops-math/SKILL.md).

## Paired Image, Segmentation, and Transform Tracking

Symptoms:

- Augmented labels no longer align with augmented images.
- Multi-modal outputs have an unexpected modality count.
- Source subject identity is unclear after random augmentation.
- Points or external annotations do not map back to the simulated image.

Fixes:

- Use `input_image_list` as `subjects -> modalities`: `[[sub0_mod0, sub0_mod1], [sub1_mod0, sub1_mod1]]`.
- Keep `segmentation_image_list[k]` paired with `input_image_list[k]`.
- Use `segmentation_image_interpolator="nearestNeighbor"` for labels.
- Read `result["which_subject"][i]` to identify which source subject produced simulation `i`.
- Preserve `result["simulated_transforms"][i]` alongside output images whenever points or external annotations must be audited.
- If physical-space consistency with `reference_image` matters, check it before augmentation instead of relying on implicit resampling.

## Randomness and Determinism

Symptoms:

- Patch samples, augmentation outputs, bias fields, histogram warps, or sparse decomposition permutation results change across runs.
- Setting `random_seed` in `extract_image_patches` did not make augmentation deterministic.

Fixes:

- `extract_image_patches(..., random_seed=N)` seeds Python's `random` module only for patch index sampling.
- Set `np.random.seed(N)` before helpers that use NumPy randomness, such as random transforms, bias fields, histogram displacements, and sparse-decomposition permutations.
- Set `random.seed(N)` before helpers that use Python `random`, such as `data_augmentation` noise choices and histogram displacement generation.
- Pass explicit `displacements` to `histogram_warp_image_intensities` when deterministic intensity warping is required.
- Keep `perms=0` in `sparse_decom2` for deterministic smoke checks unless empirical permutation p-values are the task.
- Record seeds and sampled `which_subject`/transform metadata in task outputs when reproducibility matters.

## Memory and Patch Count Explosions

Symptoms:

- Dense patch extraction hangs or exhausts memory on a 3-D volume.
- `return_as_array=True` allocates a very large batch.
- Reconstruction fails because the patch count does not match the expected placement count.

Fixes:

- Compute dense patch count before extraction with the formula in [workflows](workflows.md#extract-and-reconstruct-dense-patches).
- Increase `stride_length`, reduce `patch_size`, crop the domain first, or use integer `max_number_of_patches` for random sampling.
- Use `return_as_array=False` if list processing avoids a large contiguous allocation.
- Reconstruct only dense, compatible patch sets with the same stride/domain assumptions used for extraction.
- For masked reconstruction, confirm the number of supplied patches matches mask-centered placement after edge pruning.

## Optional Dependency and Compiled Backend Caveats

Symptoms:

- Import or runtime failure mentions scikit-learn, SciPy, statsmodels, or compiled ANTs wrapper functions.
- `regression_match_image` fails while importing polynomial or linear regression utilities.
- `sparse_decom2` fails in a compiled wrapper such as a sparse CCA backend.

Fixes:

- Verify the active environment imports `ants` from the public distribution `antspyx`.
- `antspyx` declares `scikit-learn`, `statsmodels`, `numpy`, and `pandas` dependencies; if missing, repair the package environment rather than editing skill code.
- Keep smoke tests small and in-memory to distinguish dependency/import failures from data-size failures.
- If a local source build is unavailable, prefer installed-wheel runtime inspection over assuming local compiled wrappers are present.

## Public Function Availability

Symptoms:

- `AttributeError: module 'ants' has no attribute 'crop_image_from_center_point'`.
- Source code mentions a helper that is absent from the installed `ants` namespace.

Fixes:

- Prefer verified exported helpers in [API reference](api-reference.md).
- Check `hasattr(ants, "crop_image_from_center_point")` before using source-only helpers.
- Use `ants.crop_image_center`, `ants.pad_or_crop_image_to_size`, `ants.pad_image_by_factor`, or task-local `crop_indices`/resampling logic when that helper is absent.

## Sparse Decomposition Inputs

Symptoms:

- `ValueError: Matrices must have same number of rows (samples)`.
- Components have unexpected order or scale.
- `robust > 0 not currently implemented`.
- Permutation runs are slow or non-repeatable.

Fixes:

- Ensure both matrices use rows as samples and columns as variables.
- Center and scale matrices explicitly before calling when analysis depends on standardized features.
- Leave `robust=0`; rank-transform externally if required.
- Start with low `its`, low `nvecs`, and `perms=0`; increase only for analysis-quality runs.
- If using masks or initialization lists, verify mask voxel counts match feature columns.

## One-Hot Conversion Pitfalls

Symptoms:

- Background is missing from one-hot channels.
- Channel order differs between training and inference.
- `one_hot_to_segmentation` output is a list, not a hard label image.

Fixes:

- Pass explicit `segmentation_labels`, including background label `0` when needed.
- Save the label list with downstream task outputs; channel index alone is ambiguous.
- Use `channel_first_ordering=True` only for frameworks that require `(channels, *spatial)`.
- Convert probability images or one-hot arrays to hard labels explicitly with an argmax and label lookup.

## Intensity Simulation and Matching Pitfalls

Symptoms:

- Histogram warp raises a displacement-length error.
- Bias field looks additive rather than multiplicative.
- Regression matching produces extreme intensities.

Fixes:

- Make `len(displacements)` match break-point count after endpoint clamping.
- Treat `simulate_bias_field` output as a log field; exponentiate before multiplying image intensities.
- Use small `sd_bias_field` and `sd_displacements` for bounded simulations.
- Use `truncate=True` in `regression_match_image` unless out-of-range extrapolation is intentional.
- Fit regression matching inside a non-empty, matching-space mask when background dominates intensities.
