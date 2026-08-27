# Built-In Dataset Loaders

## Purpose

Use this reference when a task names a StellarGraph dataset class or needs a
small public example graph. Dataset loaders are convenient but may download data;
do not treat them as safe offline fixtures unless the data is already cached.

## Common loader contract

All dataset classes derive from `DatasetLoader` and expose:

```python
dataset = DatasetClass()
print(dataset.base_directory)
print(dataset.data_directory)
dataset.download(ignore_cache=False)
loaded = dataset.load(...)
```

The cache root defaults to `~/stellargraph-datasets` and can be overridden with
`STELLARGRAPH_DATASETS_PATH`. The `download(ignore_cache=True)` path deletes the
expected cached files and re-fetches them; use it only when the user wants a
fresh download.

## Dataset families

| Class | Typical use | Load result shape |
| --- | --- | --- |
| `Cora` | Citation graph for node classification, GCN/GAT/GraphSAGE/Node2Vec demos | `(graph, subjects)` with optional `directed`, `largest_connected_component_only`, `subject_as_feature`, `edge_weights`, `str_node_ids` arguments |
| `CiteSeer` | Citation graph for node classification and Attri2Vec demos | `(graph, subjects)` with `largest_connected_component_only` |
| `PubMedDiabetes` | Larger citation graph for inductive GraphSAGE and calibration demos | `(graph, labels)` |
| `BlogCatalog3` | Heterogeneous user/group graph for Metapath2Vec | `graph` |
| `MovieLens` | Heterogeneous user/movie rating graph for HinSAGE link prediction | `(graph, edges_with_ratings)` |
| `AIFB` | RDF/relational graph for RGCN node classification | dataset-specific graph/labels for relational workflows |
| `MUTAG`, `PROTEINS` | Graph classification benchmark examples | `(graphs, labels)` where `graphs` is a list of `StellarGraph` objects |
| `WN18`, `WN18RR`, `FB15k`, `FB15k_237` | Knowledge graph completion examples | train/validation/test triple data with graph/KG metadata, depending loader |
| `IAEnronEmployees` | Temporal link-prediction example | temporal graph data for CTDNE-style workflow |
| `METR_LA` | Traffic time-series forecasting example | matrix/time-series data plus helper methods `train_test_split`, `scale_data`, and `sequence_data_preparation` |

## Safe usage pattern

For a task that only needs API guidance or a tiny smoke test, do not download a
public dataset. Use a synthetic graph from `data-formats.md` instead.

For a task that explicitly wants a packaged dataset:

```python
import os
from stellargraph import datasets

os.environ.setdefault("STELLARGRAPH_DATASETS_PATH", "/tmp/stellargraph-datasets")
dataset = datasets.Cora()
print(dataset.base_directory)
graph, subjects = dataset.load(largest_connected_component_only=True)
print(graph.info())
print(subjects.head())
```

Replace `/tmp/stellargraph-datasets` with a writable cache location suitable for
the user's runtime. Do not hard-code a private cache path into reusable code.

## Download boundaries

Dataset downloads are not appropriate for default verification because they
involve network access and external hosts. If a dataset workflow fails, separate
these questions:

1. Can the package import and construct a tiny synthetic graph?
2. Is the dataset cache directory writable?
3. Is the remote dataset host reachable?
4. Are the expected files present after download/unpack?
5. Does the selected loader return the shape expected by the downstream model?

Use the first question for safe local checks and only attempt the others when
the user requests real dataset execution.
