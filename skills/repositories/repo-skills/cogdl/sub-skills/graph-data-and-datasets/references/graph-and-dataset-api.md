# CogDL Graph and Dataset API

This reference distills the data APIs a future agent needs to build and inspect
CogDL graph fixtures without opening the original repository materials.

## Imports

```python
import torch
from cogdl.data import Graph, Adjacency, Dataset, DataLoader
from cogdl.datasets import (
    NodeDataset,
    GraphDataset,
    generate_random_graph,
    build_dataset_from_name,
)
```

`NodeDataset`, `GraphDataset`, and `generate_random_graph` live under
`cogdl.datasets`; core `Graph`, `Adjacency`, `Dataset`, and `DataLoader` live
under `cogdl.data`.

## Core objects

| Object | Signature / entry point | Use | Important behavior |
| --- | --- | --- | --- |
| `Graph` | `Graph(x=None, y=None, **kwargs)` | One graph with node features, labels, adjacency, masks, and arbitrary extra attributes. | `x` must be a `torch.Tensor` when supplied. Adjacency kwargs may include `edge_index`, `edge_weight`, `edge_attr`, `edge_types`, low-level `row_ptr`/`col`, and train-time variants such as `edge_index_train`. |
| `Adjacency` | `Adjacency(row=None, col=None, row_ptr=None, weight=None, attr=None, num_nodes=None, types=None, **kwargs)` | Low-level COO/CSR adjacency store used by `Graph`. | Usually access through `Graph` properties. `weight` is created as all ones when missing and requested. |
| `Dataset` | `Dataset(root, transform=None, pre_transform=None, pre_filter=None)` | Base class for datasets with raw/processed cache directories. | Construction calls download/process hooks when expected raw or processed files are missing. Use a deliberate cache root. |
| `NodeDataset` | `NodeDataset(path='data.pt', data=None, scale_feat=True, metric='auto')` | Custom node-level dataset backed by one saved `Graph` or an in-memory `Graph`. | With `data=...`, it can save the graph to `path` if missing. With `scale_feat=True`, node features are standardized. `metric='auto'` chooses `multilabel_f1` for 2-D labels and `accuracy` otherwise. |
| `GraphDataset` | `GraphDataset(path='cus_graph_data.pt', metric='accuracy')` | Custom graph-level dataset backed by a saved list of `Graph` objects. | The path must exist unless a subclass implements `process()`. Each graph should use local node ids and a graph-level label. |
| `generate_random_graph` | `generate_random_graph(num_nodes=100, num_edges=1000, num_feats=64)` | Quick synthetic node-classification `Graph`. | Generates `x`, `y`, `edge_index`, and boolean `train_mask`/`val_mask`/`test_mask`; it does not download data. |
| `DataLoader` | `DataLoader(dataset, batch_size=1, shuffle=True, **kwargs)` | Mini-batches lists/datasets of `Graph` objects. | Graph batches are block-diagonalized into one `Batch` with a `batch` vector mapping nodes to graph ids. |

## `Graph` fields and properties

| Field | Expected shape / type | Notes |
| --- | --- | --- |
| `x` | Tensor `[num_nodes, num_features]` or occasionally `[num_nodes]` | Required by many GNN models. CogDL raises `ValueError` if non-tensor features are passed to `Graph(x=...)`. |
| `y` | Node labels `[num_nodes]` or `[num_nodes, num_labels]`; graph labels often `[1]` per graph | Node-classification validation should require labels. Graph classification stores one label tensor on each graph. |
| `edge_index` | Tuple `(row, col)` of 1-D long tensors or tensor shaped `[2, num_edges]` | COO adjacency. If data arrives as `[num_edges, 2]`, transpose it before constructing `Graph`. |
| `edge_weight` | Tensor `[num_edges]` | If absent, CogDL materializes all-ones weights when requested. Normalization methods mutate effective edge weights. |
| `edge_attr` | Tensor with first dimension `num_edges` | Edge features/attributes. Keep aligned whenever edges are filtered or reordered. |
| `row_indptr` / `col_indices` | CSR row pointer `[num_nodes + 1]` and column indices `[num_edges]` | Public properties for CSR access. For constructor kwargs, prefer `edge_index` or low-level `row_ptr`/`col`; after construction, assign `graph.row_indptr = ...` and `graph.col_indices = ...` if needed. |
| `num_nodes` | Integer property | Inferred from `x` when present, else from edges. Set explicitly for isolated nodes or featureless graphs. |
| `num_edges` | Integer-like property | Derived from COO row length or CSR pointer. |
| `train_mask`, `val_mask`, `test_mask` | Boolean tensors `[num_nodes]` or index tensors | Standard node-classification splits. `Graph.mask2nid(split)` accepts boolean masks or index tensors. |

`Graph` also accepts arbitrary task-specific fields such as `all_masks`,
`train_node`, `train_target`, `adj`, or dictionaries for heterogeneous/multiplex
workflows. Treat nonstandard fields as task-owned and route wrapper/model
questions to the relevant sub-skill.

## Graph methods

| Method / property | Purpose | Mutability and caveats |
| --- | --- | --- |
| `sym_norm()` | Symmetric degree normalization for GCN-like message passing. | Mutates edge weights/normalization state. Repeated calls are skipped once normalized. |
| `row_norm()` / `col_norm()` | Row-wise or column-wise normalization. | Mutates edge weights and can mark adjacency asymmetric. |
| `add_remaining_self_loops()` | Add one self-loop per node that lacks one. | Updates both full and train adjacency when an inductive train adjacency exists. |
| `padding_self_loops()` | Append self-loops with small/default weights to the active adjacency. | Acts on the current active adjacency. Use deliberately; it is not the same as adding only missing self-loops. |
| `remove_self_loops()` | Remove edges where source equals target. | Edge weights/attributes are filtered along with edges. |
| `subgraph(node_idx, keep_order=False)` | Induce a graph on selected nodes. | Node attributes are sliced; edge ids and edge count change. Recreate or slice masks for the new node set. |
| `edge_subgraph(edge_idx, require_idx=True)` | Select edges and the incident nodes. | Default returns `(graph, nodes, edge_idx)`; pass `require_idx=False` to receive only the graph. |
| `sample_adj(batch, size=-1, replace=True)` | Sample or collect neighbors for seed nodes. | Returns `(nodes, adj_graph)`, where `adj_graph` is an adjacency-only `Graph`. |
| `local_graph()` | Context manager for temporary adjacency/attribute edits. | Out-of-place assignments are restored. In-place tensor mutations such as `graph.edge_weight += 1` can leak to the original tensors. |
| `to_networkx()` | Convert adjacency to a NetworkX graph. | Uses current adjacency and edge weights; directed semantics may be simplified to a NetworkX graph object. |
| `to_scipy_csr()` | Convert adjacency to SciPy CSR. | Useful for classical graph algorithms and sampling checks. |
| `train()` / `eval()` | Switch between train and full adjacency for inductive data. | Only changes behavior when train-specific adjacency fields such as `edge_index_train` were supplied. |
| `degrees()` | Return degree tensor. | Used for degree features and normalization checks. |
| `to(device)`, `cuda()`, `contiguous()` | Tensor device/layout helpers. | CUDA is optional acceleration; do not require it for data validation. |

There is no verified `Graph.add_self_loops()` method. Use
`add_remaining_self_loops()` for the common CogDL graph method, or construct a
new edge index with a utility and reassign it when a workflow truly needs to
append all self-loop edges.

## Custom node-classification dataset pattern

Use this pattern when a user has an edge list, features, labels, and masks and
wants a no-download CogDL dataset:

```python
import torch
from cogdl.data import Graph
from cogdl.datasets import NodeDataset

edge_index = torch.tensor(
    [[0, 1, 2, 3, 0, 2], [1, 2, 3, 0, 2, 0]], dtype=torch.long
)
x = torch.randn(4, 8)
y = torch.tensor([0, 1, 0, 1], dtype=torch.long)
train_mask = torch.tensor([True, True, False, False])
val_mask = torch.tensor([False, False, True, False])
test_mask = torch.tensor([False, False, False, True])

graph = Graph(
    x=x,
    edge_index=edge_index,
    y=y,
    train_mask=train_mask,
    val_mask=val_mask,
    test_mask=test_mask,
)
dataset = NodeDataset(path="my_node_data.pt", data=graph, scale_feat=False, metric="accuracy")
assert dataset[0].num_nodes == 4
```

Practical notes:

- Use a unique `path` to avoid silently reusing an older processed artifact.
- Use `scale_feat=False` when exact feature values matter; leave it `True` only
  when standardization is desired.
- `metric` must be one of `accuracy`, `multiclass_f1`, or `multilabel_f1`.

## Custom graph-classification dataset pattern

For graph-level tasks, save a list of independent `Graph` objects:

```python
import torch
from cogdl.data import Graph, DataLoader
from cogdl.datasets import GraphDataset

graphs = []
for label, num_nodes in [(0, 3), (1, 4)]:
    edge_index = torch.tensor([[0, 1, 2, 0], [1, 2, 0, 2]], dtype=torch.long)
    x = torch.eye(num_nodes, dtype=torch.float)
    graphs.append(Graph(x=x, edge_index=edge_index[:, : max(1, num_nodes)], y=torch.tensor([label])))

torch.save(graphs, "my_graph_data.pt")
dataset = GraphDataset(path="my_graph_data.pt", metric="accuracy")
loader = DataLoader(dataset, batch_size=2, shuffle=False)
batch = next(iter(loader))
assert batch.batch.shape[0] == batch.num_nodes
```

Each graph's `edge_index` must use node ids local to that graph. `DataLoader`
will offset them while batching.

## Metrics and losses attached to custom datasets

| Metric string | Typical label shape | Evaluator | Loss function |
| --- | --- | --- | --- |
| `accuracy` | Single-label class ids `[N]` or graph labels `[1]` | Accuracy | Cross entropy |
| `multiclass_f1` | Single-label class ids `[N]` | Multi-class micro-F1 | Cross entropy |
| `multilabel_f1` | Multi-hot labels `[N, C]` | Multi-label micro-F1 | BCE with logits |

Unsupported metric strings raise `NotImplementedError` when evaluator or loss
functions are requested.
