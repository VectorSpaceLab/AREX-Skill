# Datasets and Transforms

PyG 2.9 dataset work is centered on `torch_geometric.data.Dataset`, `torch_geometric.data.InMemoryDataset`, `torch_geometric.data.Data`, `torch_geometric.data.HeteroData`, and transforms from `torch_geometric.transforms`.

Use this reference for local, safe, self-contained datasets. Do not copy download-heavy public dataset examples into agent runtime content unless the user explicitly requests download behavior.

## Choose the Dataset Base Class

Use `InMemoryDataset` when all processed graphs fit in CPU memory:

- Implement `raw_file_names`, `processed_file_names`, `download`, and `process` as needed.
- In `process`, build a list of `Data` or `HeteroData` objects.
- Apply `pre_filter` before `pre_transform`.
- Persist with `self.save(data_list, self.processed_paths[0])`.
- In `__init__`, call `self.load(self.processed_paths[0])` after `super().__init__(...)`.

Use `Dataset` when graphs are too large to collate or should be loaded individually:

- Implement `len()` and `get(idx)`.
- Save each processed graph separately in `process`.
- Load one graph in `get(idx)`.

Constructor facts for PyG 2.9:

```python
Dataset(root=None, transform=None, pre_transform=None, pre_filter=None, log=True, force_reload=False)
InMemoryDataset(root=None, transform=None, pre_transform=None, pre_filter=None, log=True, force_reload=False)
```

## Local `InMemoryDataset` Skeleton

This pattern avoids downloads by treating the `raw` directory as optional local input and falling back to synthetic fixtures:

```python
from pathlib import Path
import torch
from torch_geometric.data import Data, InMemoryDataset

class TinyGraphDataset(InMemoryDataset):
    def __init__(self, root, transform=None, pre_transform=None, pre_filter=None, force_reload=False):
        super().__init__(root, transform=transform, pre_transform=pre_transform,
                         pre_filter=pre_filter, force_reload=force_reload)
        self.load(self.processed_paths[0])

    @property
    def raw_file_names(self):
        return []

    @property
    def processed_file_names(self):
        return "data.pt"

    def download(self):
        return None

    def process(self):
        data_list = [
            Data(
                x=torch.eye(3),
                edge_index=torch.tensor([[0, 1, 2], [1, 2, 0]], dtype=torch.long),
                y=torch.tensor([0]),
            )
        ]
        for data in data_list:
            data.validate(raise_on_error=True)
        if self.pre_filter is not None:
            data_list = [data for data in data_list if self.pre_filter(data)]
        if self.pre_transform is not None:
            data_list = [self.pre_transform(data) for data in data_list]
        self.save(data_list, self.processed_paths[0])
```

Usage:

```python
import tempfile
import torch_geometric.transforms as T

with tempfile.TemporaryDirectory() as root:
    dataset = TinyGraphDataset(root, pre_transform=T.ToUndirected())
    assert len(dataset) == 1
    assert dataset[0].is_undirected()
```

## `transform`, `pre_transform`, and `pre_filter`

- `transform` runs when a data object is accessed, after loading. Use it for cheap, stochastic, or training-time changes.
- `pre_transform` runs once during processing, before saving. Use it for deterministic heavy preprocessing that should be cached.
- `pre_filter` runs once during processing to drop graphs before saving.
- If `pre_transform` or `pre_filter` changes after data was processed, PyG warns that the cached representation was built with a different function. Pass `force_reload=True` to rebuild intentionally.

Ordering in `process` should usually be:

```python
if self.pre_filter is not None:
    data_list = [data for data in data_list if self.pre_filter(data)]
if self.pre_transform is not None:
    data_list = [self.pre_transform(data) for data in data_list]
self.save(data_list, self.processed_paths[0])
```

Validate before and after transforms when transforms modify structure:

```python
data.validate(raise_on_error=True)
data = transform(data)
data.validate(raise_on_error=True)
```

## Common Transform Workflows

Import transforms as a namespace so recipes are readable:

```python
import torch_geometric.transforms as T
```

Feature and structure transforms:

```python
transform = T.Compose([
    T.ToUndirected(),
    T.NormalizeFeatures(),
])
data = transform(data)
```

Node splits:

```python
from torch_geometric.transforms import RandomNodeSplit

splitter = RandomNodeSplit(split="train_rest", num_val=0.1, num_test=0.2)
data = splitter(data)
assert data.train_mask.dtype == torch.bool
assert data.val_mask.size(0) == data.num_nodes
assert data.test_mask.size(0) == data.num_nodes
```

Link splits:

```python
from torch_geometric.transforms import RandomLinkSplit

splitter = RandomLinkSplit(
    num_val=0.1,
    num_test=0.2,
    is_undirected=True,
    add_negative_train_samples=True,
)
train_data, val_data, test_data = splitter(data)
for split in (train_data, val_data, test_data):
    split.validate(raise_on_error=True)
```

For hetero link splitting, pass `edge_types` and, when reverse edges exist, `rev_edge_types` so the transform keeps forward and reverse edges synchronized.

## Local Data Layouts

PyG dataset roots conventionally contain:

```text
root/
  raw/
    ... user-provided source files ...
  processed/
    data.pt
    pre_transform.pt
    pre_filter.pt
```

Guidelines:

- Keep `raw_file_names` and `processed_file_names` deterministic.
- Do not write outside `root` from `download` or `process`.
- In safe agent examples, make `download()` a no-op and use tiny synthetic data or user-provided local files.
- Avoid global cache directories in bundled runtime scripts.
- Use `tempfile.TemporaryDirectory()` for smoke tests.

## CSV and Tabular Loading Pattern

For local CSV-like graph construction, separate parsing from PyG object creation:

1. Read node rows into a stable node-id mapping.
2. Build `x` and optional labels in mapping order.
3. Read edge rows and map source/destination ids to integer node indices.
4. Create `edge_index = torch.tensor([src, dst], dtype=torch.long)`.
5. Create `Data` or typed `HeteroData` stores.
6. Set `num_nodes` explicitly and call `.validate(raise_on_error=True)`.
7. Add masks or split transforms only after shape validation passes.

## Synthetic Fixture Strategy

Use tiny fixtures to verify recipes without downloads:

- Homogeneous graph: 3-5 nodes, 2-4 features, a small directed cycle, optional boolean masks.
- Heterogeneous graph: two node types and one or two canonical edge types.
- Dataset fixture: one or two graphs in a temporary `InMemoryDataset` root.
- Transform fixture: `ToUndirected`, `NormalizeFeatures`, `RandomNodeSplit`, or `RandomLinkSplit` over the tiny graph.

For deeper model, loader, or hetero-model behavior, route to the sibling sub-skills instead of expanding this dataset sub-skill.
