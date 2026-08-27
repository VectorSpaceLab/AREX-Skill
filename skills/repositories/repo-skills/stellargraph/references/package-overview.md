# Package Overview

## Purpose

Use this reference when you know the user needs StellarGraph but you still need
to choose the right route. It condenses the package's public graph-learning
surface into the workflows that this skill covers.

## What StellarGraph is for

StellarGraph is a Python library for **graph machine learning** built around
TensorFlow/Keras. The public API centers on:

- graph construction and conversion (`StellarGraph`, `StellarDiGraph`,
  `IndexedArray`, `GraphSchema`);
- graph samplers and Keras generators (random walks, full-batch, sampled,
  padded, knowledge-graph, and sliding-window flows);
- model families for node classification, link prediction, embeddings, graph
  classification, and graph time series;
- calibration, ensembles, interpretability, and the optional Neo4j connector.

## Main public workflow families

| Workflow family | Typical user goal | Main API families | Owning sub-skill |
| --- | --- | --- | --- |
| Graph construction and dataset loading | Turn Pandas/NumPy/NetworkX data into graph objects, or load bundled example datasets | `StellarGraph`, `StellarDiGraph`, `IndexedArray`, `GraphSchema`, dataset loaders such as `Cora`, `MovieLens`, `METR_LA` | `graph-data-loading` |
| Random walks and generators | Prepare walk sequences or Keras generator inputs for models | `UniformRandomWalk`, `BiasedRandomWalk`, `UniformRandomMetaPathWalk`, `SampledBreadthFirstWalk`, `TemporalRandomWalk`, `FullBatchNodeGenerator`, `GraphSAGENodeGenerator`, `HinSAGENodeGenerator`, `KGTripleGenerator`, `PaddedGraphGenerator`, `SlidingFeaturesNodeGenerator` | `sampling-generators` |
| Node classification or regression | Build a supervised/semi-supervised node model | `GCN`, `GAT`, `GraphSAGE`, `DirectedGraphSAGE`, `HinSAGE`, `ClusterNodeGenerator`, `RGCN`, `PPNP`, `APPNP` | `node-classification-gnns` |
| Link prediction and KG completion | Split edges, infer links, or score triples in knowledge graphs | `EdgeSplitter`, link generators, `link_classification`, `link_regression`, `link_inference`, `ComplEx`, `DistMult`, `RotatE`, `RotE`, `RotH` | `link-prediction-kg` |
| Unsupervised embeddings | Learn node/edge/graph embeddings for downstream use | `Node2Vec`, `Attri2Vec`, `DeepGraphInfomax`, `GraphWaveGenerator`, `WatchYourStep` | `embedding-workflows` |
| Graph classification and time series | Build graph-level classifiers or spatio-temporal GCN/LSTM models | `PaddedGraphGenerator`, `GCNSupervisedGraphClassification`, `DeepGraphCNN`, `SortPooling`, `SlidingFeaturesNodeGenerator`, `GCN_LSTM` | `graph-time-series-workflows` |
| Calibration, ensembles, saliency, Neo4j | Adjust probability outputs, ensemble models, explain predictions, or use the optional connector | `TemperatureCalibration`, `IsotonicCalibration`, `Ensemble`, `BaggingEnsemble`, saliency helpers, Neo4j classes | `model-ops-interpretability` |

## Verified package facts used by this skill

- Distribution name: `stellargraph`.
- Installed import root: `stellargraph`.
- Package version observed in the installed environment: `1.3.0b` source version,
  normalized as `1.3.0b0` in distribution metadata.
- Package metadata declares Python `>=3.6,<3.9`.
- The package imports TensorFlow/Keras in core model and generator modules.
- Optional connector import `stellargraph.connector.neo4j` succeeds without
  starting a Neo4j service, but service-backed workflows still require a live
  Neo4j instance and the `py2neo` extra.

## How to choose a route

1. Start with graph construction if the user has raw graph data, labels, or
   dataset files.
2. Move to generators when the task mentions `flow`, batches, sampling, random
   walks, or adjacency tensors.
3. Choose the model sub-skill that matches the output task family: node,
   link/KG, embedding, graph classification/time series, or operational helper.
4. When the request is about saved-model loading, calibration, ensembles,
   saliency, or Neo4j, use the operations/interpretability route even if the
   task also mentions a model family.

## Notes

- SGC in this repository is usually treated as a GCN-style node-classification
  pattern rather than a separate model class.
- Many demos are notebook workflows that are useful as evidence, but the runtime
  skill keeps the reusable steps in references and scripts.
