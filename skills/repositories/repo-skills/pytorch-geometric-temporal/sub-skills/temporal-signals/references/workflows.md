# Workflow Recipes

These recipes use only NumPy arrays and the public `torch_geometric_temporal.signal` package. They do not require a source checkout.

## Shared helper block

Use the same tiny helpers in every recipe if you want reproducible values and easy shape checks:

```python
import numpy as np
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

RELATION = ("author", "writes", "paper")


def cycle_edge_index(num_nodes: int) -> np.ndarray:
    src = np.arange(num_nodes, dtype=np.int64)
    dst = np.roll(src, -1)
    return np.stack([src, dst], axis=0)


def matrix(time: int, rows: int, cols: int, offset: float = 0.0) -> np.ndarray:
    base = np.arange(rows * cols, dtype=np.float32).reshape(rows, cols)
    return base + np.float32(time + offset)


def labels(time: int, rows: int, offset: int = 0) -> np.ndarray:
    return np.arange(rows, dtype=np.int64) + time + offset
```

## 1) StaticGraphTemporalSignal

Use this when the graph is fixed and only node features, targets, or optional per-snapshot arrays change.

```python
edge_index = cycle_edge_index(3)
edge_weight = np.array([1.0, 0.5, 0.25], dtype=np.float32)
features = [matrix(t, 3, 2) for t in range(4)]
targets = [labels(t, 3) for t in range(4)]
aux = [matrix(t, 3, 1) for t in range(4)]

signal = StaticGraphTemporalSignal(edge_index, edge_weight, features, targets, aux=aux)
first = signal[0]

assert signal.snapshot_count == 4
assert first.x.shape == (3, 2)
assert first.edge_index.shape == (2, 3)
assert first.edge_attr.shape == (3,)
assert first.y.shape == (3,)
assert first.aux.shape == (3, 1)
```

Use this pattern for static-road, static-spatial, or any other fixed-topology temporal graph.

## 2) DynamicGraphTemporalSignal

Use this when edges and weights can change with time, and features/targets also change.

```python
edge_indices = [cycle_edge_index(3) for _ in range(4)]
edge_weights = [np.array([1.0, 0.5, 0.25], dtype=np.float32) + np.float32(t) for t in range(4)]
features = [matrix(t, 3, 2) for t in range(4)]
targets = [labels(t, 3) for t in range(4)]
aux = [matrix(t, 3, 1) for t in range(4)]

signal = DynamicGraphTemporalSignal(edge_indices, edge_weights, features, targets, aux=aux)
second = signal[1]

assert signal.snapshot_count == 4
assert second.edge_index.shape == (2, 3)
assert second.edge_attr.shape == (3,)
assert second.x.shape == (3, 2)
assert second.y.shape == (3,)
assert second.aux.shape == (3, 1)
```

The temporal lists must all have the same snapshot count.

## 3) DynamicGraphStaticSignal

Use this when the node feature matrix is fixed, but edges, edge weights, or targets vary over time.

```python
edge_indices = [cycle_edge_index(3) for _ in range(4)]
edge_weights = [np.array([1.0, 0.5, 0.25], dtype=np.float32) + np.float32(t) for t in range(4)]
feature = matrix(0, 3, 2)
targets = [labels(t, 3) for t in range(4)]
aux = [matrix(t, 3, 1) for t in range(4)]

signal = DynamicGraphStaticSignal(edge_indices, edge_weights, feature, targets, aux=aux)
third = signal[2]

assert signal.snapshot_count == 4
assert third.x.shape == (3, 2)
assert third.edge_index.shape == (2, 3)
assert third.edge_attr.shape == (3,)
assert third.y.shape == (3,)
assert third.aux.shape == (3, 1)
```

Use this for time-varying structure with one shared feature matrix.

## 4) Homogeneous batch

Use the batch variants when each snapshot already contains multiple disjoint graphs encoded by a `batch` vector.

```python
edge_index = np.array([[0, 1, 2, 3], [1, 0, 3, 2]], dtype=np.int64)
edge_weight = np.array([1.0, 1.0, 1.0, 1.0], dtype=np.float32)
batch = np.array([0, 0, 1, 1], dtype=np.int64)
features = [matrix(t, 4, 2) for t in range(4)]
targets = [labels(t, 4) for t in range(4)]
aux = [matrix(t, 4, 1) for t in range(4)]

signal = StaticGraphTemporalSignalBatch(edge_index, edge_weight, features, targets, batch, aux=aux)
snapshot = signal[0]

assert signal.snapshot_count == 4
assert snapshot.x.shape == (4, 2)
assert snapshot.edge_index.shape == (2, 4)
assert snapshot.batch.shape == (4,)
assert snapshot.y.shape == (4,)
assert snapshot.aux.shape == (4, 1)
```

If the batch membership changes over time, switch to `DynamicGraphTemporalSignalBatch` and pass a list of batch vectors.

## 5) Heterogeneous signal

Use this when node and edge types are represented by dictionaries.

```python
edge_index_dict = {RELATION: np.array([[0, 1], [0, 2]], dtype=np.int64)}
edge_weight_dict = {RELATION: np.array([1.0, 0.5], dtype=np.float32)}
feature_dicts = [
    {"author": matrix(t, 2, 2), "paper": matrix(t + 10, 3, 2)}
    for t in range(4)
]
target_dicts = [
    {"author": labels(t, 2), "paper": labels(t + 10, 3)}
    for t in range(4)
]
aux = [
    {"author": matrix(t, 2, 1), "paper": matrix(t + 10, 3, 1)}
    for t in range(4)
]

signal = StaticHeteroGraphTemporalSignal(edge_index_dict, edge_weight_dict, feature_dicts, target_dicts, aux=aux)
snapshot = signal[0]

assert signal.snapshot_count == 4
assert snapshot["author"].x.shape == (2, 2)
assert snapshot["paper"].y.shape == (3,)
assert snapshot[RELATION].edge_index.shape == (2, 2)
assert snapshot["author"].aux.shape == (2, 1)
assert snapshot["paper"].aux.shape == (3, 1)
```

For dynamic heterogeneous graphs, wrap the edge, feature, and target dictionaries in lists and use `DynamicHeteroGraphTemporalSignal`.

## 6) Heterogeneous batch

Use the hetero batch variants when each snapshot contains multiple disjoint hetero graphs and you need per-type batch vectors.

```python
edge_index_dict = {RELATION: np.array([[0, 1, 2, 3], [0, 2, 3, 5]], dtype=np.int64)}
edge_weight_dict = {RELATION: np.array([1.0, 0.5, 1.5, 0.75], dtype=np.float32)}
batch_dict = {
    "author": np.array([0, 0, 1, 1], dtype=np.int64),
    "paper": np.array([0, 0, 0, 1, 1, 1], dtype=np.int64),
}
feature_dicts = [
    {"author": matrix(t, 4, 2), "paper": matrix(t + 10, 6, 2)}
    for t in range(4)
]
target_dicts = [
    {"author": labels(t, 4), "paper": labels(t + 10, 6)}
    for t in range(4)
]
aux = [
    {"author": matrix(t, 4, 1), "paper": matrix(t + 10, 6, 1)}
    for t in range(4)
]

signal = StaticHeteroGraphTemporalSignalBatch(edge_index_dict, edge_weight_dict, feature_dicts, target_dicts, batch_dict, aux=aux)
snapshot = signal[0]

assert signal.snapshot_count == 4
assert snapshot["author"].x.shape == (4, 2)
assert snapshot["paper"].x.shape == (6, 2)
assert snapshot["author"].batch.shape == (4,)
assert snapshot["paper"].batch.shape == (6,)
assert snapshot[RELATION].edge_index.shape == (2, 4)
```

If batch memberships can change over time, switch to `DynamicHeteroGraphTemporalSignalBatch` and supply a list of batch dictionaries.

## 7) Slicing

Use integer or slice access to extract a window without shuffling.

```python
signal = DynamicGraphTemporalSignal(
    [cycle_edge_index(3) for _ in range(4)],
    [np.array([1.0, 0.5, 0.25], dtype=np.float32) for _ in range(4)],
    [matrix(t, 3, 2) for t in range(4)],
    [labels(t, 3) for t in range(4)],
)

window = signal[1:3]
first = window[0]

assert window.snapshot_count == 2
assert first.x.shape == (3, 2)
assert first.y.shape == (3,)
```

Slice access returns a new iterator of the same class, with the requested time window only.

## 8) temporal_signal_split

Use this when you want a chronological train/test split.

```python
signal = StaticGraphTemporalSignal(
    cycle_edge_index(3),
    np.array([1.0, 0.5, 0.25], dtype=np.float32),
    [matrix(t, 3, 2) for t in range(4)],
    [labels(t, 3) for t in range(4)],
)

train, test = temporal_signal_split(signal, train_ratio=0.5)

assert train.snapshot_count + test.snapshot_count == signal.snapshot_count
assert train.snapshot_count > 0
assert test.snapshot_count > 0
```

The split preserves order and truncates with `int(train_ratio * snapshot_count)`, so small ratios can produce an empty side. If you need a guaranteed non-empty split, check the counts first or slice manually.
