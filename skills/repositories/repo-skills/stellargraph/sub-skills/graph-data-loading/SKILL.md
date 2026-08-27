---
name: graph-data-loading
description: "Guides StellarGraph graph construction, graph queries, data-format
  validation, built-in dataset loaders, and safe tiny graph smoke checks."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Graph Data Loading

Use this sub-skill when a StellarGraph task starts with raw graph data,
`StellarGraph`/`StellarDiGraph` construction, graph conversion, feature/type
validation, or built-in dataset loading.

## Read first

- [`references/data-formats.md`](references/data-formats.md) for self-contained
  Pandas, NumPy, `IndexedArray`, heterogeneous, directed, weighted, and NetworkX
  construction patterns.
- [`references/api-reference.md`](references/api-reference.md) for verified
  constructor signatures, query/conversion methods, and graph readiness checks.
- [`references/datasets.md`](references/datasets.md) for dataset loader classes,
  cache behavior, download boundaries, and load return shapes.
- [`references/troubleshooting.md`](references/troubleshooting.md) when graph
  constructors reject columns, IDs, types, missing nodes, duplicate IDs, or
  feature shapes.
- [`scripts/stellargraph_data_smoke.py`](scripts/stellargraph_data_smoke.py) for
  a safe local smoke that constructs tiny graphs and inspects dataset classes
  without downloading data.

## Route here when the user asks to

- load graph data from Pandas DataFrames, NumPy arrays, `IndexedArray`, or
  NetworkX;
- decide between `StellarGraph` and `StellarDiGraph`;
- represent homogeneous vs heterogeneous graphs, multiple edge types, edge
  weights, node features, edge features, or type columns;
- inspect graph summaries with `info`, `number_of_nodes`, `number_of_edges`,
  `node_feature_sizes`, `edge_feature_sizes`, `nodes`, `edges`, `neighbors`,
  or adjacency conversion;
- use dataset loaders such as `Cora`, `CiteSeer`, `MovieLens`, `MUTAG`, `WN18`,
  or `METR_LA`;
- diagnose dataset cache/download issues or `STELLARGRAPH_DATASETS_PATH`.

## Route elsewhere

- For `flow`, random walks, mini-batches, sparse adjacency tensors, or Keras
  generators, read [`../sampling-generators/SKILL.md`](../sampling-generators/SKILL.md).
- For node classification model wiring, read
  [`../node-classification-gnns/SKILL.md`](../node-classification-gnns/SKILL.md).
- For link prediction and knowledge graph completion, read
  [`../link-prediction-kg/SKILL.md`](../link-prediction-kg/SKILL.md).
- For Neo4j connector classes and database service requirements, read
  [`../model-ops-interpretability/SKILL.md`](../model-ops-interpretability/SKILL.md).

## Operating workflow

1. Identify graph directionality and heterogeneity before writing model code:
   homogeneous vs heterogeneous, directed vs undirected, one edge type vs many,
   weighted vs unweighted.
2. Choose the input representation:
   - Pandas DataFrame for readable IDs, columns, types, and features;
   - `IndexedArray` for compact numeric features with explicit IDs;
   - NumPy arrays only when node IDs are `0, 1, 2, ...`;
   - NetworkX conversion when a graph object already exists and attributes are
     named consistently.
3. Build edge data with `source` and `target` columns unless using custom column
   names in the constructor. Add `weight` for weighted edges and an edge type
   column or edge-type dictionary for multiple relation types.
4. Build node features as numeric rows indexed by node ID. For multiple node
   types, use a dictionary keyed by node type; IDs must be unique across types.
5. Construct `StellarGraph(...)` for undirected workflows or
   `StellarDiGraph(...)` for directed workflows.
6. Validate with small graph queries before using generators or models:
   `number_of_nodes`, `number_of_edges`, `node_feature_sizes`, `edge_types`,
   `node_types`, `info()`, and `check_graph_for_ml()` when appropriate.
7. Only after the graph object is valid, move to the generator/model sub-skill
   that owns the downstream task.

## Dataset workflow

1. Instantiate the dataset class; do not call `download()` unless the user
   wants network access.
2. Set `STELLARGRAPH_DATASETS_PATH` to a writable cache when the default user
   cache is unsuitable.
3. Use each loader's `load(...)` signature rather than assuming every dataset
   returns the same tuple shape.
4. Convert labels or targets with scikit-learn/Pandas before model fitting.

## Safe checks

Run the bundled smoke from any environment with StellarGraph installed:

```bash
python sub-skills/graph-data-loading/scripts/stellargraph_data_smoke.py --help
python sub-skills/graph-data-loading/scripts/stellargraph_data_smoke.py
```

Add `--repo-root PATH` only when intentionally testing an uninstalled local
checkout. The script does not download datasets.

## Quality guardrails

- Do not infer node features from non-numeric label columns; encode labels
  separately for supervised workflows.
- Do not reuse the same external node ID across different node types; disambiguate
  IDs before construction.
- Do not pass edge endpoints that are missing from explicit `nodes` unless you
  intentionally want node inference from `edges`.
- Do not keep model code in this sub-skill; it should produce a valid graph
  object and then route to the correct generator/model route.
