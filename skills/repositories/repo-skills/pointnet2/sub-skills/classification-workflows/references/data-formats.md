# ModelNet40 data formats for classification

The classification scripts support two ModelNet40 layouts. Use this reference before constructing a train/evaluation command so the chosen loader, point count, and model input shape agree.

## Default HDF5 layout

Default classification runs omit `--normal` and use the HDF5 loader:

```text
data/modelnet40_ply_hdf5_2048/
  shape_names.txt
  train_files.txt
  test_files.txt
  ply_data_train0.h5
  ply_data_train1.h5
  ...
  ply_data_test0.h5
  ...
```

Expected files and fields:

- `shape_names.txt`: one class name per line; ModelNet40 should have 40 entries.
- `train_files.txt` / `test_files.txt`: line-separated HDF5 paths. The original files usually store paths relative to the repository root, such as `data/modelnet40_ply_hdf5_2048/ply_data_train0.h5`.
- Each HDF5 file contains:
  - `data`: point clouds shaped like `[num_examples, 2048, 3]` or at least `[num_examples, >=num_point, >=3]`.
  - `label`: class labels shaped like `[num_examples, 1]` or `[num_examples]`.

Loader behavior from `modelnet_h5_dataset.py`:

- `ModelNetH5Dataset(list_filename, batch_size, npoints, shuffle)` reads HDF5 filenames from the list file.
- `next_batch()` slices `current_data[start:end, 0:npoints, :]`; it does not resample points.
- `num_channel()` returns `3`.
- `train.py`, `train_multi_gpu.py`, and `evaluate.py` assert `NUM_POINT <= 2048` in HDF5 mode.
- The module contains a top-level download block that runs `wget`, `unzip`, `mv`, and `rm` when `data/modelnet40_ply_hdf5_2048` is missing. Do not import it merely to validate an offline or CI layout.

Validate HDF5 layout without triggering the loader:

```bash
python sub-skills/classification-workflows/scripts/validate_modelnet_layout.py --mode h5 --repo-root . --num-point 1024
```

Run a tiny HDF5 data smoke when `h5py` is available:

```bash
python sub-skills/classification-workflows/scripts/smoke_modelnet_loader.py --mode h5 --repo-root . --split test --num-point 16 --batch-size 2
```

## Normal-resampled text layout

Normal-resampled classification runs add `--normal` and use the text-file loader:

```text
data/modelnet40_normal_resampled/
  shape_names.txt
  modelnet40_train.txt
  modelnet40_test.txt
  airplane/
    airplane_0001.txt
    airplane_0002.txt
    ...
  chair/
    chair_0001.txt
    ...
  ...
```

Expected files and fields:

- `shape_names.txt`: class names; ModelNet40 should have 40 entries.
- `modelnet40_train.txt` / `modelnet40_test.txt`: shape ids such as `airplane_0001`.
- For every shape id, the loader derives the class directory by joining every underscore-separated token except the final numeric id. For `night_stand_0001`, the class directory is `night_stand`.
- Each sample file is comma-delimited numeric text. The normal-resampled data described by the README contains 10,000 points per shape with columns `x,y,z,nx,ny,nz`.

Loader behavior from `modelnet_dataset.py`:

- `ModelNetDataset(root, npoints, split, normal_channel=True)` reads `modelnet40_train.txt` or `modelnet40_test.txt` and opens `<root>/<class>/<shape_id>.txt`.
- It slices the first `npoints` rows, normalizes XYZ coordinates, and returns either XYZ only or XYZ+normal depending on `normal_channel`.
- With `--normal`, the classification scripts pass `normal_channel=True`, so the loader returns 6 channels.
- The scripts assert `NUM_POINT <= 10000` in normal mode.

Important shape note: the stock classification model files observed for `pointnet2_cls_ssg`, `pointnet2_cls_msg`, and `pointnet_cls_basic` define `placeholder_inputs()` as `BxNx3`. A true XYZ+normal run therefore needs a model architecture adapted for 6-channel input. If the user only needs the official default classification path, use HDF5 mode instead.

Validate normal-resampled layout:

```bash
python sub-skills/classification-workflows/scripts/validate_modelnet_layout.py --mode normal --repo-root . --num-point 5000
```

Run a tiny normal-loader smoke:

```bash
python sub-skills/classification-workflows/scripts/smoke_modelnet_loader.py --mode normal --repo-root . --split train --num-point 16 --batch-size 2 --normal-channel
```

## Choosing `--num_point`

| Mode | Hard source assertion | Practical default | Smoke default | What happens if too high |
|---|---:|---:|---:|---|
| HDF5 | `<= 2048` | `1024` | `16` or `32` | `train.py` / `evaluate.py` raise an assertion before training. |
| Normal-resampled | `<= 10000` | README cites `5000` for XYZ+normal experiments | `16` or `32` | Source assertion may pass, but individual sample files can still be too short. |

The source loaders take the first `npoints`; they do not randomly resample to fill missing points. The bundled validator and smoke loader check that sampled files contain at least the requested point count.

## Custom ModelNet-style data

For HDF5-style custom data:

1. Keep `shape_names.txt` in the dataset directory.
2. Put train/test HDF5 file paths in `train_files.txt` and `test_files.txt`.
3. Store datasets named exactly `data` and `label`.
4. Ensure labels are integer class ids in the same order as `shape_names.txt`.
5. Keep point arrays at least `[examples, num_point, 3]`.

For normal-resampled text data:

1. Keep `shape_names.txt`, `modelnet40_train.txt`, and `modelnet40_test.txt`.
2. Use shape ids whose class name is recoverable by dropping the final underscore token.
3. Store every sample at `<root>/<class>/<shape_id>.txt`.
4. Use comma-delimited numeric rows.
5. Use at least 6 columns for a true `--normal` run, or adapt the loader/model if using a different feature schema.

## Validator expectations

`validate_modelnet_layout.py` is intentionally stricter than the raw source loaders in places where early feedback is helpful:

- It reports missing dataset roots instead of importing a module that may download data.
- It checks required split files before opening any samples.
- It resolves HDF5 list entries relative to both the repository root and the dataset root.
- It can sample a bounded number of normal text files per split and report malformed rows, missing class directories, and files with too few points.
- It exits nonzero when required pieces are missing, making it suitable for future assertion-backed usability tests.
