# Data Configuration Troubleshooting

## Config Load Fails

Symptoms:

- `FileNotFoundError` for the config path.
- Missing `_base_` file.
- Import or registry errors while loading a config.

Fixes:

- Check the config path from the current shell with `ls` or the bundled `inspect_mmseg_config.py --config ... --show-keys` command.
- Resolve `_base_` paths relative to the file that declares `_base_`, not relative to the shell.
- Initialize registries with `register_all_modules(init_default_scope=True)` when building datasets or transforms from a custom Python snippet.
- If a config imports Python classes directly, ensure the package and optional component dependencies are installed before loading it.

## `--cfg-options` Does Not Apply

Symptoms:

- Override appears ignored.
- Parser errors on tuple/list values.
- Nested field changes the wrong dataloader or pipeline.

Fixes:

- Use dotted keys such as `train_dataloader.batch_size=1`.
- Quote tuple/list values in shells, for example `model.backbone.strides="(1, 2, 1, 1)"`.
- Avoid whitespace in comma-list shorthand, for example `model.backbone.out_indices=0,1,2,3`.
- Inspect the exact field with `inspect_mmseg_config.py --show-keys FIELD` after applying the override.
- Override `val_dataloader` and `test_dataloader` separately when they are not aliases after config expansion.

## Dataset Directory Is Empty Or Mismatched

Symptoms:

- Dataset length is zero.
- `seg_map_path` files are missing.
- Training starts but every worker reports file-not-found.

Fixes:

- Run `check_dataset_layout.py` with the same `data_root`, `img_path`, `seg_map_path`, `img_suffix`, and `seg_map_suffix` used in the config.
- Include full dataset suffixes, not just extensions, for datasets like Cityscapes.
- Use `--recursive` when images and masks are nested under city/scene subdirectories.
- If an `ann_file` is configured, confirm each line is a stem or relative stem without suffix unless the dataset class documents otherwise.
- For unlabeled test data, omit `seg_map_path` or remove `LoadAnnotations` from the test pipeline.

## `reduce_zero_label` Or `ignore_index` Is Wrong

Symptoms:

- Background disappears from training.
- Binary segmentation learns only foreground or reports strange metrics.
- Class ids appear shifted by one.

Fixes:

- Use `reduce_zero_label=True` only when original label 0 should be ignored and real classes start at 1.
- Keep `reduce_zero_label=False` for foreground/background datasets where 0 is a real class.
- Remember that `LoadAnnotations` reduces zero before applying custom class `label_map`.
- Keep `ignore_index=255` unless the whole config, loss, evaluator, and mask encoding agree on another value.
- Confirm `decode_head.num_classes` and any `auxiliary_head.num_classes` match the post-reduction class count.

## Class Or Palette Mismatch

Symptoms:

- Dataset construction raises `ValueError` about new classes or palette length.
- Visualization colors do not match expected classes.
- Custom class subset maps unexpected ids to `255`.

Fixes:

- For built-in datasets, custom `metainfo.classes` must be a subset of the dataset class `METAINFO.classes`.
- Provide a palette with exactly one RGB triplet per class for deterministic custom datasets.
- Use `get_classes(dataset_alias)` and `get_palette(dataset_alias)` to inspect built-in aliases.
- If using a class subset, inspect `dataset.metainfo` or a small built dataset to confirm `label_map`.

## Converter Dependency Missing

Symptoms:

- Import errors for `cityscapesscripts`, `scipy`, `detail`, `PIL`, `cv2`, or geospatial packages.
- Converter works on one machine but not another.

Fixes:

- Install optional conversion dependencies only in an environment where conversion is requested.
- Keep conversion isolated from training if the training job does not need the optional package.
- Record the converter input archives, output layout, and class-id mapping in task notes outside the runtime skill tree.
- If native converters are unavailable, implement a small project-local converter from the patterns in `dataset-conversion.md`.

## Dataset Browsing Or Visualization Fails

Symptoms:

- GUI/display errors when browsing a dataset.
- Visualizer fails because palette or classes are missing.
- Browsing fails on unlabeled test data.

Fixes:

- Use non-display output options when available in the current checkout, such as saving browsed samples to an output directory instead of showing windows.
- Ensure `visualizer.dataset_meta = dataset.metainfo` when writing a custom browse snippet.
- Provide `classes` and `palette` for plain `BaseSegDataset` in test or visualization mode.
- Remove annotation-loading transforms for unlabeled test browsing, or browse a labeled validation split instead.
