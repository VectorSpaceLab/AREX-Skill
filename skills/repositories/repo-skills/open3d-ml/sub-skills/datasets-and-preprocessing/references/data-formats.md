# Data Formats and Dataset Contracts

## Purpose

Read this when you need to reason about how Open3D-ML datasets, custom data
folders, and split objects should look before you train or visualize anything.

## Core dataset base classes

- `BaseDataset` requires at least `dataset_path` and `name`.
- `BaseDatasetSplit` wraps a dataset and a split name and exposes `__len__`,
  `get_data(idx)`, and `get_attr(idx)`.
- The dataset registry and base classes are framework-agnostic; model/pipeline
  code consumes the split output dictionaries.

## Common split names

Across the repo, you will see these split spellings:

- `train` / `training`
- `val` / `validation`
- `test` / `testing`
- `all`

Some dataset classes normalize or alias these values. For custom data, stick to
one naming convention and document it in the skill routing notes.

## Common `get_data()` keys

### Segmentation-style datasets

A segmentation split commonly returns a dictionary with:

- `point`: point coordinates, usually `float32`, shape `(N, 3)` or `(N, 4+)`.
- `feat`: optional extra per-point features, often `float32`, shape `(N, F)`.
- `label`: integer labels, often `int32`, shape `(N,)`.

### Object-detection-style datasets

An object-detection split commonly returns:

- `point`: point cloud with intensity or other channels.
- `calib`: calibration data when the dataset uses it.
- `bounding_boxes`: a list of `BoundingBox3D` objects or equivalent box data.

### Custom visualization data

The visualization layer accepts dictionaries with:

- `name`: unique point-cloud name.
- `points`: the point positions.
- Optional per-point arrays such as `labels`, `pred`, `random_colors`,
  `int_attr`, or custom scalar/vector arrays.

## `Custom3D` layout

`Custom3D` in the repo expects separate split directories under the dataset
root. The split files are `.npy` arrays.

### Train/validation format

For non-test splits, each `.npy` file is expected to contain at least:

- columns 0-2: `x, y, z`
- column 3: label
- column 4+: optional extra features

### Test format

For test splits, each `.npy` file is expected to contain at least:

- columns 0-2: `x, y, z`
- column 3+: optional features

### Practical notes

- If a split has no `.npy` files, training and inference will fail early.
- Keep labels consistent with the dataset's `label_to_names` mapping.
- If features are absent, the loader may use `None` and let the model decide
  how to subsample or transform the points.

## Bounding boxes

A visualization or object-detection workflow may use box objects with:

- `center`, `front`, `up`, `left`, `size`
- `label_class`, `confidence`
- optional `meta`, `identifier`

The box coordinates are expressed in a local orientation frame, not as a flat
2D rectangle.

## Save-result expectations

Datasets that support evaluation usually implement `save_test_result(results,
attr)` and may write prediction files to a dataset-specific test folder.
If you build a custom dataset, keep that path configurable and document the
saved file format.

## Quick validation rules

- Train/validation files should not silently omit label columns.
- Test files should not rely on training labels.
- Shapes should be 2D arrays, not ragged Python objects.
- File names should be stable enough that split ordering can be reproduced.
- Dataset directories should be small enough for a fixture-based validation
  script before full training.
