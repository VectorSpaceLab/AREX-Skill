# PhysicsNeMo datapipe data formats

## Array readers

### NPZ / NumPy

- Good for compact fixtures and array-style scientific ML data.
- Typical layout: one or more arrays with sample axis first.
- Use `index_key` when the stored file structure needs a named sample axis.

### HDF5

- Good for weather, CFD, and other multi-field datasets.
- Verify the top-level keys and the leading dimension before adding transforms.
- HDF5 files often carry fields like input states, targets, coordinates, or statistics arrays.

### Zarr / TensorStore Zarr

- Good for large or chunked datasets.
- Zarr is convenient for local groups; TensorStore Zarr adds explicit concurrency/cache control.
- Coordinated subsampling is useful when several arrays must preserve sample alignment.

## Mesh readers

### `MeshReader`

- Reads native PhysicsNeMo mesh archives such as `.pmsh`.
- Useful when the downstream model or datapipe expects mesh objects rather than bare tensors.

### `DomainMeshReader`

- Reads native PhysicsNeMo domain-mesh archives such as `.pdmsh`.
- Boundary meshes may be attached and can be filtered or validated depending on the workflow.

## VTK and visualization-backed data

- `VTKReader` is appropriate when the optional VTK/PyVista stack is installed.
- Treat VTK conversion and visualization as a separate dependency surface from plain array loading.

## TensorDict conventions

- Reader output should preserve named fields and metadata.
- `point_data`, `cell_data`, and global fields should keep their leading sample semantics consistent.
- `Normalize` and `SubsamplePoints` assume the keys they touch already exist and have compatible leading axes.
- `MultiDataset` can merge datasets only when the outputs are compatible enough for the chosen collation strategy.

## What to check before handing data to a model

- File pattern matches the actual files.
- Field names match the model/transform expectations.
- The loader returns the intended metadata if the training loop depends on source indices or filenames.
- Optional extras required by the chosen reader are installed.
