# Graph property workflows

## Choose the right dataset family

Use this workflow when the request is about graph-level labels or graph-level
benchmarks:

- `ogbg-mol*` for molecular graphs.
- `ogbg-ppa` for classification on protein-protein association graphs.
- `ogbg-code2` for code-to-graph conversion and token-sequence prediction.

## Common loader pattern

```python
from ogb.graphproppred import GraphPropPredDataset, Evaluator

dataset = GraphPropPredDataset(name="ogbg-molhiv")
split_idx = dataset.get_idx_split()
graph, label = dataset[0]
```

The PyG and DGL wrappers follow the same dataset name but require the matching
backend packages to be installed.

## Evaluator patterns

- `rocauc` and `ap` expect `y_true` / `y_pred` arrays with shape
  `(num_graphs, num_tasks)`.
- `rmse` expects numeric graph-level predictions with the same shape.
- `acc` is used by `ogbg-ppa`.
- `F1` is used by `ogbg-code2` and takes `seq_ref` / `seq_pred` token lists.

## Molecular graphs

When the task needs a graph representation for a SMILES string, use
`ogb.utils.smiles2graph`. The helper returns the standard OGB graph dict with
`edge_index`, `edge_feat`, `node_feat`, and `num_nodes`.

## Code-to-graph conversion

The code2 workflow converts a Python snippet into an AST graph and masks the
method name to avoid leakage. The bundled smoke helper is a safe miniature
version of that flow and is useful when you want to check the AST pipeline
without downloading dataset mapping files.

## Common mistakes

- Using a dataset name from the wrong prefix.
- Feeding a 1-D label array to a graph evaluator that expects 2-D arrays.
- Treating `ogbg-code2` as a numeric classification task.
- Forgetting that PyG/DGL wrappers are optional extras.
