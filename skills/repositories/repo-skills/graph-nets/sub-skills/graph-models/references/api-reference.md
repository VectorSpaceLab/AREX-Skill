# Graph Nets model API reference

This reference covers the model layer of the installed `graph_nets` package: `graph_nets.blocks`, `graph_nets.modules`, and the Sonnet adapter behavior used by both Sonnet 1 and Sonnet 2 stacks.

## Common contracts

- Model inputs and outputs are `graphs.GraphsTuple` instances containing TensorFlow tensors.
- A `*_model_fn` is a zero-argument callable. It is called during module construction and must return a Sonnet module or any callable with a compatible `__call__` signature.
- Blocks concatenate selected features on the last axis with `tf.concat(..., axis=-1)`. The selected features must have equal rank and equal non-last dimensions after broadcasting or aggregation.
- Reducers must match the `tf.math.unsorted_segment_*` signature: `(values, segment_indices, num_groups) -> reduced_values`.
- All public modules inherit from Graph Nets' `_base.AbstractModule`, which adapts to the installed Sonnet major version. User-defined demo modules still need the right public Sonnet base: `snt.AbstractModule` in Sonnet 1, `snt.Module` in Sonnet 2.

## Broadcasters

| Function | Reads | Produces | Typical use | Required fields |
| --- | --- | --- | --- | --- |
| `blocks.broadcast_globals_to_edges(graph, num_edges_hint=None)` | `globals`, `n_edge` | one global feature row per edge | Add graph-level context to an edge model | `globals`, `n_edge` |
| `blocks.broadcast_globals_to_nodes(graph, num_nodes_hint=None)` | `globals`, `n_node` | one global feature row per node | Add graph-level context to a node model | `globals`, `n_node` |
| `blocks.broadcast_sender_nodes_to_edges(graph)` | `nodes`, `senders` | sender-node feature row per edge | Condition edge updates on source nodes | `nodes`, `senders` |
| `blocks.broadcast_receiver_nodes_to_edges(graph)` | `nodes`, `receivers` | receiver-node feature row per edge | Condition edge updates on target nodes | `nodes`, `receivers` |

Operational notes:

- Broadcasters validate only fields they need. Unused fields may be `None`.
- The optional edge/node hints are performance/XLA hints; do not use them to repair an invalid graph.
- Sender and receiver broadcasters gather `graph.nodes[graph.senders]` or `graph.nodes[graph.receivers]`, so `senders` / `receivers` must index the flattened batched node tensor.

## Aggregators and reducers

| Class/function | Reads | Segment ids | Number of groups | Produces |
| --- | --- | --- | --- | --- |
| `EdgesToGlobalsAggregator(reducer)` | `edges`, `n_edge` | graph index repeated by `n_edge` | number of graphs | one edge summary per graph |
| `NodesToGlobalsAggregator(reducer)` | `nodes`, `n_node` | graph index repeated by `n_node` | number of graphs | one node summary per graph |
| `SentEdgesToNodesAggregator(reducer)` | `edges`, `senders`, `receivers`, usually `n_node` or static `nodes` size | `senders` | number of flattened nodes | one sent-edge summary per node |
| `ReceivedEdgesToNodesAggregator(reducer)` | `edges`, `senders`, `receivers`, usually `n_node` or static `nodes` size | `receivers` | number of flattened nodes | one received-edge summary per node |
| `unsorted_segment_min_or_zero(values, indices, num_groups)` | values and segment ids | `indices` | `num_groups` | segment minimum, zero for empty segments |
| `unsorted_segment_max_or_zero(values, indices, num_groups)` | values and segment ids | `indices` | `num_groups` | segment maximum, zero for empty segments |

Reducer choices:

- Common reducers: `tf.math.unsorted_segment_sum`, `tf.math.unsorted_segment_mean`, `tf.math.unsorted_segment_prod`, `blocks.unsorted_segment_min_or_zero`, `blocks.unsorted_segment_max_or_zero`.
- Use the `*_or_zero` reducers when empty segments should produce zeros rather than TensorFlow's extreme finite min/max defaults.
- Aggregators require a callable reducer; blocks raise `ValueError` if aggregation is enabled and the matching reducer argument is `None`.

## Low-level update blocks

### `blocks.EdgeBlock`

Constructor:

```python
blocks.EdgeBlock(
    edge_model_fn,
    use_edges=True,
    use_receiver_nodes=True,
    use_sender_nodes=True,
    use_globals=True,
    name="edge_block")
```

Behavior:

1. Validates `senders`, `receivers`, and `n_edge` for any edge update.
2. Collects enabled inputs in this order: existing `edges`, receiver nodes, sender nodes, broadcast globals.
3. Concatenates on the last axis.
4. Applies the edge model and returns `graph.replace(edges=updated_edges)`.

Required fields by flag:

| Flag | Additional required fields |
| --- | --- |
| `use_edges=True` | `edges` |
| `use_receiver_nodes=True` | `nodes`, `receivers` |
| `use_sender_nodes=True` | `nodes`, `senders` |
| `use_globals=True` | `globals`, `n_edge` |

At least one of `use_edges`, `use_receiver_nodes`, `use_sender_nodes`, or `use_globals` must be `True`.

### `blocks.NodeBlock`

Constructor:

```python
blocks.NodeBlock(
    node_model_fn,
    use_received_edges=True,
    use_sent_edges=False,
    use_nodes=True,
    use_globals=True,
    received_edges_reducer=tf.math.unsorted_segment_sum,
    sent_edges_reducer=tf.math.unsorted_segment_sum,
    name="node_block")
```

Behavior:

1. Optionally aggregates updated or existing edges into receiver nodes.
2. Optionally aggregates updated or existing edges into sender nodes.
3. Optionally appends existing node features.
4. Optionally broadcasts globals to nodes.
5. Concatenates on the last axis, applies the node model, and returns `graph.replace(nodes=updated_nodes)`.

Required fields by flag:

| Flag | Additional required fields |
| --- | --- |
| `use_received_edges=True` | `edges`, `senders`, `receivers`, and enough node count information (`nodes` first dimension or `n_node`) |
| `use_sent_edges=True` | `edges`, `senders`, `receivers`, and enough node count information (`nodes` first dimension or `n_node`) |
| `use_nodes=True` | `nodes` |
| `use_globals=True` | `globals`, `n_node` |

At least one of `use_received_edges`, `use_sent_edges`, `use_nodes`, or `use_globals` must be `True`. If an edge-aggregation flag is enabled, its reducer must not be `None`.

### `blocks.GlobalBlock`

Constructor:

```python
blocks.GlobalBlock(
    global_model_fn,
    use_edges=True,
    use_nodes=True,
    use_globals=True,
    nodes_reducer=tf.math.unsorted_segment_sum,
    edges_reducer=tf.math.unsorted_segment_sum,
    name="global_block")
```

Behavior:

1. Optionally aggregates edges to each graph.
2. Optionally aggregates nodes to each graph.
3. Optionally appends existing globals.
4. Concatenates on the last axis, applies the global model, and returns `graph.replace(globals=updated_globals)`.

Required fields by flag:

| Flag | Additional required fields |
| --- | --- |
| `use_edges=True` | `edges`, `n_edge` |
| `use_nodes=True` | `nodes`, `n_node` |
| `use_globals=True` | `globals` |

At least one of `use_edges`, `use_nodes`, or `use_globals` must be `True`. If node or edge aggregation is enabled, the matching reducer must not be `None`.

## High-level modules

### `modules.GraphIndependent`

Constructor:

```python
modules.GraphIndependent(
    edge_model_fn=None,
    node_model_fn=None,
    global_model_fn=None,
    name="graph_independent")
```

Use for independent encoders/decoders or per-field transformations. A `None` model function passes that field through unchanged. Non-`None` model functions are wrapped once at construction time.

Reads and updates:

- Reads `edges` only if `edge_model_fn` is not `None`.
- Reads `nodes` only if `node_model_fn` is not `None`.
- Reads `globals` only if `global_model_fn` is not `None`.
- Leaves `senders`, `receivers`, `n_node`, and `n_edge` unchanged.
- Does not assume compatible shapes between edges, nodes, and globals because fields are processed independently.

### `modules.GraphNetwork`

Constructor:

```python
modules.GraphNetwork(
    edge_model_fn,
    node_model_fn,
    global_model_fn,
    reducer=tf.math.unsorted_segment_sum,
    edge_block_opt=None,
    node_block_opt=None,
    global_block_opt=None,
    name="graph_network")
```

Use for general message passing. It composes:

1. `EdgeBlock(edge_model_fn, **edge_block_opt)`
2. `NodeBlock(node_model_fn, **node_block_opt)` on the edge-updated graph
3. `GlobalBlock(global_model_fn, **global_block_opt)` on the edge-and-node-updated graph

Default options use all edge inputs, received-edge aggregation, node features, globals, and edge/node/global aggregation. With defaults, no model-relevant field may be `None` and all participating features must be concatenable on non-last axes.

Option defaults after expansion:

```python
edge_block_opt = {
    "use_edges": True,
    "use_receiver_nodes": True,
    "use_sender_nodes": True,
    "use_globals": True,
}
node_block_opt = {
    "use_received_edges": True,
    "use_sent_edges": False,
    "use_nodes": True,
    "use_globals": True,
    "received_edges_reducer": reducer,
    "sent_edges_reducer": reducer,
}
global_block_opt = {
    "use_edges": True,
    "use_nodes": True,
    "use_globals": True,
    "edges_reducer": reducer,
    "nodes_reducer": reducer,
}
```

### `modules.InteractionNetwork`

Constructor:

```python
modules.InteractionNetwork(
    edge_model_fn,
    node_model_fn,
    reducer=tf.math.unsorted_segment_sum,
    name="interaction_network")
```

Use when only edges and nodes should be updated. It ignores globals and permits `graph.globals` to be `None`. It composes:

- `EdgeBlock(..., use_globals=False)`
- `NodeBlock(..., use_sent_edges=False, use_globals=False, received_edges_reducer=reducer)`

Required fields: `nodes`, `edges`, `senders`, `receivers`, `n_node`, `n_edge`. The input edge and node features must be concatenable for the edge block, and updated edge and node features must be concatenable for the node block.

### `modules.RelationNetwork`

Constructor:

```python
modules.RelationNetwork(
    edge_model_fn,
    global_model_fn,
    reducer=tf.math.unsorted_segment_sum,
    name="relation_network")
```

Use when pairwise node relations are transformed into graph-level outputs. It ignores input edge features and input globals, so those may be `None`. It composes:

- `EdgeBlock(..., use_edges=False, use_receiver_nodes=True, use_sender_nodes=True, use_globals=False)`
- `GlobalBlock(..., use_edges=True, use_nodes=False, use_globals=False, edges_reducer=reducer)`

The returned graph has updated `globals`; original `nodes`, `edges`, `senders`, and `receivers` are preserved.

Required fields: `nodes`, `senders`, `receivers`, `n_node`, `n_edge`.

### `modules.DeepSets`

Constructor:

```python
modules.DeepSets(
    node_model_fn,
    global_model_fn,
    reducer=tf.math.unsorted_segment_sum,
    name="deep_sets")
```

Use for set-style inputs that can be represented as graphs without using edge connectivity. It composes:

- `NodeBlock(..., use_received_edges=False, use_sent_edges=False, use_nodes=True, use_globals=True)`
- `GlobalBlock(..., use_edges=False, use_nodes=True, use_globals=False, nodes_reducer=reducer)`

Required fields: `nodes`, `globals`, and `n_node`. `edges`, `senders`, and `receivers` may be `None` because connectivity is unused. The implementation returns updated nodes and globals; if only original DeepSets-style globals are desired, replace only the globals on the input graph:

```python
output = deep_sets(input_graph)
output = input_graph.replace(globals=output.globals)
```

### `modules.CommNet`

Constructor:

```python
modules.CommNet(
    edge_model_fn,
    node_encoder_model_fn,
    node_model_fn,
    reducer=tf.math.unsorted_segment_sum,
    name="comm_net")
```

Use for communication networks that update nodes from neighboring sender-node features. It ignores input edge features and globals, so those may be `None`, but it requires graph connectivity. It composes:

- `EdgeBlock(..., use_edges=False, use_receiver_nodes=False, use_sender_nodes=True, use_globals=False)`
- `NodeBlock(..., use_received_edges=False, use_sent_edges=False, use_nodes=True, use_globals=False, name="node_encoder_block")`
- `NodeBlock(..., use_received_edges=True, use_sent_edges=False, use_nodes=True, use_globals=False, received_edges_reducer=reducer)`

The returned graph has updated `nodes`; original `edges`, `globals`, `senders`, and `receivers` are preserved.

Required fields: `nodes`, `senders`, `receivers`, `n_node`, `n_edge`.

### `modules.SelfAttention`

Constructor:

```python
modules.SelfAttention(name="self_attention")
```

Call signature:

```python
output_graph = modules.SelfAttention()(
    node_values, node_keys, node_queries, attention_graph)
```

Expected tensor shapes:

- `node_values`: `[total_num_nodes, num_heads, value_size]`
- `node_keys`: `[total_num_nodes, num_heads, key_size]`
- `node_queries`: `[total_num_nodes, num_heads, key_size]` (query/key sizes must match)
- `attention_graph`: a `GraphsTuple` whose `senders`, `receivers`, `n_node`, and `n_edge` define which receiver nodes attend to which sender nodes

Behavior:

1. Broadcast sender keys and values to edges.
2. Broadcast receiver queries to edges.
3. Compute per-edge, per-head logits with `sum(sender_key * receiver_query, axis=-1)`.
4. Normalize logits per receiver node with an unsorted-segment softmax.
5. Aggregate weighted sender values into receiver nodes with received-edge summation.
6. Nodes with no received edges get zero updated values.

Use `SelfAttention` only when the graph connectivity already describes the attention neighborhoods. It does not make a graph fully connected for you.

## Demo architecture API

The bundled scripts reproduce the demo model classes without depending on notebooks or a source checkout:

| Script | Stack | Classes | Notes |
| --- | --- | --- | --- |
| `scripts/demo_models_tf1.py` | Sonnet 1 / TF1-style graph execution | `MLPGraphIndependent`, `MLPGraphNetwork`, `EncodeProcessDecode` | Uses `snt.AbstractModule`, `snt.nets.MLP`, and `snt.LayerNorm()` |
| `scripts/demo_models_tf2.py` | Sonnet 2 / TF2 eager execution | `MLPGraphIndependent`, `MLPGraphNetwork`, `EncodeProcessDecode` | Uses `snt.Module`, `snt.nets.MLP`, and `snt.LayerNorm(axis=-1, create_offset=True, create_scale=True)` |

Shared demo constants:

```python
NUM_LAYERS = 2
LATENT_SIZE = 16
```

`EncodeProcessDecode` pattern:

1. Encode input edges/nodes/globals independently.
2. Repeatedly concatenate the initial latent graph and current latent graph along the feature axis.
3. Apply a core `MLPGraphNetwork` for message passing.
4. Decode with `MLPGraphIndependent`.
5. Optionally project edges/nodes/globals to explicit output sizes with a final `GraphIndependent` of `snt.Linear` layers.

See [`workflows.md`](workflows.md) for task-level recipes and [`troubleshooting.md`](troubleshooting.md) for common failure modes.
