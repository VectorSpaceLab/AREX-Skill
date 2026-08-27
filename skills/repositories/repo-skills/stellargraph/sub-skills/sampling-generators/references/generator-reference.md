# Generator Reference

## Purpose

Use this reference to select a StellarGraph Keras generator, call its `flow`
method correctly, and verify batch shapes before creating model heads.

## Generator selection table

| Task/model family | Generator | Verified constructor | Flow inputs |
| --- | --- | --- | --- |
| Full-batch homogeneous node models (`GCN`, `GAT`, `PPNP`, `APPNP`) | `FullBatchNodeGenerator` | `(G, name=None, method='gcn', k=1, sparse=True, transform=None, teleport_probability=0.1, weighted=False)` | `flow(node_ids, targets=None, use_ilocs=False)` |
| Full-batch homogeneous link models | `FullBatchLinkGenerator` | same as full-batch node generator | `flow(link_ids, targets=None, use_ilocs=False)` |
| Homogeneous GraphSAGE node tasks | `GraphSAGENodeGenerator` | `(G, batch_size, num_samples, seed=None, name=None, weighted=False)` | `flow(node_ids, targets=None, shuffle=False, seed=None)` |
| Homogeneous GraphSAGE link tasks | `GraphSAGELinkGenerator` | `(G, batch_size, num_samples, seed=None, name=None, weighted=False)` | `flow(link_ids, targets=None, shuffle=False, seed=None)` |
| Directed GraphSAGE | `DirectedGraphSAGENodeGenerator`, `DirectedGraphSAGELinkGenerator` | `(G, batch_size, in_samples, out_samples, seed=None, name=None, weighted=False)` | node or link `flow(...)` |
| Heterogeneous HinSAGE | `HinSAGENodeGenerator`, `HinSAGELinkGenerator` | `(G, batch_size, num_samples, head_node_type=None, schema=None, seed=None, name=None)` or link variant with `head_node_types` | node/link `flow(...)` |
| Attri2Vec | `Attri2VecNodeGenerator`, `Attri2VecLinkGenerator` | `(G, batch_size, name=None)` | node or link sequences |
| Node2Vec Keras layer | `Node2VecNodeGenerator`, `Node2VecLinkGenerator` | `(G, batch_size, name=None)` | node or link sequences |
| Cluster-GCN | `ClusterNodeGenerator` | `(G, clusters=1, q=1, lam=0.1, weighted=False, name=None)` | `flow(node_ids, targets=None, name=None)` |
| RGCN | `RelationalFullBatchNodeGenerator` | `(G, name=None, sparse=True, transform=None, weighted=False)` | `flow(node_ids, targets=None, use_ilocs=False)` |
| Knowledge graph completion | `KGTripleGenerator` | `(G, batch_size)` | `flow(edges, negative_samples=None, sample_strategy='uniform', shuffle=False, seed=None)` |
| Graph classification | `PaddedGraphGenerator` | `(graphs, name=None)` | `flow(graphs, targets=None, symmetric_normalization=True, weighted=False, batch_size=1, name=None, shuffle=False, seed=None)` |
| Graph time series | `SlidingFeaturesNodeGenerator` | `(G, window_size, batch_size=1)` | `flow(sequence_iloc_slice, target_distance=None)` |

## Full-batch generators

Full-batch generators materialize features and adjacency for the whole graph.
They are the usual pairing for `GCN`, `GAT`, `PPNP`, and `APPNP` on homogeneous
or relational graphs.

Key choices:

- `sparse=True` is usually better for real sparse graphs; output contains sparse
  index/value placeholders.
- `sparse=False` is easier for small shape debugging and smoke tests.
- `method` controls adjacency preprocessing. Common values include `"gcn"`,
  `"self_loops"`, `"ppnp"`, `"none"`, and similar transforms implemented by
  the generator.
- `weighted=True` uses edge weights when the graph and model path support them.

Typical node flow:

```python
generator = FullBatchNodeGenerator(graph, method="gcn", sparse=True)
train_gen = generator.flow(train_node_ids, train_targets)
```

For link prediction, `link_ids` are pairs of node IDs:

```python
generator = FullBatchLinkGenerator(graph, method="gcn")
link_gen = generator.flow([("a", "b"), ("b", "c")], targets=[1, 0])
```

## Sampled node/link generators

GraphSAGE, DirectedGraphSAGE, HinSAGE, Attri2Vec, and Node2Vec generators sample
neighborhoods or node pairs in mini-batches. Their output is Keras-compatible and
is consumed by the corresponding model's `in_out_tensors()` or `default_model()`.

Rules:

- `batch_size` is the number of head nodes or links per batch.
- `num_samples` normally has one entry per neighborhood-sampling layer.
- Directed GraphSAGE uses separate `in_samples` and `out_samples` lists.
- HinSAGE requires node/edge type schema consistency; pass `head_node_type` or
  `head_node_types` when inference from data is ambiguous.
- `flow_from_dataframe` expects a DataFrame indexed by node IDs or with source/
  target columns depending on generator class; inspect the sub-skill for the
  owning task before using it.

## Specialized generators

- `ClusterNodeGenerator` partitions a homogeneous graph into clusters for
  scalable GCN/GAT/APPNP-style training. Use it instead of the deprecated
  `ClusterGCN` model wrapper when following current code paths.
- `RelationalFullBatchNodeGenerator` feeds `RGCN` and expects relational edge
  types.
- `KGTripleGenerator` feeds knowledge graph scoring models; its `edges` argument
  is a sequence of triples/edge records compatible with the graph's edge type
  representation.
- `PaddedGraphGenerator` takes a list of `StellarGraph` objects and pads variable
  graph sizes into batches for graph classification.
- `SlidingFeaturesNodeGenerator` creates windows over sequence-valued node
  features for `GCN_LSTM` workflows.

## Batch inspection pattern

Before compiling or fitting a model, inspect one batch:

```python
sequence = generator.flow(ids, targets)
inputs, y = sequence[0]
print(type(inputs), y.shape if y is not None else None)
for i, array in enumerate(inputs if isinstance(inputs, list) else [inputs]):
    print(i, getattr(array, "shape", None))
```

If this fails, fix graph IDs, target shapes, or generator selection before adding
Keras layers.
