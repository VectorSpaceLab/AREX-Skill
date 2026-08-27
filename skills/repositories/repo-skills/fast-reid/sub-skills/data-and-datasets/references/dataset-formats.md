# FastReID dataset formats

This reference is a self-contained guide to FastReID v1.3 dataset identities, expected layouts, and item schemas. It is distilled for operation; use it instead of relying on source checkout notes.

## Root resolution

FastReID's built-in dataset loader root is resolved as:

1. `FASTREID_DATASETS` environment variable, if set.
2. Otherwise `datasets` relative to the process working directory.

The dataset root is the parent directory under which built-in dataset folders such as `Market-1501-v15.09.15`, `DukeMTMC-reID`, `MSMT17_V2`, `veri`, `vehicleid`, and `VERI-Wild` live.

## Canonical item tuple

All image datasets eventually provide three lists:

```python
train = [(img_path, pid, camid), ...]
query = [(img_path, pid, camid), ...]
gallery = [(img_path, pid, camid), ...]
```

- `img_path`: image file path string consumed by FastReID's image reader.
- `pid`: person/vehicle identity. Built-in train splits often prefix this with the dataset name string, then `CommDataset(..., relabel=True)` remaps it to a contiguous integer target.
- `camid`: camera identity. Built-ins convert raw camera ids to zero-based values; train splits often prefix them too.
- Query and gallery ids usually remain numeric except where a dataset has custom list semantics.

`ImageDataset` owns the `train`, `query`, and `gallery` lists. `CommDataset` wraps one concatenated item list for PyTorch loading and returns dictionaries with `images`, `targets`, `camids`, and `img_paths`.

## Built-in registry keys

Common built-in keys are case-sensitive:

- Person ReID: `Market1501`, `DukeMTMC`, `MSMT17`, `CUHK03`, `AirportALERT`, `iLIDS`, `PKU`, `PRAI`, `PRID`, `GRID`, `SAIVT`, `SenseReID`, `SYSU_mm`, `Thermalworld`, `PeS3D`, `CAVIARa`, `VIPeR`, `LPW`, `Shinpuhkan`, `WildTrackCrop`, `cuhkSYSU`.
- Vehicle ReID: `VeRi`, `VehicleID`, `SmallVehicleID`, `MediumVehicleID`, `LargeVehicleID`, `VeRiWild`, `SmallVeRiWild`, `MediumVeRiWild`, `LargeVeRiWild`.

Use these exact class names in `cfg.DATASETS.NAMES` and `cfg.DATASETS.TESTS` unless you register a custom class.

## Layout: Market1501

Preferred layout:

```text
<datasets-root>/
  Market-1501-v15.09.15/
    bounding_box_train/
      0001_c1s1_001051_00.jpg
      ...
    query/
      0001_c1s1_001051_00.jpg
      ...
    bounding_box_test/
      0001_c1s1_001051_00.jpg
      ...
    images/                  # optional only for the 500k gallery variant
```

Compatibility behavior:

- FastReID also accepts a legacy direct layout where `bounding_box_train`, `query`, and `bounding_box_test` live directly below `<datasets-root>`; it warns that this structure is deprecated.
- File names are parsed with `([-\d]+)_c(\d)`: pid and one-digit camera id.
- `pid == -1` is ignored as junk; `pid == 0` is treated as background; camera ids must be in `1..6` before zero-basing.

## Layout: DukeMTMC-reID

```text
<datasets-root>/
  DukeMTMC-reID/
    bounding_box_train/
    query/
    bounding_box_test/
```

- Registry key: `DukeMTMC`.
- File names are parsed with `([-\d]+)_c(\d)`.
- Camera ids must be in `1..8` before zero-basing.

## Layout: MSMT17

FastReID detects either v1 or v2 main folder under the dataset root.

```text
<datasets-root>/
  MSMT17_V2/
    mask_train_v2/
    mask_test_v2/
    list_train.txt
    list_val.txt
    list_query.txt
    list_gallery.txt
```

V1 equivalent:

```text
<datasets-root>/
  MSMT17_V1/
    train/
    test/
    list_train.txt
    list_val.txt
    list_query.txt
    list_gallery.txt
```

- Registry key: `MSMT17`.
- List rows are parsed as `<relative-image-path> <pid>`.
- Camera id is derived from the third underscore-separated segment of the relative image path, then converted to zero-based.
- Query/gallery pids are offset internally by the number of training pids so they do not collide with training ids.
- `combineall=True` adds validation rows to training; do not assume validation rows are included by default.

## Layout: VeRi

```text
<datasets-root>/
  veri/
    image_train/
    image_query/
    image_test/
```

- Registry key: `VeRi`.
- File names are parsed with `([\d]+)_c(\d\d\d)`: numeric vehicle id and three-digit camera id.
- Vehicle ids must be in `0..776`; camera ids must be in `1..20` before zero-basing.

## Layout: VehicleID and variants

```text
<datasets-root>/
  vehicleid/
    image/
      <image-id>.jpg
      ...
    train_test_split/
      train_list.txt
      test_list_13164.txt      # VehicleID default test split
      test_list_800.txt        # SmallVehicleID
      test_list_1600.txt       # MediumVehicleID
      test_list_2400.txt       # LargeVehicleID
```

- Registry keys: `VehicleID`, `SmallVehicleID`, `MediumVehicleID`, `LargeVehicleID`.
- List rows are parsed as `<image-id> <vehicle-id>`.
- Image paths are resolved as `image/<image-id>.jpg`.
- For evaluation, FastReID shuffles the test list and places the first image of each vehicle id into gallery; later images for the same id become query. If each vehicle id has only one listed image, query becomes empty.

## Layout: VeRiWild and variants

```text
<datasets-root>/
  VERI-Wild/
    images/
      <vehicle-id>/
        <image-id>.jpg
        ...
    train_test_split/
      vehicle_info.txt
      train_list.txt
      test_10000_query.txt     # VeRiWild / LargeVeRiWild default
      test_10000.txt
      test_3000_query.txt      # SmallVeRiWild
      test_3000.txt
      test_5000_query.txt      # MediumVeRiWild
      test_5000.txt
```

- Registry keys: `VeRiWild`, `SmallVeRiWild`, `MediumVeRiWild`, `LargeVeRiWild`.
- List rows are parsed like `<vehicle-id>/<image-file>`.
- `vehicle_info.txt` maps image ids to camera ids and image paths; FastReID skips its first header row.
- Images are resolved as `images/<vehicle-id>/<image-id>.jpg`.

## Additional built-ins with simpler or project-like layouts

These built-ins are registered, but layout details vary and are less common in the core configs:

- Directory-only or image-folder datasets include `VIPeR`, `GRID`, `iLIDS`, `PKU`, `PRAI`, `PRID`, `SAIVT`, `SenseReID`, `SYSU_mm`, `Thermalworld`, `PeS3D`, `CAVIARa`, `LPW`, `Shinpuhkan`, `WildTrackCrop`, `cuhkSYSU`, and `AirportALERT`.
- `CUHK03` expects a `cuhk03` folder with release material and split MAT/JSON files; it can generate split JSON files from MAT inputs when enough metadata exists.
- For project-specific extension datasets, register a custom dataset class with the shared registry mechanics described in `data-api.md`.

## Preflight expectations before training/evaluation

A dataset tree is not ready merely because the required directories exist. Also check:

- Train split has at least one parseable item.
- Evaluation split has non-empty query and gallery lists.
- File names or list rows match the expected pid/camid pattern.
- Camera ids are in the valid range before FastReID zero-bases them.
- For identity samplers, the training set has enough identities and the global batch size is divisible by `DATALOADER.NUM_INSTANCE`.
