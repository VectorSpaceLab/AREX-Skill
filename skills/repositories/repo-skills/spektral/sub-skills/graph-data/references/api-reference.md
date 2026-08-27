# Graph Data API Reference

This reference summarizes the Spektral 1.3.1 graph-data surfaces verified for the generated skill.

## `Graph`

Signature: `Graph(x=None, a=None, e=None, y=None, **kwargs)`

A `Graph` stores graph matrices as attributes:

| Attribute | Meaning | Expected shape/type |
| --- | --- | --- |
| `x` | Node features | NumPy array with shape `(n_nodes, n_node_features)`; 1D input is reshaped to `(n_nodes, 1)` with a warning |
| `a` | Adjacency matrix | NumPy dense array or SciPy sparse matrix with shape `(n_nodes, n_nodes)` |
| `e` | Edge features | NumPy array with shape `(n_edges, n_edge_features)` or dense `(n_nodes, n_nodes, n_edge_features)` |
| `y` | Node or graph labels | Scalar, `(n_labels,)`, `(n_nodes,)`, or `(n_nodes, n_labels)` depending on task |

Useful properties:

- `n_nodes`
- `n_edges`
- `n_node_features`
- `n_edge_features`
- `n_labels`
- `keys`

Utility methods:

- `graph.numpy()` returns non-`None` values among `x`, `a`, `e`, `y` in that order.
- `graph.get(*keys)` returns non-`None` selected attributes.
- Additional keyword arguments become attributes and can be accessed with `graph['name']`.

## `Dataset`

Signature: `Dataset(transforms=None, **kwargs)`

Subclass `Dataset` and implement `read()` to return a list of `Graph` objects. Optionally implement `download()` if data must be materialized before `read()`.

Important methods:

- `apply(transform)`: mutate each graph by replacing it with `transform(graph)`.
- `map(transform, reduce=None)`: map over graphs, optionally reducing the result.
- `filter(function)`: keep only graphs for which `function(graph)` is true.
- `__getitem__`: supports integer, slice, list, tuple, or NumPy array indexing; slices return shallow dataset copies.

Important properties:

- `path`: defaults to `~/spektral/datasets/<ClassName>`.
- `n_graphs`, `n_nodes`, `n_node_features`, `n_edge_features`, `n_labels`.
- `signature`: TensorFlow TypeSpec/shape/dtype metadata inferred from the first graph.

For mixed mode, put the shared adjacency matrix in `dataset.a` and return graphs whose `a` attribute is absent.

## Loaders

| Loader | Signature | Requirements | Notes |
| --- | --- | --- | --- |
| `SingleLoader` | `(dataset, epochs=None, sample_weights=None)` | `len(dataset) == 1`; no batch size | Converts SciPy adjacency to `tf.SparseTensor`; supports sample weights |
| `DisjointLoader` | `(dataset, node_level=False, batch_size=1, epochs=None, shuffle=True)` | Many graphs allowed | Returns disjoint union with graph-id vector `i`; adjacency is sparse tensor |
| `BatchLoader` | `(dataset, mask=False, batch_size=1, epochs=None, shuffle=True, node_level=False)` | Many graphs allowed | Zero-pads to dense arrays; `mask=True` appends a binary mask feature to `x` |
| `PackedBatchLoader` | `(dataset, mask=False, batch_size=1, epochs=None, shuffle=True, node_level=False)` | Enough memory to pre-pack | Precomputes padded tensors once, then batches them |
| `MixedLoader` | `(dataset, batch_size=1, epochs=None, shuffle=True)` | `dataset.a` must exist; per-graph `a` must not | Shared adjacency, batched node/edge signals |

Every loader is iterable. For Keras `fit`, use `loader.load()` and pass `steps_per_epoch=loader.steps_per_epoch` when needed.

## Data utilities

- `to_disjoint(x_list=None, a_list=None, e_list=None)`: stack graphs into disjoint mode and compute graph-id vector.
- `to_batch(x_list=None, a_list=None, e_list=None, mask=False)`: zero-pad to batch mode; converts sparse adjacency to dense arrays.
- `to_mixed(x_list=None, a=None, e_list=None)`: stack signals while sharing one adjacency matrix.
- `batch_generator(data, batch_size=32, epochs=None, shuffle=True)`: batch any equally sized arrays/lists.
- `to_tf_signature(signature)`: convert a dataset signature to TensorFlow signature objects.
- `sp_matrices_to_sp_tensors(inputs)`: convert SciPy sparse matrices in an input tuple to TensorFlow sparse tensors.

## Transforms

| Transform | Signature | Effect |
| --- | --- | --- |
| `AdjToSpTensor` | `()` | Convert adjacency to TensorFlow sparse tensor |
| `ClusteringCoeff` | `()` | Add clustering coefficient as node feature |
| `Constant` | `(value)` | Concatenate a constant node feature |
| `Degree` | `(max_degree)` | Concatenate one-hot degree features using `max_degree + 1` depth |
| `Delaunay` | `()` | Build a Delaunay adjacency from coordinates; may need SciPy compatibility attention if `tri.vertices` is unavailable |
| `GCNFilter` | `(symmetric=True)` | Apply GCN normalization with self-loops |
| `LaplacianPE` | `(k)` | Add Laplacian positional encodings |
| `LayerPreprocess` | `(layer_class)` | Apply `layer_class.preprocess(graph.a)` when available |
| `NormalizeAdj` | `(symmetric=True)` | Normalize adjacency without self-loops |
| `NormalizeOne` | `()` | Normalize node features to sum to one |
| `NormalizeSphere` | `()` | Normalize coordinates to a sphere |
| `OneHotLabels` | `(depth=None, labels=None)` | One-hot encode labels by index depth or label list |

`Degree(max_degree)` expects `max_degree` to be an integer. If you compute it with `dataset.map(lambda g: g.a.sum(-1).max(), reduce=max)`, cast the result to `int` before constructing the transform.
