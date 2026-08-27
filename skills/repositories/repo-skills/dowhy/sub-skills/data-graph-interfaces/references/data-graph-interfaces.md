# Data and Graph Interfaces

This reference covers DoWhy graph formats, graph/data alignment, built-in
synthetic datasets, data transformers, plotting, and the deprecated graph
learner boundary.

## Graph representations

DoWhy primarily works with NetworkX directed graphs.

```python
import networkx as nx

graph = nx.DiGraph([("W", "T"), ("W", "Y"), ("T", "Y")])
```

The graph can then be passed to classic `CausalModel` workflows, some GCM
workflows, and lower-level graph helpers. For downstream estimation/refutation,
route to `../effect-estimation/SKILL.md`. For `dowhy.gcm`, route to
`../graphical-causal-models/SKILL.md`.

### Accepted string formats

`dowhy.graph.build_graph_from_str(graph_str)` returns a NetworkX directed graph.
It accepts:

- DOT graph strings such as `digraph { W -> T; W -> Y; T -> Y; }`.
- GML graph strings containing `graph [...]`.
- DAGitty strings beginning with `dag`, which are converted to DOT internally.
- A text-file path ending in `.txt`, where the file contains one of the graph
  encodings.
- File paths ending in `.dot` or `.gml`, parsed with the corresponding NetworkX
  readers.

Do not depend on a local checkout path in reusable code. If a user has an input
file, read it from their project path or copy the graph string into the code
that needs it.

### DOT parser fallback

DOT parsing tries pygraphviz first and then pydot. If pygraphviz is missing,
DoWhy can still parse many DOT strings through pydot if pydot is installed. GML
and direct NetworkX graphs avoid this optional parser dependency.

### DAGitty conversion

DAGitty text is normalized by replacing the leading `dag` with `digraph` and by
converting DAGitty attributes such as `latent` into DOT-style attributes. Use
this for importing a DAGitty diagram, not for checking whether a graph is
causally valid.

## Building a graph from variable roles

`dowhy.graph.build_graph(...)` creates a simple directed graph from treatment,
outcome, common-cause, instrument, effect-modifier, and mediator names.

```python
from dowhy.graph import build_graph

graph = build_graph(
    action_nodes=["T"],
    outcome_nodes=["Y"],
    common_cause_nodes=["W"],
    instrument_nodes=["Z"],
    effect_modifier_nodes=["X"],
    mediator_nodes=["M"],
)
```

Role semantics:

- Treatments point to outcomes.
- Common causes point to both treatments and outcomes.
- Instruments point to treatments.
- Effect modifiers are treated as direct causes of the outcome in the simple
  graph builder.
- Mediators sit on treatment-to-outcome paths.

For richer assumptions, supply an explicit NetworkX graph, DOT, or GML instead
of relying on the simple builder.

## `CausalGraph` wrapper

`dowhy.causal_graph.CausalGraph` accepts a NetworkX `DiGraph`, a GCM
probabilistic causal model, a graph string, a `.txt` graph file, or role-name
inputs. It adds DoWhy metadata such as observed-node attributes and provides
helpers for:

- `get_common_causes`, `get_instruments`, and `get_effect_modifiers`.
- `check_valid_backdoor_set` and `check_valid_frontdoor_set`.
- `do_surgery` for removing incoming or outgoing edges around intervention
  nodes.
- `get_adjacency_matrix` and directed-path checks.

`missing_nodes_as_confounders=True` adds DataFrame columns missing from the
graph as common causes of treatment/outcome. Use it only when that assumption is
intended; silent graph expansion can be surprising.

## Graph/data column alignment

Before fitting, sampling, identifying, or handing off to another sub-skill, run
a schema check:

```python
graph_nodes = set(graph.nodes)
data_columns = set(df.columns)
missing_columns = graph_nodes - data_columns
unused_columns = data_columns - graph_nodes
```

Interpretation:

- Missing columns are usually blocking for tasks that fit models or select
  parent columns. Rename graph nodes or DataFrame columns; do not silently drop
  required parents.
- Extra data columns are allowed for many classic workflows but should be made
  explicit. In GCM fitting, every graph node must have a matching column.
- Unobserved graph nodes may be represented with `observed="no"` metadata and
  can affect identification. Make them explicit rather than pretending they are
  data columns.

## Built-in datasets

Useful public dataset helpers include:

- `dowhy.datasets.linear_dataset(...)`: synthetic potential-outcomes-style
  data with metadata keys such as `df`, treatment/outcome names, confounder
  names, instruments, effect modifiers, frontdoor variables, DOT/GML graph
  strings, and the true ATE.
- `dowhy.datasets.simple_iv_dataset(...)`: compact IV data generator.
- `dowhy.datasets.xy_dataset(...)`: simple X/Y synthetic data.
- `dowhy.datasets.dataset_from_random_graph(...)` and
  `linear_dataset_from_graph(...)`: generate data from a graph and variable
  type specifications.
- `dowhy.datasets.sales_dataset(...)`: synthetic sales/time-indexed business
  data.
- `lalonde_dataset()` and `psid_dataset()` load bundled observational datasets
  from the installed package when available.

Dataset helpers are for examples, smoke tests, and controlled experiments. Do
not treat generated true ATEs as evidence for a user's real graph.

## Data transformers

`dowhy.data_transformer.DimensionalityReducer` is an abstract base class. The
bundled implementation `dowhy.data_transformers.pca_reducer.PCAReducer` wraps
scikit-learn PCA and optionally standardizes inputs:

```python
from dowhy.data_transformers.pca_reducer import PCAReducer

reduced = PCAReducer(feature_matrix, ndims=2, standardize=True).reduce()
```

Use reducers before causal modeling only when the transformed dimensions have a
clear role in the graph or the user accepts the interpretability trade-off. If
a transformed feature is used in the graph, its column name must still align
with graph node labels.

## Plotting

`dowhy.utils.plotting.plot(graph, ...)` chooses the best available backend:

1. Graphviz/pygraphviz for nicer graph layouts when available.
2. NetworkX/matplotlib fallback if pygraphviz import or graphviz plotting
   fails.

Other helpers include `plot_adjacency_matrix`, `bar_plot`, and
`pretty_print_graph` for time-lag edge metadata.

For scripts and headless runs, set `display_plot=False` and provide a filename
only when the user explicitly wants an output file.

## Deprecated graph learner boundary

`CausalModel.learn_graph()` and `dowhy.graph_learners` are deprecated. If the
user needs causal discovery, recommend using external causal-discovery tools
such as causal-learn or dodiscover directly, then pass the discovered graph into
DoWhy as a NetworkX graph, DOT, or GML. Do not build new workflows around the
deprecated learner wrappers.
