---
name: datapipes
description: "Build and debug PhysicsNeMo reader-to-Dataset-to-DataLoader data
  pipelines for TensorDict, mesh, streaming, and Hydra-configured workflows."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# PhysicsNeMo Datapipes Operating Skill

Use this sub-skill when the user needs to load scientific ML data into PhysicsNeMo, build reader → dataset → transform → `DataLoader` workflows, validate `TensorDict` payloads, choose file formats, configure Hydra datapipes, or debug data-format/collation/device/streaming failures.

## Trigger phrases

Use this sub-skill for requests that mention any of:

- PhysicsNeMo datapipes, readers, `Dataset`, `DataLoader`, `TensorDict`, `MultiDataset`, `MeshDataset`, or `IterableDatasetBase`.
- Loading NPZ/NumPy, HDF5, Zarr/TensorStore, VTK/STL, `.pmsh`, or `.pdmsh` data into a model.
- `Normalize`, `SubsamplePoints`, `Compose`, `KNearestNeighbors`, `MeshToTensorDict`, custom readers/transforms/collators, Hydra `${dp:...}` configs, or data-pipeline reproducibility.
- Errors involving missing fields, wrong file patterns, mismatched `TensorDict` keys/shapes, optional dependencies, CPU↔CUDA transfer, stream prefetching, or online/iterable generators.

## Fast route

1. **Classify the data source.** Use the reader selection notes below, then open [references/data-formats.md](references/data-formats.md) for exact layout expectations.
2. **Build the smallest pipeline.** Start with `Reader`, inspect `len(reader)`, `reader.field_names`, and `reader[0]`; then wrap with `Dataset`, then `DataLoader`. Recipes are in [references/datapipe-workflows.md](references/datapipe-workflows.md).
3. **Validate the payload.** Confirm keys, shapes, dtypes, metadata, device, batch dimension, and collation strategy before connecting to a model.
4. **Add transforms last.** Apply `Normalize`, `SubsamplePoints`, spatial/mesh transforms, or custom transforms only after raw reader output is correct. Use [references/api-reference.md](references/api-reference.md) for exact constructor names.
5. **Debug synchronously first.** For hard failures, set `prefetch_factor=0` or call `loader.disable_prefetch()` before investigating CUDA streams or threaded I/O. See [references/troubleshooting.md](references/troubleshooting.md).
6. **Run a tiny smoke when in doubt.** The bundled helper [scripts/create_tiny_npz_datapipe.py](scripts/create_tiny_npz_datapipe.py) creates a temporary NPZ fixture and exercises `NumpyReader → Dataset → DataLoader` on CPU or CUDA.

## Reader selection

- **Single `.npz` with sample axis in the first dimension:** use `NumpyReader(path, fields=..., index_key=...)`.
- **Directory of `.npz` sample files:** use `NumpyReader(directory, file_pattern="sample_*.npz", fields=...)`; this mode supports reader-side coordinated subsampling.
- **Single or directory HDF5:** use `HDF5Reader`; it reads root-level datasets by key and indexes the first dimension in single-file mode.
- **Zarr groups:** use `ZarrReader` for local Zarr groups, attributes-as-tensors, store caching, and single-group or directory mode.
- **Large/local Zarr with async reads:** use `TensorStoreZarrReader` when `tensorstore` is installed and you want explicit cache/concurrency controls.
- **STL-style VTK surface samples:** use `VTKReader` only when the optional VTK/PyVista stack is installed and the sample directories contain supported mesh files.
- **Native PhysicsNeMo mesh archives:** use `MeshReader` for `.pmsh` single meshes and `DomainMeshReader` for `.pdmsh` domain meshes; pair with `MeshDataset` and mesh transforms.
- **No stable length or index:** implement `IterableDatasetBase` and let `DataLoader` use the main-thread generator path.

## Validation checklist

Before handing a datapipe to a training or inference loop, verify:

- `len(reader)` is correct for map-style data, or `len(loader)` intentionally raises for iterable data.
- `reader.field_names` or the first sample contains the expected keys.
- `reader[0]` returns `(TensorDict, metadata)` for tensor readers, or `(Mesh/DomainMesh, metadata)` for mesh readers.
- `Dataset(reader, device=...)` moves tensors to the intended device before transforms.
- Transform input keys exist and have compatible first dimensions for coordinated subsampling.
- The selected collator matches sample shape: default stacking for fixed shapes; concat/custom collation for variable-length point clouds or graph objects.
- `DataLoader(..., collate_metadata=True)` returns metadata only if the training loop needs source indices, filenames, or `dataset_index`.
- `seed=` and `loader.set_epoch(epoch)` are used when stochastic readers/transforms must be reproducible.

## Route to sibling sub-skills

- For **which model family or example to pair with a datapipe**, route to [model-selection](../model-selection/SKILL.md).
- For **mesh creation, mesh validation, repair, geometry calculations, or mesh serialization beyond loading**, route to [mesh-and-geometry](../mesh-and-geometry/SKILL.md).
- For **distributed samplers, DDP/FSDP2, ShardTensor, domain parallel input scatter, or multi-GPU launch issues**, route to [distributed-and-domain-parallel](../distributed-and-domain-parallel/SKILL.md).
- For **diffusion/generative datasets tied to sampler or preconditioner workflows**, route to [diffusion-and-generative](../diffusion-and-generative/SKILL.md) after the data path is validated.
- For **active-learning orchestration, logging/checkpoints, or ONNX export after data loading**, route to [active-learning-and-deployment](../active-learning-and-deployment/SKILL.md).

## Operating cautions

- Treat readers as CPU I/O adapters. Do not put GPU kernels, model calls, downloads, credential prompts, or long preprocessing inside a `Reader._load_sample` implementation.
- Transforms mutate/update `TensorDict`-style payloads; order matters.
- PhysicsNeMo's `DataLoader` is thread/stream oriented rather than PyTorch multiprocessing oriented. Pinned reader output plus `device="cuda"` is what enables asynchronous host-to-device transfer.
- Never assume large domain examples are smoke tests. Use tiny generated fixtures for validation, then document external-data and optional-dependency requirements separately.
