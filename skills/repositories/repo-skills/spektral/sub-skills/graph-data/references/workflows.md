# Graph Data Workflows

## Create a tiny custom dataset

```python
import numpy as np
import scipy.sparse as sp
from spektral.data import Dataset, Graph

class ToyGraphs(Dataset):
    def read(self):
        graphs = []
        for n in [3, 4]:
            x = np.eye(n, dtype="float32")
            a = sp.eye(n, dtype="float32", format="csr")
            y = np.array([1.0, 0.0], dtype="float32")
            graphs.append(Graph(x=x, a=a, y=y))
        return graphs

dataset = ToyGraphs()
```

Rules:

- `read()` must return a list of `Graph` objects.
- `download()` is optional and runs when `dataset.path` does not exist.
- Call `super().__init__(**kwargs)` if you override `__init__`; set custom fields before the call.
- For mixed mode, store the shared adjacency in `self.a` inside `read()` and return `Graph` objects without their own adjacency.

## Choose and inspect a loader

```python
from spektral.data import DisjointLoader

loader = DisjointLoader(dataset, batch_size=2, epochs=1, shuffle=False)
inputs, target = next(iter(loader))
x, a, i = inputs
print(x.shape, a.shape, i.shape, target.shape)
```

Use one quick `next(iter(loader))` check before wiring a model. This catches most mode and label-shape mistakes early.

## Single mode

Use `SingleLoader` when `len(dataset) == 1`.

```python
from spektral.data import SingleLoader

loader = SingleLoader(dataset, epochs=1)
inputs = next(iter(loader))
```

The loader returns graph matrices directly and converts SciPy sparse adjacency to TensorFlow sparse tensors.

## Disjoint mode

Use `DisjointLoader` for batches of variable-size graphs when your model can operate on a sparse disjoint union.

```python
from spektral.data import DisjointLoader

loader = DisjointLoader(dataset, batch_size=32, node_level=False)
model.fit(loader.load(), steps_per_epoch=loader.steps_per_epoch, epochs=10)
```

Set `node_level=True` when labels are per-node and should be vertically stacked across the disjoint union.

## Batch mode

Use `BatchLoader` for dense padded batches, especially dense pooling layers.

```python
from spektral.data import BatchLoader
from spektral.layers import GraphMasking

loader = BatchLoader(dataset, batch_size=32, mask=True)
```

With `mask=True`, Spektral appends a binary mask as the last node feature. In the model, start with `GraphMasking` to remove the mask feature and propagate Keras masks.

## Mixed mode

Use `MixedLoader` for one shared graph support with many graph signals.

```python
class SignalsOnOneGraph(Dataset):
    def read(self):
        self.a = shared_sparse_adjacency
        return [Graph(x=x_i, y=y_i) for x_i, y_i in samples]

loader = MixedLoader(SignalsOnOneGraph(), batch_size=32)
```

The graphs returned by `read()` must not store their own `a`; `dataset.a` is the shared adjacency.

## Apply transforms

```python
from spektral.transforms import Degree, GCNFilter, LayerPreprocess
from spektral.layers import GCNConv

max_degree = int(dataset.map(lambda g: g.a.sum(-1).max(), reduce=max))
dataset.apply(Degree(max_degree))
dataset.apply(GCNFilter())
# equivalent layer-aware pattern for layers with preprocess(a):
dataset.apply(LayerPreprocess(GCNConv))
```

Transforms mutate each graph in place through `Dataset.apply()`. Apply transforms before constructing loaders.

## Convert lists manually

For lower-level control:

```python
from spektral.data.utils import to_disjoint, to_batch, to_mixed

x, a, i = to_disjoint(x_list=[g.x for g in dataset], a_list=[g.a for g in dataset])
x_batch, a_batch = to_batch(x_list=[g.x for g in dataset], a_list=[g.a for g in dataset])
x_mixed, a_shared = to_mixed(x_list=[g.x for g in dataset], a=shared_a)
```

Manual conversion is useful for debugging shape issues or writing custom loaders.

## Smoke check

Run:

```bash
python sub-skills/graph-data/scripts/smoke_data_modes.py
```

The script constructs tiny in-memory datasets and validates loader shapes, `Degree`, `filter`, and `LayerPreprocess` without downloading data.
