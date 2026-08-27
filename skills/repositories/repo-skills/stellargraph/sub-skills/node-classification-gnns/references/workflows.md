# Node Classification Workflows

## Full-batch GCN/GAT/PPNP/APPNP

Use this pattern for small to medium homogeneous graphs where the model can see
the full adjacency during each update.

```python
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelBinarizer
import tensorflow as tf
from stellargraph.mapper import FullBatchNodeGenerator
from stellargraph.layer import GCN

train_ids, test_ids = train_test_split(targets.index, train_size=0.5, random_state=7)
encoder = LabelBinarizer()
train_targets = encoder.fit_transform(targets.loc[train_ids])
test_targets = encoder.transform(targets.loc[test_ids])

generator = FullBatchNodeGenerator(graph, method="gcn", sparse=True)
gcn = GCN([16, 16], generator=generator, activations=["relu", "relu"], dropout=0.5)
x_inp, x_out = gcn.in_out_tensors()
pred = tf.keras.layers.Dense(train_targets.shape[1], activation="softmax")(x_out)
model = tf.keras.Model(inputs=x_inp, outputs=pred)
model.compile("adam", loss="categorical_crossentropy", metrics=["accuracy"])
model.fit(generator.flow(train_ids, train_targets), epochs=5)
model.evaluate(generator.flow(test_ids, test_targets))
```

Swap `GCN` for `GAT`, `PPNP`, or `APPNP` only after selecting the matching
constructor parameters and generator `method`/sparse settings.

## Sampled GraphSAGE

Use GraphSAGE for inductive or larger homogeneous graphs where mini-batch
neighborhood sampling is preferable.

```python
from stellargraph.mapper import GraphSAGENodeGenerator
from stellargraph.layer import GraphSAGE

generator = GraphSAGENodeGenerator(graph, batch_size=50, num_samples=[10, 5])
model_stack = GraphSAGE(layer_sizes=[32, 32], generator=generator, bias=True, dropout=0.5)
x_inp, x_out = model_stack.in_out_tensors()
```

`num_samples` has one entry per GraphSAGE layer. The generator samples neighbors
of each head node in each batch; it requires node features.

## Directed GraphSAGE

Use `DirectedGraphSAGE` and the directed generator when edge direction is part
of the task. Supply separate incoming and outgoing sample counts:

```python
from stellargraph.mapper import DirectedGraphSAGENodeGenerator
from stellargraph.layer import DirectedGraphSAGE

generator = DirectedGraphSAGENodeGenerator(
    graph, batch_size=32, in_samples=[5, 5], out_samples=[5, 5]
)
model_stack = DirectedGraphSAGE([32, 32], generator=generator)
```

## HinSAGE for heterogeneous graphs

Use HinSAGE when the prediction target is a node type inside a heterogeneous
network.

```python
from stellargraph.mapper import HinSAGENodeGenerator
from stellargraph.layer import HinSAGE

generator = HinSAGENodeGenerator(
    graph, batch_size=32, num_samples=[8, 4], head_node_type="user"
)
hinsage = HinSAGE([32, 32], generator=generator, dropout=0.5)
x_inp, x_out = hinsage.in_out_tensors()
```

If `head_node_type` is omitted, inference may fail when target IDs are not
sufficient to infer a single type. Heterogeneous feature dimensions and relation
schema also constrain valid architectures.

## Cluster-GCN path

The installed API marks `ClusterGCN` as deprecated. For new guidance, use
`ClusterNodeGenerator` with `GCN`:

```python
from stellargraph.mapper import ClusterNodeGenerator
from stellargraph.layer import GCN

generator = ClusterNodeGenerator(graph, clusters=10, q=1, lam=0.1)
gcn = GCN([32, 32], generator=generator, activations=["relu", "relu"])
```

Use this path for larger homogeneous graphs where cluster sampling gives a
scalable approximation to full-batch GCN-style training.

## RGCN for relational graphs

Use RGCN when edge relation types should be modeled directly:

```python
from stellargraph.mapper import RelationalFullBatchNodeGenerator
from stellargraph.layer import RGCN

generator = RelationalFullBatchNodeGenerator(graph, sparse=True)
rgcn = RGCN([16, 16], generator=generator, num_bases=0, activations=["relu", "relu"])
x_inp, x_out = rgcn.in_out_tensors()
```

RGCN examples often use RDF/knowledge-graph-like datasets. Keep relation types
clean and verify graph schema before fitting.

## SGC-style workflow

Simplified Graph Convolution in StellarGraph examples is a simplified GCN-style
workflow. Treat it as a linearized GCN/propagation recipe rather than searching
for a standalone public `SGC` model class in this package version.
