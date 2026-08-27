# Troubleshooting

## Import fails before any Graph Nets code runs

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `ModuleNotFoundError: No module named 'tensorflow'` | TensorFlow is not installed by `graph_nets` metadata | Install a stack from [compatibility](compatibility.md). |
| `ModuleNotFoundError: No module named 'sonnet'` | Missing `dm-sonnet` dependency or wrong environment | Install `dm-sonnet<2` for TF1 or `dm-sonnet>=2,<3` for TF2. |
| TensorFlow protobuf descriptor error mentioning generated code or `Descriptors cannot be created directly` | Old TensorFlow wheel with protobuf `>=4` | Install `protobuf<3.20` in the same environment. |
| NumPy attribute or binary incompatibility errors in TensorFlow | Old TensorFlow with too-new NumPy | Use a NumPy version compatible with the selected TensorFlow stack; the verified stacks use NumPy `<1.20`. |
| `networkx.OrderedMultiDiGraph` missing | NetworkX 3.x | Use `networkx<3` or update conversion code before relying on Graph Nets NetworkX helpers. |

## TensorFlow execution-style mismatch

- In TF2/Sonnet2 environments, top-level `tf.Session` and `tf.placeholder` are not available. Use eager tensors, `utils_tf.nest_to_numpy`, and `utils_tf.specs_from_graphs_tuple`; do not call placeholder helpers unless the user intentionally selected a TF1-compatible runtime.
- In TF1/Sonnet1 environments, use `tf.Session`, initialize variables, and use `utils_tf.make_runnable_in_session` before `sess.run` when a `GraphsTuple` contains Python `None` fields.
- If a user has a modern TensorFlow release far newer than the verified TF2 stack, run the root install check first; Graph Nets is legacy and may need pinned TensorFlow rather than latest TensorFlow.

## GPU warnings

Graph Nets does not require GPU for the workflows in this skill. Old TensorFlow wheels may print messages about visible NVIDIA devices but missing CUDA libraries. Treat those as optional GPU acceleration warnings unless the user explicitly needs GPU training. CPU is sufficient for graph conversion, utility, and small module smoke checks.

## Data and model errors

- For `ValueError` involving `n_node`, `n_edge`, `receivers`, `senders`, `edges`, or mismatched data dictionary keys, read [graph-data troubleshooting](../sub-skills/graph-data/references/troubleshooting.md).
- For `utils_tf` padding, placeholder, `tf.function`, concat, or shape errors, read [TensorFlow ops troubleshooting](../sub-skills/tensorflow-ops/references/troubleshooting.md).
- For missing fields in `EdgeBlock`, `NodeBlock`, `GlobalBlock`, reducer errors, Sonnet version issues, or feature concatenation failures, read [graph-models troubleshooting](../sub-skills/graph-models/references/troubleshooting.md).

## Fast isolation procedure

1. Run the root diagnostic:
   ```bash
   python path/to/graph-nets/scripts/check_graph_nets_install.py --pretty
   ```
2. If import succeeds but graph data fails, run the graph-data smoke script from that sub-skill.
3. If TensorFlow utility failures remain, run the TensorFlow ops smoke script in the intended TF1 or TF2 environment.
4. If model construction fails, run the graph-models smoke script and compare Sonnet major version to the code style.
5. Only after these tiny checks pass should a future agent run longer native tests or notebook-derived examples.
