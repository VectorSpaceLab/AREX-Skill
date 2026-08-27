# Data I/O and Evaluation Troubleshooting

Use this matrix when a dataset/model load, file roundtrip, or metric evaluation
fails. Keep local workflows moving when a remote registry asset is unavailable.

| Symptom | Likely cause | Remedy | Fast check |
|---|---|---|---|
| `load_dataset(...)` or `load_model(...)` stalls or raises a Hugging Face/cache error | Asset is not in the local cache and network is unavailable, blocked, or not approved. | Use `list_datasets`/`list_models` to confirm the name locally, then ask whether network is allowed. For cache-only runs, start Python with `HF_HUB_OFFLINE=1` and handle cache-miss failures explicitly. Use a user-provided file or tiny synthetic fixture if loading is optional. | Run only registry listing first; it should not download bytes. |
| Registry filter raises `ValueError: Unrecognized filter argument` | Typo or non-tag filter key. | Use documented tags: datasets use `is_discrete`, `has_ground_truth`, `n_samples`, etc.; models use `is_parameterized`, `is_discrete`, `n_nodes`, etc. | Call `list_datasets()` or `list_models()` without filters, then add one filter at a time. |
| `ValueError: Dataset/Model with name ... not found` | Wrong registry id, missing family prefix, or typo. | Use exact ids returned by the registry, including prefixes such as `bnlearn/`, `bnrep/`, `dagitty/`, or `tubingen/<id>`. | `name in list_models()` or `name in list_datasets()` before loading. |
| `Unsupported file format: ...` from `save` or `load` | Model-level helper only supports a bounded filetype map. | For `DiscreteBayesianNetwork.save/load`, use `bif`, `uai`, `xmlbif`, `xdsl`, or `net`. Use direct `XBNReader/XBNWriter` for XBN and `PomdpXReader/PomdpXWriter` for PomdpX-style XML. | Print the explicit `filetype` you pass; do not rely on an unusual extension. |
| A file with extension `.xml` is read as BIF or the wrong parser is used | The extension is not one of the recognized model-level keys, or `filetype` was omitted. | Pass `filetype="xmlbif"`, `"xdsl"`, or the exact intended reader class. Keep extensions and filetype values aligned in automation. | Use `DiscreteBayesianNetwork.load(path, filetype="xmlbif")` for XMLBIF files. |
| BIF parse fails on comments, variable names, or CPD tables | Malformed BIF syntax, non-portable variable/state names, missing probability block, or wrong parent order. | Minimize to one variable/probability block, validate with `BIFReader(string=...)`, and prefer simple names. For properties, pass `include_properties=True`. | Try `BIFReader(string=text).get_model()` before writing to disk. |
| XMLBIF/XML/XDSL parser raises an XML parse error | File is not well-formed XML or is the wrong XML dialect. | Check root tags and choose the matching class: XMLBIF, XDSL, XBN, or PomdpX. XDSL reader supports CPT blocks and rejects whitespace in node names. | Parse with the specific reader class and a tiny known-good file/string. |
| UAI roundtrip produces variables named `var_0`, `var_1`, ... | UAI format is index/cardinality based and does not preserve arbitrary pgmpy variable names in the same way as BIF/XML formats. | Keep a mapping outside the UAI file if original names matter, or prefer BIF/XMLBIF/NET/XDSL for name-preserving BN interchange. | Inspect `UAIReader(path).variables` before comparing by labels. |
| Linear Gaussian JSON load fails with key errors or math/domain errors | JSON does not match the LGBN schema: missing `nodes`, `arcs`, `cpds`, missing intercept, unknown parent coefficient, or non-positive variance. | Validate keys and one-element coefficient/variance arrays before loading. Use `LinearGaussianBayesianNetwork.save` to generate a reference file. | Confirm every CPD has `coefficients["(Intercept)"]`, `variance[0] > 0`, and `parents`. |
| `The true_causal_graph and est_causal_graph must be on the same nodes` | Supervised metrics require identical node sets, including isolated nodes. | Add isolated nodes to the estimated or true graph before evaluation, or compare only the intended induced subgraph after making that choice explicit. | `set(true_graph.nodes()) ^ set(est_graph.nodes())` should be empty. |
| Orientation metric rejects a graph type | `OrientationConfusionMatrix` supports `DAG` only; PDAG orientation can be partially directed/undirected. | Use `SHD` or `AdjacencyConfusionMatrix` for PDAGs, or convert to a DAG only when the orientation semantics are valid for the task. | `type(graph)` and metric tags from `get_metrics(requires_true_graph=True)`. |
| Unsupervised metric says data is not a DataFrame or columns are missing | `BaseUnsupervisedMetric` requires `pandas.DataFrame` and columns for all graph nodes. | Convert to a DataFrame with graph-node column names and verify coverage before scoring. | `set(causal_graph.nodes()) - set(data.columns)` should be empty. |
| `CorrelationScore`, `ImpliedCIs`, or `FisherC` gives implausible p-values or errors | CI test does not match variable type, data is too small, or missing values/categorical dtypes were not handled. | Choose `chi_square`/discrete tests for categorical data and `pearsonr` for continuous data; clean missing values according to the analysis plan. | Run the CI test on one variable pair before the full metric. |
| `FisherC` fails on latent variables | Fisher C implementation rejects DAGs with latent variables. | Remove/observe latent variables only if justified, select a different metric, or route back to the causal/modeling task for an appropriate representation. | `len(causal_graph.latents) == 0`. |
| `StructureScore` fails before any model is fitted | Structure score needs a candidate graph and data, but not fitted CPDs. The graph may be absent or its variable types may not match the scoring method. | Route learning/model construction first if no graph exists. Use a discrete score such as `bic-d` for discrete data and Gaussian/conditional-Gaussian scores for continuous/mixed data. | Check `causal_graph.nodes()` and data dtypes before scoring. |
| Metrics are slow or progress bars pollute logs | Implied-CI metrics scale over node pairs and can show progress bars. | Use a smaller graph/sample for smoke tests and pass `show_progress=False` where supported. | Run on a three-node fixture first. |

## Safe fallback workflow for network-bound names

1. List registries locally and verify the requested name exists.
2. If loading can be skipped, proceed with the user-supplied local artifact or a
   synthetic fixture.
3. If loading is required, ask whether network is allowed or require a populated
   Hugging Face cache.
4. Keep the failure message in the handoff, including whether the registry lookup
   succeeded and whether only the remote asset fetch failed.

## Hard usability cases to verify

- A user asks for `load_model("bnlearn/asia")` in a cache-only environment while
  also asking for a local BIF roundtrip. The local BIF and graph-metric flow
  should still complete; the remote example load should be reported as optional
  and blocked only by cache/network.
- A discovered graph lacks isolated variables present in the ground-truth graph.
  The workflow should align node sets intentionally before `SHD` or confusion
  matrices and should explain whether isolated nodes were retained or an induced
  subgraph comparison was chosen.
