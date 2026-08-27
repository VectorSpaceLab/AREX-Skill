# TensorFlow utility troubleshooting

Use this checklist when Graph Nets `utils_tf` code fails in placeholder,
eager, batching, slicing, completion, or padding workflows.

## Version and execution-mode failures

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `AttributeError: module 'tensorflow' has no attribute 'Session'` | Running TF2 eager code while following a TF1 session recipe. | Use the TF2 eager workflows and `nest_to_numpy`, or run in a verified TF1-compatible stack. |
| `AttributeError: module 'tensorflow' has no attribute 'placeholder'` from `placeholders_from_data_dicts` or `placeholders_from_networkxs` | The placeholder helpers call top-level `tf.placeholder`, which is absent in the verified TF2 stack. | Do not use these helpers in TF2. Use eager tensors plus `specs_from_graphs_tuple` for `tf.function`, or switch to a TF1-compatible stack for placeholder feeding. |
| `sess.run` refuses a `GraphsTuple` with `None` fields | TensorFlow sessions cannot fetch Python `None` leaves. | Wrap the graph immediately before fetching: `fetches = utils_tf.make_runnable_in_session(graph)`. |
| Eager code calls `make_runnable_in_session` unnecessarily | TF2 eager can carry Python `None` fields directly, and `make_runnable_in_session` is for TF1 fetches. | Leave the `None` fields alone unless a specific utility rejects them. |

## `None` field mismatches

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `get_feed_dict` raises that a field should be `None` in both placeholders and feed values | Placeholder template and feed graph do not have identical missing-field structure. | Build placeholders from an example with the same feature/edge availability, or complete/remove the same fields on both structures. |
| `concat` raises about different key sets or all/no feature fields | At least one input graph has a feature field (`nodes`, `edges`, or `globals`) as `None` while another has a tensor. | Normalize inputs first: either complete that feature with zeros on every graph, or set it to `None` on every graph. |
| `stop_gradient` raises `Cannot stop gradient through ... if ... are None` | A selected stop flag targets a missing feature field. | Set the relevant `stop_*` flag to `False`, or complete that feature before stopping gradients. |
| `specs_from_graphs_tuple` raises that a field was `None` | TF2 signatures cannot contain Python `None` leaves in a `GraphsTuple`. | Replace missing features with zero tensors (`set_zero_*_features`) or an intentional empty tensor/nested structure before creating the signature. |

## Fully connected and zero-feature completion

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `Can only add fully connected a graph with None edges, receivers and senders` | A graph already has at least one edge-structure field. | Fully connect only featureless edge structure. Remove all three fields (`edges`, `senders`, `receivers`) or construct from node-only data first. |
| `fully_connect_graph_static` says node or graph count must be known at construction time | Static method cannot infer fixed equal node count from TensorFlow shapes. | Use `fully_connect_graph_dynamic`; reserve static for equal-size graphs with statically known leading dimensions. |
| `fully_connect_graph_static` says node count is not the same in all graphs | Batched graphs have uneven node counts, or static divisibility cannot prove equality. | Use `fully_connect_graph_dynamic`. |
| `set_zero_edge_features` says receivers or senders are `None` | Edge feature creation needs edge topology already present. | Add topology first with `fully_connect_graph_*` or provide `senders`/`receivers` in the data. |
| `set_zero_*_features` rejects an existing feature field | The utility only completes missing features. | Do not call it on already populated features; use `graph.replace(field=...)` intentionally if replacing is required. |
| Zero features have the wrong dtype for downstream code | Default dtype is `tf.float32`. | Pass `dtype=` explicitly, e.g. `dtype=tf.float64` or `dtype=tf.int32`. |

## Padding and masks

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `There is not enough space to pad the GraphsTuple` | Padding sizes do not leave room for the required first dummy padding graph. | Make `pad_nodes_to > valid_num_nodes` and `pad_graphs_to > valid_num_graphs`; `pad_edges_to` may equal valid edge count but cannot be smaller. |
| Padded tensors do not have static leading sizes | Padding target sizes were dynamic tensors or shape inference was obscured. | Prefer integer padding targets when compiling fixed-shape pipelines. Verify `tensor.shape.as_list()[0]` after padding. |
| Loss includes padded elements | The Graph Nets library treats zeros as valid graph values; padding must be masked. | Use `get_graphs_tuple_size` before padding and `get_mask` for node, edge, and graph leading dimensions. Apply masks to per-node/per-edge/per-graph losses. |
| `experimental_unconnected_padding_edges=True` fails on CPU with gather/scatter/index errors | That option deliberately creates out-of-range padding-edge endpoints and relies on non-CPU TensorFlow behavior. | Keep `experimental_unconnected_padding_edges=False` for CPU-safe execution. If using GPU/TPU, document that behavior as experimental and still mask padded values. |
| `remove_graphs_tuple_padding` returns too much or too little | The `valid_size` came from the padded graph instead of the original graph. | Capture `valid_size = get_graphs_tuple_size(graph)` before padding and reuse that exact object. |

## Indexing and slicing

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `Valid tensor indices must be scalars` | `get_graph` received a vector/tensor with non-scalar shape. | Pass a Python `int`, scalar `tf.int32`/`tf.int64`, or a `slice` whose start/stop are Python ints or scalar int tensors. |
| `Valid tensor indices must have types tf.int32 or tf.int64` | `get_graph` received a float or non-integer tensor index. | Cast or create scalar integer tensors explicitly. |
| `slices with step/stride are not supported` | `get_graph` only supports contiguous graph slices. | Use `slice(start, stop)` without a `step`. For strided selection, gather data outside `utils_tf.get_graph` and rebuild a new GraphsTuple. |
| Sliced graph has unexpected sender/receiver indices | `get_graph` re-bases edge endpoints to the selected graph batch. | This is expected; endpoints are local to the sliced `GraphsTuple`. |

## Shape and dtype failures

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `data_dicts_to_graphs_tuple` raises about inconsistent keys | Dicts in the batch disagree about which fields are present/non-`None`. | Normalize every dict to the same non-`None` feature and edge-structure fields before converting. |
| Edge indices produce invalid gathers in later blocks | `senders`/`receivers` refer outside the node range after manual construction. | Verify indices against cumulative `n_node` counts, or build topology with Graph Nets helpers. |
| `concat(axis!=0)` produces structurally inconsistent graphs | Nonzero-axis concat only concatenates feature tensors and assumes graph structure fields already match. | Use `axis=0` for batching. Use nonzero axis only when `senders`, `receivers`, `n_node`, and `n_edge` are known identical. |
| `repeat` has unknown output leading shape | `sum_repeats_hint` was omitted and static shape is required later. | Pass `sum_repeats_hint=int(sum(repeats))` when the total is known at graph construction time. |
| `specs_from_graphs_tuple` creates overly static signatures | Dynamic flags were left false for dimensions that vary across examples. | Set `dynamic_num_graphs`, `dynamic_num_nodes`, and/or `dynamic_num_edges` to `True` for varying leading dimensions. |

## NetworkX-adjacent placeholder issues

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Empty-node or empty-edge NetworkX samples create `None` placeholder fields | Shape cannot be inferred from an empty sample. | Pass `node_shape_hint`, `edge_shape_hint`, and `data_type_hint` if placeholders must still include those fields. |
| Code depends on `OrderedMultiDiGraph` and fails with newer NetworkX | The verified Graph Nets stacks use NetworkX versions where `OrderedMultiDiGraph` still exists, but it is deprecated and removed in NetworkX 3. | Stay on a compatible NetworkX `<3` runtime for Graph Nets 1.x, or adapt data code to avoid the removed class. |
