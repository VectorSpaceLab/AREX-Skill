# API reference

This page collects the dataset-facing contracts that matter for custom data
registration, preprocessing, and batch collation.

## Registry API

### `DATASET_REGISTRY`

- Type: plain dictionary
- Role: holds the realized dataset dictionaries registered by user modules
- Population time: import time, through `register_dataset`

### `register_dataset(name: str)`

Decorator contract:

- The wrapped function is called immediately.
- The returned value is stored in `DATASET_REGISTRY[name]`.
- No lazy loader is retained.

Practical consequence:

- If the registration function creates or downloads a dataset, that work
  happens during import.
- Keep registration functions short, deterministic, and side-effect aware.

## Dataset wrapper classes

### `GraphormerDataset(dataset=None, dataset_spec=None, dataset_source=None, seed=0, train_idx=None, valid_idx=None, test_idx=None)`

Role:

- Routes built-in dataset names through the source lookup tables.
- Routes custom dataset objects through Graphormer DGL or PyG wrappers.

Important behavior:

- Built-in `dataset_source` values are handled by the lookup tables.
- Custom dataset objects only accept `dataset_source` values of `dgl` or `pyg`.
- After setup, the wrapper exposes:
  - `train_idx`
  - `valid_idx`
  - `test_idx`
  - `dataset_train`
  - `dataset_val`
  - `dataset_test`

### `GraphormerPYGDataset(dataset, seed=0, train_idx=None, valid_idx=None, test_idx=None, train_set=None, valid_set=None, test_set=None)`

Important behavior:

- If explicit split indices are absent, it creates a random 70/20/10 split
  from the full dataset using the provided seed.
- If source subsets are provided, it wraps them directly.
- `__getitem__` assigns `item.idx`, reshapes `item.y` to one dimension, then
  applies Graphormer preprocessing.

### `GraphormerDGLDataset(dataset, seed=0, train_idx=None, valid_idx=None, test_idx=None)`

Important behavior:

- If explicit split indices are absent, it creates a random 70/20/10 split.
- Only homogeneous graphs are accepted.
- Integer node and edge features are extracted from DGL graph data.
- Float features are ignored by the Graphormer graph construction path.
- The output is converted into a PyG-style graph item before preprocessing.

### `BatchedDataDataset(dataset, max_node=128, multi_hop_max_dist=5, spatial_pos_max=1024)`

Role:

- Wraps the split-specific dataset for fairseq batching.
- Provides the collater that forms Graphormer batch dictionaries.

Important behavior:

- `__getitem__` returns the underlying graph item.
- `collater` forwards the batch to the Graphormer collator with the configured
  node, spatial, and multi-hop limits.

### `TargetDataset(dataset)`

Role:

- Extracts target tensors from graph items.
- Stacks targets in the collater.

## Preprocessing helpers

### `preprocess_item(item)`

Expected input:

- PyG-style graph item with `edge_attr`, `edge_index`, and `x`

What it does:

- Converts integer features into a single-embedding space with a fixed offset
  scheme.
- Builds an adjacency matrix.
- Computes shortest paths and edge-path features.
- Adds the Graphormer fields used by the model.

Fields added or rewritten:

- `x`
- `attn_bias`
- `attn_edge_type`
- `spatial_pos`
- `in_degree`
- `out_degree`
- `edge_input`

## Batch schema

The Graphormer collator returns a dictionary with these keys:

| key | meaning |
| --- | --- |
| `idx` | graph indices in the batch |
| `attn_bias` | attention bias, including the graph token slot |
| `attn_edge_type` | encoded edge types for every node pair |
| `spatial_pos` | shortest-path distances |
| `in_degree` | node in-degree features |
| `out_degree` | node out-degree features |
| `x` | node features after single-embedding conversion |
| `edge_input` | truncated multi-hop edge history |
| `y` | target tensor |

## Split and padding facts

- Graphs larger than the batch node limit are dropped during collation.
- Spatial positions above the configured limit are masked with `-inf`.
- Multi-hop edge histories are sliced before padding.
- The task wrapper passes its own `max_nodes`, `multi_hop_max_dist`, and
  `spatial_pos_max` values into the batch wrapper.
