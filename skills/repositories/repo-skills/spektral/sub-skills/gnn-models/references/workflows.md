# GNN Model Workflows

## General graph classification with `GeneralGNN`

```python
from spektral.data import DisjointLoader
from spektral.models import GeneralGNN

loader = DisjointLoader(dataset_train, batch_size=32)
model = GeneralGNN(output=dataset_train.n_labels, activation="softmax")
model.compile(optimizer="adam", loss="categorical_crossentropy")
model.fit(loader.load(), steps_per_epoch=loader.steps_per_epoch, epochs=10)
```

Use this when you want a strong default GNN. Keep `pool='sum'` for graph-level outputs. Set `pool=None` for node-level outputs.

## Node prediction with `GCN`

```python
from spektral.data import SingleLoader
from spektral.models import GCN
from spektral.transforms import LayerPreprocess
from spektral.layers import GCNConv

dataset.apply(LayerPreprocess(GCNConv))
loader = SingleLoader(dataset)
model = GCN(n_labels=dataset.n_labels)
```

`GCN` is a two-layer model. It accepts `(x, a)` and also tolerates `(x, a, i)` so it can be used with disjoint loader inputs.

## Functional model with a graph convolution

```python
from tensorflow.keras import Input, Model
from tensorflow.keras.layers import Dense
from spektral.layers import GCNConv, GlobalSumPool

x_in = Input(shape=(dataset.n_node_features,))
a_in = Input(shape=(None,), sparse=True)
i_in = Input(shape=(), dtype="int64")

x = GCNConv(32, activation="relu")([x_in, a_in])
x = GlobalSumPool()([x, i_in])
out = Dense(dataset.n_labels, activation="softmax")(x)
model = Model([x_in, a_in, i_in], out)
```

This pairs naturally with `DisjointLoader`. Adjust `Input` shapes and sparse flags to match the loader output.

## Batch-mode padded model

```python
from tensorflow.keras import Input, Model
from spektral.data import BatchLoader
from spektral.layers import GraphMasking, GCNConv, GlobalSumPool

loader = BatchLoader(dataset, batch_size=32, mask=True)

x_in = Input(shape=(None, dataset.n_node_features + 1))
a_in = Input(shape=(None, None))
x = GraphMasking()(x_in)
x = GCNConv(32, activation="relu")([x, a_in])
out = GlobalSumPool()(x)
model = Model([x_in, a_in], out)
```

Use `mask=True` and `GraphMasking` together. If you do not request a mask from the loader, do not put `GraphMasking` at the input.

## Custom `MessagePassing` layer

```python
import tensorflow as tf
from spektral.layers import MessagePassing

class ToyMessagePassing(MessagePassing):
    def __init__(self, channels, **kwargs):
        super().__init__(aggregate="mean", **kwargs)
        self.channels = channels

    def build(self, input_shape):
        in_channels = input_shape[0][-1]
        self.kernel = self.add_weight(
            shape=(in_channels, self.channels),
            initializer="glorot_uniform",
            name="kernel",
        )
        self.built = True

    def call(self, inputs):
        x, a = inputs
        x = tf.matmul(x, self.kernel)
        return self.propagate(x=x, a=a)

    def message(self, x):
        return self.get_sources(x)
```

`MessagePassing` forwards matching keyword arguments from `propagate()` to `message()`, `aggregate()`, and `update()`. It sets `index_sources`, `index_targets`, and `n_nodes` before calling those hooks.

## Explain a prediction with `GNNExplainer`

```python
from spektral.models import GNNExplainer
from spektral.layers import GCNConv

explainer = GNNExplainer(model, n_hops=2, preprocess=GCNConv.preprocess)
a_mask, x_mask = explainer.explain_node(x, a, node_idx=0, epochs=100)
subgraph = explainer.plot_subgraph(a_mask, x_mask, node_idx=0)
```

Set `graph_level=True` when explaining a graph-level model. If the model uses preprocessed adjacency, pass the same preprocessing function so the explainer can recover a binary computational graph.

## Utility operations

```python
from spektral.utils.convolution import gcn_filter, normalized_adjacency
from spektral.utils.sparse import sp_matrix_to_sp_tensor

adj_preprocessed = gcn_filter(adj)
adj_tensor = sp_matrix_to_sp_tensor(adj_preprocessed)
```

Use these helpers when writing custom loaders, custom models, or tests that bypass `Dataset.apply()`.

## No-download model smoke

Run:

```bash
python sub-skills/gnn-models/scripts/smoke_models.py
```

The smoke script constructs synthetic graphs, validates `GeneralGNN`, `GCN`, `GCNConv` with batch masking, and a custom `MessagePassing` layer. It is a wiring check, not a training benchmark.
