# Dense search API contract

The public CPU Python contract here is Faiss 1.15.0 with Python `>=3.10` and
NumPy arrays. The prepared CPU build reports `OPTIMIZE DD AVX2`. GPU and other
accelerator variants are not implied by this route; use the accelerated sibling
when they are required.

## Inputs and metrics

| Contract | Required behavior |
| --- | --- |
| Database/query | `xb` and `xq` are 2-D matrices `(n, d)` and `(nq, d)` with the same `d`; all index methods consume 32-bit floats. |
| Layout | Make arrays C-contiguous with `np.ascontiguousarray(x, dtype="float32")`; do this explicitly before retaining or passing data. |
| L2 | `METRIC_L2` returns squared Euclidean distance; smaller is better. `IndexFlatL2(d)` is exact. |
| Inner product | `METRIC_INNER_PRODUCT` returns dot products; larger is better. `IndexFlatIP(d)` is exact. |
| Cosine | Normalize **both** database and query rows to unit L2 norm, then use `METRIC_INNER_PRODUCT`; `faiss.normalize_L2(x)` mutates the 2-D float32 array. |

Cosine is not a separate metric enum in this workflow. Normalization must happen
before `add` for `xb` and before every `search`/`range_search` for `xq`. A query
that is normalized against an unnormalized database, or vice versa, is an IP
search with norm bias rather than cosine search. Preserve unnormalized arrays if
the application needs them; normalization is in-place.

A minimal metric setup is:

```python
xb = np.ascontiguousarray(xb, dtype="float32")
xq = np.ascontiguousarray(xq, dtype="float32")
faiss.normalize_L2(xb)                 # only when using cosine
faiss.normalize_L2(xq)
index = faiss.IndexFlatIP(xb.shape[1])
index.add(xb)
D, I = index.search(xq, k)
```

For direct utilities without retaining an index, `faiss.knn(xq, xb, k,
metric)` returns `(D, I)` with the same `(nq, k)` shape contract. Use
`faiss.pairwise_distances(xq, xb, metric)` for the full `(nq, nb)` matrix; it
is exact and can be much larger than a top-k result.

## Index lifecycle and constructors

| Index | Construction | Training | Add/search behavior |
| --- | --- | --- | --- |
| `IndexFlatL2(d)` / `IndexFlatIP(d)` | Stores full float vectors and exhaustively compares them. | Already trained (`is_trained` is true). | `add(xb)` assigns sequential labels; exact top-k and range search. |
| `IndexIVFFlat(quantizer, d, nlist, metric)` | Uses a coarse quantizer to select inverted lists; stores raw vectors in each selected list. | Required. `is_trained` starts false; call `train(xtrain)` before `add`. | Non-exhaustive search; `nprobe` controls how many coarse lists are visited. |
| `IndexHNSWFlat(d, M[, metric])` | Stores full vectors with an HNSW graph; `M` controls graph connectivity. | No separate training for Flat storage (`is_trained` is true); `add` builds links. | Approximate graph search; `hnsw.efConstruction` affects build quality and `hnsw.efSearch` affects query work/recall. |
| `IndexNSGFlat(d, R[, metric])` | Stores full vectors with an NSG graph; `R` controls graph degree. | No separate training for Flat storage; graph is built while adding. | Approximate graph search. Benchmark its build/search behavior for the target workload; do not assume HNSW tuning fields apply. |
| `IndexNNDescentFlat(d, K[, metric])` | Stores full vectors with an NN-Descent graph; `K` controls graph construction neighborhood. | No separate training for Flat storage. | Approximate graph search. Treat available tuning and range behavior as implementation-specific. |

For IVF, use representative training vectors with the same dimension and
metric/data distribution as the database. Training learns coarse centroids; it
does not add vectors. Re-run training if the data distribution changes
substantially. `add` is only valid after training for an IVF index. Do not
concurrently mutate an index while searching it.

The Python wrappers enforce `x.shape[1] == index.d`, convert inputs to
contiguous float32 for the standard float32 methods, and require `k > 0`.
Validate these conditions yourself at application boundaries so errors are
clear before entering a hot path.

## Search results and related operations

`D, I = index.search(xq, k)` returns:

- `D`: float32, shape `(nq, k)`, ordered from best to worse under the metric.
- `I`: int64, shape `(nq, k)`, labels corresponding to `D`.
- Added-without-custom-ID vectors have labels `0 .. ntotal - 1` in add order.
- When fewer than `k` vectors are available, missing labels are `-1`. The
  missing distance is the metric's worst float sentinel: positive max-float for
  L2 and negative max-float for inner product in the CPU Python wrapper. Never
  treat a `-1` label as a valid database ID.

`index.assign(xq, k)` returns only the int64 label matrix with shape `(nq, k)`
and the same `-1` padding. It is useful when distances are unnecessary.

`lims, D, I = index.range_search(xq, radius)` returns a variable-length result
set:

- `lims` has length `nq + 1`; query `j` owns the half-open slice
  `lims[j]:lims[j + 1]` in the flat `D` and `I` arrays.
- `D` is float32 and `I` is int64; the flat arrays can be empty when no query
  has a match.
- L2 keeps vectors with distance `< radius`; inner product keeps scores `>
  radius`. Choose thresholds in the same metric scale as the index.
- Range search is optional in the base API and not universal across all index
  types. Flat, IVF, and HNSW implement it in this CPU scope; check the concrete
  class before relying on it for another graph index.
- Approximate IVF/HNSW range search can omit true neighbors. Compare with Flat
  if completeness matters.

## Search-time controls

| Control | Where | Meaning and tuning rule |
| --- | --- | --- |
| `index.nprobe` | IVF indexes | Number of coarse lists visited per query; default is `1`. Increase toward `nlist` to improve recall at higher latency. Keep `1 <= nprobe <= nlist`. |
| `index.hnsw.efConstruction` | HNSW | Candidate expansion while building. Set before `add`; larger values generally cost more build time and memory/work but can improve graph quality. |
| `index.hnsw.efSearch` | HNSW | Candidate expansion during search. Set at least `k`; increase until recall meets the target, measuring latency. |
| `SearchParametersHNSW.efSearch` | Per-call HNSW override | Use when different queries need different budgets; it overrides the index-level value. |
| `index.parallel_mode` | IVF | Advanced OpenMP scheduling: `0` splits over queries (default), `1` over inverted lists, `2` over both, and `3` uses finer query granularity. Benchmark before changing it. |

`nprobe` and `efSearch` are work/quality knobs, not accuracy guarantees. Always
measure recall against `IndexFlatL2` or `IndexFlatIP` on a representative sample;
use the same metric and normalization for the baseline.

## Factory strings

`faiss.index_factory(d, description, metric=faiss.METRIC_L2)` builds the CPU
index described by a compact string. Examples:

```python
exact_l2 = faiss.index_factory(64, "Flat", faiss.METRIC_L2)
exact_ip = faiss.index_factory(64, "Flat", faiss.METRIC_INNER_PRODUCT)
ivf_flat = faiss.index_factory(64, "IVF256,Flat", faiss.METRIC_L2)
hnsw_flat = faiss.index_factory(64, "HNSW32,Flat", faiss.METRIC_L2)
nsg_flat = faiss.index_factory(64, "NSG32,Flat", faiss.METRIC_L2)
```

Factory descriptions that name codecs (`PQ`, `SQ`, or similar), binary
representations, transforms, refiners, or ID wrappers belong to the sibling
routes rather than this reference. Factory syntax is version-sensitive: if a
string fails, inspect the concrete type and package version instead of silently
falling back to a different index.

## OpenMP controls

Faiss exposes process-level controls:

```python
old_threads = faiss.omp_get_max_threads()
try:
    faiss.omp_set_num_threads(4)
    D, I = index.search(xq, k)
finally:
    faiss.omp_set_num_threads(old_threads)
```

Use a positive, deliberate count for reproducible smoke tests and avoid
multiplying Faiss threads by an already-threaded BLAS or application worker
pool. These calls affect the process, so restore the previous count in library
code and tests. The effective CPU performance also depends on the prepared
build's SIMD/OpenMP support and host; this scope verifies CPU behavior only.
