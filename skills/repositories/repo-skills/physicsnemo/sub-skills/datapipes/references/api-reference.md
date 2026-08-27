# PhysicsNeMo datapipe API reference

This file records the core constructor and route facts that the sub-skill uses most often.

| Object | Signature / key facts | Notes |
| --- | --- | --- |
| `Dataset` | `Dataset(reader, *, transforms=None, device=None, num_workers=2)` | Moves reader output to the target device before transforms. |
| `DataLoader` | `DataLoader(dataset, *, batch_size=1, shuffle=False, sampler=None, drop_last=False, collate_fn=None, collate_metadata=False, prefetch_factor=2, num_streams=4, use_streams=True, seed=None)` | PhysicsNeMo loader is stream/thread oriented, not PyTorch multiprocessing-centric. |
| `MeshDataset` | `MeshDataset(reader, *, transforms=None, device=None, num_workers=1)` | For native mesh readers. |
| `MultiDataset` | `MultiDataset(*datasets, output_strict=True)` | Concatenates datasets into one index space. |
| `NumpyReader` | `NumpyReader(path, *, fields=None, default_values=None, file_pattern='*.npz', index_key=None, pin_memory=False, include_index_in_metadata=True, coordinated_subsampling=None)` | Use for NPZ/NumPy samples. |
| `HDF5Reader` | `HDF5Reader(path, *, fields=None, file_pattern='*.h5', index_key=None, pin_memory=False, include_index_in_metadata=True)` | Use for HDF5 datasets. |
| `ZarrReader` | `ZarrReader(path, *, fields=None, default_values=None, group_pattern='*.zarr', pin_memory=False, include_index_in_metadata=True, coordinated_subsampling=None, cache_stores=True)` | Use for local Zarr groups. |
| `TensorStoreZarrReader` | `TensorStoreZarrReader(path, *, fields=None, default_values=None, group_pattern='*.zarr', cache_bytes_limit=10000000, data_copy_concurrency=72, file_io_concurrency=72, pin_memory=False, include_index_in_metadata=True, coordinated_subsampling=None)` | Best when the workflow needs explicit cache/concurrency controls. |
| `VTKReader` | `VTKReader(path, *, keys_to_read=None, exclude_patterns=None, pin_memory=False, include_index_in_metadata=True)` | Optional VTK/PyVista stack required for runtime use. |
| `MeshReader` | `MeshReader(path, *, pattern='**/*.pmsh', pin_memory=False, include_index_in_metadata=True, subsample_n_points=None, subsample_n_cells=None)` | PhysicsNeMo native mesh archives. |
| `DomainMeshReader` | `DomainMeshReader(path, *, pattern='**/*.pdmsh', pin_memory=False, include_index_in_metadata=True, subsample_n_points=None, subsample_n_cells=None, extra_boundaries=None, drop_interior_cells=False, drop_in_file_boundaries=False)` | Native domain-mesh archives with optional boundary handling. |
| `Normalize` | `Normalize(input_keys, means=None, stds=None, *, method=None, mins=None, maxs=None, stats_file=None, eps=1e-08)` | Use after the raw keys and shapes are correct. |
| `SubsamplePoints` | `SubsamplePoints(input_keys, n_points, *, algorithm='poisson_fixed', weights_key=None)` | Useful for point-cloud or mesh point subsetting. |
| `Compose` | `Compose(transforms)` | Standard transform chain container. |
| `KNearestNeighbors` | `KNearestNeighbors(points_key, queries_key, k, *, output_prefix='neighbors', extract_keys=None, drop_first_neighbor=False)` | Common geometry helper for graph-style datapipes. |
| `MeshToTensorDict` | `MeshToTensorDict()` | Converts mesh payloads into TensorDict-style data. |

## Practical notes

- Readers load from storage; transforms operate on loaded samples; the loader batches and prefetches.
- The first dimension usually acts as the sample axis for array readers.
- Data format, file pattern, and index-key mismatches are the most common failure mode.
- For mesh data, make sure the payload type matches `MeshDataset` and the mesh reader you chose.
