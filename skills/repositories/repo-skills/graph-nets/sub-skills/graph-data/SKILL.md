---
name: graph-data
description: "Create, validate, batch, slice, and convert Graph Nets graph data
  with GraphsTuple, data dictionaries, NumPy arrays, and NetworkX graphs."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Graph Data

Use this sub-skill when a task needs to build or inspect Graph Nets data before it reaches TensorFlow or Sonnet modules. It covers `graphs.GraphsTuple`, per-graph data dictionaries, NumPy arrays, NetworkX conversion, batching, unbatching, and slicing.

## Read first

- [Data formats](references/data-formats.md): field semantics, valid `None` combinations, batch offsets, data dictionary rules, and NetworkX feature conventions.
- [API reference](references/api-reference.md): exact NumPy conversion and slicing functions, expected inputs/outputs, and common preflight checks.
- [Troubleshooting](references/troubleshooting.md): fast diagnosis for key-set, endpoint, feature, and NetworkX compatibility failures.
- [Smoke script](scripts/graph_data_smoke.py): deterministic round-trip check that prints JSON and can be run from any working directory.

## Typical workflows

1. **Create a `GraphsTuple` directly** when arrays are already in batched form. Provide all seven fields: `nodes`, `edges`, `receivers`, `senders`, `globals`, `n_node`, and `n_edge`; keep `n_node` and `n_edge` non-`None`.
2. **Create from per-graph data dictionaries** when each sample is easier to describe independently. Use `utils_np.data_dicts_to_graphs_tuple`, and make every dictionary have the same non-`None` field set.
3. **Create from NetworkX** when graph topology is naturally object-based. Use `utils_np.networkx_to_data_dict` for one graph or `utils_np.networkxs_to_graphs_tuple` for a batch; enforce ordered integer node keys and the `"features"` attribute convention.
4. **Round-trip or inspect a batch** with `utils_np.graphs_tuple_to_data_dicts`, `utils_np.graphs_tuple_to_networkxs`, or `utils_np.get_graph`.
5. **Use `GraphsTuple.replace` or `GraphsTuple.map`** for structural-preserving field updates; invalid `None` combinations still raise immediately.

## Boundary routing

- TensorFlow placeholders, tensor batching, padding, specs, `tf.Session` handling, and `utils_tf` workflows belong to [tensorflow-ops](../tensorflow-ops/SKILL.md).
- Sonnet blocks, graph network modules, learned architecture choices, and model call requirements belong to [graph-models](../graph-models/SKILL.md).
- Long notebook-style training recipes belong to the root [demo recipes](../../references/demo-recipes.md) and, for model construction, [graph-models](../graph-models/SKILL.md).

## Minimum preflight checklist

- Confirm whether the graph is featureful or featureless separately for nodes, edges, and globals.
- Confirm `receivers` and `senders` are both present or both absent; featureless edges still need endpoints.
- Confirm `n_node` and `n_edge` are present for manually constructed `GraphsTuple` objects and for featureless/empty data dictionaries that cannot infer counts from arrays.
- When batching, confirm all data dictionaries have identical non-`None` key sets, including number fields if any dictionary provides them.
- When using NetworkX, confirm the runtime has `networkx.OrderedMultiDiGraph` or another compatible `networkx<3` graph class accepted by the conversion path.
