# Python workflows

These recipes keep the Python API phases explicit and small. They use only
application-owned arrays, labels, and temporary files. Validate arrays before
calling the extension, because the binding's query path does not provide the
same explicit dimension check as insertion.

## Build, query, and inspect

```python
import hnswlib
import numpy as np

vectors = np.asarray(vectors, dtype=np.float32)
assert vectors.ndim == 2 and vectors.shape[1] == dim
ids = np.asarray(ids, dtype=np.int64)
assert ids.shape == (vectors.shape[0],)

index = hnswlib.Index(space="l2", dim=dim)
index.init_index(
    max_elements=len(vectors),
    M=16,
    ef_construction=200,
    random_seed=100,
)
index.add_items(vectors, ids=ids, num_threads=1)
index.set_ef(max(k, 50))
labels, distances = index.knn_query(vectors[:2], k=k, num_threads=1)
assert labels.shape == (2, k)
assert distances.shape == (2, k)
```

For a one-vector call, `vectors[0]` is valid input and still produces arrays
of shape `(1, k)`. For a one-vector scalar-label insertion, pass
`np.int64(label)`; for matrix insertion, pass a one-dimensional integer array.
Prefer explicit labels even when generated sequential labels appear convenient.

Use `index.space`, `index.dim`, `index.M`, `index.ef_construction`,
`index.max_elements`, `index.element_count`, `index.ef`, and
`index.num_threads` to record state. `get_current_count()` is the count method,
not the number of successful calls; updates to existing labels do not increase
it. To inspect vectors, pass IDs explicitly:

```python
requested = np.asarray(sorted(index.get_ids_list()), dtype=np.int64)
returned = index.get_items(requested, return_type="numpy")
```

## Filtered search

```python
allowed = {101, 103, 107}
def accept(label):
    return int(label) in allowed

labels, distances = index.knn_query(
    queries, k=2, num_threads=1, filter=accept
)
assert all(int(label) in allowed for label in labels.ravel())
```

The callable receives external labels. It runs through a Python callback, so
filtered search is recommended with `num_threads=1`; this avoids unnecessary
GIL contention and makes callback state easier to reason about. Before asking
for `k`, count live IDs accepted by the filter. Every query row must have at
least `k` eligible candidates. If not, reduce `k`, widen the filter, or add
eligible data; do not pad or reinterpret a raised exception as valid output.

BFIndex accepts the same query/filter shape. It is useful for checking filtered
correctness, but the same eligible-cardinality rule applies.

## Tune recall against BFIndex

```python
ann = hnswlib.Index(space=space, dim=dim)
ann.init_index(max_elements=len(data), M=16, ef_construction=200)
ann.add_items(data, ids=ids, num_threads=1)
ann.set_ef(max(k, 64))

oracle = hnswlib.BFIndex(space=space, dim=dim)
oracle.init_index(max_elements=len(data))
oracle.add_items(data, ids=ids)

ann_labels, _ = ann.knn_query(queries, k=k, num_threads=1)
bf_labels, _ = oracle.knn_query(queries, k=k, num_threads=1)
recall = sum(
    len(set(map(int, got)).intersection(map(int, truth)))
    for got, truth in zip(ann_labels, bf_labels)
) / (len(queries) * k)
```

Keep data, labels, space, dimension, and `k` identical. Raise `ef` first when
recall is below the application target; then consider `M` and
`ef_construction`. A tiny self-query is a binding smoke check, not evidence of
large-dataset recall or latency.

## Update and delete

A repeated ID updates in place:

```python
index.add_items(np.asarray([[9, 9]], dtype=np.float32),
                ids=np.asarray([101], dtype=np.int64))
assert np.allclose(index.get_items(np.asarray([101])), [[9, 9]])
```

For ordinary deletion, mark and query only live IDs:

```python
index.mark_deleted(101)
# index.knn_query(..., filter=lambda label: label != 101)
index.unmark_deleted(101)
```

Marking twice and unmarking a live/nonexistent ID are precondition failures.
Deletion hides an item but does not reduce capacity or necessarily decrease the
internal element count. Coordinate a deletion lifecycle externally if multiple
workers can mutate labels.

For slot reuse, make the policy part of construction:

```python
index.init_index(max_elements=capacity, allow_replace_deleted=True)
index.add_items(initial, ids=initial_ids)
index.mark_deleted(old_id)
index.add_items(new_vector, ids=np.asarray([new_id]), replace_deleted=True)
```

The replacement flag must be enabled at load too. If a saved deleted index is
loaded with the default `allow_replace_deleted=False`, a subsequent replacement
must be rejected; reload it with `True` when slot reuse is intended. A deleted
slot must exist, and the new label should not collide with a live label.

## Resize and file persistence

Resize only in a quiescent phase:

```python
index.resize_index(new_capacity)
assert index.max_elements == new_capacity
index.add_items(more_data, ids=more_ids)
```

Do not resize below `element_count`, and do not resize concurrently with
`add_items` or `knn_query`. For file persistence, prefer a temporary file and
fresh wrapper:

```python
index.save_index(path)
loaded = hnswlib.Index(space=space, dim=dim)
loaded.load_index(path, max_elements=larger_capacity)
loaded.set_ef(index.ef)  # file load resets ef to 10
```

`load_index` may be called on a wrapper with an existing native index, but a
fresh wrapper makes ownership and state transitions obvious. Use the same
space/dimension and handle missing, unreadable, incompatible, or truncated
files as deployment errors. The index file is a native binary artifact, not a
portable text format.

## Pickle round trip

```python
import pickle

snapshot = pickle.dumps(index)
copy = pickle.loads(snapshot)
copy.set_num_threads(1)
labels_copy, distances_copy = copy.knn_query(queries, k=k, num_threads=1)
```

Check explicit vectors and labels after the round trip. Pickle retains the
binding's `ef`, unlike `save_index`/`load_index`, and can retain deletion and
replacement state. Never take the pickle snapshot while another thread calls
`add_items`; make the snapshot after the mutation phase or protect it with an
application lock. Do not assume a pickle created by another hnswlib build or
version is a long-term interchange format.

## Concurrency phases

The documented safe combinations are concurrent `add_items` calls with other
`add_items` calls, and concurrent `knn_query` calls with other `knn_query`
calls. Do not overlap `add_items` with `knn_query`. Do not overlap
`resize_index` with adding or querying. Treat save/load, pickle, and internal
index-state extraction as exclusive with insertion; also serialize deletion,
replacement, and external label bookkeeping. Python callbacks in filters need
single-threaded search unless the application has deliberately measured and
synchronized their state.
