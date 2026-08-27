# Optional and accelerator backends

These paths are documented from package source and tests but were not native
verified on the local CPU environment unless explicitly noted below. Treat
availability, build success, and performance as environment-specific.

## DiskANN

Distribution: `leann-backend-diskann`; registry name: `diskann`.

DiskANN is designed for disk-oriented, larger-than-memory search. Its builder
uses a native `diskannpy` extension, writes a temporary `<prefix>_data.bin`,
constructs a graph and PQ files in a child process, then removes the temporary
input. When recomputation is enabled it invokes the bundled graph partition
flow. The partitioner produces:

- `<prefix>_disk_graph.index` (relayout graph);
- `<prefix>_partition.bin` (partition map);
- `<prefix>_disk.index_medoids.bin` and
  `<prefix>_disk.index_max_base_norm.bin` (required auxiliary data);
- `<prefix>_pq_compressed.bin` and `<prefix>_pq_pivots.bin` (PQ data).

A partitioned searcher detects the graph/map pair. The build cleanup removes
`<prefix>_disk.index` and `<prefix>_disk_beam_search.index` only when required
files exist; never copy or delete a subset manually. Standard non-partition
search instead needs `<prefix>_disk.index` and the PQ files.

The DiskANN partition tests are intentionally hardware/memory-skipped in CI.
The current local prepared facts mark DiskANN optional and not locally native-
verified; use a native build/search smoke test before publication.

## FlashLib exact GPU backend

Distribution: `leann-backend-flashlib`; registry name: `flashlib`.

Install requires `flashlib` and `torch`; CUDA is required at search time. The
builder only persists full float32 vectors in `<prefix>.flashlib.npy` and IDs
in `<prefix>.flashlib_id_map.json`. The searcher loads vectors into CUDA and
fits `NearestNeighbors` at startup. It is exact GPU k-NN in the current source,
not the approximate IVF backend.

## FlashLib IVF GPU backend

Distribution: `leann-backend-flashlib-ivf`; registry name: `flashlib_ivf`.

CUDA is required at both build (GPU k-means training) and search. The builder
serializes tensor state with `torch.save` to
`<prefix>.flashlib_ivf.pt` and writes the ordered ID map to
`<prefix>.flashlib_ivf_id_map.json`; the searcher reloads tensors onto CUDA and
does not retrain. It uses squared L2 internally and normalizes for mips/cosine.

The package test covers registration, persistence/reload, matched `(nlist,
 nprobe)` comparison, and recall thresholds only when CUDA and FlashLib are
available. Those thresholds are test gates, not promises for arbitrary data.

## HNSW native build and platform variants

Distribution: `leann-backend-hnsw`; registry name: `hnsw`.
The source-built local verification passed for HNSW `0.3.8` on CPU and required
initialized FAISS, msgpack-c, cppzmq, ZeroMQ, and explicit BLAS/LAPACK CMake
libraries. Prebuilt wheels and source builds can have different ABI behavior.

The HNSW package contains Windows DLL search-path setup for vcpkg-built native
libraries and disables GPU FAISS in its CMake configuration. On Apple Silicon,
MLX/MPS may be used by the embedding layer, but that does not make HNSW,
DiskANN, or FlashLib native search GPU backends. The prepared facts mark MLX,
MPS, CUDA FlashLib, and DiskANN as optional/not locally native-verified.

## Distribution and device gate

Before selecting an optional backend:

1. Confirm the exact distribution is installed in the same Python environment
   that runs LEANN.
2. Run registry discovery and inspect whether the exact registry name appears.
3. Probe the native dependency (`diskannpy`, `torch.cuda`, or `flashlib`) without
   building a production index.
4. Build a small isolated fixture, then search it with matching metric and
   dimension.
5. Preserve all backend artifacts and run the read-only inspector.

A registry entry proves import/registration only. It does not prove CUDA device
compatibility, native ABI compatibility, or model/provider availability.
