# Graph model workflows

Use these workflows to choose a model architecture, wire Sonnet factories, and validate field/shape assumptions before training or exporting code.

## 1. Pick the smallest architecture that matches the task

| Task intent | Preferred module | Why | Main required inputs |
| --- | --- | --- | --- |
| Encode or decode edge/node/global features independently | `modules.GraphIndependent` | No message passing, field-wise transformation only | Only fields with non-`None` model functions |
| General message passing over edges, nodes, and globals | `modules.GraphNetwork` | Full Graph Network update: edge -> node -> global | Defaults require edges, nodes, globals, senders, receivers, `n_node`, `n_edge` |
| Physical interaction or message passing that ignores globals | `modules.InteractionNetwork` | Updates edges and nodes; globals pass through | nodes, edges, senders, receivers, counts |
| Pairwise relational reasoning to graph-level output | `modules.RelationNetwork` | Builds relation edges from sender/receiver nodes, then aggregates to globals | nodes, senders, receivers, counts; input edges/globals can be `None` |
| Set processing with no edge dependence | `modules.DeepSets` | Node update from node+global, then node aggregation to globals | nodes, globals, `n_node`; edges/connectivity can be `None` |
| Node communication from neighbor sender features | `modules.CommNet` | Computes messages from sender nodes and updates nodes | nodes, senders, receivers, counts; input edges/globals can be `None` |
| Attention over an existing connectivity pattern | `modules.SelfAttention` | Multi-head receiver attention over sender neighborhoods | values/keys/queries with head axes; attention graph connectivity |

If the task starts with raw Python dictionaries, NetworkX objects, padding, masks, or placeholders, prepare those pieces through the neighboring graph-data or TensorFlow-ops sub-skill first.

## 2. Write safe Sonnet model factories

A Graph Nets block stores a model produced by a zero-argument factory. Prefer this pattern:

```python
from graph_nets import modules
import sonnet as snt


def make_mlp_model(output_size=32):
    return snt.nets.MLP([output_size, output_size])

model = modules.GraphNetwork(
    edge_model_fn=lambda: make_mlp_model(32),
    node_model_fn=lambda: make_mlp_model(32),
    global_model_fn=lambda: make_mlp_model(32))
```

Do not pass an already-called tensor transformation as the factory result unless it is intentionally reusable as a callable. Do not instantiate a new Sonnet submodule inside every call of a module that has already been constructed; instantiate in the zero-argument factory or in the module's `__init__`.

### Sonnet 1 vs Sonnet 2 style

```python
# Sonnet 1 / TF1 custom wrapper style.
class MyTF1Model(snt.AbstractModule):
    def __init__(self, name="MyTF1Model"):
        super(MyTF1Model, self).__init__(name=name)
        with self._enter_variable_scope():
            self._network = modules.GraphNetwork(edge_fn, node_fn, global_fn)

    def _build(self, graph):
        return self._network(graph)
```

```python
# Sonnet 2 / TF2 custom wrapper style.
class MyTF2Model(snt.Module):
    def __init__(self, name="MyTF2Model"):
        super().__init__(name=name)
        self._network = modules.GraphNetwork(edge_fn, node_fn, global_fn)

    def __call__(self, graph):
        return self._network(graph)
```

The bundled demo scripts show the full pattern:

- [`../scripts/demo_models_tf1.py`](../scripts/demo_models_tf1.py)
- [`../scripts/demo_models_tf2.py`](../scripts/demo_models_tf2.py)

## 3. Build an independent encoder or decoder

Use `GraphIndependent` when edge/node/global fields do not interact.

```python
from graph_nets import modules
import sonnet as snt

encoder = modules.GraphIndependent(
    edge_model_fn=lambda: snt.nets.MLP([16, 16]),
    node_model_fn=lambda: snt.nets.MLP([16, 16]),
    global_model_fn=lambda: snt.nets.MLP([16, 16]))
latent_graph = encoder(input_graph)
```

Partial transforms are valid:

```python
# Project only nodes; pass edges and globals through unchanged.
node_decoder = modules.GraphIndependent(
    edge_model_fn=None,
    node_model_fn=lambda: snt.Linear(3),
    global_model_fn=None)
output_graph = node_decoder(latent_graph)
```

Checklist:

- Non-`None` model functions require the corresponding field to be non-`None`.
- Field shapes do not need to match each other because fields are processed independently.
- Gradients flow only from each output field to its matching input field.

## 4. Build a general `GraphNetwork`

Default message-passing recipe:

```python
from graph_nets import blocks, modules
import tensorflow as tf
import sonnet as snt


def mlp_factory(size):
    return lambda: snt.nets.MLP([size, size])

gn = modules.GraphNetwork(
    edge_model_fn=mlp_factory(32),
    node_model_fn=mlp_factory(32),
    global_model_fn=mlp_factory(32),
    reducer=tf.math.unsorted_segment_sum)
output_graph = gn(input_graph)
```

Customize field use when some input fields are absent or intentionally ignored:

```python
# Example: ignore input globals but still update edges and nodes.
gn_no_global_context = modules.GraphNetwork(
    edge_model_fn=lambda: snt.nets.MLP([32]),
    node_model_fn=lambda: snt.nets.MLP([32]),
    global_model_fn=lambda: snt.nets.MLP([32]),
    edge_block_opt={
        "use_edges": True,
        "use_receiver_nodes": True,
        "use_sender_nodes": True,
        "use_globals": False,
    },
    node_block_opt={
        "use_received_edges": True,
        "use_sent_edges": False,
        "use_nodes": True,
        "use_globals": False,
    },
    global_block_opt={
        "use_edges": True,
        "use_nodes": True,
        "use_globals": False,
    })
```

Use `blocks.unsorted_segment_max_or_zero` or `blocks.unsorted_segment_min_or_zero` when empty receivers, nodes, or graphs should map to zero under max/min reduction.

Validation checklist:

- With default options, `edges`, `nodes`, `globals`, `senders`, `receivers`, `n_node`, and `n_edge` must all be non-`None`.
- If `use_received_edges` or `use_sent_edges` is enabled, make sure the matching reducer is not `None`.
- If `use_edges` or `use_nodes` is enabled in `GlobalBlock`, make sure `edges_reducer` or `nodes_reducer` is not `None`.
- All selected tensors that are concatenated must match on non-last dimensions.

## 5. Use low-level blocks directly

Direct blocks are useful when you need a custom ordering or want to update only one field.

### Edge-only update

```python
edge_block = blocks.EdgeBlock(
    edge_model_fn=lambda: snt.nets.MLP([8]),
    use_edges=True,
    use_receiver_nodes=True,
    use_sender_nodes=True,
    use_globals=False)
edge_updated = edge_block(input_graph)
```

### Node update from sent and received edges

```python
node_block = blocks.NodeBlock(
    node_model_fn=lambda: snt.nets.MLP([8]),
    use_received_edges=True,
    use_sent_edges=True,
    use_nodes=True,
    use_globals=False,
    received_edges_reducer=tf.math.unsorted_segment_sum,
    sent_edges_reducer=blocks.unsorted_segment_max_or_zero)
node_updated = node_block(edge_updated)
```

### Global update from nodes only

```python
global_block = blocks.GlobalBlock(
    global_model_fn=lambda: snt.nets.MLP([8]),
    use_edges=False,
    use_nodes=True,
    use_globals=False,
    nodes_reducer=tf.math.unsorted_segment_mean)
global_updated = global_block(node_updated)
```

Direct-block checklist:

- Never set all `use_*` flags in a block to `False`.
- For any aggregation flag that is `True`, provide a reducer.
- For any source flag that is `True`, ensure the graph field is non-`None` before building the block.

## 6. Use specialized high-level modules

### `InteractionNetwork`

```python
interaction = modules.InteractionNetwork(
    edge_model_fn=lambda: snt.nets.MLP([32]),
    node_model_fn=lambda: snt.nets.MLP([32]),
    reducer=tf.math.unsorted_segment_sum)
output = interaction(input_graph)
```

Use when graph-level features are irrelevant. `globals` may be `None`; nodes, edges, senders, and receivers are required.

### `RelationNetwork`

```python
relation = modules.RelationNetwork(
    edge_model_fn=lambda: snt.nets.MLP([32]),
    global_model_fn=lambda: snt.nets.MLP([8]),
    reducer=blocks.unsorted_segment_max_or_zero)
output = relation(input_graph)
# output.globals contains the relation-level prediction; original nodes/edges are preserved.
```

Use when pairwise sender/receiver node relations are enough. Input `edges` and `globals` may be `None`.

### `DeepSets`

```python
deep_sets = modules.DeepSets(
    node_model_fn=lambda: snt.nets.MLP([32]),
    global_model_fn=lambda: snt.nets.MLP([8]),
    reducer=tf.math.unsorted_segment_mean)
output = deep_sets(set_graph)
```

Use when edge connectivity should not affect computation. `edges`, `senders`, and `receivers` may be `None`; `nodes`, `globals`, and `n_node` are required.

### `CommNet`

```python
comm_net = modules.CommNet(
    edge_model_fn=lambda: snt.nets.MLP([16]),
    node_encoder_model_fn=lambda: snt.nets.MLP([16]),
    node_model_fn=lambda: snt.nets.MLP([16]),
    reducer=tf.math.unsorted_segment_sum)
output = comm_net(input_graph)
```

Use when messages depend on sender-node features and the output of interest is updated node state. Input edge features and globals may be `None`; graph connectivity is required.

## 7. Apply `SelfAttention` over graph connectivity

`SelfAttention` does not create attention edges. Use an attention graph whose `senders` and `receivers` encode the allowed sender-to-receiver attention pairs.

```python
from graph_nets import modules

self_attention = modules.SelfAttention()
attended_graph = self_attention(
    node_values=node_values,      # [total_num_nodes, num_heads, value_size]
    node_keys=node_keys,          # [total_num_nodes, num_heads, key_size]
    node_queries=node_queries,    # [total_num_nodes, num_heads, key_size]
    attention_graph=attention_graph)
updated_values = attended_graph.nodes
```

Checklist:

- `node_keys` and `node_queries` must agree on the last `key_size` axis.
- `node_values`, `node_keys`, and `node_queries` must agree on `[total_num_nodes, num_heads]`.
- `attention_graph.senders` and `attention_graph.receivers` must be non-`None` and valid for the flattened node set.
- Receiver nodes with no incoming attention edges produce zeros.

## 8. Use the encode-process-decode demo pattern

The bundled demo classes provide the model skeleton used by Graph Nets examples:

```python
# Select the script matching the installed Sonnet major version.
from demo_models_tf2 import EncodeProcessDecode  # for Sonnet 2 environments

model = EncodeProcessDecode(edge_output_size=2, node_output_size=3, global_output_size=1)
outputs_by_step = model(input_graph, num_processing_steps=3)
last_output = outputs_by_step[-1]
```

Core idea:

1. `MLPGraphIndependent` encodes each field to latent features.
2. Each processing step concatenates the initial latent graph and the current latent graph with `utils_tf.concat([...], axis=1)`.
3. `MLPGraphNetwork` performs one message-passing step.
4. `MLPGraphIndependent` decodes each field.
5. A final `GraphIndependent` applies optional linear output projections.

Do not copy notebook training loops unless the user explicitly needs a full demo reproduction; for architecture reuse, the bundled scripts are sufficient.

## 9. Quick installed-package smoke

Run the sub-skill's tiny smoke before depending on the model layer in a new environment:

```bash
python scripts/graph_model_smoke.py --pretty
```

Expected behavior:

- Prints JSON only.
- Reports TensorFlow, Sonnet, and Graph Nets versions when available.
- Builds a tiny `GraphIndependent` with pure TensorFlow callables.
- Runs in TF2 eager mode or TF1 graph/session mode depending on the installed stack.

Use [`troubleshooting.md`](troubleshooting.md) for errors surfaced by the smoke.
