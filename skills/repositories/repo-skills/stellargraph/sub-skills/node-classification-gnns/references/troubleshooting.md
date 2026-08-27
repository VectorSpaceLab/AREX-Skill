# Node Classification Troubleshooting

## Model and generator are incompatible

**Symptoms**

- model constructor rejects the generator;
- `in_out_tensors()` returns unexpected inputs;
- Keras complains about missing adjacency, neighbor, or index tensors.

**Recovery**

- Pair full-batch models (`GCN`, `GAT`, `PPNP`, `APPNP`) with
  `FullBatchNodeGenerator` unless using Cluster-GCN.
- Pair `GraphSAGE` with `GraphSAGENodeGenerator`, `DirectedGraphSAGE` with the
  directed generator, `HinSAGE` with `HinSAGENodeGenerator`, and `RGCN` with
  `RelationalFullBatchNodeGenerator`.
- Build `x_inp, x_out` from the same generator instance used for `flow(...)`.

## Sparse/dense mismatch

**Symptoms**

- dense model receives sparse index/value tensors, or sparse model receives a
  dense adjacency tensor;
- saliency/interpretability code says the model has the wrong input count.

**Recovery**

- Keep `sparse=True` or `sparse=False` consistent from generator through model
  construction, fitting, and any later interpretability call.
- For tiny debugging, use `sparse=False`; for real sparse graphs, prefer
  `sparse=True` after the shape is understood.

## Labels do not align with node IDs

**Symptoms**

- target shape differs from selected node IDs;
- Keras output and label dimensions disagree;
- generator reports invalid node IDs.

**Recovery**

- Split label Series/DataFrames by index values that match `graph.nodes()`.
- Pass `train_ids` to `generator.flow(train_ids, train_targets)` and ensure
  `train_targets` rows are in the same order.
- Use one-hot labels for `categorical_crossentropy`; use binary/column labels
  for binary cross-entropy; use numeric arrays for regression.

## Heterogeneous graph sent to homogeneous model

**Symptoms**

- `expected a graph with a single node type` or single-edge-type errors;
- full-batch model cannot infer node feature sizes.

**Recovery**

- Use `HinSAGE` when node/edge types are central and the target is a node type.
- Use `RGCN` when relation types are the main modeling signal.
- If the graph is actually homogeneous but was loaded as heterogeneous, rebuild
  the graph with one node type and one edge type or explicitly merge types.

## Feature problems

**Symptoms**

- `check_graph_for_ml` fails;
- TensorFlow layer receives object/string dtype;
- input feature dimension is zero or inconsistent.

**Recovery**

- Encode categorical node attributes into numeric columns before graph creation.
- Keep labels separate from features unless intentionally using labels as model
  input features.
- Inspect `graph.node_feature_sizes()` and ensure the selected model supports
  the feature sizes for all target node types.

## Deprecated Cluster-GCN confusion

**Symptom**

- Searching for a `ClusterGCN` model path gives deprecation warnings.

**Recovery**

- Use `ClusterNodeGenerator` with `GCN` for cluster training guidance.

## Safe diagnostic

Run:

```bash
python sub-skills/node-classification-gnns/scripts/gcn_node_smoke.py
```

If it passes, basic graph, generator, GCN, and Dense-head wiring works. Compare
your real workflow's graph type, target IDs, sparse setting, and output head to
the smoke pattern.
