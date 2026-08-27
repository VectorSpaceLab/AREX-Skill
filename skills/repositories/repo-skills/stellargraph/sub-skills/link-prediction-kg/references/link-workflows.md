# Link Prediction Workflows

## Leakage-safe split pattern

`EdgeSplitter` can remove positive edges and sample negative examples. A common
pattern is to create a test split first, then a train split from the remaining
graph, so train edges do not include held-out positives.

```python
from stellargraph.data import EdgeSplitter

edge_splitter_test = EdgeSplitter(graph)
graph_test, edge_ids_test, edge_labels_test = edge_splitter_test.train_test_split(
    p=0.1, method="global", keep_connected=True, seed=7
)

edge_splitter_train = EdgeSplitter(graph_test, graph)
graph_train, edge_ids_train, edge_labels_train = edge_splitter_train.train_test_split(
    p=0.1, method="global", keep_connected=True, seed=8
)
```

Use `keep_connected=True` for homogeneous connected graphs when breaking
connectivity would invalidate the downstream model. If there are not enough
removable edges, lower `p` or relax connectivity only with an explicit reason.

## GCN-style full-batch link classification

```python
import tensorflow as tf
from stellargraph.mapper import FullBatchLinkGenerator
from stellargraph.layer import GCN, link_classification

generator = FullBatchLinkGenerator(graph_train, method="gcn")
gcn = GCN([16, 16], generator=generator, activations=["relu", "relu"])
x_inp, x_out = gcn.in_out_tensors()
pred = link_classification(output_dim=1, output_act="sigmoid", edge_embedding_method="ip")(x_out)
model = tf.keras.Model(inputs=x_inp, outputs=pred)
model.compile(optimizer="adam", loss="binary_crossentropy", metrics=["accuracy"])
model.fit(generator.flow(edge_ids_train, edge_labels_train), epochs=5)
```

`FullBatchLinkGenerator` passes node-pair output indices into the full-batch GCN
embedding tensor. Use the same generator for model construction and flow.

## GraphSAGE link prediction

Use GraphSAGE for sampled/inductive homogeneous link prediction:

```python
from stellargraph.mapper import GraphSAGELinkGenerator
from stellargraph.layer import GraphSAGE, link_classification

generator = GraphSAGELinkGenerator(graph_train, batch_size=32, num_samples=[10, 5])
graphsage = GraphSAGE([32, 32], generator=generator, bias=True, dropout=0.5)
x_inp, x_out = graphsage.in_out_tensors()
pred = link_classification(output_dim=1, output_act="sigmoid", edge_embedding_method="ip")(x_out)
```

`num_samples` must match the GraphSAGE layer count.

## HinSAGE link prediction

Use `HinSAGELinkGenerator` and `HinSAGE` when source and target nodes are
heterogeneous, such as user-movie rating prediction.

```python
from stellargraph.mapper import HinSAGELinkGenerator
from stellargraph.layer import HinSAGE, link_regression

generator = HinSAGELinkGenerator(
    graph, batch_size=32, num_samples=[8, 4], head_node_types=["user", "movie"]
)
hinsage = HinSAGE([32, 32], generator=generator, dropout=0.5)
x_inp, x_out = hinsage.in_out_tensors()
pred = link_regression(output_dim=1, clip_limits=(1, 5), edge_embedding_method="ip")(x_out)
```

Use regression heads for ratings or numeric edge attributes; use classification
heads for binary or multiclass edge labels.

## Embedding-based link prediction

Node2Vec, Metapath2Vec, GraphWave, Attri2Vec, and GraphSAGE unsupervised
embeddings can be used as features for downstream scikit-learn link classifiers.
Use the embedding route to generate embeddings, then build edge features such as
Hadamard, average, absolute difference, or weighted L1/L2 combinations.

## Temporal link prediction

For CTDNE-style workflows, generate time-respecting walks with `TemporalRandomWalk`,
train node embeddings, then create link features for a downstream classifier.
Do not use static random walks when the task requires temporal edge ordering.
