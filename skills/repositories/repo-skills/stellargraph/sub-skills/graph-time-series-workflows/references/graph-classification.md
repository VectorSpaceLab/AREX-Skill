# Graph Classification

## Core pattern

Graph classification uses a **list of graphs** and graph-level labels. It does
not use one node label per node.

```python
from stellargraph.mapper import PaddedGraphGenerator
from stellargraph.layer import GCNSupervisedGraphClassification
import tensorflow as tf

generator = PaddedGraphGenerator(graphs=graphs)
model_stack = GCNSupervisedGraphClassification(
    layer_sizes=[32, 32],
    activations=["relu", "relu"],
    generator=generator,
    dropout=0.5,
)
x_inp, x_out = model_stack.in_out_tensors()
pred = tf.keras.layers.Dense(units=num_classes, activation="softmax")(x_out)
model = tf.keras.Model(inputs=x_inp, outputs=pred)
train_gen = generator.flow(train_graph_indices, train_targets, batch_size=16)
```

The generator's `flow` accepts graph indices/selection and graph-level targets.
Use `symmetric_normalization=True` for the default normalized adjacency path.

## DeepGraphCNN and SortPooling

`DeepGraphCNN` uses graph convolution layers plus `SortPooling` to create a
fixed-size representation from variable-size graphs.

Verified constructor:

```python
DeepGraphCNN(layer_sizes, activations, k, generator, bias=True, dropout=0.0, ...)
```

`k` controls the number of nodes retained by sort pooling. Choose it from the
graph-size distribution; if `k` is too small, important nodes may be discarded;
if too large, padding dominates.

## PaddedGraphGenerator signature

```python
PaddedGraphGenerator(graphs, name=None)
flow(
    graphs,
    targets=None,
    symmetric_normalization=True,
    weighted=False,
    batch_size=1,
    name=None,
    shuffle=False,
    seed=None,
)
```

`graphs` passed to `flow` may be selected graph indices/objects depending on the
workflow. Keep target rows aligned with this selection.

## Practical checks

- All graphs in the list should have compatible node feature dimensions.
- Targets are graph-level labels, not node labels.
- Inspect first batch shapes before model compile/fitting.
- Avoid downloading graph benchmark datasets for a smoke; create two tiny graphs
  for shape checks.
