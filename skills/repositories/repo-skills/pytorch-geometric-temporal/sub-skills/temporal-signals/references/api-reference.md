# Temporal Signal API Reference

## Purpose

Read this when you need the exact iterator constructor to use, what temporal lengths must match, what object an integer snapshot returns, and how slicing or `temporal_signal_split` behaves.

The signal iterators accept NumPy arrays or `None` values and convert snapshot contents to PyTorch/PyG tensors at access time.

## Imports

```python
from torch_geometric_temporal.signal import (
    StaticGraphTemporalSignal,
    DynamicGraphTemporalSignal,
    DynamicGraphStaticSignal,
    StaticGraphTemporalSignalBatch,
    DynamicGraphTemporalSignalBatch,
    DynamicGraphStaticSignalBatch,
    StaticHeteroGraphTemporalSignal,
    DynamicHeteroGraphTemporalSignal,
    DynamicHeteroGraphStaticSignal,
    StaticHeteroGraphTemporalSignalBatch,
    DynamicHeteroGraphTemporalSignalBatch,
    DynamicHeteroGraphStaticSignalBatch,
    temporal_signal_split,
)
```

## Select the iterator family

| Data condition | Homogeneous class | Heterogeneous class | Snapshot object on integer access |
| --- | --- | --- | --- |
| Static graph, temporal node features/targets | `StaticGraphTemporalSignal` | `StaticHeteroGraphTemporalSignal` | `Data` for homogeneous, `HeteroData` for hetero |
| Dynamic graph, temporal node features/targets | `DynamicGraphTemporalSignal` | `DynamicHeteroGraphTemporalSignal` | `Data` for homogeneous, `HeteroData` for hetero |
| Dynamic graph, one static node-feature matrix, temporal targets | `DynamicGraphStaticSignal` | `DynamicHeteroGraphStaticSignal` | `Data` for homogeneous, `HeteroData` for hetero |
| Static graph batch, temporal features/targets | `StaticGraphTemporalSignalBatch` | `StaticHeteroGraphTemporalSignalBatch` | PyG `Batch`; hetero batch is also a `HeteroData` subclass |
| Dynamic graph batch, temporal features/targets | `DynamicGraphTemporalSignalBatch` | `DynamicHeteroGraphTemporalSignalBatch` | PyG `Batch` |
| Dynamic graph batch, static features, temporal targets | `DynamicGraphStaticSignalBatch` | `DynamicHeteroGraphStaticSignalBatch` | PyG `Batch` |

Treat hetero batch snapshots as batch snapshots first: their runtime class is usually a dynamic PyG class such as `HeteroDataBatch`, which is both a `Batch` and a `HeteroData` subclass.

## Homogeneous constructors

| Class | Constructor signature | Temporal length contract | Integer snapshot fields |
| --- | --- | --- | --- |
| `StaticGraphTemporalSignal` | `(edge_index, edge_weight, features, targets, **kwargs)` | `len(features) == len(targets) == len(each extra)` | `Data(x, edge_index, edge_attr, y, **extras)` |
| `DynamicGraphTemporalSignal` | `(edge_indices, edge_weights, features, targets, **kwargs)` | `len(edge_indices) == len(edge_weights) == len(features) == len(targets) == len(each extra)` | `Data(x, edge_index, edge_attr, y, **extras)` |
| `DynamicGraphStaticSignal` | `(edge_indices, edge_weights, feature, targets, **kwargs)` | `len(edge_indices) == len(edge_weights) == len(targets) == len(each extra)` | `Data(x=feature, edge_index, edge_attr, y, **extras)` |
| `StaticGraphTemporalSignalBatch` | `(edge_index, edge_weight, features, targets, batches, **kwargs)` | `len(features) == len(targets) == len(each extra)`; `batches` is one static vector or `None` | `Batch(x, edge_index, edge_attr, y, batch, **extras)` |
| `DynamicGraphTemporalSignalBatch` | `(edge_indices, edge_weights, features, targets, batches, **kwargs)` | `len(edge_indices) == len(edge_weights) == len(features) == len(targets) == len(batches) == len(each extra)` | `Batch(x, edge_index, edge_attr, y, batch, **extras)` |
| `DynamicGraphStaticSignalBatch` | `(edge_indices, edge_weights, feature, targets, batches, **kwargs)` | `len(edge_indices) == len(edge_weights) == len(targets) == len(batches) == len(each extra)` | `Batch(x=feature, edge_index, edge_attr, y, batch, **extras)` |

## Heterogeneous constructors

Use node-type strings for feature, target, and batch dictionaries. Use relation tuples `(source_type, relation_name, destination_type)` for edge dictionaries.

| Class | Constructor signature | Temporal length contract | Integer snapshot fields |
| --- | --- | --- | --- |
| `StaticHeteroGraphTemporalSignal` | `(edge_index_dict, edge_weight_dict, feature_dicts, target_dicts, **kwargs)` | `len(feature_dicts) == len(target_dicts) == len(each extra)` | `HeteroData`; node stores get `.x`, `.y`, extras; edge stores get `.edge_index`, `.edge_attr` |
| `DynamicHeteroGraphTemporalSignal` | `(edge_index_dicts, edge_weight_dicts, feature_dicts, target_dicts, **kwargs)` | `len(edge_index_dicts) == len(edge_weight_dicts) == len(feature_dicts) == len(target_dicts) == len(each extra)` | `HeteroData` |
| `DynamicHeteroGraphStaticSignal` | `(edge_index_dicts, edge_weight_dicts, feature_dict, target_dicts, **kwargs)` | `len(edge_index_dicts) == len(edge_weight_dicts) == len(target_dicts) == len(each extra)` | `HeteroData` |
| `StaticHeteroGraphTemporalSignalBatch` | `(edge_index_dict, edge_weight_dict, feature_dicts, target_dicts, batch_dict, **kwargs)` | `len(feature_dicts) == len(target_dicts) == len(each extra)`; `batch_dict` is one static dict or `None` | hetero PyG `Batch` |
| `DynamicHeteroGraphTemporalSignalBatch` | `(edge_index_dicts, edge_weight_dicts, feature_dicts, target_dicts, batch_dicts, **kwargs)` | `len(edge_index_dicts) == len(edge_weight_dicts) == len(feature_dicts) == len(target_dicts) == len(batch_dicts) == len(each extra)` | hetero PyG `Batch` |
| `DynamicHeteroGraphStaticSignalBatch` | `(edge_index_dicts, edge_weight_dicts, feature_dict, target_dicts, batch_dicts, **kwargs)` | `len(edge_index_dicts) == len(edge_weight_dicts) == len(target_dicts) == len(batch_dicts) == len(each extra)` | hetero PyG `Batch` |

## Shape and dtype contracts

| Field | Expected shape | Conversion/result |
| --- | --- | --- |
| `edge_index` or relation value in `edge_index_dict` | `[2, num_edges]` | `torch.LongTensor`; stored as `.edge_index` |
| `edge_weight` or relation value in `edge_weight_dict` | usually `[num_edges]`; `[num_edges, edge_features]` is accepted by the iterator | `torch.FloatTensor`; stored as `.edge_attr` |
| `features[t]` / `feature` | usually `[num_nodes, num_node_features]` | `torch.FloatTensor`; stored as `.x` |
| `targets[t]` | usually `[num_nodes]` or `[num_nodes, target_dim]` | integer arrays become `torch.LongTensor`; float arrays become `torch.FloatTensor`; stored as `.y` |
| `batches` / `batches[t]` | `[num_nodes_total]` for homogeneous batches | `torch.LongTensor`; stored as `.batch` |
| `batch_dict` / `batch_dicts[t]` | node-type dict whose values are `[num_nodes_of_type]` | per-node-type `.batch` in the hetero batch snapshot |
| homogeneous `**kwargs` | each kwarg is a temporal sequence of NumPy arrays | each extra becomes a top-level `Data`/`Batch` attribute with the kwarg name |
| hetero `**kwargs` | each kwarg is a temporal sequence of node-type dictionaries or `None` | each extra becomes `snapshot[node_type][kwarg_name]` for present node types |

The iterators validate only temporal sequence lengths. They do not validate every PyG shape, node index range, relation-key alignment, or model-specific requirement before returning a snapshot.

## `None`, omitted keys, and optional attributes

- Core homogeneous fields may be `None`: a snapshot can have `snapshot.x is None`, `snapshot.edge_index is None`, `snapshot.edge_attr is None`, or `snapshot.y is None`.
- Homogeneous extra attributes passed through `**kwargs` should use arrays at every temporal step. A `None` element is not safely skipped because the iterator expects a NumPy-like `.dtype` when converting extras.
- Heterogeneous feature/target/edge/batch dictionaries may be `None` for an entire snapshot. Inside a dictionary, values set to `None` are skipped for that node or relation type.
- Heterogeneous extra attributes may use `None` for a whole temporal step or omit a node type inside a dictionary; missing extras simply are not attached for that snapshot/type.

## Access, iteration, slicing, and split

| Operation | Behavior |
| --- | --- |
| `for snapshot in iterator:` | Iterates from `t=0` to `snapshot_count - 1`; when exhausted, internal `t` resets to 0 before raising `StopIteration`. Reusing the iterator in a new `for` loop starts at 0. |
| `iterator[i]` | Returns one PyG snapshot object: `Data`, `Batch`, `HeteroData`, or hetero `Batch` depending on the class. |
| `iterator[a:b]` | Returns a new iterator object of the same class, with temporal sequences sliced by Python list/slice semantics. Static graph arrays and static feature matrices are reused, not deep-copied. |
| `iterator.snapshot_count` | Public snapshot count set at construction. Prefer this over `len(iterator)` because not every class implements `__len__`. |
| `temporal_signal_split(iterator, train_ratio=0.8)` | Computes `train_snapshots = int(train_ratio * iterator.snapshot_count)`, returns `(iterator[:train_snapshots], iterator[train_snapshots:])`, preserves chronological order, and performs no shuffle or deep copy. |

`temporal_signal_split` supports the homogeneous, batch, hetero, and hetero-batch signal classes listed above. Ratios that produce 0 training or 0 test snapshots are not blocked by the function; validate the sizes yourself when a non-empty train/test split is required.
