# I/O, Data, and Metrics API Map

This reference is for operating tasks that start from pgmpy registries, local
model/data artifacts, or evaluation outputs. It keeps algorithm selection,
model construction, and inference out of scope.

## Dataset registry

| Operation | API | Returns | Local/network behavior | Use when |
|---|---|---|---|---|
| Discover datasets | `from pgmpy.datasets import list_datasets`; `list_datasets(**filter_tags)` | Sorted `list[str]` | Local package registry lookup; no dataset bytes are read. | Choosing a candidate by tags before loading. |
| Load dataset | `load_dataset(name, n_samples=None, seed=None, **sim_kwargs)` | `Dataset(name, data, expert_knowledge, ground_truth, tags)` | Static/covariance/Tubingen assets are read through Hugging Face cache and can download on cache miss; simulated datasets generate data locally after class construction. | Getting a `pandas.DataFrame` plus optional ground-truth graph or expert knowledge. |

Useful `list_datasets` filters include `is_discrete`, `is_continuous`,
`is_mixed`, `is_ordinal`, `is_simulated`, `is_interventional`,
`has_ground_truth`, `has_expert_knowledge`, `has_missing_data`, `n_variables`,
and `n_samples`. Invalid filter names raise `ValueError`.

`load_dataset` details:

- `n_samples` subsamples static data with `seed` or controls/generated sample
  count for simulated/covariance datasets where supported.
- Oversized static subsamples are capped and warn.
- Tubingen pairs use names like `"tubingen/1"` through `"tubingen/108"`; invalid
  pair ids raise `ValueError`.
- The returned `Dataset.data` is a `pandas.DataFrame`; categorical and ordinal
  variables can use pandas categorical dtypes.
- `Dataset.ground_truth` is a pgmpy graph object when `tags["has_ground_truth"]`
  is true; `Dataset.expert_knowledge` is a causal-discovery `ExpertKnowledge`
  object when provided.

## Example model registry

| Operation | API | Returns | Local/network behavior | Use when |
|---|---|---|---|---|
| Discover models | `from pgmpy.example_models import list_models`; `list_models(**filter_tags)` | Sorted `list[str]` | Local package registry lookup; no model bytes are read. | Finding built-in model ids such as `bnlearn/asia`, `bnrep/asia`, or `dagitty/m_bias`. |
| Load model | `load_model(name)` | `DAG`, `DiscreteBayesianNetwork`, `LinearGaussianBayesianNetwork`, or optional functional model family | Reads Hugging Face cache and can download on cache miss. | Benchmarking, examples, inference/simulation handoff, or metric fixtures. |

Useful `list_models` filters include `name`, `is_parameterized`, `is_discrete`,
`is_continuous`, `is_hybrid`, `n_nodes`, and `n_edges`. Invalid filter names
raise `ValueError`.

Model families:

- Discrete parameterized models are loaded through BIF data and return
  `DiscreteBayesianNetwork` with CPDs.
- Continuous models are loaded from the linear-Gaussian JSON representation and
  return `LinearGaussianBayesianNetwork`.
- Structure-only Dagitty examples return `DAG`.
- Functional/Pyro-style models are optional dependency surfaces; the minimum
  environment did not install torch/pyro.

## Network and cache policy

Use registry listing before loading. Treat dataset/model loading as potentially
network-bound unless you already know the asset is cached. For cache-only runs,
set the standard Hugging Face offline environment before starting Python, for
example `HF_HUB_OFFLINE=1`, and handle cache-miss exceptions by asking the user
whether network is allowed. Do not let a remote model/dataset name block a local
I/O or metric workflow if the task can be satisfied with a user-supplied file or
a tiny synthetic fixture.

## Discrete Bayesian-network I/O

### Model-level helper

`DiscreteBayesianNetwork.save(filename, filetype="bif")` and
`DiscreteBayesianNetwork.load(filename, filetype="bif", **kwargs)` support these
formats through the model helper:

| Filetype | Reader/writer classes | Notes |
|---|---|---|
| `bif` | `BIFReader`, `BIFWriter` | Common text interchange for discrete BNs; readers accept `path` or `string`; `include_properties=True` preserves variable properties. |
| `xmlbif` | `XMLBIFReader`, `XMLBIFWriter` | XMLBIF 0.3 style; writer may sanitize invalid state names and warn. |
| `net` | `NETReader`, `NETWriter` | HUGIN NET format; readers can include properties and supply a default network name. |
| `uai` | `UAIReader`, `UAIWriter` | UAI reader/writer supports BAYES and MARKOV network types; model-level BN helper uses the discrete BN path. |
| `xdsl` | `XDSLReader`, `XDSLWriter` | GeNIe/XDSL CPT blocks; reader rejects node names containing whitespace. |

The helper first validates the supplied `filetype`, then lets a recognized file
extension in `filename` override it. Use explicit file types in scripts to avoid
surprises, and prefer simple variable/state names without spaces or special
characters for cross-tool portability.

### Direct reader/writer classes

Use `pgmpy.readwrite` classes directly when you need strings, properties,
format-specific warnings, round-value control, or less common formats:

```python
from pgmpy.readwrite import BIFReader, BIFWriter

writer = BIFWriter(model, round_values=6)
bif_text = str(writer)
roundtrip = BIFReader(string=bif_text).get_model(state_name_type=str)
```

Available public classes include `BIFReader/Writer`, `XMLBIFReader/Writer`,
`NETReader/Writer`, `UAIReader/Writer`, `XDSLReader/Writer`,
`XBNReader/Writer`, and `PomdpXReader/Writer`.

Important distinctions:

- XBN is exposed through `XBNReader`/`XBNWriter`; it is not part of
  `DiscreteBayesianNetwork.save/load`'s model-level filetype map.
- PomdpX readers/writers operate on POMDP-style XML model data, not as a generic
  discrete-BN save/load replacement.
- UAI uses generated variable names like `var_0`, `var_1`, ... when reading raw
  UAI files, because the format is index/cardinality based.
- Direct readers generally accept exactly one of `path` or `string`; passing
  neither raises `ValueError`.

## Linear Gaussian JSON I/O

`LinearGaussianBayesianNetwork.save(filename)` writes JSON, and
`LinearGaussianBayesianNetwork.load(filename_or_file_object)` reads JSON from a
path or file-like object. The schema shape is:

```json
{
  "nodes": ["x1", "x2"],
  "arcs": [["x1", "x2"]],
  "cpds": {
    "x1": {"coefficients": {"(Intercept)": [0.0]}, "variance": [1.0], "parents": []},
    "x2": {"coefficients": {"(Intercept)": [1.0], "x1": [0.5]}, "variance": [2.0], "parents": ["x1"]}
  }
}
```

The bundled repository schema required `nodes`, `arcs`, and `cpds`, with one
positive variance per CPD and coefficient arrays of length one. Use this JSON
path for linear Gaussian networks rather than BIF/XMLBIF/UAI.

## Data artifact validation before metrics or learning handoff

For a user-supplied data file or loaded dataset:

1. Load into a `pandas.DataFrame` with stable column names.
2. Confirm every graph node required for evaluation appears in `df.columns`.
3. Preserve categorical/ordinal dtypes if the downstream CI test or structure
   score depends on discrete values.
4. Keep missing-data decisions explicit; pgmpy datasets mark missingness in
   `Dataset.tags`, but arbitrary user data needs its own check.
5. Use `seed` and `n_samples` only where the loading/simulation API supports
   them; do not silently subsample evaluation data unless requested.

## Metric selection

| Situation | Metric | Inputs | Graph support | Output | Notes |
|---|---|---|---|---|---|
| Count structural edge additions/deletions/reversals | `SHD(edge_reverse_penalty=1 or 2)` | `true_causal_graph`, `est_causal_graph` | `DAG`, `PDAG` | `int` | Graphs must have identical node sets; penalty 2 counts reversal as delete+add. |
| Compare skeleton edge presence | `AdjacencyConfusionMatrix(metrics=None or list)` | Same as supervised | `DAG`, `PDAG` | `dict` with optional DataFrame `cm`, precision/recall/F1/NPV/specificity | Ignores edge orientation. |
| Compare directions on common skeleton edges | `OrientationConfusionMatrix(metrics=None or list)` | Same as supervised | `DAG` only | `dict` | Conditions on edges present in both skeletons. |
| Compare graph d-connections to statistical correlations | `CorrelationScore(ci_test=..., score=..., significance_level=..., return_summary=...)` | `X`, `causal_graph` | `DAG` | score float or pairwise DataFrame | Needs a CI test suitable for data type, e.g. `chi_square` for discrete or `pearsonr` for continuous. |
| Test implied CIs | `ImpliedCIs(ci_test=..., show_progress=False)` | `X`, `causal_graph` | `DAG` | DataFrame with p-values | Tests missing-edge CI implications. |
| Combine implied CI p-values | `FisherC(ci_test=..., compute_rmsea=False, show_progress=False)` | `X`, `causal_graph` | `DAG` | p-value or `(p_value, rmsea)` | Rejects graphs with latent variables. |
| Score structure against data | `StructureScore(scoring_method="bic-d" or another structure score id)` | `X`, `causal_graph` | `DAG` | numeric score | Parameters are not required; data columns and score family must match variable types. |

Discover metrics programmatically with:

```python
from pgmpy.metrics import get_metrics

supervised_metric_classes = get_metrics(requires_true_graph=True)
unsupervised_metric_classes = get_metrics(requires_data=True)
```

## Copyable local recipes

### Local registry listing without downloads

```python
from pgmpy.datasets import list_datasets
from pgmpy.example_models import list_models

print(list_datasets(is_discrete=True, has_ground_truth=True)[:5])
print(list_models(is_parameterized=True, is_discrete=True)[:5])
```

### Temporary BIF roundtrip

```python
from pathlib import Path
from tempfile import TemporaryDirectory

from pgmpy.factors.discrete import TabularCPD
from pgmpy.models import DiscreteBayesianNetwork

model = DiscreteBayesianNetwork([("A", "B")])
model.add_cpds(
    TabularCPD("A", 2, [[0.6], [0.4]], state_names={"A": ["false", "true"]}),
    TabularCPD(
        "B",
        2,
        [[0.8, 0.2], [0.2, 0.8]],
        evidence=["A"],
        evidence_card=[2],
        state_names={"A": ["false", "true"], "B": ["no", "yes"]},
    ),
)
model.check_model()

with TemporaryDirectory() as tmp:
    path = Path(tmp) / "tiny.bif"
    model.save(str(path), filetype="bif")
    loaded = DiscreteBayesianNetwork.load(str(path), filetype="bif")
    loaded.check_model()
```

### Supervised metric with aligned nodes

```python
from pgmpy.base import DAG
from pgmpy.metrics import AdjacencyConfusionMatrix, OrientationConfusionMatrix, SHD

true_graph = DAG([("A", "B"), ("B", "C")])
est_graph = DAG([("B", "A"), ("B", "C")])
est_graph.add_nodes_from(true_graph.nodes())

print(SHD()(true_graph, est_graph))
print(AdjacencyConfusionMatrix(metrics=["precision", "recall"])(true_graph, est_graph))
print(OrientationConfusionMatrix(metrics=["precision", "recall"])(true_graph, est_graph))
```

### Unsupervised score after a learning or fitting handoff

```python
from pgmpy.metrics import StructureScore

missing = set(causal_graph.nodes()) - set(data.columns)
if missing:
    raise ValueError(f"Data is missing graph variables: {sorted(missing)}")

score = StructureScore(scoring_method="bic-d")(X=data, causal_graph=causal_graph)
```
