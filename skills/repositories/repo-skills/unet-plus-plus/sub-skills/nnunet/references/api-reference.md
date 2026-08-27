# nnU-Net API reference

## Core trainer and model classes

### `nnUNetPlusPlusTrainerV2`

```python
nnUNetPlusPlusTrainerV2(
    plans_file,
    fold,
    output_folder=None,
    dataset_directory=None,
    batch_dice=True,
    stage=None,
    unpack_data=True,
    deterministic=True,
    fp16=False,
)
```

- The default UNet++ trainer class used by this repository's PyTorch stack.
- Builds on `nnUNetTrainer` and swaps in `Generic_UNetPlusPlus`.
- Uses deep supervision and the nnU-Net training loop.

### `Generic_UNetPlusPlus`

```python
Generic_UNetPlusPlus(
    input_channels,
    base_num_features,
    num_classes,
    num_pool,
    num_conv_per_stage=2,
    feat_map_mul_on_downscale=2,
    conv_op=nn.Conv2d,
    norm_op=nn.BatchNorm2d,
    norm_op_kwargs=None,
    dropout_op=nn.Dropout2d,
    dropout_op_kwargs=None,
    nonlin=nn.LeakyReLU,
    nonlin_kwargs=None,
    deep_supervision=True,
    dropout_in_localization=False,
    final_nonlin=softmax_helper,
    weightInitializer=InitWeights_He(1e-2),
    pool_op_kernel_sizes=None,
    conv_kernel_sizes=None,
    upscale_logits=False,
    convolutional_pooling=False,
    convolutional_upsampling=False,
    max_num_features=None,
    basic_block=ConvDropoutNormNonlin,
    seg_output_use_bias=False,
)
```

- The UNet++ architecture implementation.
- Supports 2D or 3D convolutions depending on `conv_op`.
- Deep supervision is enabled by default.

### `nnUNetTrainer`

- The base trainer used by the nnU-Net family.
- Handles plans, preprocessing, augmentation, training, validation, and
  prediction utilities.
- Public methods of interest include `initialize`, `run_training`, `validate`,
  `load_latest_checkpoint`, `load_best_checkpoint`, and
  `predict_preprocessed_data_return_seg_and_softmax`.

### `nnUNetTrainerV2`

- Refined trainer with `get_moreDA_augmentation`, SGD, and deep-supervision
  weighting changes.
- `validate` and prediction methods temporarily disable deep supervision.

### `nnUNetTrainerV2CascadeFullRes`

- Full-resolution cascade trainer that expects low-resolution predictions from
  the previous stage.
- Adds segmentation-from-previous-stage inputs and cascade-specific data
  augmentation.

## Helper functions and utilities

### `get_default_configuration`

```python
get_default_configuration(
    network,
    task,
    network_trainer,
    plans_identifier=default_plans_identifier,
    search_in=(nnunet.__path__[0], "training", "network_training"),
    base_module='nnunet.training.network_training',
)
```

- Resolves the plans file, output folder, dataset directory, batch-dice mode,
  stage, trainer class, and domain information for a requested network/task.
- Accepts `2d`, `3d_lowres`, `3d_fullres`, and `3d_cascade_fullres`.

### `SegmentationNetwork._compute_steps_for_sliding_window`

```python
SegmentationNetwork._compute_steps_for_sliding_window(patch_size, image_size, step_size)
```

- Used by the sliding-window inference path.
- The repo's unit test verifies exact step placement and overlap behavior.

### `predict_cases`

- Main multi-case inference helper in `nnunet.inference.predict`.
- Handles preprocessing, fold loading, TTA, softmax aggregation, and export.

### `merge`

- Merges multiple `.npz` prediction folders for ensembling.
- Can optionally run postprocessing from a trained model's JSON file.

### `export_pretrained_model`

```python
export_pretrained_model(
    task_name,
    output_file,
    models=("2d", "3d_lowres", "3d_fullres", "3d_cascade_fullres"),
    nnunet_trainer=default_trainer,
    nnunet_trainer_cascade=default_cascade_trainer,
    plans_identifier=default_plans_identifier,
    folds=(0, 1, 2, 3, 4),
    strict=True,
)
```

- Packs fold checkpoints, `plans.pkl`, `postprocessing.json`, and ensemble
  metadata into a zip archive.

### `download_by_name` / `download_by_url` / `install_from_zip_entry_point`

- Public pretrained-model management helpers.
- Require `requests` for download-by-name and download-by-url operations.

### `pretend_to_be_other_trainer`

- The implementation behind `nnUNet_change_trainer_class`.
- Rewrites checkpoint metadata in place, so it should be treated as an advanced
  repair utility.

## Practical notes

- The inspected snapshot reported `nnUNetPlusPlusTrainerV2` as the default
  trainer.
- The advanced DP/DDP scripts in this repo snapshot are older and should be
  treated as cautionary code paths rather than the default route.
- When in doubt, route to `references/cli-reference.md` for command syntax and
  `references/workflows.md` for the recommended order of operations.
