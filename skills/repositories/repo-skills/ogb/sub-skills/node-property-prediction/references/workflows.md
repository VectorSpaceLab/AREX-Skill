# Node property workflows

## Choose the right dataset

Use this workflow for node-level prediction tasks with the `ogbn-*` prefix.
The official families are:

- `ogbn-arxiv`
- `ogbn-products`
- `ogbn-proteins`
- `ogbn-mag`
- `ogbn-papers100M`

## Common loader pattern

```python
from ogb.nodeproppred import NodePropPredDataset, Evaluator

dataset = NodePropPredDataset(name="ogbn-arxiv")
split_idx = dataset.get_idx_split()
graph, labels = dataset[0]
```

For heterogeneous datasets such as `ogbn-mag`, the labels and split indices are
dictionaries keyed by node type.

## Evaluator patterns

- `rocauc` expects 2-D arrays of node labels and predictions.
- `acc` expects class predictions with the same 2-D shape.

## Common decisions

- Use the library-agnostic loader when you only need the official graph and
  labels.
- Use the PyG or DGL wrappers only when the backend package is installed and
  the task needs those data structures.
- Treat `dataset[0]` as the full graph for the one-graph datasets.

## Heterogeneous caveats

- `ogbn-mag` returns dict-valued labels and dict-valued splits.
- The hetero path is not the same as the homogeneous path even when the metric
  is still accuracy.
- The large binary dataset path can short-circuit on `data.npz`.

## Common mistakes

- Using `dataset[0]` as if it were a graph/label pair in every case.
- Passing 1-D arrays into the evaluator.
- Assuming `ogbn-mag` behaves like `ogbn-arxiv`.
