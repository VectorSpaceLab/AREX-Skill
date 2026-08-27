---
name: data-io-and-evaluation
description: "Guide pgmpy datasets, example models, model I/O formats, and
  evaluation metrics."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Data I/O and Evaluation

Use this sub-skill when a task asks to discover or load pgmpy built-in datasets
or example models, validate local data artifacts, read or write model files, or
evaluate learned structures/models with pgmpy metrics.

Do **not** use this sub-skill to choose or run learning algorithms, construct new
models/CPDs, or perform inference on a loaded model. Route structure/parameter
learning to `learning-structure-and-parameters`, graph/CPD construction to
`modeling-and-factors`, and posterior queries/simulation on loaded models to
`inference-sampling-and-simulation`.

## First decisions

1. Decide whether the task can stay local:
   - `list_datasets(...)` and `list_models(...)` inspect registries and should
     not fetch data.
   - `load_dataset(...)` and `load_model(...)` may read the local Hugging Face
     cache or download public assets when the cache is missing. Keep network
     use explicit and optional.
2. Pick the I/O layer:
   - Use model-level `model.save(...)` and `DiscreteBayesianNetwork.load(...)`
     for common discrete-BN files: BIF, UAI, XMLBIF, XDSL, and NET.
   - Use `pgmpy.readwrite` reader/writer classes for format-specific options,
     strings, properties, XBN, PomdpX, or round-value control.
   - Use `LinearGaussianBayesianNetwork.save/load` for its JSON schema.
3. Pick the metric by inputs:
   - Ground-truth graph available: use `SHD`, `AdjacencyConfusionMatrix`, or
     `OrientationConfusionMatrix` after aligning node sets.
   - No ground truth but data available: use `CorrelationScore`, `ImpliedCIs`,
     `FisherC`, or `StructureScore` with a data frame whose columns cover graph
     nodes.
4. Confirm the evaluation artifact exists. Metrics evaluate an existing graph or
   fitted/discovered model; they do not fit parameters or discover structures.
5. For automation, write outputs to user or temporary paths, set seeds where an
   API supports them, and disable progress bars on long metric checks.

## Routing table

| Need | Primary pgmpy entry point | Notes |
|---|---|---|
| List dataset names by tags | `pgmpy.datasets.list_datasets(**filters)` | Local registry lookup. Common filters include `is_discrete`, `is_continuous`, `has_ground_truth`, `n_samples`, and `n_variables`. |
| Load a built-in dataset | `pgmpy.datasets.load_dataset(name, n_samples=None, seed=None, **sim_kwargs)` | Returns a `Dataset` with `data`, `ground_truth`, `expert_knowledge`, and `tags`; may require cache/network except for purely simulated assets. |
| List example model names by tags | `pgmpy.example_models.list_models(**filters)` | Local registry lookup. Filters include `is_parameterized`, `is_discrete`, `is_continuous`, `n_nodes`, and `n_edges`. |
| Load an example model | `pgmpy.example_models.load_model(name)` | Returns a `DAG`, `DiscreteBayesianNetwork`, `LinearGaussianBayesianNetwork`, or optional functional model family; may require cache/network. |
| Persist a discrete BN | `model.save(path, filetype=...)` and `DiscreteBayesianNetwork.load(path, filetype=...)` | Supports BIF, UAI, XMLBIF, XDSL, and NET through model-level helpers. |
| Format-specific parsing/writing | `pgmpy.readwrite.*Reader` / `*Writer` | Use for BIF, XMLBIF, NET, UAI, XDSL, XBN, and PomdpX options or string-based reads. |
| Persist a linear Gaussian BN | `LinearGaussianBayesianNetwork.save(path)` and `.load(path)` | JSON file/object with `nodes`, `arcs`, and `cpds`; see the bundled reference for schema notes. |
| Supervised graph comparison | `SHD`, `AdjacencyConfusionMatrix`, `OrientationConfusionMatrix` | Graphs must have identical node sets. Orientation confusion supports DAGs only. |
| Unsupervised graph/data evaluation | `CorrelationScore`, `ImpliedCIs`, `FisherC`, `StructureScore` | Requires a pandas data frame with columns for every graph node. |

## Bundled references and script

- [I/O, data, and metrics API map](references/io-data-and-metrics.md)
  lists registry APIs, supported file formats, model-level versus class-level
  I/O, data artifact checks, and metric selection recipes.
- [Troubleshooting](references/troubleshooting.md) covers cache/network misses,
  unsupported file types, malformed BIF/XML/UAI content, metric node alignment,
  and using metrics before fitting or discovery.
- [data_io_smoke.py](scripts/data_io_smoke.py) lists local registries, builds a
  tiny discrete BN, writes/reads a temporary BIF file, and computes graph metrics
  without reading repository fixtures or using network by default.

## Minimal copyable pattern

```python
from pgmpy.base import DAG
from pgmpy.metrics import SHD

true_graph = DAG([("A", "B"), ("B", "C")])
est_graph = DAG([("B", "A"), ("B", "C")])

# Supervised metrics require identical node sets, including isolated nodes.
est_graph.add_nodes_from(true_graph.nodes())
print(SHD()(true_causal_graph=true_graph, est_causal_graph=est_graph))
```

If that fails, inspect the exact graph node sets before changing the metric. Most
metric errors come from missing/extra nodes, using a PDAG with a DAG-only metric,
or passing data whose columns do not cover the graph variables.
