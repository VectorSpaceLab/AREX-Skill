# Python API reference

This reference describes the observed hnswlib 0.9.0 Python extension. The
extension exposes `Index` for approximate HNSW search and `BFIndex` for exact
linear search. Both are CPU-native and support `l2`, `ip`, and `cosine`.

## `Index` construction and state

```python
p = hnswlib.Index(space="l2", dim=dim)
p.init_index(
    max_elements,
    M=16,
    ef_construction=200,
    random_seed=100,
    allow_replace_deleted=False,
)
```

The constructor validates `space` as one of `"l2"`, `"ip"`, or `"cosine"` and
stores the integer `dim`. It creates an uninitialized index; `add_items` and
`knn_query` require a successful `init_index` or `load_index`. The construction
parameters have these roles:

- `max_elements` is the current capacity. It can be increased with
  `resize_index` or by loading a saved index with a larger `max_elements`.
- `M` controls graph connectivity and memory. The public guidance commonly
  starts around 12--48; the default is 16.
- `ef_construction` controls build-time accuracy versus build cost. The default
  is 200.
- `random_seed` controls graph-level random initialization. The default is 100.
- `allow_replace_deleted` must be true if later additions will reuse deleted
  slots through `replace_deleted=True`.

Before initialization, `max_elements` and `element_count` properties are zero;
`ef` reports the default query setting (10). After initialization, the useful
read-only properties are `space`, `dim`, `M`, `ef_construction`,
`max_elements`, and `element_count`. The method equivalents are
`get_max_elements()` and `get_current_count()`. `ef` and `num_threads` are
read/write properties. `set_ef(value)` and `set_num_threads(value)` are
property-equivalent setters.

## Add and update

```python
p.add_items(data, ids=None, num_threads=-1, replace_deleted=False)
```

`data` is one vector `(dim,)` or a matrix `(rows, dim)`. With one row, a scalar
integer label is accepted; with multiple rows, pass a one-dimensional label
array with one entry per row. If `ids` is omitted, labels are generated from
the binding's internal counter and should not be used as an external metadata
contract. The native label type is an unsigned-size integer, so use stable,
non-negative integer labels.

The binding force-casts input to contiguous `float32`. For reliable behavior,
convert explicitly, keep the trailing dimension equal to `dim`, and pass
finite values. Existing labels update their vectors rather than creating a
second item. New labels consume capacity. `num_threads=-1` means the configured
default; small batches may internally be reduced to one thread.

`replace_deleted=True` is not an ordinary update flag. It is valid only when
the index was initialized or loaded with `allow_replace_deleted=True`, and a
marked deleted slot must be available. The new label/data replaces the deleted
slot while preserving the configured capacity.

## Query

```python
labels, distances = p.knn_query(
    data, k=1, num_threads=-1, filter=None
)
```

The input may be `(dim,)` or `(rows, dim)` and the return is always a pair of
2-D NumPy arrays shaped `(rows, k)`. Labels are integer external IDs and
observed distances are `float32`. The rows correspond to input query rows and
columns are ordered closest first (lowest distance first for each built-in
space). Set `ef >= k`; larger `ef` usually improves recall and costs more
query work. If fewer than `k` live candidates exist, or a filter leaves fewer
than `k` candidates for a query, the binding raises rather than returning a
short row. A Python `filter` is called with each external label and should
return a truthy value for allowed IDs.

The C++ binding's query path accepts 1-D/2-D buffers but does not explicitly
repeat the insertion dimensionality check. Treat a query with a trailing
length other than `dim` as unsupported and validate it in application code
before calling `knn_query`.

## Data and metadata access

```python
vectors = p.get_items(ids, return_type="numpy")
rows = p.get_items(ids, return_type="list")
ids = p.get_ids_list()
```

Pass an explicit one-dimensional collection of labels to `get_items`; a scalar
label is rejected by the observed binding. `return_type` must be `"numpy"` or
`"list"`. The NumPy result is normally `(len(ids), dim)` and the list result is
a list of lists. In the observed extension, `ids=None` is an empty ID list, so
it returns an empty array/list rather than enumerating every label. To retrieve
all items, call `get_ids_list()` and pass the resulting IDs. The ID list comes
from an unordered map; sort it before order-sensitive comparisons. In the
observed implementation, marking a label deleted does not remove its entry
from this label map; use query results (or explicit lifecycle bookkeeping) to
identify labels currently eligible for search. Replacement removes the old
label from the active label map.

For `cosine`, `add_items` normalizes vectors before storage and query vectors
are normalized for search. Therefore `get_items` returns normalized vectors,
not necessarily the original row values. `Index` also exposes `index_file_size()`
for an initialized index.

## Deletion, resize, and persistence

```python
p.mark_deleted(label)
p.unmark_deleted(label)
p.resize_index(new_size)
p.save_index(path)
q = hnswlib.Index(space="l2", dim=dim)
q.load_index(path, max_elements=0, allow_replace_deleted=False)
```

`mark_deleted` excludes an existing live label from search. It raises if the
label is absent or already marked. `unmark_deleted` restores a marked label
and raises when the precondition is not met. Deletion does not reduce the
configured capacity. `resize_index` is structural and must not be concurrent
with adding or querying; do not shrink below the current element count.

`save_index` writes a native binary index. Load into an uninitialized or fresh
compatible `Index`; `max_elements=0` uses the saved capacity, while a larger
value provides growth room. `allow_replace_deleted` on load must be true for a
post-load replacement workflow. `ef` is not stored in the index file and is
reset to 10 on load, so set it again. The saved metric/dimension and the new
wrapper's intended metric/dimension must agree.

## Pickle

`Index` implements Python pickle. A round trip preserves the graph, vectors,
labels, construction metadata, deletion state, thread default, and query `ef`
through the binding's state dictionary. Pickle is useful for a Python-only
snapshot, but it is not a substitute for a deliberately managed index-file
format or cross-version compatibility policy. Do not call `pickle.dumps`,
`__getstate__`, or related index-state creation concurrently with `add_items`.

## `BFIndex`

```python
bf = hnswlib.BFIndex(space="l2", dim=dim)
bf.init_index(max_elements)
bf.add_items(data, ids=None)
labels, distances = bf.knn_query(data, k=1, num_threads=-1, filter=None)
bf.delete_vector(label)
bf.save_index(path)
bf.load_index(path, max_elements=0)
```

BFIndex has no `M`, `ef`, deletion-mark/unmark, or replacement controls. It
stores vectors and performs an exact linear scan in the selected space. It
exposes `get_max_elements()`, `get_current_count()`, `num_threads`, and
`set_num_threads`. Its filter has the same external-label callback contract,
and `k` must be available among the stored/eligible vectors. Build one BFIndex
with the same data, IDs, space, and dimension as an HNSW index when measuring
label-overlap recall.
