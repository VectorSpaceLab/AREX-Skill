# API overview

## Top-level package layout

The installed package exposes these public families:

- `ogb.graphproppred`
- `ogb.nodeproppred`
- `ogb.linkproppred`
- `ogb.lsc`
- `ogb.io`
- `ogb.utils`

The root package also exposes `ogb.__version__`.

## Common loader pattern

Most dataset classes follow the same shape:

- `__init__(name, root='dataset', meta_dict=None)` or a dataset-specific
  equivalent.
- `__getitem__` returns either a graph/label pair or a single graph object.
- `get_idx_split(...)` or `get_edge_split(...)` returns the official split
  dictionary.
- The `meta_dict` argument is a debug/debugging path that lets you point the
  loader at an already prepared dataset directory.

## Graph property prediction

Public names:

- `GraphPropPredDataset`
- `PygGraphPropPredDataset` if `torch_geometric` is installed
- `DglGraphPropPredDataset` if `dgl` is installed
- `Evaluator`

Common shapes:

- `dataset[i] -> (graph, label)`.
- `graph` is a dictionary with `edge_index`, `num_nodes`, and optional
  `node_feat` / `edge_feat` keys.
- `get_idx_split()` returns `{'train', 'valid', 'test'}`.
- `Evaluator.eval()` returns a metric dictionary such as `{'rocauc': ...}`,
  `{'ap': ...}`, `{'rmse': ...}`, `{'acc': ...}`, or `{'F1': ...}` depending
  on the dataset.

Special cases:

- `ogbg-code2` uses sequence labels and F1-style sequence evaluation.
- Molecular graph datasets rely on `smiles2graph` when you are building graphs
  from SMILES strings.

## Node property prediction

Public names:

- `NodePropPredDataset`
- `PygNodePropPredDataset` if `torch_geometric` is installed
- `DglNodePropPredDataset` if `dgl` is installed
- `Evaluator`

Common shapes:

- `dataset[0] -> (graph, labels)` because the official datasets contain one
  graph.
- `get_idx_split()` returns `{'train', 'valid', 'test'}`.
- Heterogeneous datasets such as `ogbn-mag` return dict-valued node labels and
  dict-valued splits.
- `Evaluator.eval()` returns `{'rocauc': ...}` or `{'acc': ...}`.

## Link prediction

Public names:

- `LinkPropPredDataset`
- `PygLinkPropPredDataset` if `torch_geometric` is installed
- `DglLinkPropPredDataset` if `dgl` is installed
- `Evaluator`

Common shapes:

- `dataset[0] -> graph`.
- `get_edge_split()` returns `{'train', 'valid', 'test'}` with edge/sampling
  dictionaries that vary by dataset.
- The evaluator consumes predicted scores for positive/negative edges and
  returns ranking metrics or ROC-AUC depending on the dataset.

## OGB-LSC

| Class | Evaluator | Typical task shape | Notes |
| --- | --- | --- | --- |
| `PCQM4MDataset` | `PCQM4MEvaluator` | graph regression on molecules | deprecated; use `PCQM4Mv2Dataset` for new work |
| `PCQM4Mv2Dataset` | `PCQM4Mv2Evaluator` | graph regression on molecules | has `test-dev` and `test-challenge` submission helpers |
| `MAG240MDataset` | `MAG240MEvaluator` | heterogeneous node classification | offers `to_pyg_hetero_data()` and split helpers |
| `WikiKG90MDataset` | `WikiKG90MEvaluator` | knowledge-graph completion | deprecated; use `WikiKG90Mv2Dataset` for new work |
| `WikiKG90Mv2Dataset` | `WikiKG90Mv2Evaluator` | knowledge-graph completion | uses top-10 submission arrays and MRR |

## Dataset export

`ogb.io.DatasetSaver` is the public utility for packaging new OGB-compatible
releases. Its workflow is:

1. `save_graph_list(graph_list)`
2. `save_target_labels(target_labels)` when the dataset family needs labels
3. `save_split(split_dict, split_name)`
4. `copy_mapping_dir(mapping_dir)`
5. `save_task_info(task_type, eval_metric, num_classes=None)`
6. `get_meta_dict()`
7. `zip()`
8. `cleanup()`

## Molecule helper

`ogb.utils.smiles2graph(smiles_string, removeHs=True, reorder_atoms=False)`
converts a SMILES string into the canonical OGB graph dictionary with
`edge_index`, `edge_feat`, `node_feat`, and `num_nodes`.
