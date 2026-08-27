# Node Model Reference

## Model/generator compatibility

| Model family | Verified constructor | Generator pairing | Graph requirements |
| --- | --- | --- | --- |
| `GCN` | `(layer_sizes, generator, bias=True, dropout=0.0, activations=None, ..., squeeze_output_batch=True)` | `FullBatchNodeGenerator`; also `ClusterNodeGenerator` for cluster training | Homogeneous graph for full-batch path; numeric node features. |
| `GAT` | `(layer_sizes, generator=None, attn_heads=1, attn_heads_reduction=None, ..., saliency_map_support=False, multiplicity=1, num_nodes=None, num_features=None, ...)` | `FullBatchNodeGenerator` | Homogeneous graph; choose sparse/dense generator consistently. |
| `GraphSAGE` | `(layer_sizes, generator=None, aggregator=None, bias=True, dropout=0.0, normalize='l2', activations=None, ..., n_samples=None, input_dim=None, multiplicity=None)` | `GraphSAGENodeGenerator` | Homogeneous graph with node features; sample list length matches layers. |
| `DirectedGraphSAGE` | same constructor pattern as `GraphSAGE` | `DirectedGraphSAGENodeGenerator` | Directed graph and separate incoming/outgoing neighborhood samples. |
| `HinSAGE` | `(layer_sizes, generator=None, aggregator=None, bias=True, dropout=0.0, normalize='l2', activations=None, ..., n_samples=None, input_neighbor_tree=None, input_dim=None, multiplicity=None)` | `HinSAGENodeGenerator` | Heterogeneous graph; target/head node type must be clear. |
| `RGCN` | `(layer_sizes, generator, bias=True, num_bases=0, dropout=0.0, activations=None, ...)` | `RelationalFullBatchNodeGenerator` | Relational graph with edge types; full-batch node targets. |
| `PPNP` | `(layer_sizes, generator, activations, bias=True, dropout=0.0, kernel_regularizer=None)` | `FullBatchNodeGenerator` | Homogeneous graph with propagation preprocessing. |
| `APPNP` | `(layer_sizes, generator, activations, bias=True, dropout=0.0, teleport_probability=0.1, kernel_regularizer=None, approx_iter=10)` | `FullBatchNodeGenerator` | Homogeneous graph; approximate propagation. |
| Cluster-GCN path | `ClusterGCN` is deprecated; use `GCN` with `ClusterNodeGenerator` | `ClusterNodeGenerator` | Homogeneous graph partitioned into clusters. |

## Keras tensor conventions

Most StellarGraph model classes create embedding tensors; users then attach a
Keras output layer for the prediction task.

```python
x_inp, x_out = model_stack.in_out_tensors()
```

- For multi-class classification, use a Dense head with `activation="softmax"`
  and one-hot labels with categorical cross-entropy.
- For binary classification, use `activation="sigmoid"` with binary labels and
  binary cross-entropy.
- For regression, use `activation="linear"` and a regression loss.

The exact `x_inp` list depends on the generator and sparse/dense choice. Always
build the model from the same generator instance that will create the training
sequence.

## Aggregator and architecture notes

GraphSAGE supports aggregators such as mean, max-pooling, mean-pooling, and
attentional aggregation. If a task does not need a custom aggregator, let the
model default drive the choice.

HinSAGE extends GraphSAGE to heterogeneous graphs by using type-aware
neighborhoods. Its head node type and schema matter: use a HinSAGE generator
when node and edge types are part of the learning signal.

RGCN is the better fit when the graph is relational/knowledge-graph-like and the
edges have relation types that should each be modeled.

PPNP and APPNP separate neural prediction from graph propagation. Use them when
the task specifically calls for personalized propagation behavior.

SGC-style workflows are usually implemented through a simplified GCN/propagation
pattern rather than a separate public `SGC` class in this package version.

## Target data rules

- Keep target labels indexed by node ID so train/test splits can pass IDs to the
  generator and matching rows as targets.
- One-hot encode class labels for categorical cross-entropy examples.
- Keep feature columns numeric and labels separate from graph node features
  unless intentionally adding labels as features.
- For inductive GraphSAGE examples, be explicit about which graph contains train
  nodes and which graph or node IDs are used for inference.
