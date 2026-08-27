# Graph property API reference

## Public names

- `GraphPropPredDataset(name, root='dataset', meta_dict=None)`
- `PygGraphPropPredDataset(...)` when `torch_geometric` is installed
- `DglGraphPropPredDataset(...)` when `dgl` is installed
- `Evaluator(name)`

## Dataset return shapes

- `dataset[i] -> (graph, label)`
- `graph` is a dictionary with `edge_index`, `num_nodes`, and optional
  `node_feat` / `edge_feat` entries.
- `get_idx_split()` returns the official `train` / `valid` / `test` indices.

## Evaluator inputs

- `rocauc`, `ap`, `rmse`, `acc`:
  `{'y_true': array_or_tensor, 'y_pred': array_or_tensor}` with matching
  2-D shapes.
- `F1`:
  `{'seq_ref': list_of_token_lists, 'seq_pred': list_of_token_lists}`.

## Dataset names and common use

- Molecular classification: `ogbg-molbace`, `ogbg-molbbbp`, `ogbg-molclintox`,
  `ogbg-molmuv`, `ogbg-molpcba`, `ogbg-molsider`, `ogbg-moltox21`,
  `ogbg-moltoxcast`, `ogbg-molhiv`, `ogbg-molchembl`
- Molecular regression: `ogbg-molesol`, `ogbg-molfreesolv`, `ogbg-mollipo`
- Non-molecule graph classification: `ogbg-ppa`
- Code-to-graph: `ogbg-code2`

## Helper

`smiles2graph(smiles_string, removeHs=True, reorder_atoms=False)` returns a
plain graph dictionary that can be passed to OGB-compatible graph loaders or
used as a starting point for external molecular datasets.
