# API Reference

## Purpose

Read this when you need the verified signatures for the repo's config, dataset, and data-loading helpers.

## Verified signatures

### `utils.config.Config.fromfile(filename)`

- Loads Python, YAML, or JSON config files.
- Returns a `Config` object with attribute access.
- The repo uses it for `configs/culane.py` and `configs/tusimple.py`.

### `utils.common.merge_config()`

- Parses the command line.
- Loads the config file from the positional `config` argument.
- Applies any explicit overrides from the CLI.
- Returns `(args, cfg)`.

### `data.dataset.LaneClsDataset`

```python
LaneClsDataset(
    path,
    list_path,
    img_transform=None,
    target_transform=None,
    simu_transform=None,
    griding_num=50,
    load_name=False,
    row_anchor=None,
    use_aux=False,
    segment_transform=None,
    num_lanes=4,
)
```

### `data.dataset.LaneTestDataset`

```python
LaneTestDataset(path, list_path, img_transform=None)
```

### `data.dataloader.get_train_loader`

```python
get_train_loader(batch_size, data_root, griding_num, dataset, use_aux, distributed, num_lanes)
```

### `data.dataloader.get_test_loader`

```python
get_test_loader(batch_size, data_root, dataset, distributed)
```

### `scripts/convert_tusimple_safe.py`

The bundled helper uses a simple CLI with `--root` for the TuSimple dataset root. It should mirror the source conversion flow without hardcoded paths.

## Important behavior notes

- `LaneClsDataset` reads an image and a label mask from the list file, then projects the mask onto the configured row anchors.
- `LaneTestDataset` strips an incorrect leading `/` from CULane list entries when present.
- The data loader chooses the row-anchor set and `cls_num_per_lane` from the dataset family.
- The repo's configuration parser includes a `--use_aux` boolean-like override that needs a clear true/false value.
