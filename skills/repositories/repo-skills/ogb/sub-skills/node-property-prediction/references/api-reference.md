# Node property API reference

## Public names

- `NodePropPredDataset(name, root='dataset', meta_dict=None)`
- `PygNodePropPredDataset(...)` when `torch_geometric` is installed
- `DglNodePropPredDataset(...)` when `dgl` is installed
- `Evaluator(name)`

## Dataset return shapes

- `dataset[0] -> (graph, labels)` for the one-graph datasets.
- Heterogeneous datasets may return dict-valued labels and split dictionaries.
- `get_idx_split()` returns the official `train` / `valid` / `test` indices,
  or dict-valued splits for hetero graphs.

## Evaluator inputs

- `rocauc` and `acc` use `{'y_true': ..., 'y_pred': ...}` with matching 2-D
  shapes.
- The evaluator reads the dataset metadata to determine the task size and
  metric.

## Dataset notes

- `ogbn-proteins` uses ROC-AUC.
- `ogbn-products`, `ogbn-arxiv`, and `ogbn-mag` use accuracy.
- `ogbn-papers100M` is the binary/raw-format large-scale dataset.
