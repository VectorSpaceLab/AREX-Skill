# Data Formats for StellarGraph Objects

## Purpose

Use this reference to construct a valid in-memory `StellarGraph` or
`StellarDiGraph` before moving to samplers, generators, or models.

## Core constructor pattern

Verified constructor signatures:

```python
StellarGraph(
    nodes=None,
    edges=None,
    *,
    is_directed=False,
    source_column="source",
    target_column="target",
    edge_weight_column="weight",
    edge_type_column=None,
    node_type_default="default",
    edge_type_default="default",
    dtype="float32",
    graph=None,
    node_type_name="label",
    edge_type_name="label",
    node_features=None,
)
StellarDiGraph(nodes=None, edges=None, *, source_column="source", target_column="target", ...)
```

Use `StellarGraph` for undirected edges and `StellarDiGraph` for directed edges.
`StellarDiGraph` is equivalent to `StellarGraph(..., is_directed=True)` with a
separate public constructor.

## Pandas homogeneous graph

```python
import pandas as pd
from stellargraph import StellarGraph

nodes = pd.DataFrame(
    {"feat_0": [1.0, 0.0, 1.0], "feat_1": [0.0, 1.0, 1.0]},
    index=["a", "b", "c"],
)
edges = pd.DataFrame({"source": ["a", "b"], "target": ["b", "c"]})

graph = StellarGraph(nodes=nodes, edges=edges)
print(graph.node_feature_sizes())  # {'default': 2}
```

Rules:

- Node DataFrame index values are node IDs.
- Edge DataFrames need `source` and `target` columns by default.
- Numeric non-special node columns are node features.
- Numeric non-special edge columns are edge features; `weight` is the default
  edge-weight column.
- If `nodes` is omitted, nodes are inferred from edge endpoints with no features.

## Weighted and typed edges

For a single edge DataFrame with explicit types:

```python
edges = pd.DataFrame(
    {
        "source": ["u1", "u1", "u2"],
        "target": ["m1", "m2", "m1"],
        "relation": ["rates", "rates", "rates"],
        "weight": [5.0, 3.0, 4.0],
    }
)
graph = StellarGraph(nodes=nodes, edges=edges, edge_type_column="relation")
```

For multiple edge types with separate DataFrames:

```python
edges = {
    "friend": pd.DataFrame({"source": ["u1"], "target": ["u2"]}),
    "rates": pd.DataFrame({"source": ["u1"], "target": ["m1"], "weight": [5.0]}),
}
graph = StellarGraph(nodes=nodes_by_type, edges=edges)
```

## Heterogeneous nodes

Use a dictionary keyed by node type. Each value is an `IndexedArray` or DataFrame
whose rows belong to that type.

```python
users = pd.DataFrame({"age": [22.0, 35.0]}, index=["user:1", "user:2"])
movies = pd.DataFrame({"year": [1999.0]}, index=["movie:1"])
nodes = {"user": users, "movie": movies}
```

Important: external node IDs must be unique across all node types. If an input
source uses overlapping integer IDs for users and movies, prefix or otherwise
disambiguate them before constructing the graph.

## NumPy and IndexedArray

Use NumPy only when IDs are the row numbers `0, 1, 2, ...`:

```python
import numpy as np
from stellargraph import StellarGraph

features = np.array([[1.0, 0.0], [0.0, 1.0]])
edges = pd.DataFrame({"source": [0], "target": [1]})
graph = StellarGraph(nodes=features, edges=edges)
```

Use `IndexedArray(values, index=ids)` when features are a NumPy array but IDs
are not row numbers:

```python
from stellargraph import IndexedArray
features = IndexedArray([[1.0, 0.0], [0.0, 1.0]], index=["a", "b"])
```

For nodes with no features, `IndexedArray(index=node_ids)` creates valid rows
with zero-width features.

## NetworkX conversion

Use `StellarGraph.from_networkx(...)` when a NetworkX graph already holds
structure and features:

```python
import networkx as nx
from stellargraph import StellarGraph

g = nx.Graph()
g.add_node("a", feature=[1.0, 0.0], label="paper")
g.add_node("b", feature=[0.0, 1.0], label="paper")
g.add_edge("a", "b", weight=1.0, label="cites")
sg_graph = StellarGraph.from_networkx(
    g,
    node_type_attr="label",
    edge_type_attr="label",
    edge_weight_attr="weight",
    node_features="feature",
)
```

The legacy `StellarGraph(nx_graph)` constructor path exists but is deprecated;
prefer `from_networkx` for new guidance.

## Validation before modeling

Run these checks before choosing generators:

```python
print(graph.info())
print(graph.node_types, graph.edge_types)
print(graph.node_feature_sizes())
print(graph.edge_feature_sizes())
print(graph.number_of_nodes(), graph.number_of_edges())
graph.check_graph_for_ml()
```

`check_graph_for_ml(features=True)` is useful when a downstream neural model
requires numeric node features. Use `features=False` only for workflows such as
pure structure-based random walks where missing node features are intentional.
