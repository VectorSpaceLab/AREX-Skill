# Compatibility

## Purpose

Read this before installing or debugging Graph Nets. The package is a legacy TensorFlow/Sonnet graph neural network library whose source supports two major runtime families. A mismatched TensorFlow, Sonnet, NetworkX, NumPy, or protobuf version is the most common cause of import and execution failures.

## Verified runtime families

| Family | Use when | Verified stack during skill creation | Important behavior |
| --- | --- | --- | --- |
| TF1 / Sonnet1 | Legacy notebooks, placeholder/feed-dict workflows, `tf.Session` examples, Sonnet 1 modules | TensorFlow `1.15.5`, Sonnet `1.36`, TensorFlow Probability `0.8.0`, NetworkX `2.6.3`, NumPy `1.18.5`, protobuf `3.19.6` | Top-level `tf.Session`, `tf.placeholder`, `tf.reset_default_graph`, and `tf.global_variables_initializer` exist. |
| TF2 / Sonnet2 | Eager tensor workflows, Sonnet 2 modules, `tf.function` signatures, TF2 demo style | TensorFlow `2.2.0`, Sonnet `2.0.2`, NetworkX `2.8.8`, NumPy `1.19.5`, protobuf `3.19.6` | Top-level `tf.Session` and `tf.placeholder` are absent; use eager tensors and `utils_tf.specs_from_graphs_tuple`. |

The two families should usually live in separate Python environments because TensorFlow/Sonnet major versions conflict.

## Dependency rules

- Install TensorFlow explicitly; the `graph_nets` package metadata intentionally does not require it.
- Keep `networkx<3` for Graph Nets conversion helpers that construct or expect `networkx.OrderedMultiDiGraph`. NetworkX 3 removed that attribute.
- Pin `protobuf<3.20` for the old TensorFlow wheels. Newer protobuf releases can fail while importing TensorFlow with descriptor errors.
- Pin `numpy<1.20` for the verified legacy TensorFlow stacks. Much newer NumPy releases can break old TensorFlow wheels or old code paths.
- Install `tensorflow_probability<0.9` only for the TF1/Sonnet1 notebook-style stack or when a user specifically needs it; core package imports and the bundled smoke checks do not require it in the TF2 stack.
- GPU is optional for the workflows captured by this skill. CPU validates the selected graph data, TensorFlow utility, and module behavior.

## Choosing a stack

Use TF1/Sonnet1 when:

- A user explicitly has legacy code with `tf.Session`, placeholders, or Sonnet 1 `snt.AbstractModule`.
- They are reproducing old notebook cells that assume `%tensorflow_version 1.x` behavior.
- They need `utils_tf.placeholders_from_data_dicts`, `placeholders_from_networkxs`, `get_feed_dict`, or `make_runnable_in_session` exactly as written.

Use TF2/Sonnet2 when:

- A user wants eager execution, `tf.GradientTape`, or `tf.function` input signatures.
- They are building Sonnet 2 `snt.Module` objects.
- They need `utils_tf.specs_from_graphs_tuple` for variable-size graph batches.

## Quick diagnostics

Run:

```bash
python path/to/graph-nets/scripts/check_graph_nets_install.py --pretty
```

Interpretation:

- `networkx_has_ordered_multidigraph: false`: install `networkx<3` or use a compatible graph class before calling the NetworkX conversion helpers.
- `tf_has_placeholder: false` and `tf_has_session: false`: this is expected in the verified TF2 stack; do not use placeholder/session workflows unless switching to TF1/compat mode.
- `model_smoke.ok: false`: check TensorFlow/Sonnet major-version mismatch, missing TensorFlow, or invalid package install.

## Refresh triggers

Refresh this skill if the package begins supporting current TensorFlow releases without these pins, drops Sonnet 1 or TF1 support, replaces `OrderedMultiDiGraph`, or changes public `graphs`, `utils_np`, `utils_tf`, `blocks`, or `modules` signatures.
