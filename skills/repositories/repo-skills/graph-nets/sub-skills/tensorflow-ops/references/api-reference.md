# TensorFlow utility API reference

This reference covers `graph_nets.utils_tf` utilities for TensorFlow-backed
`graphs.GraphsTuple` values. For NumPy-only and NetworkX-only conversion, route
to the sibling graph-data sub-skill.

## Build tensor GraphsTuple values

| API | Use | Required input shape/fields | Notes |
| --- | --- | --- | --- |
| `utils_tf.data_dicts_to_graphs_tuple(data_dicts, name=...)` | Convert a list of graph data dicts to a batched `GraphsTuple` whose fields are TensorFlow tensors. | Each dict must use a consistent set of non-`None` graph fields. If `nodes` is absent/`None`, provide `n_node`; if edges are absent, `edges`, `senders`, and `receivers` must all be absent/`None`. | Casts `senders`, `receivers`, `n_node`, and `n_edge` to `tf.int32`. Feature dtypes follow supplied tensors/arrays. |
| `utils_tf.placeholders_from_data_dicts(data_dicts, force_dynamic_num_graphs=True, name=...)` | Build a TF1 `GraphsTuple` of placeholders matching example data dicts. | Example dicts define trailing feature shapes. Leading node/edge dimensions are dynamic. | TF1-only in the verified stacks because the implementation uses top-level `tf.placeholder`. |
| `utils_tf.placeholders_from_networkxs(graph_nxs, node_shape_hint=None, edge_shape_hint=None, data_type_hint=tf.float32, force_dynamic_num_graphs=True, name=...)` | Build TF1 placeholders from NetworkX sample graphs. | NetworkX graph features define node/edge/global trailing shapes; hints fill empty-node or empty-edge cases. | Use only for placeholder construction. Do pure NetworkX conversion guidance through graph-data. |
| `utils_tf.get_feed_dict(placeholders, graph)` | Feed a NumPy-valued `GraphsTuple` into a placeholder `GraphsTuple` even when some fields are `None`. | `None` fields must match exactly between placeholder structure and feed graph. | Use the returned dict in `sess.run(..., feed_dict=...)`. |
| `utils_tf.make_runnable_in_session(graph, name=...)` | Replace `None` fields with no-op fetches so a TF1 session can run a `GraphsTuple`. | Any tensor or `None` field combination. | Call immediately before `sess.run`. The returned session result preserves `None` for those fields. |

## Graph transforms and batching

| API | Use | Preconditions | Output/cautions |
| --- | --- | --- | --- |
| `utils_tf.concat(input_graphs, axis, name=...)` | Concatenate graphs along batch axis (`axis=0`) or concatenate feature dimensions (`axis!=0`). | Non-empty list; every graph must have the same fields non-`None`. | For `axis=0`, senders/receivers are offset by preceding node counts. For `axis!=0`, graph structure fields are assumed to match but are not checked. |
| `utils_tf.repeat(tensor, repeats, axis=0, name=..., sum_repeats_hint=None)` | TensorFlow equivalent of `numpy.repeat`, useful for broadcasting graph-level or node-level quantities. | `repeats` is a 1-D integer sequence aligned to `tensor.shape[axis]`. | `sum_repeats_hint` sets static output shape when known. Handles zero-repeat groups. |
| `utils_tf.identity(graph, name=...)` | Apply `tf.identity` to every non-`None` `GraphsTuple` field. | Any `GraphsTuple` with tensor or `None` fields. | Useful for naming scopes or enforcing fetch boundaries without changing values. |
| `utils_tf.stop_gradient(graph, stop_edges=True, stop_nodes=True, stop_globals=True, name=...)` | Stop gradients through selected feature fields. | Any selected field must be non-`None`. | Raises if asked to stop a missing feature field; leave a stop flag `False` or complete the feature first. |
| `utils_tf.get_graph(input_graphs, index, name=...)` | Extract one graph or a contiguous slice from a batched tensor `GraphsTuple`. | `index` is an integer, scalar int tensor, or slice with integer/scalar-tensor start/stop and no `step`. | Re-bases senders/receivers by subtracting the first selected node offset. |
| `utils_tf.get_num_graphs(input_graphs, name=...)` | Return batch size from `n_node` leading dimension. | `input_graphs.n_node` is present. | Returns a Python int when static, otherwise a scalar tensor. |
| `utils_tf.nest_to_numpy(nest_of_tensors)` | Convert eager tensors in any nested structure to NumPy arrays. | TF2/eager tensors; non-tensor leaves are allowed. | Leaves Python objects and `None` unchanged. Common after eager GraphsTuple utilities. |

## Completing structure and features

| API | Use | Preconditions | Output/cautions |
| --- | --- | --- | --- |
| `utils_tf.fully_connect_graph_static(graph, exclude_self_edges=False, name=...)` | Add complete directed edges when each graph has the same statically known number of nodes. | `edges`, `senders`, and `receivers` are all `None`; leading dimensions of `nodes` and `n_node` are statically known; node count divides graph count evenly. | Fast/static but unsafe for uneven graph sizes. Use dynamic when sizes vary or are unknown. |
| `utils_tf.fully_connect_graph_dynamic(graph, exclude_self_edges=False, name=...)` | Add complete directed edges when graph sizes may vary or be known only at runtime. | `edges`, `senders`, and `receivers` are all `None`; `n_node` is present. | Uses TensorFlow control flow/TensorArray. Returns `n_edge`, `senders`, and `receivers`; edge features remain `None` until completed. |
| `utils_tf.set_zero_node_features(graph, node_size, dtype=tf.float32, name=...)` | Replace missing node features with zeros. | `graph.nodes is None`; `n_node` is present; `node_size` is not `None`. | Produces shape `[sum(n_node), node_size]`. `node_size=0` is valid for empty feature vectors. |
| `utils_tf.set_zero_edge_features(graph, edge_size, dtype=tf.float32, name=...)` | Replace missing edge features with zeros. | `graph.edges is None`; `senders` and `receivers` are present; `edge_size` is not `None`. | Uses static sender length when available, otherwise `sum(n_edge)`. |
| `utils_tf.set_zero_global_features(graph, global_size, dtype=tf.float32, name=...)` | Replace missing global features with zeros. | `graph.globals is None`; `global_size` is not `None`. | Produces shape `[num_graphs, global_size]`. |

## Padding and fixed-shape batches

| API | Use | Preconditions | Output/cautions |
| --- | --- | --- | --- |
| `utils_tf.GraphsTupleSize(num_nodes, num_edges, num_graphs)` | Carry valid sizes for node-, edge-, and graph-indexed fields. | Values are scalar integers or scalar tensors. | Used by padding removal and masks. |
| `utils_tf.get_graphs_tuple_size(graphs_tuple)` | Compute total valid nodes, edges, and graphs in a batch. | `n_node` and `n_edge` are present. | Returns `GraphsTupleSize(num_nodes, num_edges, num_graphs)`. |
| `utils_tf.pad_graphs_tuple(graphs_tuple, pad_nodes_to, pad_edges_to, pad_graphs_to, experimental_unconnected_padding_edges=False)` | Pad a GraphsTuple to static node/edge/graph lengths. | All feature fields that need padding are non-`None`; `pad_nodes_to` and `pad_graphs_to` are strictly larger than the valid sizes; `pad_edges_to` is at least the valid edge count. | Adds one dummy graph with padding nodes/edges, then zero-node/zero-edge graphs if needed. Avoid `experimental_unconnected_padding_edges=True` on CPU. |
| `utils_tf.remove_graphs_tuple_padding(padded_graphs_tuple, valid_size)` | Strip padded tails using a previously captured valid size. | `valid_size` is from the original unpadded batch. | Slices every GraphsTuple field/nest back to valid lengths. |
| `utils_tf.get_mask(valid_length, full_length)` | Build a boolean mask for valid leading elements after padding. | Scalar integer/tensor lengths. | Returns shape `[full_length]`; true for valid prefix and false for trailing padding. If `valid_length > full_length`, the returned mask is all true. |

## `tf.function` signatures

`utils_tf.specs_from_graphs_tuple(graphs_tuple_sample, dynamic_num_graphs=False,
dynamic_num_nodes=True, dynamic_num_edges=True, description_fn=tf.TensorSpec)`
returns a `GraphsTuple` whose leaves are specs, not tensors. Use it as the
`input_signature` for TF2 `tf.function` wrappers around Graph Nets models or
utility pipelines.

Important rules:

- Every `GraphsTuple` field must be non-`None`. Replace missing feature fields
  with zero features or empty nested tensor structures before creating a spec.
- `dynamic_num_graphs=True` makes the leading dimension of every field dynamic.
- `dynamic_num_nodes=True` makes `nodes` leading dimension dynamic.
- `dynamic_num_edges=True` makes `edges`, `senders`, and `receivers` leading
  dimensions dynamic.
- Nested node/edge/global feature structures are supported when their tensor
  leaves share the expected leading dimensions.
