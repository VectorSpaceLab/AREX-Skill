# Graph data API reference

Use these APIs from `graph_nets.graphs` and `graph_nets.utils_np` for NumPy and NetworkX graph data workflows. TensorFlow-specific helpers are routed to the sibling TensorFlow operations sub-skill.

## Imports

```python
import networkx as nx
import numpy as np
from graph_nets import graphs
from graph_nets import utils_np
```

## Field constants

`graph_nets.graphs` defines canonical string constants:

| Constant | Value |
| --- | --- |
| `graphs.NODES` | `"nodes"` |
| `graphs.EDGES` | `"edges"` |
| `graphs.RECEIVERS` | `"receivers"` |
| `graphs.SENDERS` | `"senders"` |
| `graphs.GLOBALS` | `"globals"` |
| `graphs.N_NODE` | `"n_node"` |
| `graphs.N_EDGE` | `"n_edge"` |

Useful field groups:

- `graphs.GRAPH_FEATURE_FIELDS`: `nodes`, `edges`, `globals`.
- `graphs.GRAPH_INDEX_FIELDS`: `receivers`, `senders`.
- `graphs.GRAPH_DATA_FIELDS`: `nodes`, `edges`, `receivers`, `senders`, `globals`.
- `graphs.GRAPH_NUMBER_FIELDS`: `n_node`, `n_edge`.
- `graphs.ALL_FIELDS`: all seven fields.

## `graphs.GraphsTuple(...)`

Construct a batch object directly when arrays are already concatenated and endpoint ids are already batched absolute ids.

```python
graph = graphs.GraphsTuple(
    nodes=nodes,
    edges=edges,
    receivers=receivers,
    senders=senders,
    globals=globals_,
    n_node=n_node,
    n_edge=n_edge)
```

Preflight:

- `n_node` and `n_edge` must be non-`None` arrays or array-like values.
- `receivers` and `senders` must be both non-`None` or both `None`.
- If `receivers` and `senders` are `None`, `edges` must also be `None`.
- Keep endpoint lengths consistent with `sum(n_edge)` even though the namedtuple validates only `None` compatibility.

## `GraphsTuple.replace(**kwargs)`

Returns a copy with selected fields replaced, then validates `None` compatibility.

Use for small structural updates:

```python
without_globals = graph.replace(globals=None)
```

Do not drop only one endpoint field:

```python
# Valid: drop edge features and edge topology together.
no_edge_topology = graph.replace(edges=None, receivers=None, senders=None)
```

## `GraphsTuple.map(field_fn, fields=graphs.GRAPH_FEATURE_FIELDS)`

Applies a callable once per selected field and returns a validated copy. The default mapped fields are `nodes`, `edges`, and `globals`.

```python
normalized = graph.map(lambda x: None if x is None else x.astype(np.float32))
```

Use explicit fields for topology/count transformations:

```python
same_graph = graph.map(lambda x: x, fields=graphs.ALL_FIELDS)
```

## `utils_np.networkx_to_data_dict(graph_nx, node_shape_hint=None, edge_shape_hint=None, data_type_hint=np.float32)`

Converts one NetworkX graph to a single data dictionary.

Expected graph convention:

- `graph_nx` behaves like a NetworkX graph; `networkx.OrderedMultiDiGraph` from `networkx<3` is the safest class.
- Node keys are sequential integers in insertion order.
- Nodes and edges use the `"features"` attribute key.
- Edge attribute `"index"`, when present, determines output edge order.
- Graph globals live in `graph_nx.graph["features"]`; absent means `globals=None`.

Outputs a dictionary containing all seven Graph Nets fields. `n_node` and `n_edge` are counts for the single graph. If the graph has no nodes or no edges, shape hints can request zero-length feature arrays rather than `None`.

## `utils_np.data_dict_to_networkx(data_dict)`

Converts one data dictionary into a `networkx.OrderedMultiDiGraph`.

Behavior:

- Node ids become integer keys `0..n_node-1`.
- Node and edge features are stored under `"features"`.
- Edge order is stored in edge attribute `"index"`.
- If `nodes=None`, `n_node` is required to create featureless nodes.
- If `receivers=None`, no edges are added.
- If `edges=None` but endpoints are present, edges are added with `features=None`.
- `graph.graph["features"]` is set even when globals are `None`.

## `utils_np.networkxs_to_graphs_tuple(graph_nxs, node_shape_hint=None, edge_shape_hint=None, data_type_hint=np.float32)`

Converts an iterable of NetworkX graphs into one batched `GraphsTuple`.

This is equivalent to `networkx_to_data_dict` for each graph followed by `data_dicts_to_graphs_tuple`. Use the shape hints when empty graphs must batch with featureful graphs.

Common failure causes:

- Passing one graph instead of an iterable of graphs.
- Nonsequential node keys.
- Missing node or edge `"features"` attributes.
- Mixing `None` and non-`None` feature values among nodes or among edges.
- Empty graphs without shape hints in a featureful batch.

## `utils_np.graphs_tuple_to_networkxs(graphs_tuple)`

Splits a batched `GraphsTuple` and converts each item to a `networkx.OrderedMultiDiGraph`.

Use this for visualization or object-based inspection after batching. If the environment has `networkx>=3`, the helper may fail because `OrderedMultiDiGraph` was removed.

## `utils_np.data_dicts_to_graphs_tuple(data_dicts)`

Batches an iterable of per-graph data dictionaries.

Behavior:

- Copies input dictionaries before mutation.
- Adds missing data fields with `None`.
- Requires every dictionary to have exactly the same non-`None` key set.
- Converts values to NumPy arrays; casts `receivers`, `senders`, `n_node`, and `n_edge` to `np.int32`.
- Fills missing `n_node` from `nodes.shape[0]`, or `0` when `nodes=None`.
- Fills missing `n_edge` from `receivers.shape[0]`, or `0` when `receivers=None`.
- Concatenates feature/index arrays and stacks global/count arrays.
- Adds cumulative node-count offsets to `receivers` and `senders`.

Preflight helper:

```python
def defined_keys(d):
    return {k for k, v in d.items() if v is not None}

key_sets = [defined_keys(d) for d in data_dicts]
assert all(ks == key_sets[0] for ks in key_sets), key_sets
```

## `utils_np.graphs_tuple_to_data_dicts(graph)`

Unbatches a `GraphsTuple` into a list of per-graph data dictionaries.

Behavior:

- Splits `nodes` by cumulative `n_node`.
- Splits `edges`, `receivers`, and `senders` by cumulative `n_edge`.
- Subtracts cumulative node offsets from endpoints to restore local indices.
- Unstacks `globals` into per-graph values.
- Includes all seven fields in every returned dictionary; fields absent from the batch appear as `None` per graph.

## `utils_np.get_graph(input_graphs, index)`

Extracts one graph or a sub-batch from a NumPy `GraphsTuple`.

```python
one_graph_batch = utils_np.get_graph(batch, 0)
sub_batch = utils_np.get_graph(batch, slice(1, 3))
```

Notes:

- An integer index returns a `GraphsTuple` with one graph, not a bare data dictionary.
- A slice returns a `GraphsTuple` whose counts and endpoint offsets have been recomputed.
- The helper accepts only `int` or `slice`; other index types raise `TypeError`.

## Minimal deterministic round-trip

```python
GraphClass = nx.OrderedMultiDiGraph
g = GraphClass()
g.add_node(0, features=np.array([1.0, 0.0], dtype=np.float32))
g.add_node(1, features=np.array([0.0, 1.0], dtype=np.float32))
g.add_edge(0, 1, features=np.array([0.5], dtype=np.float32), index=0)
g.graph["features"] = np.array([2.0], dtype=np.float32)

data_dict = utils_np.networkx_to_data_dict(g)
batch = utils_np.data_dicts_to_graphs_tuple([data_dict])
restored_dict, = utils_np.graphs_tuple_to_data_dicts(batch)
restored_nx, = utils_np.graphs_tuple_to_networkxs(batch)
```

For a maintained executable version with JSON output, use [the bundled smoke script](../scripts/graph_data_smoke.py).
