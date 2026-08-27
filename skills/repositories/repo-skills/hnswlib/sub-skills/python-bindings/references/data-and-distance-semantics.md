# Data and distance semantics

## Accepted buffers and safe shapes

The binding accepts Python buffer-like input and force-casts it to contiguous
`float32` storage. The intended vector contract is:

- one vector: shape `(dim,)`, interpreted as one row;
- batch: shape `(rows, dim)`, interpreted as `rows` vectors;
- no other rank: 3-D and higher input is rejected by the binding;
- labels: one-dimensional integer array of length `rows`, or a scalar integer
  only when `rows == 1`.

Use an explicit boundary helper before calling native code:

```python
def checked_vectors(value, dim):
    x = np.asarray(value, dtype=np.float32)
    if x.ndim not in (1, 2):
        raise ValueError("vectors must be 1-D or 2-D")
    if x.shape[-1] != dim:
        raise ValueError(f"expected trailing dimension {dim}, got {x.shape[-1]}")
    if not np.isfinite(x).all():
        raise ValueError("vectors must be finite")
    return x
```

The insertion path explicitly raises for a wrong trailing dimension and for an
ID count/shape mismatch. The query path obtains the row and feature counts but
does not perform the same explicit `features == dim` check in the observed C++
binding. A wrong-dimension query is therefore unsupported even if a particular
call appears to return; validate it locally to avoid an unsafe native read.

Casts from integer or float64 arrays are convenient, but callers should make
the conversion visible so precision and memory ownership are understood. IDs
are cast to the native unsigned-size label type. Use non-negative, unique IDs
unless deliberately updating an existing label; do not rely on negative-ID
conversion.

## Result layout and cardinality

`knn_query` returns `(labels, distances)` as two NumPy arrays. For `q` query
rows and `k` requested neighbors, both shapes are `(q, k)`, including when the
input was a single `(dim,)` vector. The observed dtypes are integer labels
(typically `uint64`) and `float32` distances. Columns are closest first.

The binding allocates a rectangular result and raises if any query cannot
supply exactly `k` eligible items. This occurs when `k` exceeds the live index
population, when `ef`/graph settings cannot produce `k`, or when a Python
filter allows fewer than `k` candidates. A filter cannot produce padded or
partial rows. Count eligible IDs before issuing a filtered query.

## Built-in spaces

The Python binding accepts exactly these names:

| `space` | Distance returned | Meaning |
| --- | --- | --- |
| `l2` | `sum((a - b) ** 2)` | squared Euclidean distance |
| `ip` | `1 - sum(a * b)` | inner-product distance |
| `cosine` | `1 - normalized_dot(a, b)` | cosine distance |

Lower distance is closer in all three spaces. `ip` is a distance encoding, not
a similarity score and not a true metric; values can be negative and an item
need not be closest to itself under every inner-product arrangement.

For `cosine`, the extension constructs its inner-product space with a
normalization flag. On insertion it normalizes each vector; on query it
normalizes each query. `get_items` consequently returns normalized vectors.
The normalization uses an epsilon in the denominator, so an all-zero vector
is accepted but has no meaningful direction. Prefer finite, non-zero vectors
when cosine direction is important. You may provide unnormalized vectors; do
not compare their raw magnitudes with cosine distances.

A useful deterministic check for a query `q` and returned neighbor `x` is:

```python
l2 = np.sum((q - x) ** 2)
ip = 1.0 - np.sum(q * x)
cosine = 1.0 - np.dot(q / np.linalg.norm(q), x / np.linalg.norm(x))
```

Allow small float32 tolerance. For cosine, compare against normalized values.

## Search controls

`ef` is the dynamic candidate-list size during query. The documented safe
relationship is `ef >= k`; higher values generally improve recall and increase
cost. `ef_construction` controls the build-time candidate list and graph
quality. `M` controls graph links, memory, and behavior on difficult/high-
dimensional data. `num_threads=-1` uses the index's configured default,
initialized from available CPU hardware; `num_threads`/`set_num_threads` can
change that default. Small batches may be internally forced to one thread.

An HNSW result is approximate. Exact distance comparisons should use a
same-space `BFIndex` with identical data and labels. Recall is label overlap,
not equality of rank order when distances are tied.

## Storage and retrieval caveats

The index owns copied vector storage after `add_items`. `get_items` requires an
explicit list/array of labels in this binding and can return NumPy or nested
Python lists. `get_ids_list` is not guaranteed to be sorted. Deletion hides a
label from search but does not make `get_items` a general “all live rows” API;
request explicit IDs according to the lifecycle state.
