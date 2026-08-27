# CogDL Data Formats and Validation

This reference gives the concrete schemas and invariants needed to prepare
CogDL graph data safely.

## Node-classification `Graph` schema

A standard node-classification graph should contain:

```python
graph = Graph(
    x=x,                         # torch.Tensor [num_nodes, num_features]
    edge_index=edge_index,       # [2, num_edges] or (row, col), dtype long
    y=y,                         # [num_nodes] or [num_nodes, num_labels]
    train_mask=train_mask,       # bool [num_nodes] or index tensor
    val_mask=val_mask,
    test_mask=test_mask,
)
```

Required invariants before routing to an experiment or wrapper:

- `x` is a tensor when present; most neural models require it.
- `edge_index` has exactly two rows/components, integer dtype, equal source and
  destination lengths, and node ids in `[0, num_nodes - 1]`.
- `y` exists and its first dimension equals `num_nodes`.
- `train_mask`, `val_mask`, and `test_mask` exist. Boolean masks must have
  length `num_nodes`; index masks must be 1-D integer tensors with valid ids.
- Split masks should usually be disjoint. Require full coverage only if the task
  expects every node to belong to one of the splits.
- Set `graph.num_nodes` explicitly when the graph has isolated nodes and no
  feature matrix from which the node count can be inferred.

Use the bundled validator for saved node fixtures:

```bash
python scripts/validate_graph_masks.py --path my_node_data.pt
python scripts/validate_graph_masks.py --path my_node_data.pt --require-cover
```

## COO adjacency

CogDL accepts COO adjacency as either:

```python
edge_index = torch.tensor([[src0, src1, ...], [dst0, dst1, ...]], dtype=torch.long)
# or
edge_index = (row_long_tensor, col_long_tensor)
```

Common repairs:

- Edge list shaped `[num_edges, 2]`: use `edge_index = edge_list.t().contiguous()`.
- Non-long dtype: use `edge_index = edge_index.long()`.
- One-based node ids: subtract one before construction.
- Out-of-range ids: either fix the edge list or set `num_nodes` high enough only
  when those ids are legitimate isolated/known nodes.

`edge_weight` must have shape `[num_edges]`. `edge_attr` must have first
dimension `num_edges`. When filtering edges manually, filter weights and
attributes with the same edge mask.

## CSR adjacency

CogDL exposes CSR through:

- `graph.row_indptr`: row pointer tensor of length `num_nodes + 1`.
- `graph.col_indices`: column index tensor of length `num_edges`.

For new data, prefer COO because it is easier to validate. If CSR is already
available, either construct with low-level adjacency keys or assign properties
after construction:

```python
graph = Graph(x=x, y=y, num_nodes=num_nodes)
graph.row_indptr = row_ptr.long()
graph.col_indices = col_indices.long()
```

COO and CSR conversion may reorder edges. Do not assume edge attribute ordering
is unchanged after calling conversion, self-loop, or normalization methods unless
the attributes are carried through the same CogDL operation.

## Masks and node ids

CogDL's `Graph.mask2nid(split)` accepts both boolean masks and index tensors:

```python
train_ids = graph.train_nid  # equivalent to graph.mask2nid("train")
val_ids = graph.val_nid
test_ids = graph.test_nid
```

Best practice for new node-classification data:

- Store boolean masks with dtype `torch.bool` and length `num_nodes`.
- Keep masks disjoint unless an algorithm explicitly allows overlap.
- For subgraphs, slice masks by the selected node ids or rebuild them for the
  new local node ordering.
- For `edge_subgraph`, remember that CogDL reindexes to the incident-node set;
  masks from the original graph cannot be reused without mapping through the
  returned node ids.

## Graph-classification schema and batching

A graph-classification dataset is a list-like collection of `Graph` objects:

```python
graphs = [Graph(x=x_i, edge_index=edge_i, y=torch.tensor([label_i])) for ...]
torch.save(graphs, "graphs.pt")
dataset = GraphDataset(path="graphs.pt")
```

Invariants:

- Each graph uses local node ids starting at zero.
- `x.shape[0] == graph.num_nodes` when features are present.
- Each graph has a graph-level `y`, usually shape `[1]` for classification.
- If `x` is missing, graph-classification wrappers can create one-hot degree
  features when configured to do so. That is a training-wrapper decision, not a
  data-format requirement.

`DataLoader` batches graph lists by concatenating node attributes and producing a
block-diagonal adjacency. The resulting batch has an additional `batch` tensor:

```python
loader = DataLoader(dataset, batch_size=8, shuffle=False)
for batch in loader:
    assert batch.batch.shape[0] == batch.num_nodes
    # batch.batch[n] is the graph id for node n inside this mini-batch.
```

## Mutation and view semantics

- `sym_norm`, `row_norm`, and `col_norm` mutate adjacency weights or
  normalization state. Clone or use `local_graph()` before exploratory changes.
- `add_remaining_self_loops`, `padding_self_loops`, and `remove_self_loops`
  change the active adjacency and can change edge counts.
- `local_graph()` restores out-of-place adjacency/attribute assignments after
  the context exits. In-place tensor mutations still affect the underlying
  tensor object.
- `train()` switches to train-specific adjacency only if the graph was created
  with train adjacency fields such as `edge_index_train`; otherwise `train()`
  and `eval()` are effectively the same for data access.

Safe temporary edit pattern:

```python
with graph.local_graph():
    row, col = graph.edge_index
    keep = torch.arange(min(10, graph.num_edges))
    graph.edge_index = (row[keep], col[keep])
    # Inspect temporary graph here.
# Original edge_index is restored for out-of-place assignment above.
```

Avoid this if you expect restoration:

```python
with graph.local_graph():
    graph.edge_weight += 1  # in-place mutation can leak outside the context
```

## Fixture creation helper

Create deterministic no-download fixtures for smoke tests or examples:

```bash
python scripts/create_tiny_graph_dataset.py --output-dir tiny-cogdl-data --kind both
```

The helper writes a node-classification `Graph` artifact and a graph-
classification list artifact, then validates them through `NodeDataset`,
`GraphDataset`, and `DataLoader`.

## Pre-handoff validation checklist

Before handing a data object to `experiment()` or wrapper code:

1. Decide task type: node classification, graph classification, network
   embedding, link prediction, heterogeneous/multiplex, or application pipeline.
2. Validate feature, label, edge, and mask shapes for node tasks.
3. For graph tasks, validate every graph independently and run one `DataLoader`
   batch.
4. Label any built-in dataset load as cache/network-dependent unless already
   cached and approved.
5. Route model, wrapper, CLI, and training-budget decisions to the appropriate
   sibling sub-skill.
