# Troubleshooting Data, Graph, Do-Sampler, Plotting, And Temporal Interfaces

Use this reference when a user reports errors while parsing graphs, aligning graph
nodes with DataFrames, using `df.causal.do`, plotting, importing discovery
output, or preparing temporal lagged data.

## Graph Parse Errors

### Symptom

- `ValueError` with an "Incorrect graph format" message.
- A graph string works in another tool but not in DoWhy.
- Inline DOT/GML parsing fails.

### Causes

- The string does not match DoWhy's expected DOT/GML/DAGitty patterns.
- Inline DOT is not a `digraph { ... }` / graph block.
- Inline GML is not a `graph [ ... ]` block.
- A file path does not end in `.dot`, `.gml`, or `.txt` as expected by the helper.
- A DAGitty string does not begin with `dag`.
- Newlines, attributes, or unsupported syntax confuse the parser backend.

### Fix

1. If possible, create a `networkx.DiGraph` directly.
2. Convert to GML for portable parsing:

   ```python
   gml = "\n".join(nx.generate_gml(graph))
   parsed = build_graph_from_str(gml)
   ```

3. For DOT, use a minimal directed graph block first:

   ```python
   dot = "digraph { W -> X; W -> Y; X -> Y; }"
   ```

4. Validate `set(parsed.nodes)` and `set(parsed.edges)` before using the graph in
   modeling.

## DOT Parsing And Plotting Backends

### Symptom

- `Pygraphviz cannot be loaded. Trying pydot...`
- `Pydot cannot be loaded`.
- Graph parses but plotting falls back or fails.
- Graphviz layout options appear ignored.

### Causes

- DOT parsing from strings/files tries `pygraphviz` first and then `pydot`.
- Plotting uses a separate backend path: Graphviz plotting first, then a
  NetworkX/matplotlib fallback.
- `pygraphviz` requires both the Python package and the system Graphviz library.
- A headless environment may not be able to display figures interactively.

### Fix

- For parsing without DOT dependencies, convert the graph to GML or pass a
  `networkx.DiGraph` directly.
- For plotting in scripts, pass `display_plot=False` and a `filename`.
- Treat missing Graphviz as an optional presentation issue unless parsing itself
  depends on DOT.
- If high-quality Graphviz output is required, install system Graphviz and the
  Python `pygraphviz` package according to the target environment's package
  policy.

## Graph/Data Alignment

### Symptom

- Warnings about treatment or outcome variables not in data.
- Warnings about unobserved graph variables.
- Runtime `KeyError` from DataFrame column selection.
- GCM or sampler code complains about missing nodes or columns.

### Causes

- Graph node names do not exactly match DataFrame column names.
- Case, spaces, punctuation, or renamed columns differ.
- The graph includes latent/unobserved nodes but the workflow expects observed
  data for them.
- Data has extra columns not represented in the graph.
- `missing_nodes_as_confounders=True` added DataFrame columns as graph nodes and
  hid a naming problem.

### Fix

Run this before downstream modeling:

```python
graph_nodes = set(graph.nodes)
data_columns = set(df.columns)
print("graph nodes missing from data:", graph_nodes - data_columns)
print("data columns not in graph:", data_columns - graph_nodes)
```

Then:

1. Rename DataFrame columns or graph nodes so observed variables match exactly.
2. Decide whether any graph-only nodes are intentionally unobserved.
3. Remove unused data columns or keep them only if the downstream method ignores
   them safely.
4. Recreate `CausalModel`, GCM objects, or pandas sampler state after changing
   graph/data schema.
5. Avoid using `missing_nodes_as_confounders` as a default; use it only when the
   user intentionally wants all extra observed columns treated as confounders.

## Pandas Do-Sampler Dtypes

### Symptom

- `object format is not supported` or similar unsupported-format exception.
- Missing `variable_types` errors from kernel-density sampling.
- Discrete variables are treated as continuous.
- Categorical/string columns fail even though values look discrete.

### Causes

- Empty `variable_types` triggers pandas dtype conversion: int/float -> `c`,
  bool -> `b`, category -> `d`, anything else unsupported.
- Plain strings usually have object dtype and are unsupported by auto-inference.
- Partial `variable_types` can still force auto-inference for unspecified object
  columns.
- DoWhy's type codes are custom and are not the same as pandas dtype strings.

### Fix

Provide a complete mapping for every relevant column:

```python
variable_types = {
    "W": "c",       # continuous
    "X": "d",       # discrete treatment
    "segment": "d", # unordered category
    "Y": "c",
}
```

For string categories, also consider:

```python
df["segment"] = df["segment"].astype("category")
```

Use type codes:

- `c`: continuous;
- `b`: binary;
- `d`: discrete;
- `o`: ordered discrete;
- `u`: unordered discrete.

## Missing Or Oversized `variable_types`

### Symptom

- `Number of variables in the DataFrame is lesser than the variable_types dict`.
- Sampler fails with a key error for a variable type.

### Causes

- The mapping contains variables not in `df.columns`.
- The mapping omits treatment, outcome, or adjustment variables.
- A graph adjustment set includes a variable not typed in the mapping.

### Fix

- Ensure `set(variable_types).issubset(set(df.columns))` unless an advanced
  sampler-specific reason exists.
- Ensure treatment, outcome, and all common causes/adjustment variables are keys.
- Recompute mapping after renaming DataFrame columns.

## Weighting Sampler Exact-Match Failure

### Symptom

- `The intervention value(s) provided do not exactly match any observed data points...`

### Cause

The default `weighting` sampler filters to rows whose treatment column exactly
matches the requested `x={...}` value before weighted resampling. This is fragile
for continuous treatments or out-of-support intervention values.

### Fix

- For discrete treatment values, choose values observed in the data.
- For continuous treatments, avoid using exact fixed values with `weighting`
  unless the value exists in the sample and exact matching is meaningful.
- Consider a different do-sampler, classic effect estimation, or a GCM
  intervention workflow depending on the user's goal.

## MCMC And Optional Sampler Dependencies

### Symptom

- Import error for `pymc3`.
- MCMC sampler is slow or fails in a minimal environment.
- MCMC complains about unsupported variable types.

### Causes

- `mcmc` imports PyMC3 at module import time.
- The MCMC sampler builds a Bayesian network and samples; it is substantially
  heavier than weighting.
- Its observed-variable path supports continuous (`c`) and binary (`b`) nodes in
  the model construction branch; other types can raise unrecognized-type errors.

### Fix

- Use `method="weighting"` for minimal smoke tests.
- Use `method="mcmc"` only when PyMC3 is installed and a Bayesian-network
  sampling workflow is intended.
- Keep samples small for validation before expensive MCMC runs.
- Provide complete `variable_types` and validate graph acyclicity.

## Stateful Do-Sampler

### Symptom

- Repeated `.causal.do` calls appear to reuse stale graph, outcome, variables, or
  params.
- Results change after resetting.
- A different method works only after `reset()`.

### Cause

`stateful=True` stores sampler state on the DataFrame accessor namespace. State
is shared across calls on that DataFrame accessor and is reset only when the
method changes, `stateful=False`, or `df.causal.reset()` is called.

### Fix

Call:

```python
df.causal.reset()
```

before changing any of:

- graph;
- common causes;
- outcome;
- treatment variables;
- variable types;
- sampler params;
- method;
- DataFrame content.

Use `stateful=True` only inside a tightly scoped repeated-sampling block.

## Dataset Helper Surprises

### Symptom

- A dataset helper attempts a network call.
- Synthetic dataset column names are not what the user expected.
- Treatment or outcome dtypes differ from intended sampler types.

### Causes

- Public-data helpers such as Lalonde/PSID loaders read URLs at runtime.
- Synthetic helpers use role-based generated names like `v0`, `y`, `W0`, `Z0`,
  `X0`, and `FD0`.
- Binary treatments are often bool; categorical treatments may be pandas
  category; one-hot options change column names.

### Fix

- For no-download checks, use `linear_dataset`, `simple_iv_dataset`,
  `dataset_from_random_graph`, or `sales_dataset`.
- Inspect `data["df"].dtypes` and the returned role-name fields.
- Build `variable_types` from the actual columns after generation.
- Use returned `gml_graph` or `dot_graph` only after validating it matches the
  DataFrame columns.

## Data Transformer Alignment

### Symptom

- PCA/reduced data no longer matches graph node names.
- Downstream DoWhy calls fail after dimensionality reduction.

### Cause

`PCAReducer` returns an array of transformed components. It does not update a
causal graph or DataFrame schema.

### Fix

- Wrap output in a DataFrame with explicit component names.
- Build or update the causal graph using those component names.
- Keep original graph semantics separate from transformed feature-space
  semantics.

## Temporal Helper Errors

### Symptom

- Temporal CSV/DOT creation returns `None`.
- `create_graph_from_networkx_array` raises for `o-o` or `x-x`.
- `shift_columns_by_lag_using_unrolled_graph` returns an empty DataFrame.
- Shifted data contains leading zeros.

### Causes

- Non-integer `time_lag` values.
- Ambiguous or unsupported temporal link markers.
- Unrolled node base names are not present in the raw DataFrame.
- Node names do not follow `base_lag` with an integer final segment.
- The helper uses `fill_value=0` for shifted warm-up rows.

### Fix

1. Validate all lag values are integers.
2. Convert external discovery output to `-->`, `<--`, or empty markers only.
3. Print `sorted(unrolled_graph.nodes)` and compare base names to `df.columns`.
4. Drop the first `max_lag` rows or replace zeros with an appropriate missing
   policy before modeling.
5. Revalidate graph/data column alignment after shifting.

## Deprecated Graph Learners

### Symptom

- Deprecation warning from `CausalModel.learn_graph()`.
- User asks for `dowhy.graph_learners` CDT/GES/LiNGAM workflow.

### Cause

`CausalModel.learn_graph()` and `dowhy.graph_learners` are deprecated. DoWhy's
current boundary is to use external discovery packages directly and pass the
resulting DAG into DoWhy.

### Fix

- Do not build new workflows around deprecated graph learners.
- Use an external package to learn a graph, review it as a hypothesis, convert it
  to `networkx.DiGraph`, GML, or DOT, and pass it to DoWhy via `graph=`.
- Validate the learned graph is directed, acyclic, and aligned with DataFrame
  columns before estimation or GCM modeling.

## Quick Isolation Script

If the problem may be environment-related, run the bundled smoke script from any
working directory:

```bash
python scripts/smoke_graph_and_do.py --samples 100
```

Run that command from this sub-skill directory, or invoke the same bundled script
through whatever path your agent exposes. It checks graph parsing and the pandas
do-sampler without downloads and defaults to GML parsing to avoid DOT parser
dependencies.
