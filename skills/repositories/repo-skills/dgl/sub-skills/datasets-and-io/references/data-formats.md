# Data Formats for DGL Datasets and IO

## `CSVDataset` Folder Contract

A `dgl.data.CSVDataset(data_path, ...)` folder must contain a `meta.yaml` file and the CSV files named by that metadata. `CSVDataset` is a `DGLDataset`, so it parses once, writes a processed cache named `<dataset_name>.bin` under its save path, and reloads the cache unless `force_reload=True`.

Minimal homogeneous folder:

```text
my_dataset/
  meta.yaml
  nodes.csv
  edges.csv
```

Minimal `meta.yaml`:

```yaml
dataset_name: my_dataset
node_data:
  - file_name: nodes.csv
edge_data:
  - file_name: edges.csv
```

`nodes.csv` must have a node-id column, default `node_id`:

```csv
node_id,feat,label,train_mask,val_mask,test_mask
0,"0.1,0.2",1,True,False,False
1,"0.3,0.4",0,False,True,False
```

`edges.csv` must have source and destination id columns, default `src_id` and `dst_id`:

```csv
src_id,dst_id,weight
0,1,0.5
1,0,0.7
```

Edges are directed. Add reverse rows yourself or apply a transform such as `dgl.transforms.AddReverse` if the model expects both directions.

## Full `meta.yaml` Schema

`CSVDataset` supports schema version `1.0.0`.

```yaml
version: 1.0.0
dataset_name: some_complex_data
separator: ","
node_data:
  - file_name: nodes_user.csv
    ntype: user
    graph_id_field: graph_id
    node_id_field: node_id
  - file_name: nodes_item.csv
    ntype: item
    graph_id_field: graph_id
    node_id_field: node_id
edge_data:
  - file_name: edges_like.csv
    etype: [user, like, item]
    graph_id_field: graph_id
    src_id_field: src_id
    dst_id_field: dst_id
graph_data:
  file_name: graphs.csv
  graph_id_field: graph_id
```

Top-level fields:

| Field | Required | Meaning |
| --- | --- | --- |
| `version` | No | Must be omitted or `1.0.0`. |
| `dataset_name` | Yes | Dataset/cache name; also controls the processed `.bin` name. |
| `separator` | No | CSV separator; default is `,`. |
| `node_data` | Yes | List of node CSV entries. Each node type must be unique. |
| `edge_data` | Yes | List of edge CSV entries. Each canonical edge type must be unique. |
| `graph_data` | No | One graph-level CSV entry for graph labels/features. |

Node entry fields:

| Field | Required | Default | Meaning |
| --- | --- | --- | --- |
| `file_name` | Yes | none | CSV path relative to the dataset folder. |
| `ntype` | No | `_V` | Node type; use one CSV per type for heterographs. |
| `graph_id_field` | No | `graph_id` | Column used to split multiple graphs; can be absent in single-graph CSVs. |
| `node_id_field` | No | `node_id` | Required column containing raw node IDs. |

Edge entry fields:

| Field | Required | Default | Meaning |
| --- | --- | --- | --- |
| `file_name` | Yes | none | CSV path relative to the dataset folder. |
| `etype` | No | `[_V, _E, _V]` | Canonical edge type triplet `[src_ntype, relation, dst_ntype]`. |
| `graph_id_field` | No | `graph_id` | Column used to split multiple graphs; can be absent in single-graph CSVs. |
| `src_id_field` | No | `src_id` | Required source node-id column. |
| `dst_id_field` | No | `dst_id` | Required destination node-id column. |

Graph entry fields:

| Field | Required | Default | Meaning |
| --- | --- | --- | --- |
| `file_name` | Yes | none | Graph-level CSV path relative to the dataset folder. |
| `graph_id_field` | No | `graph_id` | Required graph-id column in graph-level CSV. |

## Homogeneous vs Heterogeneous CSV

Homogeneous CSV omits `ntype` and `etype`, or uses the defaults `_V` and `[_V, _E, _V]`.

Heterogeneous CSV uses one node CSV per node type and one edge CSV per canonical edge type:

```yaml
dataset_name: shop_graph
node_data:
  - file_name: users.csv
    ntype: user
  - file_name: items.csv
    ntype: item
edge_data:
  - file_name: follows.csv
    etype: [user, follows, user]
  - file_name: buys.csv
    etype: [user, buys, item]
```

Important constraints:

- `etype` must be a three-item list, not a scalar such as `buys`.
- The `src_id` values of an edge CSV must appear in the source node type CSV named by `etype[0]`.
- The `dst_id` values must appear in the destination node type CSV named by `etype[2]`.
- Raw node IDs may be strings or numbers; DGL maps them to contiguous internal IDs per graph and node type.
- Duplicate raw node IDs within the same `graph_id` and node type are invalid.

## Multiple Graphs

For a dataset containing multiple graphs, add a `graph_id` column to node and edge CSVs and usually a `graph_data` CSV:

```yaml
dataset_name: graph_collection
node_data:
  - file_name: nodes.csv
edge_data:
  - file_name: edges.csv
graph_data:
  file_name: graphs.csv
```

```csv
# nodes.csv
graph_id,node_id,feat
0,0,"0.1,0.2"
0,1,"0.3,0.4"
1,0,"0.5,0.6"
```

```csv
# graphs.csv
graph_id,label
0,1
1,0
```

If `graph_data` exists, every graph id found in node/edge CSVs must appear in the graph CSV. If graph data has one column, `CSVDataset.__getitem__()` returns `(graph, label_tensor)`; with multiple graph-data columns it returns `(graph, data_dict)`.

## Feature and Mask Parsing

The default parser consumes every non-ID, non-graph-id column as data:

- Numeric scalar columns become tensor features directly.
- Boolean strings such as `True`/`False` are commonly used for masks; verify resulting tensor dtype before training.
- Vector features should be quoted CSV strings that Python can parse as list-like values, such as `"0.1, 0.2, 0.3"`.
- Empty feature cells are not supported by the default parser; write a custom `ndata_parser`, `edata_parser`, or `gdata_parser` when values are categorical, nullable, JSON-like, or non-numeric.
- Columns whose header contains `Unnamed` are ignored by DGL's default parser, usually indicating an accidental DataFrame index export.

Recommended split mask names for downstream examples are `train_mask`, `val_mask`, and `test_mask`, stored in `g.ndata` for node prediction or `g.edata` for edge prediction.

## Graph Serialization Format

Use DGL's binary graph serializer for processed caches and explicit graph handoffs:

```python
import dgl
import torch

labels = {"label": torch.tensor([0, 1])}
dgl.save_graphs("graphs.bin", [g0, g1], labels=labels, formats=["coo"])
graphs, label_dict = dgl.load_graphs("graphs.bin")
first_graph, all_labels = dgl.load_graphs("graphs.bin", idx_list=[0])
```

Notes:

- `save_graphs()` stores graph structure plus `ndata` and `edata`; graph-level data belongs in the `labels` dict.
- `load_graphs(..., idx_list=[...])` loads selected graphs, but the labels dict still contains labels for all graphs saved in the file.
- Local parent directories are created automatically for files; passing an existing directory as `filename` is invalid.
- Paths with `s3://`, `hdfs://`, or `viewfs://` are supported by the serializer when the runtime has the required storage support.
- Batched DGL graphs are not supported by graph serialization; unbatch first if needed.

## `DGLDataset` Cache Layout

A custom dataset should keep all processed artifacts under `self.save_path`, not beside source code. Common files:

```text
<save_path>/
  graphs.bin
  info.pkl
```

Use `save_graphs()` for graphs and labels, and `save_info()` for Python metadata such as `num_classes`, split names, vocabulary sizes, or preprocessing options. `has_cache()` should require every file that `load()` needs; returning true when `info.pkl` is missing causes DGL to try `load()`, catch the failure, and reprocess.

`hash_key` changes the dataset hash and helps separate caches for preprocessing variants. Include options that affect graph topology, features, splits, or labels.

## Download and Repository Environment Knobs

DGL dataset utilities use these public environment variables:

- `DGL_DOWNLOAD_DIR`: default raw/cache root when `raw_dir` is omitted; default is `~/.dgl`.
- `DGL_REPO`: base URL for DGL-hosted dataset downloads; default is `https://data.dgl.ai/`.

For reproducible code, prefer explicit `raw_dir=` and `save_dir=` arguments over global environment variables. Use `force_reload=True` after changing raw files or parser logic.

## GraphBolt `OnDiskDataset` Handoff Summary

GraphBolt `OnDiskDataset` is a separate large-graph/minibatch-streaming format. It uses `metadata.yaml`, not `meta.yaml`. Route execution details to `dataloading-graphbolt`, but use this checklist to prepare a valid handoff:

```yaml
dataset_name: my_graphbolt_dataset
graph:
  nodes:
    - type: user
      num: 1000
  edges:
    - type: user:follows:user
      format: csv
      path: edges/follows.csv
feature_data:
  - domain: node
    type: user
    name: feat
    format: numpy
    in_memory: true
    path: features/user_feat.npy
tasks:
  - name: node_classification
    num_classes: 3
    train_set:
      - type: user
        data:
          - name: seeds
            format: numpy
            in_memory: true
            path: sets/train_seeds.npy
          - name: labels
            format: numpy
            in_memory: true
            path: sets/train_labels.npy
    validation_set: []
    test_set: []
```

Key differences from `CSVDataset`:

- Metadata filename is `metadata.yaml`.
- Edge `type` is a string field in the GraphBolt spec; for heterographs use the format expected by the GraphBolt loader/version in use.
- Graph structure entries name `format` and `path`; `numpy` edge arrays should be shaped `(2, num_edges)`.
- Feature entries use `domain`, `type`, `name`, `format`, `in_memory`, and relative `path`.
- Task sets expose minibatch fields such as `seeds`, `labels`, and `indexes` for GraphBolt datapipe execution.

## DGL-Go CSV Handoff

When preparing CSV data for DGL-Go, validate the CSV folder here first, then route CLI/project commands to `dglgo-cli`. A good handoff says:

- The folder contains `meta.yaml`, node CSVs, edge CSVs, and optional graph CSVs.
- The folder passes `scripts/csv_dataset_linter.py`.
- The graph is homogeneous or lists canonical heterograph edge triplets.
- Feature, label, and mask column names are documented for the generated DGL-Go config.
