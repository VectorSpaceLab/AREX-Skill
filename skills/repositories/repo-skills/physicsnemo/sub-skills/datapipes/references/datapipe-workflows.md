# PhysicsNeMo datapipe workflows

## Smallest useful pipeline

1. Pick a reader for the on-disk format.
2. Inspect one sample.
3. Wrap the reader in `Dataset`.
4. Add transforms only after the raw reader output is correct.
5. Wrap in `DataLoader` and verify batch keys, shapes, dtypes, and metadata.

## Common recipes

### NPZ / NumPy

- Use `NumpyReader(path, fields=[...], index_key=...)` when a file or directory contains sample-wise `.npz` files.
- Good for synthetic fixtures and small scientific ML tests.
- When the data is already array-shaped, keep the first smoke simple: one reader, one dataset, one loader.

### HDF5

- Use `HDF5Reader(path, fields=[...])` for `.h5` files or directories of HDF5 files.
- This is the simplest route for weather and many CFD datasets.
- Verify the root keys and the first-dimension sample axis before adding transforms.

### Zarr / TensorStore

- Use `ZarrReader` for ordinary local Zarr groups.
- Use `TensorStoreZarrReader` when the workflow needs explicit cache and concurrency controls.
- Good for larger weather, climate, and long-running training datasets.

### VTK / mesh files

- Use `VTKReader` for supported VTK-style surface or mesh data when the optional VTK/PyVista stack is available.
- Use `MeshReader` or `DomainMeshReader` for PhysicsNeMo native mesh archives.
- Pair mesh readers with `MeshDataset` and mesh transforms when the downstream model expects mesh objects.

### Multi-dataset and iterables

- Use `MultiDataset` to concatenate multiple map-style datasets into one index space.
- Use `IterableDatasetBase` when the source has no stable length or meaningful index.
- For iterables, let `DataLoader` stay on its main-thread generator path and expect `len(loader)` to be undefined.

## Validation checklist

- `reader[0]` returns the expected payload shape and metadata.
- Transform input keys exist and have compatible leading dimensions.
- The batch collator matches the sample type.
- `seed` and `set_epoch` are used when reproducibility matters.
- Optional data extras are installed when the chosen reader requires them.
- Prefetch/stream behavior is only investigated after the raw reader output is correct.
