# Link property API reference

## Public names

- `LinkPropPredDataset(name, root='dataset', meta_dict=None)`
- `PygLinkPropPredDataset(...)` when `torch_geometric` is installed
- `DglLinkPropPredDataset(...)` when `dgl` is installed
- `Evaluator(name)`

## Dataset return shapes

- `dataset[0] -> graph`
- `get_edge_split()` returns the official `train`, `valid`, and `test` edge
  dictionaries.
- The exact split payload varies by dataset family and must be read from the
  official loader.

## Evaluator inputs

- `hits@K` / `rocauc`:
  `{'y_pred_pos': vector, 'y_pred_neg': vector}`.
- `mrr`:
  `{'y_pred_pos': vector, 'y_pred_neg': matrix}`.
- The evaluator returns a metric dictionary whose key matches the configured
  metric.

## Dataset notes

- `ogbl-ppa` -> `hits@100`
- `ogbl-collab` -> `hits@50`
- `ogbl-citation2` -> `mrr`
- `ogbl-wikikg2` -> `mrr`
- `ogbl-ddi` -> `hits@20`
- `ogbl-biokg` -> `mrr`
- `ogbl-vessel` -> `rocauc`
