# Sampling Workflows

Use PyG sampling loaders when the graph is too large for full-batch training or when link supervision should be processed in edge mini-batches. Sampling loaders return relabeled subgraphs plus metadata that maps sampled nodes and edges back to the original graph.

## NeighborLoader for node mini-batches

```python
import torch
from torch_geometric.data import Data
from torch_geometric.loader import NeighborLoader

x = torch.randn(8, 32)
y = torch.randint(0, 4, (8,))
edge_index = torch.tensor([
    [2, 3, 3, 4, 5, 6, 7],
    [0, 0, 1, 1, 2, 3, 4],
])
data = Data(x=x, y=y, edge_index=edge_index)

loader = NeighborLoader(
    data,
    input_nodes=torch.tensor([0, 1]),
    num_neighbors=[2, 1],
    batch_size=1,
    replace=False,
    shuffle=False,
)
```

Key parameters:

- `data`: `Data`, `HeteroData`, or a feature-store/graph-store pair.
- `num_neighbors`: list of neighbors per hop, such as `[15, 10]`; `-1` means all neighbors for that hop.
- `input_nodes`: seed nodes as a long tensor, boolean mask, node type string, or `(node_type, ids_or_mask)` tuple for hetero graphs. `None` means all nodes.
- `batch_size`: number of seed nodes per batch.
- `replace`: sample neighbors with replacement when `True`.
- `subgraph_type`: `"directional"`, `"bidirectional"`, or `"induced"`.
- `disjoint`: keep one subgraph per seed node and add a `batch` vector to sampled nodes.
- `time_attr` and `input_time`: enable temporal node sampling; `input_time` requires `time_attr`.
- `weight_attr`: biased neighbor sampling with non-negative finite edge weights whose local neighborhood sum is non-zero.
- `is_sorted`: assert `edge_index` is sorted by destination column; with temporal sampling, rows must also be sorted by time within neighborhoods.
- `filter_per_worker`: controls whether feature filtering happens in worker processes or the main process.

Expected output for homogeneous data:

- `batch.batch_size`: number of seed nodes.
- `batch.n_id`: original/global node ids for sampled local nodes.
- `batch.e_id`: original/global edge ids for sampled edges when available.
- `batch.input_id`: original indices of the selected input nodes.
- `batch.num_sampled_nodes`: sampled node counts per hop when produced by the backend.
- `batch.num_sampled_edges`: sampled edge counts per hop when produced by the backend.

Training loop pattern:

```python
for batch in loader:
    out = model(batch.x, batch.edge_index)
    seed_out = out[:batch.batch_size]
    seed_y = batch.y[:batch.batch_size]
    loss = criterion(seed_out, seed_y)
```

The first `batch.batch_size` nodes are the seed nodes. Compute node-level loss and metrics on that prefix unless the task intentionally uses all sampled nodes.

## Choosing `num_neighbors` and model depth

- Keep the number of sampled hops aligned with the number of message-passing layers for ordinary node classification.
- Sampling more hops than model layers wastes work because deeper sampled nodes cannot affect seed-node outputs.
- Sampling fewer hops than model layers requires `subgraph_type="bidirectional"` or `"induced"` when deeper message passing must traverse edges among sampled nodes.
- Neighbor growth is roughly exponential in hops; prefer two or three hops before increasing per-hop fanout.
- Use `-1` only on small graphs or low-degree edge types; it can expand to full neighborhoods.

## Subgraph type selection

- `"directional"`: includes sampled edges required for messages toward seed nodes. It is the default and works when sampling hops match GNN layers.
- `"bidirectional"`: makes sampled edges bidirectional. Use when message passing needs reverse flow or model depth exceeds sampled hops.
- `"induced"`: returns the induced subgraph over sampled nodes. It can be more complete but may require optional sparse backends and more memory.

The older `directed` argument exists for compatibility; prefer explicit `subgraph_type` in new code.

## Heterogeneous NeighborLoader

For `HeteroData`, specify seed node type and optionally edge-type-specific fanouts:

```python
loader = NeighborLoader(
    hetero_data,
    num_neighbors={edge_type: [10, 5] for edge_type in hetero_data.edge_types},
    input_nodes=("paper", hetero_data["paper"].train_mask),
    batch_size=128,
)
```

Rules:

- `input_nodes` must identify a node type, such as `"paper"` or `("paper", mask)`.
- Dictionary `num_neighbors` keys are canonical edge-type tuples like `("author", "writes", "paper")`.
- All edge types must use the same number of hops. Mixing `[10]` with `[10, 5]` raises an error.
- Output is `HeteroData`; inspect `batch[ntype].n_id`, `batch[ntype].batch_size`, and per-edge-type `edge_index`.

## LinkNeighborLoader for link prediction

Use `LinkNeighborLoader` when supervision is edge-based. It samples edges from `edge_label_index`, then samples neighborhoods around the edge endpoints.

```python
import torch
from torch_geometric.loader import LinkNeighborLoader

edge_label_index = data.edge_index[:, :100]
edge_label = torch.ones(edge_label_index.size(1))

loader = LinkNeighborLoader(
    data,
    num_neighbors=[15, 10],
    edge_label_index=edge_label_index,
    edge_label=edge_label,
    batch_size=32,
    shuffle=True,
)
```

Important parameters:

- `edge_label_index`: tensor of shape `[2, num_edges]`; for hetero graphs use `(edge_type, edge_label_index)` or just an edge type to use all edges of that type.
- `edge_label`: label per supervision edge; must match the number of columns in `edge_label_index`.
- `edge_label_time`: timestamp per supervision edge; must be provided together with `time_attr`.
- `neg_sampling`: preferred negative sampling configuration, such as `dict(mode="binary", amount=1.0)`.
- `neg_sampling_ratio`: older shortcut for binary negative sampling; prefer `neg_sampling` for new code.

Expected output:

- Homogeneous output contains local `edge_label_index` over sampled nodes and optional `edge_label`.
- `batch.n_id[batch.edge_label_index]` maps local supervised edges back to original node ids.
- With binary negative sampling, positive labels come first in each mini-batch, followed by sampled negatives.
- Negative sampling is approximate; sampled negatives may contain false negatives.

Avoid leakage: supervision edges in `edge_label_index` are not automatically removed from the message-passing graph. If overlap would leak labels, split message-passing edges and supervision edges beforehand, for example with `RandomLinkSplit(disjoint_train_ratio=...)`.

## Temporal and weighted sampling

Node temporal sampling:

```python
loader = NeighborLoader(
    data,
    num_neighbors=[10, 5],
    input_nodes=train_nodes,
    input_time=train_times,
    time_attr="time",
    temporal_strategy="last",
    batch_size=128,
)
```

Link temporal sampling:

```python
loader = LinkNeighborLoader(
    data,
    num_neighbors=[10],
    edge_label_index=edge_label_index,
    edge_label_time=edge_times,
    time_attr="time",
    batch_size=128,
)
```

Rules:

- `input_time` requires `time_attr`.
- `edge_label_time` and `time_attr` must either both be set or both be absent.
- Temporal sampling enforces neighbors at earlier or equal times than the center node or output edge.
- Temporal sampling may set `disjoint=True` internally.
- `temporal_strategy="uniform"` samples uniformly from valid temporal neighbors; `"last"` prefers the most recent valid neighbors.
- `weight_attr` requires finite, non-negative weights with a non-zero local sum.

## Optional backend reality check

`NeighborLoader` and `LinkNeighborLoader` construction can succeed even when the environment lacks an optional sampler backend. Iteration may fail without `pyg-lib` or `torch-sparse`, depending on the operation and `subgraph_type`. Use the bundled smoke test with `--check-neighbor` to distinguish import/configuration problems from missing optional backend problems.

## Native-style verification checklist

- Call `len(loader)` and inspect one mini-batch before training.
- Confirm seed nodes are first: `batch.n_id[:batch.batch_size]` should map to the requested seed ids for homogeneous node sampling.
- Confirm local edge indices are valid: `batch.edge_index.max() < batch.num_nodes`.
- For link sampling, map local supervised edges through `batch.n_id[batch.edge_label_index]` before comparing to global ids.
- For hetero sampling, verify `batch.input_type`, `batch.node_types`, `batch.edge_types`, and per-type `n_id`.
- For temporal sampling, verify timestamp tensors line up with node or edge supervision length before constructing the loader.
