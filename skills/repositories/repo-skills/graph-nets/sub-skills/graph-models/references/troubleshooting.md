# Graph model troubleshooting

Use this reference when a Graph Nets model, block, or bundled demo architecture fails to build or run. Fix input graph/data issues in the graph-data sub-skill first, and fix session, placeholder, padding, or `utils_tf` mechanics in the TensorFlow-ops sub-skill.

## Fast diagnosis table

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `ValueError: \`<field>\` field cannot be None` | A broadcaster, aggregator, block, or module needs a field that is `None` under the selected `use_*` flags | Disable the flag that reads that field, provide the field, or choose a specialized module that intentionally ignores it |
| `At least one of ... must be True` | All source flags in an `EdgeBlock`, `NodeBlock`, or `GlobalBlock` were disabled | Enable at least one source feature or replace the block with an identity/pass-through pattern |
| `... reducer should not be None` | Aggregation was enabled but its reducer argument was `None` | Provide a reducer matching `tf.math.unsorted_segment_sum`'s signature or disable the aggregation flag |
| Shape error mentioning dimensions must match, often around `concat` | Selected features disagree on rank or non-last axes after broadcast/aggregation | Make each participating field share all non-last dimensions; only the final feature axis may differ |
| Sender/receiver gather fails or attention output is wrong | `senders`/`receivers` are absent or do not index the flattened batched node tensor | Rebuild/validate graph data before model assembly |
| `AttributeError: module 'sonnet' has no attribute 'AbstractModule'` | TF1/Sonnet1 demo style is being used in a Sonnet2 environment | Use `snt.Module` and [`../scripts/demo_models_tf2.py`](../scripts/demo_models_tf2.py) |
| `AttributeError: module 'tensorflow' has no attribute 'Session'` or `placeholder` | TF1 graph/session code is running in TF2 without compat mode | Use TF2 eager style, or delegate session/placeholder conversion to TensorFlow-ops guidance |
| `LayerNorm` constructor errors | Sonnet major-version mismatch | Sonnet1 demos use `snt.LayerNorm()`; Sonnet2 demos use `snt.LayerNorm(axis=-1, create_offset=True, create_scale=True)` |
| `SelfAttention` returns zeros for some nodes | Those receiver nodes have no incoming attention edges | Add attention connectivity if that is intended, or handle zero output for isolated receivers |
| `SelfAttention` multiply/reduce shape error | `node_keys` and `node_queries` disagree on key size, or tensors disagree on head axes | Align shapes to `[total_num_nodes, num_heads, feature_size]` and match key/query last axis |

## Field requirements by component

Use this when deciding whether a `None` field is legal.

| Component | Fields that may be `None` | Fields normally required |
| --- | --- | --- |
| `GraphIndependent` | Fields whose model function is `None` | Any field with a non-`None` model function |
| Default `GraphNetwork` | none of the model-relevant graph fields | `edges`, `nodes`, `globals`, `senders`, `receivers`, `n_node`, `n_edge` |
| `InteractionNetwork` | `globals` | `nodes`, `edges`, `senders`, `receivers`, counts |
| `RelationNetwork` | input `edges`, input `globals` | `nodes`, `senders`, `receivers`, counts |
| `DeepSets` | `edges`, `senders`, `receivers` | `nodes`, `globals`, `n_node` |
| `CommNet` | input `edges`, input `globals` | `nodes`, `senders`, `receivers`, counts |
| `SelfAttention` | `attention_graph.nodes`, `attention_graph.edges`, `attention_graph.globals` can be placeholders/`None` because values/keys/queries are separate | `senders`, `receivers`, `n_node`, `n_edge`, plus value/key/query tensors |

For low-level blocks, inspect the `use_*` flags directly:

- `EdgeBlock`: `use_edges` -> `edges`; `use_receiver_nodes` -> `nodes` and `receivers`; `use_sender_nodes` -> `nodes` and `senders`; `use_globals` -> `globals` and `n_edge`. `senders`, `receivers`, and `n_edge` are required for the block itself.
- `NodeBlock`: `use_received_edges` / `use_sent_edges` -> `edges`, `senders`, `receivers`, and node count information; `use_nodes` -> `nodes`; `use_globals` -> `globals` and `n_node`.
- `GlobalBlock`: `use_edges` -> `edges` and `n_edge`; `use_nodes` -> `nodes` and `n_node`; `use_globals` -> `globals`.

## Reducer pitfalls

### Missing reducer

Bad:

```python
blocks.NodeBlock(
    node_model_fn=node_fn,
    use_received_edges=True,
    received_edges_reducer=None)
```

Good:

```python
blocks.NodeBlock(
    node_model_fn=node_fn,
    use_received_edges=True,
    received_edges_reducer=tf.math.unsorted_segment_sum)
```

### Empty-segment max/min surprises

`tf.math.unsorted_segment_max` and `tf.math.unsorted_segment_min` use extreme finite defaults for empty segments. If a graph can have nodes with no received edges or graphs with no edges/nodes, prefer:

```python
blocks.unsorted_segment_max_or_zero
blocks.unsorted_segment_min_or_zero
```

These return zeros for empty groups and were explicitly covered by the package tests.

## Shape and rank debugging

Blocks concatenate selected tensors on `axis=-1` after any broadcast or aggregation. This allows feature-size differences but not rank/non-last-axis differences.

Typical valid pattern:

```text
edges after edge model:     [total_edges, feature_e]
received edge aggregation:  [total_nodes, feature_e]
nodes:                      [total_nodes, feature_n]
broadcast globals to nodes: [total_nodes, feature_g]
concat result:              [total_nodes, feature_e + feature_n + feature_g]
```

Higher-rank features are allowed when non-last axes match:

```text
nodes:   [total_nodes, height, width, channels_n]
edges:   [total_edges, height, width, channels_e]
globals: [num_graphs, height, width, channels_g]
```

After broadcasting or aggregation, the leading element count changes to nodes/edges/graphs, but intermediate axes such as `height` and `width` still must match. If one field is transposed or a Conv2D stride changes only some partial outputs, the next concat can fail.

Debug sequence:

1. Print or inspect the shapes of every enabled source tensor.
2. Manually list what each broadcaster or aggregator will output.
3. Confirm all selected tensors have equal rank.
4. Confirm all axes except the last feature axis match after broadcast/aggregation.
5. If only one source is needed, disable other `use_*` flags to localize the failure.

## Sonnet and TensorFlow major-version issues

The installed Graph Nets package adapts its own modules through `_base.AbstractModule`, but user wrapper code and demo classes still need stack-specific style.

### Sonnet 1 / TF1 stack

- Use `snt.AbstractModule`.
- Put child module construction under `with self._enter_variable_scope():`.
- Implement `_build(...)`.
- Execute tensors in a `tf.Session()` and initialize variables.
- Use [`../scripts/demo_models_tf1.py`](../scripts/demo_models_tf1.py) for demo-style architecture code.

### Sonnet 2 / TF2 stack

- Use `snt.Module`.
- Build child modules in `__init__`.
- Implement `__call__(...)`.
- Rely on eager execution, `.numpy()`, `tf.GradientTape`, and optionally `tf.function`.
- Use [`../scripts/demo_models_tf2.py`](../scripts/demo_models_tf2.py) for demo-style architecture code.

If a future environment has TensorFlow 2 but disables eager execution, route execution mechanics to TensorFlow-ops; do not mix TF1 top-level APIs (`tf.Session`, `tf.placeholder`) into a pure TF2 example.

## `GraphNetwork` option debugging

When a user asks for a partial Graph Network, configure all three internal blocks consistently.

Example goal: update edges and nodes without reading input globals and without updating globals from input globals.

```python
gn = modules.GraphNetwork(
    edge_model_fn=edge_fn,
    node_model_fn=node_fn,
    global_model_fn=global_fn,
    edge_block_opt={"use_globals": False},
    node_block_opt={"use_globals": False},
    global_block_opt={"use_globals": False})
```

If the user does not want updated globals at all, `GraphNetwork` is often too broad. Use `InteractionNetwork` or direct `EdgeBlock` + `NodeBlock` and keep the original globals.

## `SelfAttention` debugging

`SelfAttention` has a different call signature from graph modules. It does not receive one feature-bearing graph as its only input.

Correct inputs:

```text
node_values  [total_num_nodes, num_heads, value_size]
node_keys    [total_num_nodes, num_heads, key_size]
node_queries [total_num_nodes, num_heads, key_size]
attention_graph.senders / receivers / n_node / n_edge
```

Common mistakes:

- Passing a `GraphsTuple` as the first argument instead of `node_values`.
- Supplying node tensors without a head axis.
- Mismatching `key_size` between keys and queries.
- Expecting full self-attention without constructing full sender/receiver connectivity.
- Treating zero outputs for isolated receiver nodes as an error.

## Demo architecture debugging

The demo model classes intentionally create multiple independent MLP/LayerNorm modules; parameters are not shared between every generated edge/node/global model unless you explicitly reuse a callable.

For `EncodeProcessDecode`:

- `num_processing_steps` controls how many decoded outputs are returned.
- `utils_tf.concat([latent0, latent], axis=1)` concatenates graph feature axes; both graphs must have the same non-feature axes and matching non-`None` fields.
- Output projection sizes are optional. If an output size is `None`, that field passes through the decoded field.
- Use the TF1 or TF2 demo script matching the installed Sonnet major version.

## Smoke script interpretation

Run:

```bash
python scripts/graph_model_smoke.py --pretty
```

Healthy output includes:

- `ok: true`
- TensorFlow, Sonnet, and Graph Nets version strings when available
- `mode` as `tf2-eager` or `tf1-session`
- edge/node/global output shapes matching the tiny smoke graph

If `ok` is false, the JSON `error_type` and `error` fields are safe to show in reports because the script avoids local environment paths.
