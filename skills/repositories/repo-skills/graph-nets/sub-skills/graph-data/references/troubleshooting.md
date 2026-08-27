# Graph data troubleshooting

Use this matrix before changing model code. Most data failures come from invalid `None` combinations, inconsistent batch key sets, endpoint/count mismatches, or NetworkX feature conventions.

## Fast triage checklist

1. Print the seven fields: `nodes`, `edges`, `receivers`, `senders`, `globals`, `n_node`, `n_edge`.
2. Check `n_node is not None` and `n_edge is not None`.
3. Check `receivers is None` exactly matches `senders is None`.
4. If both endpoints are `None`, check `edges is None`.
5. If endpoints exist, check `len(receivers) == len(senders) == sum(n_edge)`.
6. If node features exist, check `nodes.shape[0] == sum(n_node)`.
7. If edge features exist, check `edges.shape[0] == sum(n_edge)`.
8. For data dictionaries, compare non-`None` key sets before batching.
9. For NetworkX, verify sequential node keys and `"features"` attributes.
10. For NetworkX conversion failures under modern NetworkX, check `hasattr(networkx, "OrderedMultiDiGraph")`.

## Common failures

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `Field n_node cannot be None` | Constructed `GraphsTuple` without `n_node`, or featureless data lost its node count. | Provide `n_node` as a one-dimensional count array for each graph; in per-graph dictionaries, include `n_node` when `nodes=None` but nodes exist. |
| `Field n_edge cannot be None` | Constructed `GraphsTuple` without `n_edge`. | Provide `n_edge` as a one-dimensional count array. For no edges, use zeros rather than `None`. |
| Message names `senders` when `receivers` is `None` | Only one endpoint field was dropped or omitted. | Set both `receivers` and `senders`, or set both to `None` together. |
| Message names `receivers` when `senders` is `None` | Only one endpoint field was dropped or omitted. | Set both endpoint arrays together. |
| `edges` rejected when endpoints are `None` | Edge features were supplied without topology arrays. | Supply both `receivers` and `senders`, or set `edges=None` too. |
| `If edges are present, senders and receivers should both be defined.` | A data dictionary has `edges`, `receivers`, or `senders` partially defined. | For featureful or featureless edges, keep both endpoint keys non-`None`; only omit all three when there is no edge topology. |
| `Different set of keys found when iterating over data dictionaries` | Batch dictionaries disagree on non-`None` fields. | Normalize all dictionaries to the same fields. Use zero-length feature arrays for empty featureful graphs, and either include or omit `n_node`/`n_edge` consistently across all dictionaries. |
| Batched endpoints point to wrong nodes | Per-graph endpoints were already globally offset before `data_dicts_to_graphs_tuple`, or counts are wrong. | Use local endpoint ids in each input dictionary; let the helper add offsets. Verify `n_node` before batching. |
| Unbatched endpoints are unexpectedly local | This is expected from `graphs_tuple_to_data_dicts`. | Use batched endpoints on `GraphsTuple`; use local endpoints in per-graph dictionaries and NetworkX graphs. |
| `Cannot create a graph with unspecified number of nodes` | `data_dict_to_networkx` saw `nodes=None` without `n_node`. | Include `n_node` for featureless nodes. |
| Missing `features` key from graph nodes | A NetworkX node lacks the required attribute, often because adding an edge silently created the node. | Add every node explicitly with `features=...` before adding edges; use `None` only when all nodes are featureless. |
| Missing edge `features` key | A NetworkX edge lacks the required attribute. | Add all edges with `features=...`; use `features=None` only when all edges are featureless. |
| `Either all the nodes should have features, or none of them` | NetworkX nodes mix `features=None` and feature arrays. | Choose featureless nodes for every node, or provide arrays for every node with a compatible shape. |
| `Either all the edges should have features, or none of them` | NetworkX edges mix `features=None` and feature arrays. | Choose featureless edges for every edge, or provide arrays for every edge with a compatible shape. |
| `found node with index ... and key ...` | NetworkX node keys are not sequential integers in insertion order. | Relabel/rebuild nodes so `list(g.nodes)[i] == i`, starting at zero. |
| `AttributeError: module 'networkx' has no attribute 'OrderedMultiDiGraph'` | Runtime uses `networkx>=3`, where the class was removed. | Use a `networkx<3` environment for Graph Nets conversion workflows, or avoid helpers that construct `OrderedMultiDiGraph`. |
| Edge order changes after NetworkX conversion | Edge attributes lacked `index`, so NetworkX iteration order controlled output. | Add `index` to each edge when deterministic edge order matters. |
| Empty graph will not batch with featureful graphs | Empty graph conversion produced `nodes=None` or `edges=None`, making key sets differ. | Supply `node_shape_hint` and `edge_shape_hint`, or manually use zero-length arrays with matching trailing dimensions. |

## Defensive validation snippets

Use these checks in notebooks, scripts, or generated examples before handing data to model modules.

```python
import numpy as np


def assert_graphs_tuple_basic(g):
    assert g.n_node is not None, "n_node is required"
    assert g.n_edge is not None, "n_edge is required"
    assert (g.receivers is None) == (g.senders is None), (
        "receivers and senders must be both present or both None")
    if g.receivers is None:
        assert g.edges is None, "edges must be None when endpoints are None"
    else:
        total_edges = int(np.sum(g.n_edge))
        assert len(g.receivers) == total_edges, "receivers length != sum(n_edge)"
        assert len(g.senders) == total_edges, "senders length != sum(n_edge)"
        if g.edges is not None:
            assert g.edges.shape[0] == total_edges, "edges rows != sum(n_edge)"
    if g.nodes is not None:
        assert g.nodes.shape[0] == int(np.sum(g.n_node)), (
            "nodes rows != sum(n_node)")
```

```python
def assert_same_defined_keys(data_dicts):
    key_sets = [{k for k, v in d.items() if v is not None}
                for d in data_dicts]
    if not key_sets:
        return
    if any(ks != key_sets[0] for ks in key_sets):
        raise ValueError("incompatible data_dict key sets: {}".format(key_sets))
```

```python
def assert_networkx_graph_nets_ready(g):
    for expected, (key, attrs) in enumerate(g.nodes(data=True)):
        if key != expected:
            raise ValueError("node key/order mismatch: index {} key {}".format(
                expected, key))
        if "features" not in attrs:
            raise KeyError("node {} is missing features".format(key))
    for sender, receiver, attrs in g.edges(data=True):
        if "features" not in attrs:
            raise KeyError("edge {}->{} is missing features".format(
                sender, receiver))
```

## Decision guide

- If the data is already in arrays, fix the arrays and construct `GraphsTuple` directly.
- If the failure is about inconsistent keys, normalize per-graph dictionaries before batching.
- If the failure is about node ordering or feature keys, rebuild the NetworkX graph explicitly rather than relying on implicit node creation by edge insertion.
- If the failure is TensorFlow placeholder, padding, spec, session, or tensor-shape related, route to [tensorflow-ops](../../tensorflow-ops/SKILL.md).
- If the failure is about which model accepts `None` fields, route to [graph-models](../../graph-models/SKILL.md).
