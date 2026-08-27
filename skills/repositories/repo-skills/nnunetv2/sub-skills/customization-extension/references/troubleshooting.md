# Customization Troubleshooting

Use this reference when nnU-Net cannot find or use a custom class, or when extension behavior does not match dataset metadata/plans.

## Trainer class not found

Symptoms:

- Error says nnU-Net could not find requested trainer in `nnunetv2.training.nnUNetTrainer`.
- Error mentions setting `nnUNet_extTrainer`.
- Inference or continued training fails after loading a custom-trainer checkpoint.

Checks:

1. Confirm the checkpoint or command uses the exact class name, including case.
2. List visible classes:
   ```bash
   python sub-skills/customization-extension/scripts/list_available_nnunet_classes.py --kind trainer
   ```
3. If the trainer is external, set `nnUNet_extTrainer` to the parent directory that makes the package importable, not necessarily the directory containing only one file.
4. Re-run with the external root:
   ```bash
   python sub-skills/customization-extension/scripts/list_available_nnunet_classes.py --kind trainer --external-trainer-dir /path/to/custom_trainers_root
   ```
5. Ensure package directories have `__init__.py` where required.
6. Ensure the class inherits from `nnUNetTrainer`.

Likely fixes:

- Correct a class-name typo in `-tr`, checkpoint metadata, or documentation.
- Point `nnUNet_extTrainer` at the package parent.
- Install the package that contains the trainer and dependencies.
- Ship the trainer source alongside the checkpoint or switch to a forked nnU-Net distribution.

## `nnUNet_extTrainer` not set or set incorrectly

Symptoms:

- Built-in trainers list correctly, but external trainers are absent.
- External path is printed but the expected class is not found.

Checks:

- On Linux/macOS, multiple paths are separated by `:`.
- On Windows, multiple paths are separated by `;`.
- Empty path entries are ignored.
- The path must exist in the environment where nnU-Net runs, including cluster jobs, containers, notebooks, and subprocesses.

Fix pattern:

```bash
export nnUNet_extTrainer="/path/to/custom_trainers_root"
python sub-skills/customization-extension/scripts/list_available_nnunet_classes.py --kind trainer --external-trainer-dir "$nnUNet_extTrainer"
```

## Import error from external trainer package

Symptoms:

- `ModuleNotFoundError` names a dependency, not the trainer module itself.
- Listing or inference fails while importing the trainer module.

Interpretation:

- nnU-Net intentionally surfaces real dependency import errors. Do not treat them as class lookup misses.

Fixes:

- Install the missing dependency into the same Python environment that runs nnU-Net.
- Remove imports that are only needed for training if the checkpoint is being used for inference, or guard them carefully.
- Keep custom architecture/loss/helper modules in the distributed package.
- Avoid imports that only work from a private development checkout.

## Planner, preprocessor, normalization, or reader class not found

Symptoms:

- Planning fails for `-pl MyPlanner` or `-preprocessor_name MyPreprocessor`.
- Preprocessing/inference fails when reading plans fields such as `preprocessor_name`, `normalization_schemes`, or `image_reader_writer`.
- Dataset validation warns that `overwrite_image_reader_writer` cannot be found.

Checks:

- Custom planners must be importable under `nnunetv2.experiment_planning` for nnU-Net's built-in recursive lookup.
- Custom preprocessors must be importable under `nnunetv2.preprocessing`.
- Custom normalization classes must be importable under `nnunetv2.preprocessing.normalization` and should be registered in the channel-name mapping when selected from `dataset.json`.
- Custom reader/writers must be importable under `nnunetv2.imageio` and subclass `BaseReaderWriter`.
- Plans may store old class names; updating code without replanning can leave stale names in `plans.json`.

Fixes:

- Put the class where nnU-Net's lookup searches, or install a compatible fork/package that exposes it there.
- Replan with a distinct plans name if class names or preprocessing behavior changed.
- Rerun preprocessing when `preprocessor_name`, normalization, resampling, spacing, or `data_identifier` changes.

## Old `build_network_architecture` signature

Symptoms:

- A custom trainer worked in an older nnU-Net but now raises `TypeError` about unexpected or missing arguments.
- Network construction fails before training starts or when loading a checkpoint for inference.

Cause:

- Custom trainers that override `build_network_architecture` must match the current base-class signature and call pattern.

Fixes:

- Compare the current `nnUNetTrainer.build_network_architecture` signature and update the subclass.
- Keep the method static/class-compatible if the base method is static.
- Preserve expected arguments such as plans manager, dataset metadata, configuration manager, input channels, deep supervision, and other current options.
- Return raw logits; do not add softmax/sigmoid.

## Custom trainer missing at model-sharing target

Symptoms:

- Training worked for the model author, but users cannot run inference.
- Checkpoint loading fails on `trainer_name`.

Fixes by sharing strategy:

- If no inference-relevant behavior changed, consider renaming the checkpoint trainer to a built-in class only after verifying predictions.
- If behavior changed, ship trainer source and dependencies and tell users to set `nnUNet_extTrainer`.
- For a complete development workflow, provide a pinned fork or package.
- Include a preflight step with the bundled helper so users verify class visibility before prediction.

## Custom image IO not aligned with `dataset.json`

Symptoms:

- Dataset verification fails to read images or segmentations.
- Spacing, shape, orientation, or channel count is wrong.
- Predictions write with incorrect geometry or unreadable output format.

Checks:

- `dataset.json` `file_ending` matches actual filenames unless `overwrite_image_reader_writer` intentionally overrides reader selection.
- `overwrite_image_reader_writer` matches a class under `nnunetv2.imageio`.
- `read_images()` returns `(c, x, y, z)` and a properties dict containing three-value `spacing`.
- `read_seg()` returns `(1, x, y, z)`.
- 2D images use shape `(c, 1, x, y)` and a large first spacing value such as `999`.
- `write_seg()` restores required metadata from properties.

Fixes:

- Correct `file_ending` or `overwrite_image_reader_writer` in `dataset.json`.
- Replan after changing reader/writer selection because plans store `image_reader_writer`.
- Keep reader/writer code available wherever inference or evaluation writes segmentations.

## Custom normalization not aligned with `dataset.json`

Symptoms:

- Preprocessing uses unexpected `ZScoreNormalization`.
- CT-like data is not clipped using foreground statistics.
- Custom normalizer is never called.

Checks:

- `dataset.json` uses `channel_names`, and each channel name is the intended mapping key.
- Mapping keys are case-insensitive, but spelling still matters.
- Unknown channel names fall back to `ZScoreNormalization`.
- Custom normalization was registered in the channel-name mapping and is importable.
- Planning was rerun after changing channel names or mappings.

Fixes:

- Correct channel names such as `CT`, `noNorm`, `rescale_to_0_1`, or the custom key.
- Register the custom class and replan/repreprocess.
- Use a distinct plans/data identifier if comparing normalization strategies.

## Region and ignore-label extension bugs

Symptoms:

- Region outputs map back to wrong integer labels.
- Ignore regions contribute to loss or appear as predicted foreground.
- Custom loss/sampler crashes on tuple/list region labels.

Checks:

- Region labels in `dataset.json` may be lists/tuples; custom code must not assume every label entry is an integer.
- `regions_class_order` length must match foreground regions and its order controls overwrite behavior.
- The ignore label must be named `ignore`, have the highest integer value, and not be included in `regions_class_order`.
- Custom samplers/losses should preserve partial-loss behavior for ignored voxels.

Fixes:

- Route routine metadata corrections to `data-preparation`.
- Update custom code to use nnU-Net label manager behavior rather than manually parsing labels when possible.
- Add a small synthetic case before expensive training to verify region/ignore behavior.

## Stale preprocessed data after extension changes

Symptoms:

- Code changes appear to have no effect.
- Training uses old arrays after modifying preprocessor, normalization, spacing, or resampling.

Cause:

- nnU-Net can reuse preprocessed data when identifiers do not change.

Fixes:

- Use a new plans name and/or `data_identifier` for preprocessing-affecting changes.
- Rerun planning and preprocessing for affected configurations.
- Delete or avoid stale preprocessed folders only after confirming they are no longer needed.
