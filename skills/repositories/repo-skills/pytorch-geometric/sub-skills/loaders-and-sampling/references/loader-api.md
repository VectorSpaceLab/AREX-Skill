# Loader API and Mini-Batching

PyTorch Geometric batches graph examples by concatenating node and feature tensors and by shifting edge indices so separate graphs remain disconnected inside one `Batch` object. Use `torch_geometric.loader.DataLoader`, not `torch.utils.data.DataLoader`, when the dataset yields PyG `Data` or `HeteroData` objects.

## Core APIs

```python
from torch_geometric.data import Data, HeteroData
from torch_geometric.loader import DataLoader

loader = DataLoader(dataset, batch_size=32, shuffle=True)
batch = next(iter(loader))
```

Important constructor arguments:

- `dataset`: a PyG `Dataset`, ordinary sequence of `Data`/`HeteroData`, or supported adapter.
- `batch_size`: number of graph examples per mini-batch, not number of nodes.
- `shuffle`: reshuffles graph examples between epochs.
- `follow_batch`: list of attribute names for which extra assignment vectors are created, such as `x_s_batch` and `x_t_batch`.
- `exclude_keys`: list of attributes to omit from the batch, useful for large metadata or fields not needed by the model.
- Additional keyword arguments are passed to the underlying PyTorch DataLoader, including `num_workers`, `pin_memory`, and `drop_last`.

## Expected batch outputs

For homogeneous `Data` examples, a batch typically has:

- `batch.x`: concatenated node features.
- `batch.edge_index`: concatenated and offset edge indices.
- `batch.batch`: vector mapping each node to its graph example id.
- `batch.ptr`: cumulative node offsets; `ptr[i]` to `ptr[i + 1]` identifies graph `i` in node tensors.
- `batch.num_graphs`: number of graph examples in the batch.

Tiny validation pattern:

```python
import torch
from torch_geometric.data import Data
from torch_geometric.loader import DataLoader

graph = Data(
    x=torch.ones(3, 1),
    edge_index=torch.tensor([[0, 1, 1, 2], [1, 0, 2, 1]]),
)
batch = next(iter(DataLoader([graph, graph], batch_size=2)))
assert batch.num_graphs == 2
assert batch.batch.tolist() == [0, 0, 0, 1, 1, 1]
assert batch.ptr.tolist() == [0, 3, 6]
assert batch.edge_index.tolist() == [[0, 1, 1, 2, 3, 4, 4, 5], [1, 0, 2, 1, 4, 3, 5, 4]]
```

## `follow_batch` and custom graph fields

Use `follow_batch` when one graph example contains multiple node-feature tensors and downstream pooling needs a graph assignment vector for each tensor.

```python
loader = DataLoader(data_list, batch_size=2, follow_batch=["x_s", "x_t"])
batch = next(iter(loader))
assert hasattr(batch, "x_s_batch")
assert hasattr(batch, "x_t_batch")
```

Use `exclude_keys` when an attribute is expensive or invalid to collate:

```python
loader = DataLoader(data_list, batch_size=8, exclude_keys=["raw_text", "debug_payload"])
```

## Custom increment and concat rules

By default, PyG increments attributes whose key contains `index` by `num_nodes`, concatenates index tensors along dimension `1`, and concatenates most other tensors along dimension `0`. For custom layouts, override `Data.__inc__` and `Data.__cat_dim__`, then verify the resulting batch before training.

Pair-of-graphs example:

```python
from torch_geometric.data import Data

class PairData(Data):
    def __inc__(self, key, value, *args, **kwargs):
        if key == "edge_index_s":
            return self.x_s.size(0)
        if key == "edge_index_t":
            return self.x_t.size(0)
        return super().__inc__(key, value, *args, **kwargs)
```

Bipartite edge-index example:

```python
import torch
from torch_geometric.data import Data

class BipartiteData(Data):
    def __inc__(self, key, value, *args, **kwargs):
        if key == "edge_index":
            return torch.tensor([[self.x_s.size(0)], [self.x_t.size(0)]])
        return super().__inc__(key, value, *args, **kwargs)
```

Stack graph-level vectors along a new batch dimension:

```python
from torch_geometric.data import Data

class GraphVectorData(Data):
    def __cat_dim__(self, key, value, *args, **kwargs):
        if key == "graph_descriptor":
            return None
        return super().__cat_dim__(key, value, *args, **kwargs)
```

## Heterogeneous batches

`DataLoader` also batches `HeteroData`. Inspect per-type stores instead of assuming a top-level `x`:

```python
batch = next(iter(DataLoader([hetero_data, hetero_data], batch_size=2)))
print(batch.node_types)
print(batch.edge_types)
print(batch["paper"].x.shape)
print(batch["paper", "cites", "paper"].edge_index.shape)
```

For workflows that need heterogeneous neighbor sampling rather than batching independent heterogeneous examples, use `references/sampling-workflows.md`.

## Validation checklist

- Confirm `batch.num_graphs` equals the graph-level batch size.
- Confirm `batch.batch.numel()` equals the total number of batched nodes.
- Confirm `batch.edge_index.max() < batch.num_nodes`.
- Confirm `follow_batch` creates the expected `*_batch` vectors.
- Confirm attributes containing the substring `index` are intentionally incremented; rename or override `__inc__` if not.
- Confirm `exclude_keys` did not remove a tensor required by the model or loss.
