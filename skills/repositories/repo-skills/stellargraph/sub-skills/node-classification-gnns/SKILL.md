---
name: node-classification-gnns
description: "Guides StellarGraph supervised and semi-supervised node
  classification or regression with GCN, GAT, GraphSAGE, DirectedGraphSAGE,
  HinSAGE, Cluster-GCN, RGCN, PPNP, APPNP, and Keras heads."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Node Classification GNNs

Use this sub-skill for StellarGraph workflows that predict node labels or node
attributes with TensorFlow/Keras graph neural networks.

## Read first

- [`references/model-reference.md`](references/model-reference.md) for verified
  model constructors, generator pairings, and major decision points.
- [`references/workflows.md`](references/workflows.md) for end-to-end GCN,
  GraphSAGE, HinSAGE, directed, cluster, relational, PPNP/APPNP, and SGC-style
  node workflows.
- [`references/troubleshooting.md`](references/troubleshooting.md) when shape,
  generator/model pairing, sparse/dense adjacency, labels, directedness, or
  heterogeneity fails.
- [`scripts/gcn_node_smoke.py`](scripts/gcn_node_smoke.py) for a safe tiny GCN
  graph/model wiring check without downloads or training.

## Route here when the user asks to

- classify or regress node attributes using `GCN`, `GAT`, `GraphSAGE`,
  `DirectedGraphSAGE`, `HinSAGE`, `RGCN`, `PPNP`, `APPNP`, Cluster-GCN, or SGC;
- choose a node generator/model pairing;
- add a Keras Dense prediction head to a StellarGraph model tensor;
- debug target labels, one-hot encoding, train/test node IDs, or node model
  output shapes;
- adapt a Cora/PubMed/MovieLens/AIFB-style node classification notebook into a
  smaller reusable workflow.

## Route elsewhere

- Raw graph construction, node features, and built-in datasets:
  [`../graph-data-loading/SKILL.md`](../graph-data-loading/SKILL.md).
- Generator internals and `flow` shape inspection:
  [`../sampling-generators/SKILL.md`](../sampling-generators/SKILL.md).
- Link prediction and KG completion:
  [`../link-prediction-kg/SKILL.md`](../link-prediction-kg/SKILL.md).
- Unsupervised embedding pretraining or extraction:
  [`../embedding-workflows/SKILL.md`](../embedding-workflows/SKILL.md).
- Calibration, ensembles, saved-model loading, or saliency after training:
  [`../model-ops-interpretability/SKILL.md`](../model-ops-interpretability/SKILL.md).

## Operating workflow

1. Build and validate a `StellarGraph`/`StellarDiGraph` with numeric node
   features and node IDs that match the target labels.
2. Split labels with Pandas/scikit-learn. Keep labels outside graph node features
   unless deliberately using them as additional features.
3. Select the model/generator pair:
   - `GCN`, `GAT`, `PPNP`, `APPNP`: `FullBatchNodeGenerator` on homogeneous
     graphs;
   - Cluster-GCN: `ClusterNodeGenerator` plus `GCN` for larger homogeneous
     graphs;
   - `GraphSAGE`: `GraphSAGENodeGenerator` for sampled inductive homogeneous
     graphs;
   - `DirectedGraphSAGE`: directed GraphSAGE generator with in/out samples;
   - `HinSAGE`: `HinSAGENodeGenerator` for heterogeneous graphs;
   - `RGCN`: `RelationalFullBatchNodeGenerator` for relational edge types.
4. Instantiate the model stack and call `in_out_tensors()` or `default_model()`
   as appropriate.
5. Add a Keras prediction head when the model stack returns embeddings rather
   than class logits.
6. Compile with a Keras optimizer, loss, and metrics compatible with target
   encoding.
7. Inspect one generator batch and one model output shape before running a long
   training job.

## Minimal GCN wiring pattern

```python
import tensorflow as tf
from stellargraph.mapper import FullBatchNodeGenerator
from stellargraph.layer import GCN

generator = FullBatchNodeGenerator(graph, method="gcn")
gcn = GCN(layer_sizes=[16, 16], generator=generator, activations=["relu", "relu"])
x_inp, x_out = gcn.in_out_tensors()
predictions = tf.keras.layers.Dense(units=num_classes, activation="softmax")(x_out)
model = tf.keras.Model(inputs=x_inp, outputs=predictions)
model.compile(optimizer="adam", loss="categorical_crossentropy", metrics=["accuracy"])
model.fit(generator.flow(train_node_ids, train_targets), epochs=epochs)
```

## Safe check

```bash
python sub-skills/node-classification-gnns/scripts/gcn_node_smoke.py --help
python sub-skills/node-classification-gnns/scripts/gcn_node_smoke.py
```

The script verifies graph construction, `FullBatchNodeGenerator`, `GCN`, and a
Keras Dense head on a tiny synthetic graph. It does not download Cora or train a
full notebook model.
