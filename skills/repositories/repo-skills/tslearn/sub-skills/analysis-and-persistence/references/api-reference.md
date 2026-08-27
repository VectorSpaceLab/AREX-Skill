# API reference

## Matrix profile

### `tslearn.matrix_profile.MatrixProfile`

- Constructor: `MatrixProfile(subsequence_length=1, implementation="numpy", scale=True)`
- Core methods: `fit`, `transform`, `fit_transform`
- Implementations:
  - `numpy`: reference path that computes explicit pairwise distances
  - `stump`: STUMPY-backed CPU path
  - `gpu_stump`: STUMPY-backed GPU path; treat as optional acceleration
- Input shape for the bundled checks: univariate `X` with shape `(n_ts, sz, 1)`
- Current limitation: multi-dimensional input raises `NotImplementedError`

## Persistence mixins

### `tslearn.bases.BaseModelPackage`

Provides the estimator persistence helpers shared by tslearn estimators:

- `to_json(path)` / `from_json(path)`
- `to_pickle(path)` / `from_pickle(path)`
- `to_hdf5(path)` / `from_hdf5(path)`

Behavior:

- Fitted state is required; unfitted calls raise `NotFittedError`
- JSON and Pickle use only the Python standard library
- HDF5 round-trips require `h5py`
- HDF5 storage is backed by the recursive dict helpers in `tslearn.hdftools`

### `tslearn.bases.TimeSeriesMixin`

- Adds tslearn-specific sklearn tags and helper context
- Not a user-facing persistence API, but it is part of the common estimator base

## HDF5 helpers

### `tslearn.hdftools.save_dict(d, filename, group, raise_type_fail=True)`

- Saves nested dict-like data into an HDF5 group
- Handles arrays, scalars, strings, nested dicts, and nested objects via `__dict__`

### `tslearn.hdftools.load_dict(filename, group)`

- Restores the nested dict saved by `save_dict`
- Used internally by `BaseModelPackage.to_hdf5` / `from_hdf5`

## Dependency matrix

- MatrixProfile `numpy`: no optional dependency beyond the standard tslearn stack
- MatrixProfile `stump` / `gpu_stump`: require `stumpy`
- JSON: no `h5py`
- Pickle: no `h5py`
- HDF5: requires `h5py`
