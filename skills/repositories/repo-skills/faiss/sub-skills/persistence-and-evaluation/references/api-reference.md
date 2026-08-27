# Persistence and evaluation API reference

Facts below target the verified CPU package `faiss-cpu` 1.15.0 with Python >=3.10.
The required array contract is NumPy `float32`, shape `(n, d)`, preferably C
contiguous. Faiss returns distances as `float32` and labels as `int64`; a
missing label is `-1`. GPU, cuVS, ROCm, Metal, SVS, and GPU ground-truth
operations are optional and unverified in this CPU environment.

## Index I/O and cloning

| Operation | Python form | Important behavior |
|---|---|---|
| Bytes write | `data = faiss.serialize_index(index, io_flags=0)` | Returns a NumPy `uint8` array. Keep a reference until a zero-copy reader has finished. |
| Bytes read | `index = faiss.deserialize_index(data, io_flags=0)` | `data` must contain the complete serialized payload. It constructs an index; it is not a validator for untrusted content. |
| File write | `faiss.write_index(index, filename, io_flags=0)` | Writes a CPU index. Use a new temporary path and `os.replace` for durable publication. |
| File read | `index = faiss.read_index(filename, io_flags=0)` | Some flags apply only to some index types. External OnDisk data may be another file. |
| Deep clone | `copy = faiss.clone_index(index)` | Intended to preserve search behavior independently. Verify parity for advanced or optional index types. |
| Binary I/O | `serialize_index_binary`, `deserialize_index_binary`, `write_index_binary`, `read_index_binary` | Use these for `IndexBinary`; do not use the float-index serializer interchangeably. |

The C++ API also supports `FILE*` and `IOReader`/`IOWriter`; Python wrappers
expose callback, buffered, file, vector, and zero-copy reader/writer helpers.
Those are useful for a controlled stream, but a plain complete NumPy byte array
or a named file is easier to audit.

### Read/write flags

The verified constants are:

| Constant | Value/meaning | Safe interpretation |
|---|---|---|
| `IO_FLAG_READ_ONLY` | `2` | Request read-only storage where the index type implements it; do not assume every index honors it. |
| `IO_FLAG_ONDISK_SAME_DIR` | `4` | For an OnDisk external file, strip its directory component and resolve it beside the index file. Use only when that layout is deliberate. |
| `IO_FLAG_SKIP_IVF_DATA` | `8` | Do not load IVF data into RAM. The result is not a complete populated searchable artifact unless its lists are supplied by the intended workflow. |
| `IO_FLAG_SKIP_PRECOMPUTE_TABLE` | `16` | Skip initialization of a precomputed table; search can initialize or otherwise behave differently in performance, so verify the resulting index. |
| `IO_FLAG_PQ_SKIP_SDC_TABLE` | `32` | Avoid PQ SDC-table computation; some distance/graph operations then cannot work. |
| `IO_FLAG_MMAP` | `IO_FLAG_SKIP_IVF_DATA \| 0x646f0000` | Request mmap-style IVF loading where supported. It is not a universal zero-copy mode. |
| `IO_FLAG_MMAP_IFC` | `1 << 9` (`512`) | Temporary mmap path for `IndexFlatCodes`-derived indexes and HNSW; support is index/platform dependent. |
| `IO_FLAG_SKIP_STORAGE` | `1` (write-side) | C++ graph-index write option that omits storage. Do not use when the serialized index must search by itself. |

Flags are not a security sandbox. They do not make a malicious file safe, and
mmap does not reduce the need to validate file ownership, size, permissions,
format, and lifetime.

Faiss 1.15.0 exposes process-global deserialization guards:

```python
faiss.set_deserialization_loop_limit(max_loop_count)
faiss.set_deserialization_vector_byte_limit(max_bytes_per_vector)
faiss.set_deserialization_lattice_r2_limit(max_r2)
```

The corresponding `get_...` functions report the current values. Set them
before concurrent reads and do not change them while another thread is
deserializing; the C++ contract says these setters are not thread-safe. Choose
limits from an explicit artifact budget, not from an arbitrary default.

## Reconstruction and stored codes

For indexes that implement the operation, the Python wrappers provide:

```python
x1 = index.reconstruct(key)                 # shape (d,), float32
xb_hat = index.reconstruct_batch(keys)      # shape (len(keys), d)
xb_hat = index.reconstruct_n(first, count)  # sequential ids
D, I, R = index.search_and_reconstruct(xq, k)
D, I, C = index.search_and_return_codes(xq, k, include_listnos=False)
```

`reconstruct` is an approximation for PQ/SQ/residual or other compressed
storage; compare `xb_hat` with the original vectors using an explicit metric
and report the error rather than calling it lossless. `sa_encode` returns
`uint8` codes of shape `(n, code_size)`, and `sa_decode` reconstructs from
those codes. For code APIs, Faiss rejects non-`uint8` code arrays rather than
silently casting them. ID maps and composed indexes have different
reconstruction support; route ownership and ID semantics to the composition
branch.

## Clustering and training data

`faiss.Kmeans(d, k, **kwargs)` wraps Faiss clustering. Useful bounded options
include `niter`, `nredo`, `seed`, `verbose`, `spherical`, `int_centroids`, and
`max_points_per_centroid`. Call `km.train(x)` with float32 `(n, d)` data;
`km.centroids` is a flat SWIG vector in some builds but the Python wrapper
normally exposes a NumPy array shaped `(k, d)`. `km.assign(x)` returns
`(distances, assignments)`. `km.obj` and `km.iteration_stats` expose objective
progress. Use at least `k` valid training rows and, for useful centroids, many
more rows per centroid. A tiny smoke may use `niter=5` and a fixed `seed`, but
its quality is not a production claim.

For lower-level weighted/composite clustering:

```python
clus = faiss.Clustering(d, k)
quantizer = faiss.IndexFlatL2(d)
clus.train(x, quantizer, weights=weights)  # weights shape (n,)
```

The assignment index dimension and training dimension must agree. For cosine,
normalize training vectors and use an inner-product assignment index; the
objective direction then differs from L2. `faiss.contrib.clustering` adds
helpers such as sparse assignment and may require SciPy for sparse Python
paths; core `faiss.Kmeans` does not imply that optional dependency.

## Ground truth and metrics

For a bounded in-memory baseline:

```python
metric = faiss.METRIC_L2  # or faiss.METRIC_INNER_PRODUCT
exact = faiss.IndexFlat(xb.shape[1], metric)
exact.add(np.ascontiguousarray(xb, dtype="float32"))
gt_D, gt_I = exact.search(np.ascontiguousarray(xq, dtype="float32"), k)
```

L2 results are **squared** Euclidean distances and smaller is better. Inner
product results are larger-is-better. Cosine similarity requires L2-normalized
vectors and inner product. The baseline and candidate must have identical
`d`, metric, row-to-id mapping, normalization, and `k`; otherwise a recall
number can look plausible while measuring different problems.

For a database that does not fit memory, the bounded-source pattern is a
block iterator: add one database block to an exact `IndexFlat`, search the
queries, offset returned IDs by the block start, merge each block's top-k with
`faiss.ResultHeap`, reset the flat index, then finalize. Faiss also supplies
`faiss.contrib.exhaustive_search.knn_ground_truth` for this pattern. Keep the
iterator local and bounded; do not make it download a dataset. GPU variants
belong to the accelerated branch and require a separate prepared backend.

## Evaluation formulas and helpers

For fixed-k result matrices `I` and ground truth `G`, per-query intersection
is `|set(I[q]) & set(G[q])|`. With `nq` queries and `k` unique results:

- `recall@k = sum(intersection_q) / sum(|G[q]|)`; with exactly `k` GT rows,
  this is `sum(intersection_q) / (nq*k)`.
- `precision@k = sum(intersection_q) / sum(|I[q]|)`; it equals recall only
  when both sides contain the same number of unique results.
- `faiss.eval_intersection(I, G)` returns the total intersection count for
  equal-row tables; divide by the appropriate denominator yourself.

For range search, results are flattened with `lims[q]:lims[q+1]`. For a
L2 threshold, keep distances `< threshold`; for inner product, keep values
`> threshold`. For reference IDs `G` and candidate IDs `I`:
`precision = TP / found`, `recall = TP / relevant`. Empty-query conventions
must be explicit. `faiss.contrib.evaluation.range_PR` supports `overall` and
per-query `average` modes; it intentionally compares IDs, not distances.

`faiss.OneRecallAtRCriterion(nq, R)` is suitable for parameter exploration:
call `criterion.set_groundtruth(D_or_None, gt_I)`, set `criterion.nnn` to the
number of trusted neighbors if the ground truth has more than `R`, then call
`criterion.evaluate(D, I)`. Confirm the criterion's `gt_I.shape[0] == nq` and
metric contract before use.

## ParameterSpace and operating points

`faiss.ParameterSpace` can discover and apply tunable parameters:

```python
ps = faiss.ParameterSpace()
ps.initialize(index)
ps.set_index_parameter(index, "nprobe", 4)
ps.set_index_parameters(index, "nprobe=4,quantizer_efSearch=32")
ops = ps.explore(index, xq, criterion)
```

The exact parameter names depend on the index family. `initialize` populates
reasonable ranges; inspect `ps.parameter_ranges`, `ps.n_experiments`, and
`ps.verbose` before running. `explore` trains/adds nothing for you and can run
many searches. For a safe experiment, bound query rows, set a fixed OpenMP
thread count, cap `n_experiments`, and record parameter string, wall time,
thread count, recall criterion, and dataset sizes. Timing is hardware- and
load-dependent: report medians after warmup, never compare one cold run as a
scientific speed claim. `OperatingPoints`/the returned operating-point table
keeps Pareto candidates rather than selecting a universal winner.

## IVF merge and on-disk storage

`index.merge_from(other, add_id=...)` requires compatible trained indexes:
matching dimension, metric, coarse quantizer, codec/training state, and
compatible composition. It is intended for compatible shards; validate IDs
and whether the source is consumed/emptied before relying on it.

`faiss.OnDiskInvertedLists(nlist, code_size, filename)` stores list codes and
IDs in a memory-mapped file. Its header documents the layout as codes followed
by IDs per list and warns that incremental additions/resizes are slow. For
bulk merging, `faiss.contrib.ondisk.merge_ondisk(trained_empty_index,
shard_fnames, ivfdata_fname, shift_ids=False)` reads shard indexes with
`IO_FLAG_MMAP`, merges their lists, installs the output lists, and leaves the
final index dependent on `ivfdata_fname`. Keep all files together, publish them
atomically as a set, and do not delete or rewrite `ivfdata_fname` while the
index is live. `IO_FLAG_ONDISK_SAME_DIR` is useful when relocating that set.
