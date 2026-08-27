# Heterogeneous Graph API Reference

This reference summarizes the PyG 2.9.0 heterogeneous graph APIs most often needed by coding agents. It is self-contained and uses only public `torch_geometric` imports.

## Core Imports

```python
import torch
from torch import Tensor
from torch_geometric.data import HeteroData
from torch_geometric.loader import NeighborLoader, LinkNeighborLoader
from torch_geometric.nn import GATConv, GCNConv, HeteroConv, SAGEConv, to_hetero
from torch_geometric.transforms import RandomLinkSplit, ToUndirected
```

Important API signatures in the inspected installation:

- `HeteroData(_mapping=None, **kwargs)`
- `NeighborLoader(data, num_neighbors, input_nodes=None, input_time=None, replace=False, subgraph_type='directional', disjoint=False, temporal_strategy='uniform', time_attr=None, weight_attr=None, transform=None, transform_sampler_output=None, is_sorted=False, filter_per_worker=None, neighbor_sampler=None, directed=True, **kwargs)`
- `LinkNeighborLoader(data, num_neighbors, edge_label_index=None, edge_label=None, edge_label_time=None, replace=False, subgraph_type='directional', disjoint=False, temporal_strategy='uniform', neg_sampling=None, neg_sampling_ratio=None, time_attr=None, weight_attr=None, transform=None, transform_sampler_output=None, is_sorted=False, filter_per_worker=None, neighbor_sampler=None, directed=True, **kwargs)`
- `HeteroConv(convs, aggr='sum')`
- `SAGEConv(in_channels, out_channels, aggr='mean', normalize=False, root_weight=True, project=False, bias=True, **kwargs)` supports bipartite `in_channels=(-1, -1)`.
- `GATConv(in_channels, out_channels, heads=1, concat=True, ..., add_self_loops=True, edge_dim=None, ...)` supports bipartite `in_channels=(-1, -1)`, but disable self-loops for bipartite relations.
- `GCNConv(in_channels, out_channels, ..., add_self_loops=None, normalize=True, ...)` expects a single feature dimensionality and is usually not the first choice for bipartite hetero relations.
- `to_hetero(module, metadata, aggr='sum', input_map=None, debug=False)` returns a `torch.fx.GraphModule`.
- `RandomLinkSplit(..., edge_types=None, rev_edge_types=None)` can keep forward and reverse labels aligned.

## `HeteroData` Shape Contract

`HeteroData` stores graph attributes by node type and edge type:

```python
data = HeteroData()
data['paper'].x = torch.randn(4, 16)
data['author'].x = torch.randn(3, 8)
data['author', 'writes', 'paper'].edge_index = torch.tensor([
    [0, 1, 2, 0],  # source author indices
    [0, 1, 2, 3],  # target paper indices
])
data['paper', 'cites', 'paper'].edge_index = torch.tensor([
    [0, 1, 2],
    [1, 2, 3],
])
```

Node type keys are strings such as `'paper'`. Edge type keys are exactly 3-tuples `(src_type, relation, dst_type)`, such as `('author', 'writes', 'paper')`.

For every edge store:

- `edge_index` must be a `torch.long` tensor with shape `[2, num_edges]`.
- Row 0 indexes the source node store; row 1 indexes the target node store.
- Source indices must be `< data[src_type].num_nodes`; target indices must be `< data[dst_type].num_nodes`.
- Set node features (`x`) or explicit `num_nodes` for node stores that have no features.

## Metadata

Use `data.metadata()` as the canonical representation of heterogeneous structure:

```python
node_types, edge_types = data.metadata()
# node_types: ['paper', 'author']
# edge_types: [('author', 'writes', 'paper'), ('paper', 'cites', 'paper')]
```

The metadata tuple is accepted by `to_hetero`, `HeteroConv` planning, and many hetero utilities. Keep metadata synchronized with the actual data object. If a relation is added after creating a converted model, recreate the converted model or update the model explicitly.

## Stores and Attributes

Common node-store attributes:

- `x`: node features, shape `[num_nodes, num_features]`.
- `y`: labels, often for one target node type such as `data['paper'].y`.
- `train_mask`, `val_mask`, `test_mask`: boolean masks for node-level splits.
- `num_nodes`: explicit node count when no `x` is present.

Common edge-store attributes:

- `edge_index`: connectivity, shape `[2, num_edges]`.
- `edge_attr`: edge features, shape `[num_edges, num_edge_features]`.
- `edge_label`: labels for link prediction after transforms or sampling.
- `edge_label_index`: candidate links for link prediction, either stored by transforms or passed to loaders.

## Typed Loaders

Use hetero `NeighborLoader` for node tasks:

```python
loader = NeighborLoader(
    data,
    num_neighbors={edge_type: [10, 5] for edge_type in data.edge_types},
    input_nodes=('paper', data['paper'].train_mask),
    batch_size=128,
    shuffle=True,
)

batch = next(iter(loader))
assert isinstance(batch, HeteroData)
out = model(batch.x_dict, batch.edge_index_dict)
```

Use hetero `LinkNeighborLoader` for link tasks:

```python
edge_type = ('author', 'writes', 'paper')
loader = LinkNeighborLoader(
    data,
    num_neighbors={edge_type: [10, 5] for edge_type in data.edge_types},
    edge_label_index=(edge_type, data[edge_type].edge_label_index),
    edge_label=data[edge_type].edge_label,
    batch_size=128,
    shuffle=True,
)
```

Neighbor sampling may require optional PyG sampling backends in some installations. If a loader raises an import error for a sampling backend, switch to tiny full-batch examples for smoke tests or install the matching optional package set for the current PyTorch build.

## Model API Choices

### `to_hetero`

Use `to_hetero` when the same homogeneous message-passing architecture should be replicated per edge type:

```python
class SAGE(torch.nn.Module):
    def __init__(self, hidden_channels, out_channels):
        super().__init__()
        self.conv1 = SAGEConv((-1, -1), hidden_channels)
        self.conv2 = SAGEConv((-1, -1), out_channels)

    def forward(self, x, edge_index):
        x = self.conv1(x, edge_index).relu()
        return self.conv2(x, edge_index)

model = SAGE(32, 16)
model = to_hetero(model, data.metadata(), aggr='sum')
out_dict = model(data.x_dict, data.edge_index_dict)
```

Pass dictionaries to the converted model: `x_dict` maps node type to feature tensor, and `edge_index_dict` maps edge type triplet to `edge_index`.

### `HeteroConv`

Use `HeteroConv` when different relations need different operators or parameters:

```python
conv = HeteroConv({
    ('paper', 'cites', 'paper'): GCNConv(-1, 32),
    ('author', 'writes', 'paper'): SAGEConv((-1, -1), 32),
    ('paper', 'rev_writes', 'author'): SAGEConv((-1, -1), 32),
}, aggr='sum')
out_dict = conv(data.x_dict, data.edge_index_dict)
```

For bipartite edge types, prefer operators that accept source and target dimensions, such as `SAGEConv((-1, -1), out_channels)` or `GATConv((-1, -1), out_channels, add_self_loops=False)`. Avoid adding self-loops to bipartite relations because source and target node sets differ.

## Conversion Helpers

`ToUndirected()` can add reverse relations to a heterogeneous graph. Verify generated relation names before using them in link prediction because the transform names reverse relations based on relation strings and existing metadata.

For link prediction splits, explicit naming is safer:

```python
transform = RandomLinkSplit(
    edge_types=[('user', 'rates', 'movie')],
    rev_edge_types=[('movie', 'rev_rates', 'user')],
    add_negative_train_samples=True,
)
train_data, val_data, test_data = transform(data)
```

Always confirm both forward and reverse stores exist before passing `rev_edge_types`.
