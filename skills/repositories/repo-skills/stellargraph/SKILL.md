---
name: stellargraph
description: "Routes StellarGraph graph machine learning tasks across graph
  construction, samplers, TensorFlow Keras models, link prediction, embeddings,
  graph classification, time series, calibration, ensembles, interpretability,
  datasets, and Neo4j connector workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# StellarGraph Repo Skill

Use this skill when a task involves the **StellarGraph** Python package or its
TensorFlow/Keras graph machine learning workflows. It is a router: read the
smallest sub-skill that matches the user's task, then use the bundled references
and scripts from that sub-skill.

## First checks

- StellarGraph's package metadata targets Python `>=3.6,<3.9`; prefer a Python
  3.8 environment when installing or reproducing old examples.
- Basic install for package use: `python -m pip install stellargraph`.
- Use `python -m pip install "stellargraph[demos]"` only when notebook-style
  demo dependencies such as `gensim`, `rdflib`, `numba`, Jupyter, or plotting
  helpers are needed.
- Use `python -m pip install "stellargraph[neo4j]"` only for Neo4j connector
  workflows; it still requires a running Neo4j service.
- Run [`scripts/check_stellargraph_environment.py`](scripts/check_stellargraph_environment.py)
  when you need a safe import, TensorFlow/Keras, graph-construction, and optional
  backend diagnostic before following a workflow.
- Read [`references/troubleshooting.md`](references/troubleshooting.md) for
  Python/TensorFlow/import, optional dependency, dataset-cache, GPU, and Neo4j
  failures that affect multiple workflows.
- Read [`references/repo-provenance.md`](references/repo-provenance.md) before
  deciding whether this skill is stale for a newer checkout or package version.

## Route by task

### Data, graph objects, and datasets

Read [`sub-skills/graph-data-loading/SKILL.md`](sub-skills/graph-data-loading/SKILL.md)
when the task is about:

- constructing `StellarGraph` or `StellarDiGraph` objects from Pandas, NumPy,
  `IndexedArray`, or NetworkX;
- choosing node/edge IDs, types, features, weights, or directedness;
- converting/querying graph structure or checking graph readiness for ML;
- using built-in dataset loader classes such as `Cora`, `MovieLens`, `WN18`, or
  `METR_LA` without confusing cache/download behavior with model logic.

### Walkers, samplers, and Keras generators

Read [`sub-skills/sampling-generators/SKILL.md`](sub-skills/sampling-generators/SKILL.md)
when the task is about random walks, sampled breadth-first neighborhoods,
`UnsupervisedSampler`, full-batch, sampled mini-batch, padded-graph,
knowledge-graph, or sliding-window generators.

Use this route before model routes when the failure mentions `flow`,
`Sequence`, `num_samples`, `n_size`, node/link IDs, batch dimensions, sparse
adjacency tensors, or generator/model incompatibility.

### Node classification or node regression with GNNs

Read [`sub-skills/node-classification-gnns/SKILL.md`](sub-skills/node-classification-gnns/SKILL.md)
for supervised or semi-supervised node workflows using `GCN`, `GAT`,
`GraphSAGE`, `DirectedGraphSAGE`, `HinSAGE`, `ClusterNodeGenerator` + `GCN`,
`RGCN`, `PPNP`, `APPNP`, or the SGC-style linear GCN pattern.

Use sibling routes for upstream graph construction and generator details; this
route owns model selection, Keras tensor wiring, targets, and training/evaluation
shape decisions for node tasks.

### Link prediction, link regression, and knowledge graphs

Read [`sub-skills/link-prediction-kg/SKILL.md`](sub-skills/link-prediction-kg/SKILL.md)
for edge-split workflows, `GraphSAGELinkGenerator`, `HinSAGELinkGenerator`,
`FullBatchLinkGenerator`, link inference heads, temporal link prediction, and
knowledge graph completion with `KGTripleGenerator`, `ComplEx`, `DistMult`,
`RotatE`, `RotE`, or `RotH`.

### Unsupervised embeddings and representation learning

Read [`sub-skills/embedding-workflows/SKILL.md`](sub-skills/embedding-workflows/SKILL.md)
for Node2Vec/DeepWalk, Metapath2Vec, Attri2Vec, unsupervised GraphSAGE,
Deep Graph Infomax, GraphWave, Watch Your Step, or extracting embeddings for
scikit-learn/Keras downstream models.

### Graph classification and graph time series

Read [`sub-skills/graph-time-series-workflows/SKILL.md`](sub-skills/graph-time-series-workflows/SKILL.md)
for graph-level classification with `PaddedGraphGenerator`,
`GCNSupervisedGraphClassification`, `DeepGraphCNN`, or `SortPooling`, and for
spatio-temporal forecasting with `SlidingFeaturesNodeGenerator`, fixed
adjacency, and `GCN_LSTM`.

### Model operations, interpretability, and Neo4j

Read [`sub-skills/model-ops-interpretability/SKILL.md`](sub-skills/model-ops-interpretability/SKILL.md)
for:

- `custom_keras_layers` when saving/loading Keras models that contain
  StellarGraph layers;
- calibration (`TemperatureCalibration`, `IsotonicCalibration`, expected
  calibration error, reliability plots);
- `Ensemble` and `BaggingEnsemble` wrappers;
- GCN/GAT saliency and integrated-gradient interpretability;
- optional Neo4j connector objects and service-backed generators.

## Package map

Read [`references/package-overview.md`](references/package-overview.md) when a
user names an algorithm, dataset, module, notebook title, or capability and you
need to pick the correct route before acting.

## Boundaries

- This skill teaches package operation, not repository release maintenance or CI
  pipeline editing.
- Do not run long notebook demos, dataset downloads, Neo4j services, or GPU
  checks unless the user explicitly wants that external dependency or runtime.
- Prefer safe bundled scripts and tiny synthetic fixtures before attempting full
  notebook-scale examples.
