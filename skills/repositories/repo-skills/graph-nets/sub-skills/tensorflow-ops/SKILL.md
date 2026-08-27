---
name: tensorflow-ops
description: "Operate on Graph Nets GraphsTuple objects backed by TensorFlow tensors."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# TensorFlow GraphsTuple operations

Use this sub-skill when the task already has graph data in Graph Nets `GraphsTuple`
form, or has data dicts/NetworkX samples that must become TensorFlow-backed
`GraphsTuple` values for batching, slicing, padding, `tf.function`, or TF1
session feeding.

## Route here for

- Building TensorFlow `GraphsTuple`s with `utils_tf.data_dicts_to_graphs_tuple`.
- TF1 placeholder/feed workflows with `placeholders_from_data_dicts`,
  `placeholders_from_networkxs`, `get_feed_dict`, and
  `make_runnable_in_session`.
- Eager/TF2 conversion and `tf.function` signatures with `nest_to_numpy` and
  `specs_from_graphs_tuple`.
- Tensor GraphsTuple transforms: `concat`, `repeat`, `identity`,
  `stop_gradient`, `get_graph`, and `get_num_graphs`.
- Completing featureless graphs with fully connected edges or zero-valued node,
  edge, and global feature tensors.
- Fixed-size batching with `GraphsTupleSize`, `get_graphs_tuple_size`,
  `pad_graphs_tuple`, `remove_graphs_tuple_padding`, and `get_mask`.

## Route elsewhere

- For pure NumPy/NetworkX conversion or `utils_np` round trips, use
  [graph-data](../graph-data/SKILL.md).
- For Sonnet modules, Graph Nets blocks, learned message-passing constructors,
  and model factories, use [graph-models](../graph-models/SKILL.md).

## Version decision

Choose the TensorFlow execution style before writing code:

- **TF1 / Sonnet 1 stack:** use `tf.Session`, top-level `tf.placeholder`,
  `placeholders_from_*`, `get_feed_dict`, and `make_runnable_in_session` when a
  graph has `None` fields.
- **TF2 / Sonnet 2 stack:** top-level `tf.Session` and `tf.placeholder` are not
  available. Prefer eager tensors, `utils_tf.nest_to_numpy`, and
  `utils_tf.specs_from_graphs_tuple` for `tf.function` input signatures. Do not
  route TF2 users to placeholder APIs unless they explicitly own a compatible
  TF1-style runtime.

## Operating procedure

1. Normalize graph data into a `GraphsTuple` with tensor-valued fields. Keep
   NumPy/NetworkX-only conversion details in the graph-data sub-skill.
2. Ensure every selected utility's preconditions are true: matching non-`None`
   fields for `concat`, scalar integer graph indices for `get_graph`, complete
   fields for `specs_from_graphs_tuple`, and enough padding capacity for a dummy
   graph when padding.
3. Add missing zero-valued feature tensors before model or `tf.function` use
   when a utility rejects `None` feature fields.
4. In TF1, convert `None` fields with `make_runnable_in_session` immediately
   before `sess.run`; in TF2, leave `None` fields as ordinary Python `None`
   unless a utility explicitly requires tensors.
5. Use the bundled smoke script for a quick environment check:
   `python scripts/tf_ops_smoke.py --help`, then run it in the intended Graph
   Nets TensorFlow environment.

## References

- [API reference](references/api-reference.md)
- [Workflows](references/workflows.md)
- [Troubleshooting](references/troubleshooting.md)
