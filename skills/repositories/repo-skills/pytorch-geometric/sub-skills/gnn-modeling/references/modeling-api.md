# Modeling API Reference

This reference summarizes the PyTorch Geometric 2.9 modeling APIs most often needed by coding agents. It is self-contained and focuses on installed public APIs rather than repository-local examples.

## Core Tensor Contracts

- Node features `x`: usually a floating tensor of shape `[num_nodes, num_node_features]`.
- Edge index `edge_index`: a `torch.long` tensor of shape `[2, num_edges]`; row `0` holds source node indices and row `1` holds target node indices for the default `source_to_target` flow.
- Edge attributes `edge_attr`: optional tensor of shape `[num_edges, edge_features]` when a layer supports edge features.
- Graph labels `y`: task-dependent; node classification often uses `[num_nodes]`, graph classification often uses `[num_graphs]`, regression may use floating tensors.
- Mini-batch vector `batch`: shape `[num_nodes]`, maps each node to its graph id and is required by global pooling when processing multiple graphs.

Validate these before model code:

```python
assert edge_index.dtype == torch.long
assert edge_index.dim() == 2 and edge_index.size(0) == 2
assert x.dim() == 2 and x.size(0) > int(edge_index.max())
```

## MessagePassing

`MessagePassing(aggr='sum', *, aggr_kwargs=None, flow='source_to_target', node_dim=-2, decomposed_layers=1)` is the base class for custom GNN operators.

Minimal custom layer pattern:

```python
import torch
from torch_geometric.nn import MessagePassing

class MeanNeighborConv(MessagePassing):
    def __init__(self, in_channels, out_channels):
        super().__init__(aggr='mean')
        self.lin = torch.nn.Linear(in_channels, out_channels)

    def forward(self, x, edge_index):
        x = self.lin(x)
        return self.propagate(edge_index, x=x)

    def message(self, x_j):
        return x_j
```

Important conventions:

- `propagate(edge_index, x=x, ...)` starts message passing.
- Arguments ending in `_j` refer to source-node values gathered per edge; `_i` refers to target-node values.
- `message(...)` returns per-edge messages, usually shape `[num_edges, channels]`.
- `aggregate(...)` is usually handled by the configured aggregation (`'sum'`, `'mean'`, `'max'`, or custom aggregations).
- `update(aggr_out, ...)` can apply final transforms after aggregation.
- For bipartite graphs, pass tuple inputs such as `x=(x_src, x_dst)` and, when needed, `size=(num_src, num_dst)`.
- `decomposed_layers` can reduce memory for some message passing workloads, but it may not apply to attention-style operators whose messages couple features across channels.

## Common Convolution Layers

Installed PyG 2.9 signatures include:

- `GCNConv(in_channels, out_channels, improved=False, cached=False, add_self_loops=None, normalize=True, bias=True, **kwargs)`.
- `GATConv(in_channels, out_channels, heads=1, concat=True, negative_slope=0.2, dropout=0.0, add_self_loops=True, edge_dim=None, fill_value='mean', bias=True, residual=False, **kwargs)`.
- `SAGEConv(in_channels, out_channels, aggr='mean', normalize=False, root_weight=True, project=False, bias=True, **kwargs)`.
- `HeteroConv(convs, aggr='sum')` and `to_hetero(module, metadata, aggr='sum', input_map=None, debug=False)` exist, but detailed heterogeneous modeling belongs in the heterogeneous graph sub-skill.

Selection guide:

- Use `GCNConv` for small/medium homogeneous transductive baselines and normalized spectral-style propagation.
- Use `SAGEConv` for inductive node embeddings, neighbor-sampled training, and bipartite source/destination feature tuples.
- Use `GATConv` when attention over neighbors matters; account for `heads` and `concat` changing output channel dimensions.
- Use model wrappers such as `GCN`, `GraphSAGE`, or `GIN` when a standard multi-layer stack is enough and custom forward logic is not needed.

Layer-specific output shape reminders:

- `GCNConv(in_channels, out_channels)(x, edge_index)` returns `[num_nodes, out_channels]`.
- `SAGEConv((src_channels, dst_channels), out_channels)` can accept `(x_src, x_dst)` for bipartite message passing.
- `GATConv(..., heads=h, concat=True)` returns `[num_nodes, out_channels * h]`; with `concat=False`, it returns `[num_nodes, out_channels]`.

## Aggregation And Pooling

Use aggregation modules or string aggregations inside message passing when defining neighborhood reduction. For graph-level outputs, pool node embeddings after the final node encoder:

```python
from torch_geometric.nn import global_mean_pool

node_emb = encoder(x, edge_index)
graph_emb = global_mean_pool(node_emb, batch)
out = classifier(graph_emb)
```

Common graph-level pooling choices:

- `global_mean_pool(x, batch)` for average graph representations.
- `global_add_pool(x, batch)` when graph size should affect magnitude.
- `global_max_pool(x, batch)` for strongest-feature summaries.

For `torch.compile(fullgraph=True)`, pass explicit size information to pooling functions when supported or avoid patterns that force device synchronization.

## Model Utilities

Useful neural network utilities include:

- `torch_geometric.nn.Sequential` for wiring modules whose `forward` signatures include graph tensors such as `x`, `edge_index`, and `batch`.
- Higher-level basic models under `torch_geometric.nn.models`, such as `GCN`, `GraphSAGE`, and `GIN`, for common stacks.
- `torch_geometric.profile` utilities for profiling and memory/runtime inspection when the installed optional dependencies support the workload.

Example `Sequential` pattern:

```python
from torch_geometric.nn import GCNConv, Sequential

model = Sequential('x, edge_index', [
    (GCNConv(16, 32), 'x, edge_index -> x'),
    torch.nn.ReLU(inplace=True),
    (GCNConv(32, 4), 'x, edge_index -> x'),
])
```

## Metrics

Use `torch_geometric.metrics` for graph ML metrics when the metric matches the task. Link prediction metrics commonly operate on predicted edge scores/ranks and ground-truth labels or ranking structures. Always check metric input semantics before wiring into a training loop; many link prediction metrics distinguish positive-vs-negative score tensors or require top-k settings.

For simple node classification smoke tests, standard PyTorch metrics are enough:

```python
pred = logits.argmax(dim=-1)
accuracy = (pred[mask] == y[mask]).float().mean()
```

## Shape-First Development Checklist

1. Create a tiny `Data` object with 4 to 8 nodes and known labels.
2. Assert `x`, `edge_index`, and mask dtypes/shapes before constructing the model.
3. Run one eager forward pass and assert output shape.
4. Run one backward pass and assert every trainable parameter that should receive gradients has a finite gradient.
5. Only then add loaders, sampling, metrics, compile, or larger datasets.
