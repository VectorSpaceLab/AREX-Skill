# Graph Classification and Time-Series Troubleshooting

## Graph-level vs node-level targets

**Symptoms**

- Target length equals node count instead of graph count.
- Keras output shape does not match labels.

**Recovery**

- For `PaddedGraphGenerator`, create one label per graph in the graph list.
- Use the node-classification route if the task predicts labels for nodes inside
  one graph.

## Variable graph feature mismatch

**Symptoms**

- Padded graph batches fail because feature dimensions differ.

**Recovery**

- Ensure each graph has the same node feature dimension.
- Encode missing node attributes to numeric zero/default columns before graph
  construction.

## `k` in DeepGraphCNN is wrong

**Symptoms**

- Sort pooling loses too many nodes or creates mostly padding.

**Recovery**

- Inspect graph node-count distribution and set `k` to a meaningful percentile
  or domain-specific maximum.

## Time-series shape mismatch

**Symptoms**

- `GCN_LSTM` input rank errors.
- Forecast target is shifted by the wrong horizon.

**Recovery**

- Keep `seq_len`, generator `window_size`, and model `seq_len` equal.
- Verify adjacency shape is `(num_nodes, num_nodes)`.
- Inspect one `SlidingFeaturesNodeGenerator` batch and confirm target horizon
  before training.

## Dataset download boundary

`METR_LA` examples may download data. If the task is only shape debugging, use a
tiny synthetic array and avoid network access.
