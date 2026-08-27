# Troubleshooting

Use this guide when `MetaOptimizer`, `meta_loss`, or `meta_minimize` does not behave as expected.

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Loss graph builds once but breaks or duplicates work on later calls | `make_loss` has Python side effects or creates resources that should only be created once | Move side effects outside the callable. Treat `make_loss` as pure graph construction because `meta_loss` replays it during variable discovery and during the unroll loop. |
| `ValueError: Default net_assignments can only be used if there is a single net config.` | Multiple optimizer nets were defined but no mapping was supplied | Provide `net_assignments` or reduce the constructor to one network config. |
| `ValueError: Repeated netid in net_assigments.` or assignments appear to fight each other | Duplicate network ids or accidental reuse of the same variable name | Keep network ids unique and confirm the exact optimizee names before wiring assignments. |
| Updates do not carry over to the next unroll or epoch | `update` was not run, or `reset` was called at the wrong time | Run `reset` once at the start of a new epoch/task, then run `update` after each unroll so the live optimizee state is advanced. |
| Second-order gradients fail, are `None`, or explode in complexity | `second_derivatives=True` is being used with ops that do not support higher-order gradients well | Keep `second_derivatives=False` unless the optimizee graph is known to support second derivatives. This is especially important when the loss uses queueing, normalization, or other stateful ops. |
| A variable name in `net_assignments` is not found | TensorFlow tensor names include a `:0` suffix, but assignment matching uses the prefix only | Use the unscoped name such as `x_0` or `conv/w`. Compare against the names printed by `meta_loss`. |
| Saving succeeds but loading does not restore the expected weights | The `.l2l` file path was wrong or the network config was not rebuilt with `net_path` | Pass the exact saved file path as `net_path` in the matching network config and rebuild in a fresh graph. |
| `optimizer.save(...)` returns nothing useful | `meta_loss` or `meta_minimize` has not yet populated the optimizer networks | Build the meta-loss or meta-minimize graph first, then call `save` from the session that owns those variables. |
| TensorFlow import or graph APIs fail on a modern environment | The repository expects TensorFlow 1.x graph mode and Sonnet 1.x | Use the TF1-compatible environment. The code relies on `tf.Session`, `tf.get_variable`, `tf.flags`, and `tf.contrib`. |
| The smoke script cannot import source modules | `--repo-root` points at the wrong directory | Point `--repo-root` at the repository root that contains `meta.py`, `networks.py`, and the other source modules. |

## TensorFlow while-loop state structure errors

Symptoms include `The two structures don't have the same nested structure` or messages comparing tuples with `LSTMState` inside the `unroll` while loop.

Likely cause: a newer TensorFlow 1.x / Sonnet 1.x combination is stricter about nested state types than the original 2016-era runtime. Multi-layer `CoordinateWiseDeepLSTM` and some save/load tests can expose this even when imports and stateless or zero-layer smokes pass.

Recovery:

1. First verify the minimal zero-layer or stateless optimizer smoke; this separates environment import problems from deep LSTM state issues.
2. For faithful reproduction of historical tests, use an older TensorFlow/Sonnet pair compatible with the repository's original state structure behavior.
3. If maintaining a fork, normalize the initial and next LSTM state structures before the TensorFlow `while_loop` boundary instead of treating this as a problem with `net_assignments`.
4. Document the exact TensorFlow and Sonnet versions when reporting the failure.

## Legacy TensorFlow compatibility notes

- This repository is written for TensorFlow 1.x graph mode.
- Eager execution should not be enabled.
- `tf.contrib`-based code paths are expected.
- Use the pinned TF1-compatible dependency set from the prepared inspection environment.
- If you see protobuf-related import issues, use the older protobuf runtime that matches TensorFlow 1.15.

## Quick recovery checklist

1. Rebuild the graph from a clean default graph.
2. Confirm the optimizee variable names.
3. Verify `net_assignments` and `net_path` values.
4. Keep `make_loss` free of side effects.
5. Run the bundled smoke script before moving on to deeper debugging.
