# DGL Dataset and IO Workflows

## Build a Custom `DGLDataset`

Use `dgl.data.DGLDataset` when the user has raw files or generated arrays and wants a reusable dataset object.

Skeleton:

```python
import os
import dgl
import torch
from dgl.data import DGLDataset
from dgl.data.utils import load_info, save_info

class MyDataset(DGLDataset):
    def __init__(self, raw_dir=None, save_dir=None, force_reload=False, transform=None):
        super().__init__(
            name="my_dataset",
            raw_dir=raw_dir,
            save_dir=save_dir,
            hash_key=("v1",),
            force_reload=force_reload,
            verbose=True,
            transform=transform,
        )

    def process(self):
        src = torch.tensor([0, 1, 2])
        dst = torch.tensor([1, 2, 0])
        graph = dgl.graph((src, dst), num_nodes=3)
        graph.ndata["feat"] = torch.eye(3)
        graph.ndata["label"] = torch.tensor([0, 1, 0])
        graph.ndata["train_mask"] = torch.tensor([True, True, False])
        graph.ndata["val_mask"] = torch.tensor([False, False, True])
        graph.ndata["test_mask"] = torch.tensor([False, False, True])
        self.graphs = [graph]
        self.labels = torch.tensor([0])
        self.num_classes = 2

    def __getitem__(self, idx):
        graph = self.graphs[idx]
        if self._transform is not None:
            graph = self._transform(graph)
        return graph, self.labels[idx]

    def __len__(self):
        return len(self.graphs)

    def save(self):
        os.makedirs(self.save_path, exist_ok=True)
        dgl.save_graphs(os.path.join(self.save_path, "graphs.bin"), self.graphs, {"labels": self.labels})
        save_info(os.path.join(self.save_path, "info.pkl"), {"num_classes": self.num_classes})

    def load(self):
        self.graphs, label_dict = dgl.load_graphs(os.path.join(self.save_path, "graphs.bin"))
        self.labels = label_dict["labels"]
        self.num_classes = load_info(os.path.join(self.save_path, "info.pkl"))["num_classes"]

    def has_cache(self):
        graph_path = os.path.join(self.save_path, "graphs.bin")
        info_path = os.path.join(self.save_path, "info.pkl")
        return os.path.exists(graph_path) and os.path.exists(info_path)
```

Validation steps:

1. Instantiate with `force_reload=True` once and confirm `len(dataset)` plus one item.
2. Instantiate again with `force_reload=False` and confirm it loads from cache.
3. Check every tensor length: node data length equals `g.num_nodes()`, edge data length equals `g.num_edges()`, graph labels length equals `len(dataset)`.
4. Check split masks are boolean and non-empty where the downstream task expects samples.
5. Change `hash_key` when preprocessing options change graph structure, labels, masks, features, or splits.

## `DGLDataset` Lifecycle Rules

During `__init__`, `DGLDataset` runs this flow:

1. If `force_reload=False` and `has_cache()` is true, call `load()`.
2. If `load()` fails, DGL falls back to downloading, processing, and saving.
3. If no valid cache exists, call `download()` when `url` is provided.
4. Call `process()`.
5. Call `save()`.

Implementations should respect these conventions:

- `process()` builds `DGLGraph` objects and attaches features, labels, and masks.
- `__getitem__()` applies `self._transform` on access if a transform was provided.
- `save()` writes only processed artifacts, usually under `self.save_path`.
- `load()` restores every attribute that `__getitem__`, properties, and training code need.
- `has_cache()` returns true only when every file required by `load()` exists.
- `download()` writes under `self.raw_dir` or `self.raw_path` and should verify hashes when available.

## Save and Load Graph Caches

For a standalone cache without a custom dataset class:

```python
import dgl
import torch

graph = dgl.graph(([0, 1], [1, 2]), num_nodes=3)
graph.ndata["feat"] = torch.ones(3, 4)
graph.edata["weight"] = torch.tensor([0.5, 0.7])
labels = {"label": torch.tensor([1])}

dgl.save_graphs("cache/graphs.bin", [graph], labels=labels)
graphs, label_dict = dgl.load_graphs("cache/graphs.bin")
```

Use `save_info()` / `load_info()` for metadata that is not tensor graph data:

```python
from dgl.data.utils import save_info, load_info

save_info("cache/info.pkl", {"num_classes": 3, "feature_name": "feat"})
info = load_info("cache/info.pkl")
```

Avoid serializing batched graphs directly. Use `dgl.unbatch()` first and store graph-level labels separately.

## Load a `CSVDataset`

1. Create the folder with `meta.yaml` plus CSVs.
2. Run the bundled linter:

```bash
python scripts/csv_dataset_linter.py path/to/dataset
```

3. Load with DGL:

```python
import dgl

dataset = dgl.data.CSVDataset("path/to/dataset", force_reload=True)
graph_or_pair = dataset[0]
```

4. Inspect the result:

```python
if isinstance(graph_or_pair, tuple):
    graph, graph_data = graph_or_pair
else:
    graph = graph_or_pair
    graph_data = None
print(graph)
print(graph.ndata.keys())
print(graph.edata.keys())
```

5. Reload without reparsing after the cache is correct:

```python
dataset = dgl.data.CSVDataset("path/to/dataset", force_reload=False)
```

Use `force_reload=True` after editing any CSV, `meta.yaml`, or parser logic. `CSVDataset` caches the parsed graphs as `<dataset_name>.bin` under a processed save path derived from the dataset folder.

## Use Custom Parsers for Non-Numeric CSV Columns

The default CSV parser expects numerical scalars, booleans, or list-like strings. Use custom parsers for categorical labels, missing values, JSON payloads, or string features.

```python
import numpy as np
import pandas as pd

class NodeParser:
    def __call__(self, frame: pd.DataFrame):
        out = {}
        if "label" in frame:
            labels = frame.pop("label").map({"negative": 0, "positive": 1})
            out["label"] = labels.to_numpy(dtype=np.int64)
        for column in frame:
            out[column] = frame[column].to_numpy()
        return out

dataset = dgl.data.CSVDataset(
    "path/to/dataset",
    force_reload=True,
    ndata_parser=NodeParser(),
)
```

For heterographs, `ndata_parser` can be a dict keyed by node type string, and `edata_parser` can be a dict keyed by canonical edge type tuple such as `("user", "buys", "item")`.

## Choose Between `DGLDataset`, `CSVDataset`, and GraphBolt `OnDiskDataset`

Use `DGLDataset` when:

- The raw format is arbitrary or needs preprocessing code.
- You need custom downloads, transforms, generated splits, or multiple derived caches.
- The dataset should expose properties such as `num_classes` or vocabulary metadata.

Use `CSVDataset` when:

- Data can be represented as node, edge, and optional graph CSVs.
- Feature columns are numeric or can be handled with small custom parsers.
- The result is a list of in-memory `DGLGraph` objects.

Use GraphBolt `OnDiskDataset` when:

- The graph/features are large and intended for minibatch streaming.
- The data is already organized as graph structure files, feature arrays, and task sets.
- The next step is GraphBolt `ItemSet`, `ItemSampler`, or `DataLoader`; route execution to `dataloading-graphbolt`.

Use distributed partition tools when:

- The next artifact is a partition book, `part_config`, or multi-machine training layout; route to `distributed-tools`.

## Built-In Dataset Caveats

Built-in datasets are convenient but often download from DGL-hosted URLs or third-party mirrors.

Checklist before using a built-in dataset in an agent task:

- Ask whether network access is allowed if the dataset is not already cached.
- Prefer explicit `raw_dir=` so cache location is predictable.
- Use `force_reload=True` only when refreshing a corrupt or outdated cache.
- Use `transform=` for lightweight graph transforms at access time; do not mutate cached graphs unless intended.
- Verify expected node/edge counts, feature keys, label keys, and mask keys before connecting to training code.
- For local-only or synthetic datasets, prefer deterministic seeds where the class exposes one.

## Prepare CSV for DGL-Go

This sub-skill validates CSV structure; DGL-Go command details belong to `dglgo-cli`.

Handoff checklist:

1. `meta.yaml` passes the linter.
2. The dataset is homogeneous or all heterograph `ntype`/`etype` values are explicit.
3. Feature, label, and mask columns are named and documented.
4. A quick `dgl.data.CSVDataset(..., force_reload=True)` load succeeds in Python.
5. Any custom parser needs are resolved before relying on DGL-Go configuration.

## Native Verification Candidates

Safe native-style checks to adapt after integration:

- Graph serialization roundtrip: save multiple homogeneous and heterogeneous graphs with node/edge features and labels, reload selected indices, compare features and canonical edge types.
- `DGLDataset` cache fallback: create a tiny custom dataset whose `has_cache()` requires both `graphs.bin` and `info.pkl`; delete one file and verify `force_reload=False` reprocesses rather than returning a partial object.
- CSV tiny fixtures: homogeneous, heterograph, and multi-graph folders with quoted vector features and masks.

Skip downloadable built-in datasets unless the user explicitly allows network and time cost.
