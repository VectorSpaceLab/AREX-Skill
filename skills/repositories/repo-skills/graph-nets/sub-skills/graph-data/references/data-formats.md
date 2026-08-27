# Graph Nets data formats

This reference summarizes the graph data contracts that future agents need at runtime. It is self-contained; no source checkout is required.

## `graphs.GraphsTuple` fields

`graphs.GraphsTuple` is a `namedtuple` with exactly these fields, in this order:

| Field | Meaning | Shape convention | May be `None`? |
| --- | --- | --- | --- |
| `nodes` | Node features for all graphs in the batch. | `[sum(n_node)] + node_feature_shape` | Yes: nodes still exist, but have no node features. |
| `edges` | Edge features for all graphs in the batch. | `[sum(n_edge)] + edge_feature_shape` | Yes: edges may still exist, but have no edge features. |
| `receivers` | Absolute receiver node index for each edge in the batched node array. | `[sum(n_edge)]`, integer | Yes only when `senders` and `edges` are also `None`. |
| `senders` | Absolute sender node index for each edge in the batched node array. | `[sum(n_edge)]`, integer | Yes only when `receivers` and `edges` are also `None`. |
| `globals` | Per-graph global features. | `[n_graphs] + global_feature_shape` | Yes. |
| `n_node` | Number of nodes per graph. | `[n_graphs]`, integer | No. |
| `n_edge` | Number of edges per graph. | `[n_graphs]`, integer | No. |

Important details:

- Receiver/sender indices are **batched absolute indices**, not per-graph local indices. For graph `i`, add `sum(n_node[:i])` to local endpoint ids.
- `edges=None` does **not** imply `n_edge == 0`. It means existing edges have no edge features. Keep non-`None` `receivers` and `senders` for featureless edges.
- `receivers=None` or `senders=None` means the topology has no edge-index arrays; in that case `edges` must also be `None`.
- `nodes=None` does **not** imply no nodes. Keep `n_node` accurate for featureless nodes.
- `globals=None` only removes graph-level features; it does not affect topology.

## Valid `None` combinations

Valid examples:

- All fields populated.
- Featureless nodes only: `nodes=None`, all other topology and counts present.
- Featureless edges only: `edges=None`, but `receivers`, `senders`, and `n_edge` present.
- No globals: `globals=None`.
- No edge topology: `edges=None`, `receivers=None`, `senders=None`, with `n_edge` still present (usually zeros).
- No feature state: `nodes=None`, `edges=None`, `globals=None`, with valid counts and either valid endpoints or all edge topology fields `None`.

Invalid examples that raise during `GraphsTuple` construction or `replace`:

- `n_node=None` or `n_edge=None`.
- `receivers=None` with non-`None` `senders`, or `senders=None` with non-`None` `receivers`.
- Non-`None` `edges` with both endpoint fields `None`.

## `replace` and `map`

- `graph.replace(**fields)` returns a copy and validates the resulting `None` fields.
- `graph.map(field_fn, fields=...)` reads each selected field from the original graph, applies `field_fn` once per selected field, and then validates the replacement as a whole.
- The default mapped fields are `nodes`, `edges`, and `globals`.
- If you map endpoint fields to `None`, map `edges`, `receivers`, and `senders` together; changing only one endpoint field is invalid.

Example pattern:

```python
from graph_nets import graphs

# Feature scaling that preserves topology.
scaled = graph.map(lambda x: None if x is None else x * 0.5)

# Dropping all edge topology and edge features must be simultaneous.
without_edges = graph.map(lambda _: None, fields=[
    graphs.EDGES, graphs.RECEIVERS, graphs.SENDERS])
```

## Data dictionaries

A data dictionary uses the same field names as `GraphsTuple`:

```python
{
    "nodes": node_array_or_none,
    "edges": edge_array_or_none,
    "receivers": receivers_array_or_none,
    "senders": senders_array_or_none,
    "globals": globals_array_or_none,
    "n_node": node_count_optional,
    "n_edge": edge_count_optional,
}
```

Per-graph data dictionaries usually store **local** endpoint indices. `utils_np.data_dicts_to_graphs_tuple` converts them into batched absolute indices. `utils_np.graphs_tuple_to_data_dicts` subtracts offsets and returns local endpoint indices again.

Rules for `utils_np.data_dicts_to_graphs_tuple`:

- Each dictionary may omit data fields; missing data fields are treated as `None`.
- All dictionaries in the same batch must have the same set of non-`None` keys. This includes `n_node` and `n_edge` if any dictionary supplies them.
- If `nodes` is non-`None`, `n_node` can be inferred from `nodes.shape[0]`. If `nodes=None`, provide `n_node` when featureless nodes must be preserved; otherwise the helper fills `0`.
- If `receivers` is non-`None`, `n_edge` can be inferred from `receivers.shape[0]`. If `receivers=None`, the helper fills `0`.
- `receivers`, `senders`, `n_node`, and `n_edge` are cast to `np.int32`.
- Feature arrays keep their NumPy dtype after conversion.
- `globals` and number fields are stacked over graphs; `nodes`, `edges`, `receivers`, and `senders` are concatenated over their leading dimension.

To batch an empty graph with featureful non-empty graphs, keep the key set compatible by using zero-length arrays with the same trailing feature dimensions:

```python
empty_featureful = {
    "nodes": np.zeros((0, node_dim), dtype=np.float32),
    "edges": np.zeros((0, edge_dim), dtype=np.float32),
    "receivers": np.zeros((0,), dtype=np.int32),
    "senders": np.zeros((0,), dtype=np.int32),
    "globals": np.zeros((global_dim,), dtype=np.float32),
    "n_node": 0,
    "n_edge": 0,
}
```

## NetworkX graph convention

Graph Nets NumPy conversion expects NetworkX graphs with the following conventions:

- Prefer `networkx.OrderedMultiDiGraph` from `networkx<3` because the reverse conversion creates that class.
- Node keys must be sequential integers in insertion order: `list(graph_nx.nodes)[i] == i`.
- Every node attribute dictionary must contain a `"features"` key.
- Every edge attribute dictionary must contain a `"features"` key.
- All node feature values are either non-`None`, or all are `None`; mixed node feature presence raises.
- All edge feature values are either non-`None`, or all are `None`; mixed edge feature presence raises.
- `graph_nx.graph["features"]` is used for globals. If the key is absent, globals become `None`.
- If an edge attribute contains `"index"`, `networkx_to_data_dict` sorts edges by that value before emitting `senders`, `receivers`, and `edges`.
- For an empty graph, `node_shape_hint` and `edge_shape_hint` can create zero-length feature arrays. Without hints, the corresponding feature fields remain `None`.

## Batch offsets and slicing

For a list of per-graph dictionaries:

1. The first graph keeps its local endpoint ids.
2. The second graph endpoints are offset by the first graph's `n_node`.
3. Graph `i` endpoints are offset by `sum(n_node[:i])`.

`utils_np.graphs_tuple_to_data_dicts` and `utils_np.get_graph` undo those offsets for the extracted per-graph representation. `utils_np.get_graph(batch, 2)` returns a one-graph batch; `utils_np.get_graph(batch, slice(1, 3))` returns a sub-batch.
