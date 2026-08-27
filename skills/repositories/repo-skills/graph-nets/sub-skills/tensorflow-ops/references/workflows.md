# TensorFlow GraphsTuple workflows

The recipes below use installed public modules only: `graph_nets.graphs`,
`graph_nets.utils_np`, and `graph_nets.utils_tf`. They are intended as patterns
to adapt in user code, not as commands to run against the source checkout.

## 1. Build a tensor GraphsTuple from data dicts

```python
import numpy as np
from graph_nets import utils_tf

DATA_DICTS = [
    {
        "nodes": np.array([[0.0], [1.0]], dtype=np.float32),
        "edges": np.array([[0.5]], dtype=np.float32),
        "senders": np.array([0], dtype=np.int32),
        "receivers": np.array([1], dtype=np.int32),
        "globals": np.array([1.0], dtype=np.float32),
    },
    {
        "nodes": np.array([[2.0]], dtype=np.float32),
        "edges": np.zeros([0, 1], dtype=np.float32),
        "senders": np.zeros([0], dtype=np.int32),
        "receivers": np.zeros([0], dtype=np.int32),
        "globals": np.array([2.0], dtype=np.float32),
    },
]

graphs_tuple = utils_tf.data_dicts_to_graphs_tuple(DATA_DICTS)
```

Checklist:

- Keep all graph dicts consistent about which fields are non-`None`.
- Index and count fields become `tf.int32` tensors.
- If a graph has no edge set, make `edges`, `senders`, and `receivers` all
  absent/`None`; do not leave only one of them missing.

## 2. TF1 placeholder and feed-dict path

Use this only in a TF1-compatible stack with top-level `tf.Session` and
`tf.placeholder`.

```python
import numpy as np
import tensorflow as tf
from graph_nets import utils_np, utils_tf

example_dicts = [
    {"nodes": np.zeros([2, 3], np.float32), "globals": np.zeros([1], np.float32)},
]
feed_dicts = [
    {"nodes": np.ones([4, 3], np.float32), "globals": np.array([7.0], np.float32)},
]

placeholders = utils_tf.placeholders_from_data_dicts(
    example_dicts, force_dynamic_num_graphs=True)
feed_graph = utils_np.data_dicts_to_graphs_tuple(feed_dicts)
fetches = utils_tf.make_runnable_in_session(placeholders)

with tf.Session() as sess:
    out = sess.run(fetches, feed_dict=utils_tf.get_feed_dict(placeholders, feed_graph))
```

When placeholder construction starts from NetworkX samples, use
`placeholders_from_networkxs` to infer the same placeholder structure; keep
non-placeholder NetworkX conversion details in the graph-data sub-skill.

## 3. TF2 eager path and NumPy conversion

```python
import numpy as np
from graph_nets import utils_tf

batch = utils_tf.data_dicts_to_graphs_tuple([
    {
        "nodes": np.array([[1.0], [2.0]], np.float32),
        "edges": np.array([[3.0]], np.float32),
        "senders": np.array([0], np.int32),
        "receivers": np.array([1], np.int32),
        "globals": np.array([4.0], np.float32),
    }
])
first = utils_tf.get_graph(batch, 0)
first_np = utils_tf.nest_to_numpy(first)
```

In TF2, do not call `placeholders_from_*` unless the environment intentionally
provides the TF1 placeholder API. Eager `GraphsTuple` values can be inspected
with `.numpy()` or `utils_tf.nest_to_numpy`.

## 4. Fully connect a featureless graph and add zero features

```python
import numpy as np
from graph_nets import utils_tf

# Two graphs, each with two nodes, no edge set, and no globals.
graph = utils_tf.data_dicts_to_graphs_tuple([
    {"nodes": np.array([[0.0], [1.0]], np.float32)},
    {"nodes": np.array([[2.0], [3.0]], np.float32)},
])

# Static is safe here because every graph has two statically known nodes.
graph = utils_tf.fully_connect_graph_static(graph, exclude_self_edges=True)
graph = utils_tf.set_zero_edge_features(graph, edge_size=0)
graph = utils_tf.set_zero_global_features(graph, global_size=1)

# For uneven or dynamically sized graphs, replace the static call with:
# graph = utils_tf.fully_connect_graph_dynamic(graph, exclude_self_edges=True)
```

Rules:

- Fully connected utilities require `edges`, `senders`, and `receivers` to all
  be `None` at the start.
- Edge feature creation requires the sender/receiver tensors already to exist.
- Zero feature sizes may be `0` when a downstream model accepts empty feature
  vectors; otherwise choose the model's expected feature width.

## 5. Concatenate, slice, and repeat

```python
from graph_nets import utils_tf

combined = utils_tf.concat([graph_a, graph_b], axis=0)
first_graph = utils_tf.get_graph(combined, 0)
subbatch = utils_tf.get_graph(combined, slice(1, 3))
num_graphs = utils_tf.get_num_graphs(combined)

# Repeat graph-level values to align with node counts.
per_node_values = utils_tf.repeat(combined.globals, combined.n_node, axis=0)
```

Use `axis=0` for batching. Use `axis=-1` or another feature axis only when
all non-feature graph structure fields (`senders`, `receivers`, `n_node`,
`n_edge`) are already aligned; `concat` does not verify that structure for
nonzero axes.

## 6. Prepare a TF2 `tf.function` signature

```python
import functools
import tensorflow as tf
from graph_nets import utils_tf

# specs_from_graphs_tuple rejects None fields. Complete missing features first.
if graph.edges is None:
    graph = utils_tf.set_zero_edge_features(graph, edge_size=0)
if graph.globals is None:
    graph = utils_tf.set_zero_global_features(graph, global_size=1)

signature = utils_tf.specs_from_graphs_tuple(
    graph,
    dynamic_num_graphs=True,
    dynamic_num_nodes=True,
    dynamic_num_edges=True,
)

@functools.partial(tf.function, input_signature=[signature])
def compiled_pipeline(graphs_tuple):
    # Call Graph Nets modules or pure utils_tf transforms here.
    return utils_tf.identity(graphs_tuple)

out = compiled_pipeline(graph)
```

If the original sample has `nodes is None`, complete nodes with
`set_zero_node_features` before creating the signature. Inside the function,
you may restore a field to `None` only if the called module/utility supports
that missing field.

## 7. Pad to fixed sizes, mask, then remove padding

```python
from graph_nets import utils_tf

valid_size = utils_tf.get_graphs_tuple_size(graph)

# Choose fixed integer capacities for the batch bucket. Padding needs room for
# one dummy padding graph with at least one node.
PAD_NODES_TO = 128
PAD_EDGES_TO = 256
PAD_GRAPHS_TO = 33

padded = utils_tf.pad_graphs_tuple(
    graph,
    pad_nodes_to=PAD_NODES_TO,
    pad_edges_to=PAD_EDGES_TO,
    pad_graphs_to=PAD_GRAPHS_TO,
)

nodes_mask = utils_tf.get_mask(valid_size.num_nodes, PAD_NODES_TO)
edges_mask = utils_tf.get_mask(valid_size.num_edges, PAD_EDGES_TO)
graphs_mask = utils_tf.get_mask(valid_size.num_graphs, PAD_GRAPHS_TO)

unpadded = utils_tf.remove_graphs_tuple_padding(padded, valid_size)
```

Mask shapes align to the leading dimensions of padded node-, edge-, and
graph-indexed tensors. In TF1 sessions, fetch padded or unpadded tensors via
`make_runnable_in_session` only if some fields are `None`.

## 8. Quick smoke check

The bundled script exercises a deterministic subset of the workflows above
without reading the source checkout:

```bash
python scripts/tf_ops_smoke.py --help
python scripts/tf_ops_smoke.py
```

Run it inside the intended installed Graph Nets + TensorFlow environment. It
prints a JSON summary that identifies TF1-session or TF2-eager mode.
