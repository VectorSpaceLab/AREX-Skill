# Data Formats

PyTorch Geometric graph containers are lightweight attribute stores around tensors. The most common public constructors in PyG 2.9 are:

- `torch_geometric.data.Data(x=None, edge_index=None, edge_attr=None, y=None, pos=None, time=None, **kwargs)` for homogeneous graphs.
- `torch_geometric.data.HeteroData(_mapping=None, **kwargs)` for typed node and edge stores.
- `torch_geometric.data.Batch.from_data_list(data_list)` for mini-batching multiple graph objects into one disconnected graph.

## Homogeneous `Data`

Create a graph with node features and COO edges:

```python
import torch
from torch_geometric.data import Data

x = torch.tensor([[1.0, 0.0], [0.0, 1.0], [1.0, 1.0]])
edge_index = torch.tensor([[0, 1, 2], [1, 2, 0]], dtype=torch.long)
y = torch.tensor([0, 1, 0])
data = Data(x=x, edge_index=edge_index, y=y)
data.validate(raise_on_error=True)
```

Shape checklist:

- `x`: usually `[num_nodes, num_node_features]`.
- `edge_index`: `[2, num_edges]`, `torch.long`, COO layout, zero-based source and destination ids.
- `edge_attr`: usually `[num_edges, num_edge_features]` or `[num_edges]`.
- `y`: graph, node, or edge target depending on task; document the intended semantic.
- `pos`: `[num_nodes, num_dimensions]` for geometric or point-cloud tasks.
- `time`: accepted on data objects; check whether it describes nodes or edges before batching or sampling.

`Data.validate(raise_on_error=True)` catches common structural errors, including `edge_index` not shaped `[2, num_edges]`, negative indices, and indices larger than `num_nodes - 1`. It does not replace task-specific checks such as mask presence, class balance, feature dtype, or expected target shape.

## `num_nodes` Inference

PyG can infer `num_nodes` from node-level tensors such as `x`, but graphs with only `edge_index`, isolated nodes, or removed node features are ambiguous. Set it explicitly:

```python
data = Data(edge_index=edge_index, num_nodes=3)
```

Use explicit `num_nodes` whenever:

- The graph has isolated nodes.
- `x` is absent, delayed, stored externally, or created by a later transform.
- You are validating links where `edge_index.max() + 1` is smaller than the true node count.
- You slice/subgraph data and need to preserve empty node ids.

## Attribute Classification

`Data` stores arbitrary attributes and classifies tensors by shape where possible:

```python
assert data.is_node_attr("x")
assert data.is_edge_attr("edge_attr") if "edge_attr" in data else True
```

When an attribute length can match both nodes and edges, name it explicitly and write an assertion for its intended role. Ambiguous keys such as `time` should be checked after construction and after transforms.

## Heterogeneous `HeteroData`

Use `HeteroData` for multiple node or edge types. Node stores are keyed by string node type; edge stores are keyed by canonical triples `(src_type, relation_type, dst_type)`:

```python
import torch
from torch_geometric.data import HeteroData

data = HeteroData()
data["paper"].x = torch.randn(3, 8)
data["author"].x = torch.randn(2, 4)
data[("author", "writes", "paper")].edge_index = torch.tensor(
    [[0, 1, 1], [0, 1, 2]], dtype=torch.long
)
data.validate(raise_on_error=True)
node_types, edge_types = data.metadata()
```

Hetero checklist:

- Define every node type referenced by an edge type.
- Keep edge keys canonical: `(source_node_type, relation_name, target_node_type)`.
- Validate each edge index against the source and destination node counts.
- Use `data.metadata()` when handing a hetero graph to hetero models or conversion utilities.
- Add reverse edge types when transforms, message passing, or link prediction need bidirectional information.

`HeteroData.validate()` reports dangling node types, dangling edge endpoint types, invalid edge index shapes, negative indices, and out-of-range source or destination ids.

## Batching Graph Containers

Use `Batch` for combining a list of `Data` or `HeteroData` objects. `Batch` increments index-like attributes such as `edge_index` and adds assignment vectors so graph-level operations can recover graph membership:

```python
from torch_geometric.data import Batch

batch = Batch.from_data_list([data, data.clone()])
assert batch.num_graphs == 2
assert batch.batch.size(0) == batch.num_nodes
restored = batch.to_data_list()
```

Batching rules to remember:

- `edge_index` values are shifted by cumulative node counts.
- Node-level tensors concatenate along dimension `0`.
- Edge indices concatenate along the last dimension.
- Custom attributes with names containing `index` may be incremented; if you create custom data classes, override `__inc__` and `__cat_dim__` deliberately.
- For loader choices beyond basic batching, route to `../loaders-and-sampling/SKILL.md`.

## Serialization and Interchange

Useful methods for local workflows:

- `data.to_dict()` and `Data.from_dict(mapping)` for Python dictionaries.
- `data.clone()` before applying destructive transforms.
- `data.to(device)` for moving tensors, but keep validation smoke tests CPU-only unless the user asks for GPU.
- `hetero_data.to_homogeneous()` and `data.to_heterogeneous(...)` for conversion, but verify metadata and feature compatibility after conversion.

## Minimal Validation Function

Use this pattern inside custom recipes before training or saving:

```python
def assert_basic_data(data):
    data.validate(raise_on_error=True)
    if "x" in data and data.num_nodes is not None:
        assert data.x.size(0) == data.num_nodes
    if "train_mask" in data:
        assert data.train_mask.dtype == torch.bool
        assert data.train_mask.numel() == data.num_nodes
```

For a runnable version, use `scripts/validate_basic_graph.py` from this sub-skill.
