# Built-In Dataset Catalog

Spektral datasets are Python classes under `spektral.datasets`. Many built-in datasets download files on first use, so do not use them as no-network smoke tests unless the data cache is already present.

## Cache location

Default cache root: `~/spektral/datasets`

To customize it, create `~/.spektral/config.json`:

```json
{
  "dataset_folder": "/path/to/dataset/folder"
}
```

The built-in `Dataset.path` property joins the cache root with the dataset class name unless a subclass overrides it.

## Dataset classes

| Class | Signature | Typical task/mode | Notes |
| --- | --- | --- | --- |
| `Citation` | `(name, random_split=False, normalize_x=False, dtype=np.float32, **kwargs)` | Node classification, single mode | Parent for citation networks |
| `Cora` | `(random_split=False, normalize_x=False, **kwargs)` | Node classification, single mode | Citation dataset shortcut |
| `Citeseer` | `(random_split=False, normalize_x=False, **kwargs)` | Node classification, single mode | Citation dataset shortcut |
| `Pubmed` | `(random_split=False, normalize_x=False, **kwargs)` | Node classification, single mode | Citation dataset shortcut |
| `DBLP` | `(normalize_x=False, dtype=np.float32, **kwargs)` | Node clustering/classification, single mode | Networked dataset |
| `Flickr` | `(normalize_x=False, dtype=np.float32, **kwargs)` | Node prediction, single mode | Networked dataset |
| `GraphSage` | `(name, **kwargs)` through subclasses | Large graph data | Base class for GraphSAGE-format datasets |
| `PPI` | `(**kwargs)` | Node classification | GraphSAGE-format dataset |
| `Reddit` | `(**kwargs)` | Node classification | Large GraphSAGE-format dataset |
| `MNIST` | `(p_flip=0.0, k=8, **kwargs)` | Mixed-mode graph signal classification | Builds a grid graph from MNIST images |
| `ModelNet` | `(name, test=False, n_jobs=-1, **kwargs)` | 3D object data | Uses OFF geometry files |
| `OGB` | `(dataset, **kwargs)` | Node or graph prediction | Wraps an external OGB dataset object; requires the `ogb` package in user environment |
| `QM7` | `(**kwargs)` | Molecular regression | Downloads molecular data |
| `QM9` | `(amount=None, n_jobs=1, **kwargs)` | Molecular regression | `amount` can limit data read for experiments |
| `TUDataset` | `(name, clean=False, **kwargs)` | Graph classification | Many benchmark names; `available_datasets` lists supported names |

## Safe usage pattern

```python
from spektral.datasets import TUDataset
from spektral.data import DisjointLoader

# May download on first use.
dataset = TUDataset("PROTEINS", clean=False)
loader = DisjointLoader(dataset, batch_size=32)
```

When writing robust scripts, validate whether the cache already exists or ask before allowing first-use downloads. For smoke tests, prefer synthetic `Dataset` subclasses instead.

## OGB wrapper pattern

The `OGB` class expects an object from the Open Graph Benchmark package, not a string name:

```python
from ogb.graphproppred import GraphPropPredDataset
from spektral.datasets import OGB

ogb_dataset = GraphPropPredDataset(name="ogbg-molhiv")
dataset = OGB(ogb_dataset)
```

Do not treat `OGB("ogbg-molhiv")` as a supported shortcut.

## Dataset troubleshooting anchors

- Download/network error: verify cache path, network access, and URL availability; avoid automatic retry loops in agent smoke tests.
- Memory pressure: use a smaller dataset, dataset-specific amount/test flags, or synthetic fixtures for validation.
- Unexpected labels: inspect `dataset[0].y`, `dataset.n_labels`, and whether the selected loader expects graph-level or node-level labels.
- Mixed mode confusion: verify whether adjacency belongs in `dataset.a` rather than each graph.
