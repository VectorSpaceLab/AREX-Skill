# Extension Points

This reference maps common nnU-Net v2 customization tasks to the class names, files, and metadata nnU-Net resolves at runtime. Keep custom code importable and keep class names stable because checkpoints and plans store names, not full source code.

## Class discovery model

nnU-Net uses recursive Python class lookup for many extension points. The lookup imports modules beneath a known package directory and returns a class whose `__name__` matches the requested string.

Important consequences:

- Class names are case-sensitive and must match CLI arguments, plans fields, or checkpoint metadata exactly.
- Python import errors from a discovered module's dependencies are real failures and should not be hidden.
- Package roots must contain valid importable Python modules; if nested directories are packages, include `__init__.py` where needed.
- Built-in trainer lookup searches `nnunetv2.training.nnUNetTrainer` first. External trainer directories from `nnUNet_extTrainer` are searched only when the built-in search fails.
- `nnUNet_extTrainer` may contain multiple directories separated by the OS path separator: `:` on Linux/macOS, `;` on Windows.

Use the bundled helper to inspect what a given installation can import:

```bash
python sub-skills/customization-extension/scripts/list_available_nnunet_classes.py --kind all
python sub-skills/customization-extension/scripts/list_available_nnunet_classes.py --kind trainer --external-trainer-dir /path/to/trainers
```

The helper is read-only: it lists candidate classes and imports modules to verify visibility, but does not write files or change checkpoints.

## Custom trainers

Use a trainer subclass when changing training procedure, loss, optimizer, sampling, data augmentation, scheduler, checkpointing, validation behavior, or quick network construction.

Typical base and examples:

- Base class: `nnUNetTrainer` from `nnunetv2.training.nnUNetTrainer.nnUNetTrainer`.
- Built-in variants live below `nnunetv2.training.nnUNetTrainer.variants` and are useful templates.
- `nnUNetTrainerNoDeepSupervision` is a safer base when the architecture cannot produce deep-supervision outputs.

Selection points:

- Training selects a trainer by class name through the trainer argument to `nnUNetv2_train`.
- Inference and continued training resolve the saved `trainer_name` in the checkpoint.
- External trainer lookup uses `nnUNet_extTrainer` only if the class is not found in the built-in trainer tree.

Network override warning:

- Current custom trainers should implement the current `build_network_architecture` signature used by `nnUNetTrainer` and return a network without final softmax/sigmoid.
- Old trainers with a narrower `build_network_architecture` signature can fail when nnU-Net passes newer plan/configuration arguments.

## Custom experiment planners

Use a custom `ExperimentPlanner` subclass when changing generated plans, target spacing logic, GPU memory budget behavior, topology selection, resampling functions, normalization planning, or `data_identifier` creation.

Key hooks and fields:

- Base class: `ExperimentPlanner`.
- Constructor accepts dataset id/name, GPU memory target, `preprocessor_name`, plans name, target spacing override, and transpose behavior.
- `determine_reader_writer()` sets the `image_reader_writer` stored in plans.
- `determine_normalization_scheme_and_whether_mask_is_used_for_norm()` maps `dataset.json` channel names to normalization classes.
- `determine_resampling()` and `determine_segmentation_softmax_export_fn()` define preprocessing/export resampling functions.
- `get_plans_for_configuration()` writes configuration fields such as `preprocessor_name`, `data_identifier`, `spacing`, `patch_size`, `batch_size`, `normalization_schemes`, resampling functions, and architecture.

Operational rule:

- If your planner changes preprocessing results, use a distinct plans name and/or `data_identifier`, then rerun planning and preprocessing for affected configurations.
- Routine use of `nnUNetv2_plan_and_preprocess` belongs to `planning-preprocessing`; this reference is for implementing or selecting custom planners.

## Custom preprocessors

Use a `DefaultPreprocessor` subclass when the array pipeline itself changes: loading handoff, transpose/crop/resample/normalize sequencing, segmentation transformation, foreground sampling, output properties, or saved-case behavior.

Important contracts:

- `run_case()` reads images through the plans-selected image reader/writer.
- `run_case_npy()` receives arrays, segmentations, properties, plans manager, configuration manager, and dataset metadata.
- Returned image data should be floating point; segmentation should remain an integer label map.
- Shape mismatches between image and segmentation are errors, not something a preprocessor should silently repair.
- If preprocessing output changes, choose a new `data_identifier` so stale preprocessed data is not reused.

Selection points:

- Planning accepts a preprocessor class name and stores it in each configuration as `preprocessor_name`.
- Plans handling resolves the preprocessor from `nnunetv2.preprocessing` by class name.

## Custom normalization

Normalization is controlled by channel names in `dataset.json`, then stored in plans as `normalization_schemes`.

Built-in channel-name mapping is case-insensitive:

- `CT` -> `CTNormalization`
- `zscore` or unknown names -> `ZScoreNormalization`
- `noNorm` -> `NoNormalization`
- `rescale_to_0_1` -> `RescaleTo01Normalization`
- `rgb_to_0_1` -> `RGBTo01Normalization`

To add a normalization scheme:

1. Subclass `ImageNormalization` and implement `run(self, image, seg=None)`.
2. Set `leaves_pixels_outside_mask_at_zero_if_use_mask_for_norm_is_true` appropriately.
3. Register a channel-name key in `map_channel_name_to_normalization.py`.
4. Use that channel name in `dataset.json`.
5. Replan and rerun preprocessing so the new scheme is written into plans and applied to data.

Limitations and cautions:

- Normalization is planned per channel, not as a built-in multi-channel joint normalization.
- `CTNormalization` requires intensity statistics computed from foreground voxels during planning.
- A channel-name typo usually falls back to `ZScoreNormalization`, which can be wrong but may not crash.

## Custom image IO

Use a custom reader/writer when existing readers cannot load images, segmentations, metadata, spacing, orientation, or output format correctly.

Base contract:

- Subclass `BaseReaderWriter`.
- `read_images(image_fnames)` returns `(data, properties)` where data has shape `(c, x, y, z)`.
- `read_seg(seg_fname)` returns a segmentation with shape `(1, x, y, z)`.
- `write_seg(seg, output_fname, properties)` writes the final 3D segmentation back to the requested format.
- `properties` must include `spacing` with three values matching the returned spatial axes.
- For 2D images, return shape `(c, 1, x, y)` and use a large first spacing value such as `999`.

Selection points:

- `dataset.json` can include `overwrite_image_reader_writer` with a reader/writer class name.
- Plans store the selected reader/writer as `image_reader_writer`.
- Plans handling resolves reader/writers from `nnunetv2.imageio` by class name.

## Label, region, and ignore-label interactions

Routine dataset metadata belongs to `data-preparation`, but extension code must respect these conventions:

- nnU-Net input labels are integer segmentation maps even when training with regions.
- Region-based training uses `labels` values that may be lists/tuples and requires `regions_class_order` for converting overlapping region outputs back to integer labels.
- Region order matters; encompassing regions should be placed before substructures because later labels overwrite earlier ones.
- The ignore label must be named `ignore`, must be the highest integer label, and is not predicted as a foreground region.
- Custom losses, samplers, preprocessors, and label managers must preserve ignore-label behavior so loss/evaluation only uses annotated pixels where intended.

## Network architecture customization

There are two practical levels:

- Quick trainer-level override: subclass `nnUNetTrainer` and override `build_network_architecture` for a fixed or lightly configurable network.
- Planner-level integration: implement a dynamically configurable architecture plus an `ExperimentPlanner` that can estimate memory and generate valid plans for it.

Safety checklist:

- The network must accept patch sizes generated by the planner.
- The network must support deep supervision or the trainer must disable it.
- Do not apply final softmax/sigmoid in the network; nnU-Net handles output activation where needed.
- If architecture requires new plans fields, keep inference and continued-training environments on compatible code.
