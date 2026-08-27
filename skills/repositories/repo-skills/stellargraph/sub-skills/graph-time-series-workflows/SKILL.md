---
name: graph-time-series-workflows
description: "Guides StellarGraph graph-level classification and spatio-temporal
  forecasting with PaddedGraphGenerator, GCN graph classifiers, DeepGraphCNN,
  SortPooling, SlidingFeaturesNodeGenerator, and GCN_LSTM."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Graph Classification and Time Series

Use this sub-skill for graph-level supervised learning or spatio-temporal
forecasting where the unit of prediction is a whole graph or a future sequence
on graph nodes.

## Read first

- [`references/graph-classification.md`](references/graph-classification.md) for
  `PaddedGraphGenerator`, graph-level labels, `GCNSupervisedGraphClassification`,
  `DeepGraphCNN`, and `SortPooling`.
- [`references/time-series.md`](references/time-series.md) for
  `SlidingFeaturesNodeGenerator`, fixed adjacency, `GCN_LSTM`, window sizes, and
  forecast target shapes.
- [`references/troubleshooting.md`](references/troubleshooting.md) for padded
  graph, graph-label, adjacency, sequence, and target-distance shape failures.
- [`scripts/graph_batch_smoke.py`](scripts/graph_batch_smoke.py) and
  [`scripts/time_series_shape_smoke.py`](scripts/time_series_shape_smoke.py) for
  safe tiny shape checks without downloads.

## Route here when the user asks to

- classify a collection of graphs with graph labels;
- use `PaddedGraphGenerator`, `GCNSupervisedGraphClassification`, `DeepGraphCNN`,
  or `SortPooling`;
- forecast traffic/sensor/time-series values over graph nodes;
- use `SlidingFeaturesNodeGenerator`, `FixedAdjacencyGraphConvolution`, or
  `GCN_LSTM`;
- debug graph batch padding, graph-level targets, fixed adjacency, `seq_len`, or
  sliding-window target distance.

## Route elsewhere

- Node classification on one graph: [`../node-classification-gnns/SKILL.md`](../node-classification-gnns/SKILL.md).
- Link prediction: [`../link-prediction-kg/SKILL.md`](../link-prediction-kg/SKILL.md).
- Raw graph construction: [`../graph-data-loading/SKILL.md`](../graph-data-loading/SKILL.md).
- Generator mechanics: [`../sampling-generators/SKILL.md`](../sampling-generators/SKILL.md).

## Operating workflow

1. Decide whether the sample unit is a graph (`PaddedGraphGenerator`) or a time
   window over nodes (`SlidingFeaturesNodeGenerator`).
2. For graph classification, create a list of `StellarGraph` objects and a
   target vector/DataFrame with one row per graph.
3. For time series, create a graph with sequence-valued node features and a
   fixed adjacency matrix compatible with `GCN_LSTM`.
4. Inspect one generator batch before adding model layers.
5. Add Keras output heads/losses for graph-level classification/regression or
   forecasting targets.

## Safe checks

```bash
python sub-skills/graph-time-series-workflows/scripts/graph_batch_smoke.py
python sub-skills/graph-time-series-workflows/scripts/time_series_shape_smoke.py
```
