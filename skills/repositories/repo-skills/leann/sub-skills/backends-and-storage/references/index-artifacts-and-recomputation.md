# Index artifacts and selective recomputation

## Naming model

For an index path such as `name.leann`, LEANN stores metadata beside it as
`name.leann.meta.json` and standard passage data as
`name.leann.passages.jsonl` plus `name.leann.passages.idx`. Backend builders use
the path stem (`name`) for their own artifacts. A core build also commonly
writes `name.ids.txt`, although backends with their own map may use a dedicated
map file.

The metadata is the authority for `backend_name`, `dimensions`, embedding
configuration, backend kwargs, and `passage_sources`. Relative passage paths
are resolved from the metadata file directory. A source is JSONL and its index
is a pickled map from passage ID to byte offset; each source has its own map.

## Required artifact families

| Backend | Required or normal files | Meaning |
|---|---|---|
| HNSW | `<prefix>.index`, usually `<prefix>.ids.txt` | FAISS HNSW graph; compact/CSR and vector-pruning state is encoded in the index and metadata |
| IVF | `<prefix>.index`, `<prefix>.ivf_id_map.json` | FAISS `IndexIVFFlat`; JSON maps integer FAISS IDs to passage IDs and tracks `next_id` |
| DiskANN standard | `<prefix>_disk.index`, `<prefix>_pq_compressed.bin`, `<prefix>_pq_pivots.bin` | Native disk graph and PQ data; other native auxiliary files may also be present |
| DiskANN partitioned | `<prefix>_disk_graph.index`, `<prefix>_partition.bin`, PQ files, `<prefix>_disk.index_medoids.bin`, `<prefix>_disk.index_max_base_norm.bin` | Relayout/partition path used for selective recomputation and lower disk/memory pressure |
| FlashLib | `<prefix>.flashlib.npy`, `<prefix>.flashlib_id_map.json` | Full float32 vectors plus ordered passage IDs; GPU `NearestNeighbors` is rebuilt at searcher startup |
| FlashLib IVF | `<prefix>.flashlib_ivf.pt`, `<prefix>.flashlib_ivf_id_map.json` | Serialized centroids/cell data/IDs/CSR offsets plus ordered passage IDs; tensors reload onto CUDA |

The plain `.index` suffix is not enough to identify IVF versus HNSW; read
`.meta.json` first. Never copy only the metadata or only a vector artifact.

## Passage and offset integrity

A passage lookup has two hops: a backend result label must identify a passage
ID, then that ID must exist in the source offset map, and the byte offset must
land on a JSONL record with the same ID. Therefore:

- “backend artifact missing” means the native/vector searcher cannot load its
  graph, index, tensors, or ID map;
- “passage offset missing” means search may return a label but enrichment cannot
  load text/metadata from JSONL;
- stale JSONL records not referenced by the offset map indicate an incomplete
  update/compaction and should be repaired by the owning update/rebuild path,
  not by hand-editing the files.

Run the bundled read-only checker against the `.leann` path or a directory
containing one metadata file:

```text
python scripts/inspect_leann_index.py path/to/name.leann
python scripts/inspect_leann_index.py path/to/name.leann --json
python scripts/inspect_leann_index.py path/to/name.leann --strict
```

It validates metadata, all declared JSONL/offset sources, offset-to-record
identity, and the artifact family implied by `backend_name`. `--strict` turns
non-fatal consistency warnings into failures. It deliberately does not import
FAISS, DiskANN, FlashLib, Torch, or an embedding model, and it never writes,
repairs, deletes, or downloads anything.

## Recompute path

Selective recomputation removes or prunes stored embedding vectors and obtains
fresh vectors for search candidates. The common flow is:

1. `LeannSearcher` reads metadata and creates the backend searcher.
2. For an effective recompute search, the core starts or reuses the backend's
   embedding server and passes the metadata file as the passage source.
3. The server communicates over a local ZeroMQ request/reply socket. The core
   manager chooses an available port starting at the requested/default port,
   and a direct backend call must pass the actual `zmq_port` when the backend
   requires recomputation.
4. The backend traverses its graph/index and uses fresh vectors either during
   distance evaluation or in a final rerank, depending on backend behavior.

The manager's reuse signature includes model name, embedding mode/options,
metric, metadata path, and modification signatures for referenced passage and
index files. A changed source therefore must not be hidden behind a reused
server. Provider prompt templates are filtered from server options during
search because the query template is applied before the request.

### Backend-specific recompute rules

- **HNSW:** compact/pruned indexes require `recompute_embeddings=True` and a
  valid port. A direct HNSW search without a port raises; a pruned index with
  recomputation disabled raises with a rebuild instruction.
- **DiskANN:** recompute requires a port and uses deferred final fetching while
  traversal uses PQ distances. `proportional` pruning is unsupported; use
  `global` or `local`.
- **IVF/FlashLib/FlashLib IVF:** these backends use their stored vectors for
  vector search. They can reuse the common embedding server for query
  embedding when the public searcher is configured to recompute, but they do
  not provide HNSW-style graph-neighbor selective recomputation.

A server start failure is not the same as a valid recompute result. The common
query-embedding path may fall back to direct model loading, while a backend
that needs fresh neighbor vectors still requires a working ZMQ path. Diagnose
both the server process and the backend's recompute flag.

## Dimension and label invariants

The metadata dimension must equal the embedding width and native index width.
A backend can fail at build, load, or search if these disagree. The passage ID
map must use the same IDs as the offset maps; integer FAISS labels are only
internal IDs and must not be mistaken for passage IDs.

The checker can prove file/label/offset consistency, but not native index
header dimensions or vector contents. Use a backend-native smoke test after the
checker when a dimension or metric mismatch is suspected.
