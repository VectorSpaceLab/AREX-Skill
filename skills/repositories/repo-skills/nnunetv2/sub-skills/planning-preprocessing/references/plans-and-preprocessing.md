# Plans and Preprocessing Concepts

Planning turns a dataset fingerprint into one or more configurations. Preprocessing materializes those configurations as arrays that training and inference can reuse.

## Output files to inspect

After planning and preprocessing, inspect the dataset directory under `nnUNet_preprocessed`:

- `dataset_fingerprint.json`: dataset-level evidence extracted from raw images, labels, spacings, shapes, and foreground statistics.
- `dataset.json`: copied metadata used by downstream stages.
- `nnUNetPlans.json` or another `PLANS_NAME.json`: global plans plus named configurations.
- Configuration data folders, typically named from `data_identifier`, such as `nnUNetPlans_2d` or `nnUNetPlans_3d_fullres`.
- `gt_segmentations`: copied ground-truth segmentations for validation workflows.

## Plans file structure

Global fields apply across configurations:

- `dataset_name`: dataset identity metadata.
- `plans_name` and `experiment_planner_used`: plans provenance.
- `image_reader_writer`: image I/O class chosen for the dataset.
- `label_manager`: label handling class.
- `transpose_forward` and `transpose_backward`: axis order used internally.
- `foreground_intensity_properties_per_channel`: dataset-level foreground statistics for schemes such as CT normalization.

Configuration fields define preprocessing and training geometry:

- `spacing`: target spacing used by this configuration.
- `patch_size`: training patch size selected by the planner.
- `batch_size`: batch size selected by the planner or edited later.
- `data_identifier`: folder name for preprocessed arrays. Use a unique value when prepared data differs.
- `preprocessor_name`: preprocessing class, usually `DefaultPreprocessor`.
- `normalization_schemes`: per-channel normalization classes inferred from `dataset.json` channel names.
- `use_mask_for_norm`: whether nonzero-mask normalization is used per channel.
- `resampling_fn_data`, `resampling_fn_seg`, and probability resampling fields: resampling functions plus kwargs.
- Network topology fields such as `architecture`, `conv_kernel_sizes`, `pool_op_kernel_sizes`, `num_pool_per_axis`, and stage convolution counts.

Special relationships:

- `inherits_from`: configuration inherits another configuration and overrides selected fields.
- `previous_stage` and `next_stage`: cascade links.
- `3d_cascade_fullres` commonly reuses `3d_fullres` preprocessed data.

## What preprocessing does

The default preprocessor follows the plans:

1. Loads image channels and, for training cases, segmentation.
2. Applies `transpose_forward` and corresponding spacing order.
3. Crops to nonzero region and records crop properties.
4. Normalizes each channel before resampling.
5. Resamples image and segmentation to the configuration target spacing.
6. Samples foreground locations for oversampling.
7. Saves compressed preprocessed data and per-case properties.

## Normalization behavior

`dataset.json` channel names control normalization. Matching is case-insensitive.

- `CT`: clip foreground intensities to percentiles and normalize with dataset-level foreground mean/std.
- `zscore` or unknown channel names: per-case z-score normalization.
- `noNorm`: no normalization.
- `rescale_to_0_1`: rescale to `[0, 1]`.
- `rgb_to_0_1`: divide uint8 RGB inputs by 255.

Changing channel names or normalization mapping changes preprocessing semantics. Rerun fingerprint extraction and planning when dataset metadata or fingerprint-derived statistics change; rerun preprocessing for configurations whose normalization changed.

## Resampling and target spacing

The default planner selects target spacing from dataset spacing statistics, with safeguards for anisotropic datasets. The `-overwrite_target_spacing X Y Z` CLI option affects `3d_fullres` and `3d_cascade_fullres`, and by extension can affect low-resolution planning. Treat target-spacing overrides as experimental and benchmark against the default.

Changing any of these generally requires rerunning preprocessing for affected configurations:

- `spacing`
- `preprocessor_name`
- `normalization_schemes`
- `use_mask_for_norm`
- resampling function names or kwargs
- any data-affecting edit that uses a new `data_identifier`

Training-only edits usually do not require preprocessing reruns when they reuse existing prepared data:

- increasing `batch_size` through a configuration that inherits from an existing configuration
- architecture-only settings that consume the same `data_identifier`

## Planner and preset choices

Default planning with `ExperimentPlanner` writes `nnUNetPlans` unless overridden. Current nnU-Net guidance encourages considering residual encoder planners for stronger baselines.

Residual encoder preset pattern:

```bash
nnUNetv2_plan_and_preprocess -d DATASET_ID -pl nnUNetPlannerResEncM
nnUNetv2_plan_and_preprocess -d DATASET_ID -pl nnUNetPlannerResEncL
nnUNetv2_plan_and_preprocess -d DATASET_ID -pl nnUNetPlannerResEncXL
```

Use the matching plans identifier in later train/predict commands, such as `-p nnUNetResEncUNetMPlans`, `-p nnUNetResEncUNetLPlans`, or `-p nnUNetResEncUNetXLPlans` when those preset planners generated those plans.

If changing `-gpu_memory_target`, use `-overwrite_plans_name NEW_NAME` to avoid overwriting standard or preset plans. For multi-GPU training, plan for the memory of one GPU, then adjust batch size through a derived configuration instead of passing the combined GPU memory to planning.

## Worker count guidance

Defaults are practical but memory-dependent:

- fingerprint extraction default: 8 processes.
- preprocessing defaults: `2d=8`, `3d_fullres=4`, `3d_lowres=8`, and `4` for other configurations.
- `-np N` uses one preprocessing worker count for all requested configurations.
- `-np N1 N2 ...` must have the same length and order as `-c CONFIG1 CONFIG2 ...`.

More workers can be faster but resampling can exhaust RAM. For large 3D images, start with fewer workers, monitor memory, and increase only after a successful run.
