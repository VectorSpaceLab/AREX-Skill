# Graph Data Troubleshooting

## `Graph` rejects input shapes

**Symptoms**
- `Unsupported type ... for x`
- `x must have shape (n_nodes, n_node_features)`
- `a must have shape (n_nodes, n_nodes)`
- `e must have shape (n_edges, n_edge_features) or (n_nodes, n_nodes, n_edge_features)`

**Fix**
- Convert node features to a NumPy array.
- Use rank-2 node features; a rank-1 `x` is reshaped to `(n_nodes, 1)` with a warning.
- Use a rank-2 dense NumPy or SciPy sparse adjacency.
- Store sparse edge attributes as `(n_edges, n_edge_features)` in row-major adjacency order, or dense edge attributes as `(n_nodes, n_nodes, n_edge_features)`.

## `SingleLoader` rejects a dataset

`SingleLoader` can only be used when `len(dataset) == 1`. For many graphs, choose `DisjointLoader`, `BatchLoader`, or `PackedBatchLoader`.

## Disjoint labels have the wrong shape

If labels are graph-level, leave `node_level=False` and labels are stacked as `(batch, n_labels)`. If labels are node-level, pass `node_level=True` and make each graph label length match its node count.

## Batch mode hides real node counts

`BatchLoader` zero-pads every graph in a batch. If downstream layers need to ignore padded nodes, construct the loader with `mask=True` and use `GraphMasking` in the model. Without this pair, padded rows can influence dense pooling or layer outputs.

## `MixedLoader` assertions fail

Mixed mode requires:

- `dataset.a` is set to the shared adjacency matrix.
- Each `Graph` returned by `read()` does not have its own adjacency.
- All graph signals have the same number of nodes and compatible edge-feature shapes.

If those conditions are not true, use `BatchLoader` or `PackedBatchLoader` instead.

## `Degree` transform raises a type error

`Degree(max_degree)` expects an integer. Some sparse sums return NumPy scalar floats. Cast before constructing the transform:

```python
max_degree = int(dataset.map(lambda g: g.a.sum(-1).max(), reduce=max))
dataset.apply(Degree(max_degree))
```

## `Delaunay` transform fails with missing `vertices`

Some SciPy versions expose Delaunay simplices as `simplices` rather than `vertices`. This Spektral 1.3.1 source revision calls `tri.vertices`, so a newer SciPy stack can raise `AttributeError: 'Delaunay' object has no attribute 'vertices'`. If a workflow needs this transform, either use a SciPy version compatible with that attribute or patch the transform intentionally to use `tri.simplices` after validating behavior.

## Dataset unexpectedly downloads data

A `Dataset` calls `download()` before `read()` if `dataset.path` does not exist. For built-in datasets, check the cache root in `~/.spektral/config.json` or use synthetic datasets for smoke tests.

## Loader output tuple surprises Keras

Always print or assert one batch before model wiring:

```python
batch = next(iter(loader))
print(type(batch), batch)
```

A loader with labels returns `(inputs, y)`; a loader without labels returns only inputs. Edge features add another input element. Disjoint mode adds graph ids `i`; batch and mixed modes do not.

## Sparse/dense mismatches

- `DisjointLoader` emits sparse adjacency tensors.
- `BatchLoader` emits dense padded adjacency arrays.
- `SingleLoader` converts SciPy sparse matrices to sparse tensors.
- `MessagePassing` layers require sparse adjacency and are not batch-mode layers.

If an error names `SparseTensor`, `TensorSpec`, or adjacency rank, re-check loader mode before changing the model.
