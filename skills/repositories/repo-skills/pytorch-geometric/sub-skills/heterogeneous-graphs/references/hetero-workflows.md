# Heterogeneous Graph Workflows

Use these recipes to implement common PyG heterogeneous graph tasks without relying on source checkout files or downloads.

## 1. Build and Validate a Tiny `HeteroData`

```python
import torch
from torch_geometric.data import HeteroData

data = HeteroData()
data['user'].x = torch.randn(3, 8)
data['movie'].x = torch.randn(2, 8)
data['user', 'rates', 'movie'].edge_index = torch.tensor([[0, 1, 2], [0, 1, 1]])
data['movie', 'rev_rates', 'user'].edge_index = torch.tensor([[0, 1, 1], [0, 1, 2]])

node_types, edge_types = data.metadata()
assert set(node_types) == {'user', 'movie'}
assert ('user', 'rates', 'movie') in edge_types
```

Validation checklist:

- Every relation key is a 3-tuple `(src_type, relation, dst_type)`.
- Every source and target node type has a node store with `x` or `num_nodes`.
- Every `edge_index` is `torch.long`, has shape `[2, num_edges]`, and indexes valid source and target nodes.
- Feature dimensions are compatible with the chosen model. `to_hetero` with lazy `SAGEConv((-1, -1), ...)` tolerates different source and target feature sizes.

For a reusable local check, run:

```bash
python scripts/hetero_metadata_check.py --require-reverse
```

## 2. Convert a Homogeneous SAGE Model with `to_hetero`

Use this pattern when the same architecture should be cloned for each edge type.

```python
import torch
from torch_geometric.nn import SAGEConv, to_hetero

class TinySAGE(torch.nn.Module):
    def __init__(self, hidden_channels, out_channels):
        super().__init__()
        self.conv1 = SAGEConv((-1, -1), hidden_channels)
        self.conv2 = SAGEConv((-1, -1), out_channels)

    def forward(self, x, edge_index):
        x = self.conv1(x, edge_index).relu()
        return self.conv2(x, edge_index)

model = TinySAGE(hidden_channels=16, out_channels=4)
hetero_model = to_hetero(model, data.metadata(), aggr='sum')
out = hetero_model(data.x_dict, data.edge_index_dict)
assert set(out).issubset(set(data.node_types))
```

Notes:

- Build or load data before conversion so `data.metadata()` is final.
- Use tuple `in_channels=(-1, -1)` in bipartite-capable layers inside the original model.
- The first forward pass initializes lazy modules; keep it on the target device and with representative node/edge dictionaries.
- If a target node type has no incoming edge type, `to_hetero` may not produce an output for that type. Add a relation, add reverse edges, or handle that node type separately.

## 3. Write a Relation-Specific `HeteroConv`

Use `HeteroConv` when relation types need different operators or parameters.

```python
import torch
from torch_geometric.nn import GATConv, HeteroConv, Linear, SAGEConv

class HeteroEncoder(torch.nn.Module):
    def __init__(self, hidden_channels, out_channels):
        super().__init__()
        self.conv = HeteroConv({
            ('user', 'rates', 'movie'): SAGEConv((-1, -1), hidden_channels),
            ('movie', 'rev_rates', 'user'): SAGEConv((-1, -1), hidden_channels),
            ('movie', 'similar', 'movie'): GATConv((-1, -1), hidden_channels, add_self_loops=False),
        }, aggr='sum')
        self.lin = torch.nn.ModuleDict({
            'user': Linear(hidden_channels, out_channels),
            'movie': Linear(hidden_channels, out_channels),
        })

    def forward(self, x_dict, edge_index_dict):
        x_dict = self.conv(x_dict, edge_index_dict)
        return {node_type: self.lin[node_type](x).relu()
                for node_type, x in x_dict.items()}
```

Relation-specific checklist:

- Include one convolution per relation that should contribute messages.
- Use `SAGEConv((-1, -1), ...)` for bipartite relations.
- If using attention on bipartite relations, set `add_self_loops=False` unless source and target node types are identical.
- Confirm output dictionaries contain the node types needed by the downstream loss.

## 4. Node Classification with Hetero Neighbor Sampling

```python
from torch_geometric.loader import NeighborLoader

loader = NeighborLoader(
    data,
    num_neighbors={edge_type: [15, 10] for edge_type in data.edge_types},
    input_nodes=('paper', data['paper'].train_mask),
    batch_size=256,
    shuffle=True,
)

for batch in loader:
    out = model(batch.x_dict, batch.edge_index_dict)
    logits = out['paper'][:batch['paper'].batch_size]
    y = batch['paper'].y[:batch['paper'].batch_size]
    loss = torch.nn.functional.cross_entropy(logits, y)
    break
```

Loader notes:

- `input_nodes` can be a node type string, `(node_type, mask_or_indices)`, or `None` depending on task.
- Hetero `num_neighbors` should be a dictionary keyed by edge type when fanouts differ by relation.
- Mini-batches remain `HeteroData` objects and expose `x_dict`, `edge_index_dict`, node stores, and edge stores.
- Sampling backends are optional in some installations; keep smoke tests tiny and handle missing-backend import errors separately.

## 5. Link Prediction Split and Loader

Prepare explicit forward and reverse edge stores before splitting:

```python
from torch_geometric.transforms import RandomLinkSplit

edge_type = ('user', 'rates', 'movie')
rev_edge_type = ('movie', 'rev_rates', 'user')

assert edge_type in data.edge_types
assert rev_edge_type in data.edge_types

split = RandomLinkSplit(
    num_val=0.1,
    num_test=0.2,
    edge_types=[edge_type],
    rev_edge_types=[rev_edge_type],
    add_negative_train_samples=True,
)
train_data, val_data, test_data = split(data)
```

Then sample link neighborhoods:

```python
from torch_geometric.loader import LinkNeighborLoader

loader = LinkNeighborLoader(
    train_data,
    num_neighbors={edge_type: [10, 5] for edge_type in train_data.edge_types},
    edge_label_index=(edge_type, train_data[edge_type].edge_label_index),
    edge_label=train_data[edge_type].edge_label,
    batch_size=128,
    shuffle=True,
)

for batch in loader:
    z_dict = model(batch.x_dict, batch.edge_index_dict)
    src, dst = batch[edge_type].edge_label_index
    pred = (z_dict['user'][src] * z_dict['movie'][dst]).sum(dim=-1)
    loss = torch.nn.functional.binary_cross_entropy_with_logits(
        pred, batch[edge_type].edge_label.float())
    break
```

Link prediction checklist:

- Keep `edge_type` and `rev_edge_type` paired and explicit.
- Do not treat reverse edges as separate positive labels unless the task requires it.
- Score the node embeddings corresponding to the forward label edge type.
- Confirm `edge_label_index` row 0 indexes the forward source node type and row 1 indexes the forward destination node type.

## 6. Bipartite Edge Recipe

For relations such as `('user', 'rates', 'movie')`, source and target features can have different sizes. Use bipartite-aware layers:

```python
conv = SAGEConv((-1, -1), 32)
out_movie = conv((data['user'].x, data['movie'].x), data['user', 'rates', 'movie'].edge_index)
```

In `HeteroConv`, PyG supplies the proper `(x_src, x_dst)` pair for bipartite relations when you pass `x_dict` and `edge_index_dict`.

## 7. Safe Smoke Validation Steps

Before training or committing a workflow:

1. Print `data.metadata()` and compare it to expected node and edge types.
2. Check each edge index shape, dtype, and index range.
3. Run one forward pass with `data.x_dict` and `data.edge_index_dict`.
4. Assert the output dictionary contains the supervised node type or the link-prediction source/destination types.
5. For link prediction, assert the reverse edge type exists before using `RandomLinkSplit(rev_edge_types=...)`.
