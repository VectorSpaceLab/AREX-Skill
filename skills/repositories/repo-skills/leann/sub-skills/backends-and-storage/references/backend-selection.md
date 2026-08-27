# Backend selection and update policy

This is the backend-specific decision record. It does not replace the sibling
sub-skills' generic `LeannBuilder`, `LeannSearcher`, or document-loading recipes.
Use the registered backend name exactly as shown below.

## Registry and package names

`autodiscover_backends()` scans installed distributions whose name starts with
`leann-backend-`, converts hyphens to underscores, and imports them in sorted
order. Backend modules register factories through `register_backend()`.
Import failures are skipped during discovery, so a distribution can be
installed yet absent from the registry when its native dependency cannot load.

| Distribution | Registry/backend name | Factory behavior |
|---|---|---|
| `leann-backend-hnsw` | `hnsw` | Custom FAISS HNSW graph; default storage-saving path |
| `leann-backend-ivf` | `ivf` | CPU FAISS `IndexIVFFlat` with ID-based updates |
| `leann-backend-diskann` | `diskann` | Optional on-disk DiskANN graph/PQ search |
| `leann-backend-flashlib` | `flashlib` | Optional CUDA exact k-NN (`NearestNeighbors`) |
| `leann-backend-flashlib-ivf` | `flashlib_ivf` | Optional CUDA IVF-Flat |

The current core build parser exposes `hnsw`, `diskann`, and `ivf` as its
backend choices. Optional FlashLib packages register successfully for API
construction when installed, but an application/parser must also accept their
names; do not infer CLI support solely from package installation.

## Choose by workload

| Workload or constraint | First choice | Why | Cost or boundary |
|---|---|---|---|
| CPU laptop, smallest vector storage, mostly read/search | `hnsw` | Graph can be compact/CSR and embeddings can be pruned for recomputation | Compact/pruned indexes are not incrementally mutable; recomputation needs ZMQ/model path |
| Frequent CPU add/remove/modify operations | `ivf` | Flat vectors plus `DirectMap.Hashtable` support ID-based remove then add | Full vectors are stored; IVF must be trained and `nlist` must be viable for corpus size |
| Larger-than-memory or disk-oriented corpus | `diskann` | Disk-backed graph/PQ layout and optional graph partitioning | Native optional dependency, build is heavier, and partitioning has extra artifacts |
| CUDA search with exact GPU k-NN | `flashlib` | Rebuilds a `NearestNeighbors` index from persisted vectors | Full `.npy` vectors; CUDA required at search, no LEANN graph recomputation savings |
| CUDA approximate IVF search | `flashlib_ivf` | GPU coarse cells and `nprobe` search; persists the built tensor state | CUDA required at build and search; full `.pt` tensor state; no local native verification |

These are operating trade-offs, not benchmark guarantees. Selective
recomputation can reduce stored vector data, but its latency and recall depend
on the corpus, model, hardware, and search parameters.

## HNSW storage and lifecycle

The HNSW builder's backend defaults are `is_compact=True`, `is_recompute=True`,
`M=32`, `efConstruction=200`, and `distance_metric="mips"`. The core CLI has
its own build defaults and currently defaults to non-compact mode so an
add-only update can remain possible; inspect the resulting metadata rather
than assuming a constructor default.

- **Compact:** the built FAISS graph is converted to CSR. With recomputation,
  the embedded vector storage is pruned. The searcher loads it with compact and
  pruned flags. A compact HNSW index cannot use `update_index`; rebuild it.
- **Non-compact with recomputation:** retain the update-compatible graph layout
  while pruning embedded vectors. Search must use recomputation when the index
  is pruned.
- **Non-compact without recomputation:** keep full vector storage for direct
  distance evaluation. The builder forces `is_compact=False` if a caller asks
  for `is_recompute=False` with compact enabled.
- **Incremental behavior:** non-compact HNSW supports add-only append. A changed
  or removed file is not an in-place graph edit; the CLI falls back to a full
  corpus rebuild. The fallback must reload untouched files as well as changed
  files, rather than rebuilding from the delta only.

If an HNSW search reports that recomputation is required, do not just disable
recompute: rebuild with non-recompute and non-compact storage if full vectors
are intentionally available.

## IVF modification workflow

The CPU IVF builder constructs FAISS `IndexIVFFlat` with an L2 or inner-product
flat quantizer, trains it, enables `DirectMap.Hashtable`, and adds integer IDs.
The adjacent JSON ID map translates those integers to stable passage IDs.

For an existing IVF index, the supported update order is:

1. Detect the changed/deleted passage IDs.
2. Call the IVF remove path for those IDs.
3. Compact the passage JSONL and offset map for removed IDs.
4. Re-embed changed/new chunks and append them with new FAISS integer IDs.
5. Validate that the passage IDs, offset map, and IVF ID map agree.

`add_vectors(index_path, embeddings, passage_ids)` rejects duplicate passage IDs
and mismatched row counts. `remove_ids(index_path, passage_ids)` returns the
number actually removed and does not reuse old integer IDs; a short removal
count is an inconsistency warning, not proof of success. Do not use this API on
HNSW or on a missing `.index` file.

An IVF build requires enough training data for its configured `nlist`; the
backend's default is `nlist=100`. Reduce `nlist` for small corpora or fail
explicitly rather than treating an untrained index as searchable. Search uses
`nprobe`, defaulting to `min(complexity, nlist)` when no explicit `nprobe` is
provided.

## DiskANN selection and partitioning

DiskANN is the larger-than-memory choice when a disk-backed graph and product
quantization (PQ) are preferable to keeping a complete FAISS graph in memory.
The builder writes a temporary vector binary, invokes native DiskANN with
`complexity`, `graph_degree`, memory ceilings, thread count, and optional PQ
bytes, then removes the temporary input.

With `is_recompute=True`, the build automatically invokes graph partitioning.
Partitioning produces a relaid-out disk graph and partition map and can safely
remove the large original disk graph only after medoid, PQ, and other required
auxiliary files exist. Search auto-detects the pair
`<prefix>_disk_graph.index` and `<prefix>_partition.bin`; without both it uses
the standard `<prefix>_disk.index` layout. Partitioned and standard layouts
must not be mixed or partially copied.

DiskANN has no verified incremental add/remove contract here. Treat a changed
corpus as a rebuild operation and preserve the whole artifact set.

## Selection checklist

Before building or changing a backend, record:

- registry name and installed distribution;
- corpus size versus `nlist` (IVF/FlashLib IVF) and versus DiskANN's PQ/native
  constraints;
- whether storage or frequent mutation is primary;
- dimensions, metric, and whether the model produces unit-normalized vectors;
- recomputation availability (embedding model/provider, ZMQ port, passage files);
- required hardware/native packages and the verification gate;
- the exact artifact directory to validate after the build.
