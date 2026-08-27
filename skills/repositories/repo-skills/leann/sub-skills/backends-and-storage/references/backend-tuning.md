# Backend tuning and compatibility

Tune one variable at a time on the target corpus and hardware. The values below
are implementation knobs and qualitative trade-offs, not recall, latency, or
storage guarantees.

## Metric and dimension contract

| Metric name | HNSW | IVF | DiskANN | FlashLib / FlashLib IVF |
|---|---:|---:|---:|---:|
| `mips` | inner product | inner product | inner product | normalize, then squared L2 |
| `cosine` | normalized inner product | normalized inner product | native cosine metric | normalize, then squared L2 |
| `l2` | squared L2 | squared L2 | L2 | squared L2 |

Every vector passed to a backend must have the same dimension `D` recorded in
metadata and the index. HNSW/IVF map cosine to inner product after L2
normalization. FlashLib exposes only squared L2, so its mips/cosine adapter
normalizes database and query vectors; do not mix already-normalized and
unnormalized data under one metric policy.

LEANN detects several OpenAI, Voyage, and Cohere embedding configurations as
unit-normalized and automatically selects cosine when no metric is supplied.
An explicit non-cosine metric emits a warning. This detection is a model/mode
allow-list and pattern check, not a proof that arbitrary custom vectors are
normalized; verify custom embeddings independently.

## Shared search controls

The public searcher forwards these controls to backend searchers:

| Control | Meaning | Backend effect |
|---|---|---|
| `complexity` | Candidate/traversal effort | HNSW `efSearch`; DiskANN candidate list; IVF/FlashLib IVF derives `nprobe` |
| `beam_width` | Parallel graph/IO paths per iteration | HNSW beam size; DiskANN beam/IO width; not an IVF scan control |
| `prune_ratio` | Approximate/PQ neighbor pruning ratio, normally `0.0` to `1.0` | HNSW and DiskANN native pruning; not a general IVF knob |
| `pruning_strategy` | Candidate selection policy | HNSW: `global`, `local`, `proportional`; DiskANN: `global` or `local` only |
| `batch_size` | Neighbor processing batch | HNSW-only in the core forwarding path; `0` disables it |

Higher effort normally costs more work; it does not guarantee monotonic recall
on every corpus. `top_k` is the result count and must remain meaningful for the
number of stored passages.

## HNSW knobs

- `M` controls graph degree at build time (builder default `32`); larger values
  generally consume more graph storage and build memory.
- `efConstruction` controls build effort (builder default `200`).
- `complexity` maps to `efSearch`; `beam_width` maps to `beam_size`.
- `prune_ratio` maps to the native `pq_pruning_ratio`.
- `global` uses the global PQ queue policy, `local` enables local pruning, and
  `proportional` enables ratio-based selection. These are search behaviors, not
  interchangeable storage formats.
- For OpenAI-like normalized embeddings with cosine, the searcher disables a
  relative-distance early check because narrow score ranges can otherwise
  terminate too early. Prefer cosine rather than masking a metric mismatch.

Use non-compact storage when the lifecycle needs HNSW add-only updates. Use
compact/pruned storage when storage is primary and the corpus is rebuilt as a
unit.

## CPU IVF knobs

- `nlist` is the number of coarse cells and is chosen at build/training time
  (builder default `100`). It cannot exceed the useful training population;
  reduce it for small corpora.
- `nprobe` is the number of cells scanned at search time. If omitted, the
  searcher sets `min(complexity, nlist)`.
- `distance_metric` selects the flat quantizer and normalization policy.
- `DirectMap.Hashtable` is required for the ID-based remove path. Do not replace
  it with an unverified ID-map composition and assume `remove_ids` semantics.
- After removal, integer IDs are not reused; the JSON map's `next_id` advances
  for later additions. Validate passage JSONL, offsets, and ID map together.

The `nlist`/`nprobe` pair is the principal IVF speed/quality control. Changing
`nlist` requires rebuilding/training; changing `nprobe` is a search-time choice.

## DiskANN knobs

The builder accepts `complexity`, `graph_degree`,
`search_memory_maximum`, `build_memory_maximum`, `num_threads`, and
`pq_disk_bytes`. If memory limits are omitted, the implementation derives a
search-memory value from vector size and a build-memory value from available
system memory; record explicit limits when reproducibility matters.

Search accepts `complexity`, `beam_width`, `prune_ratio`, `batch_recompute`, and
`dedup_node_dis`. `global` and `local` map to the native global-pruning flag;
`proportional` raises `NotImplementedError`. With recomputation, traversal uses
PQ distances and a deferred final fetch/rerank; without it, native traversal
uses its stored/PQ path without the same deferred fetch.

The native implementation warns for fewer than 256 vectors because its default
256 PQ centroids can produce noisy MKL `cblas_sgemm` diagnostics on some
systems. That warning is a dataset-size signal, not a correctness or benchmark
claim; HNSW is the simpler small-corpus fallback.

## FlashLib knobs

- `flashlib` is exact GPU `NearestNeighbors` in the current package source; it
  persists full vectors and does not use `nlist`/`nprobe` despite the package's
  historical IVFFlat wording.
- `flashlib_ivf` uses GPU IVF-Flat: build `nlist` (default `1024`, clamped to
  corpus size), `nprobe` (default `16` in the serialized index), `niter` (default
  `20`), and deterministic `seed` (default `0`). Search derives `nprobe` as
  `min(complexity, nlist)` unless explicitly supplied.
- Both variants convert mips/cosine to squared-L2 over unit-normalized vectors.
  Their full-vector storage is intentional; do not describe it as HNSW-style
  selective graph storage.

CUDA availability and FlashLib kernel compatibility must be checked on the
actual device. A file-level pass cannot substitute for a GPU smoke test.
