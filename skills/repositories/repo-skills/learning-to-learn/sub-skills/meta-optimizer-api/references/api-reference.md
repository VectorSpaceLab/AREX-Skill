# Meta optimizer API reference

This reference distills the public API and runtime contracts for `meta.MetaOptimizer` from the source module, tests, and the API inspection report.

## Public symbols

| Symbol | Signature | Purpose |
| --- | --- | --- |
| `meta.MetaOptimizer` | `(**kwargs)` | Create an optimizer registry keyed by network id. Constructor kwargs are passed to `networks.factory`. |
| `meta.MetaOptimizer.meta_loss` | `(self, make_loss, len_unroll, net_assignments=None, second_derivatives=False)` | Build the unrolled meta-loss graph and return a `MetaLoss` tuple. |
| `meta.MetaOptimizer.meta_minimize` | `(self, make_loss, len_unroll, learning_rate=0.01, **kwargs)` | Build the unrolled meta-training graph and return a `MetaStep` tuple. |
| `meta.MetaOptimizer.save` | `(self, sess, path=None)` | Save loaded optimizer-network variables as `.l2l` files or return them in memory. |

## Default constructor behavior

When `MetaOptimizer` is called without kwargs, it uses one default coordinatewise optimizer net with this configuration:

- net: `CoordinateWiseDeepLSTM`
- layers: `(20, 20)`
- preprocessing: `LogAndSign(k=5)`
- scale: `0.01`

If kwargs are provided, each key becomes an optimizer id and each value is a network config dictionary that is forwarded to `networks.factory`.

## Named tuple fields

| Tuple | Fields | Meaning |
| --- | --- | --- |
| `MetaLoss` | `loss`, `update`, `reset`, `fx`, `x` | `loss` is the summed meta-loss over the unroll window. `update` copies the final optimizee variables and optimizer state back into the live graph. `reset` reinitializes the optimizee state and closes the TensorArray used by the unroll loop. `fx` is the final scalar optimizee loss. `x` is the final optimizee variable collection. |
| `MetaStep` | `step`, `update`, `reset`, `fx`, `x` | `step` is the Adam update op that minimizes `MetaLoss.loss`. The remaining fields match `MetaLoss`. |

`update` and `reset` are lists of TensorFlow ops. Group them with `tf.group(*ops)` if you want a single runnable op.

## Variable interception contract

`meta_loss` does not execute `make_loss` just once.

1. It first calls `make_loss` inside a discovery pass to collect trainable optimizee variables and non-trainable constants.
2. It then replays `make_loss` inside the unroll loop while replacing trainable variables with the current tensors in `x`.
3. It writes a loss value for every unroll step plus a final loss at `len_unroll`.

Implications:

- `make_loss` must behave like pure graph construction.
- Side effects such as queue creation, downloads, dataset setup, or resource mutation should happen outside `make_loss`.
- Variable creation order matters because the replacement list follows the discovery order.
- Variable names are matched by the prefix before `:0`.
- Trainable variables are replaced; non-trainable variables are re-used.

## Net assignment rules

`net_assignments` is a list of `(net_id, [variable_name, ...])` pairs.

- If `net_assignments` is `None`, the constructor config must define exactly one optimizer net.
- Each `net_id` must exist in the constructor kwargs.
- Repeated `net_id` values are rejected.
- Variable names must match the discovered optimizee names exactly, without the `:0` suffix.
- The code does not deduplicate overlapping variable assignments; a variable may appear in more than one assignment, and the resulting deltas are accumulated in the order of `net_assignments`.
- The optimizee names printed by `meta_loss` are the safest source of truth when authoring assignments.

Example:

```python
optimizer = meta.MetaOptimizer(
    cw={
        "net": "CoordinateWiseDeepLSTM",
        "net_options": {"layers": (), "initializer": "zeros"},
    },
    adam={
        "net": "Adam",
        "net_options": {"learning_rate": 0.1},
    },
)
loss = optimizer.meta_loss(
    problems.simple_multi_optimizer(num_dims=2),
    len_unroll=3,
    net_assignments=[("cw", ["x_0"]), ("adam", ["x_1"])],
)
```

## Save/load `.l2l` semantics

`MetaOptimizer.save(sess, path=None)` saves the networks that were created by `meta_loss` or `meta_minimize`.

| Call | Result |
| --- | --- |
| `optimizer.save(sess)` | Returns a dictionary keyed by optimizer id. Each value is the nested variable payload that would be written to disk. |
| `optimizer.save(sess, path=save_dir)` | Writes one pickle file per optimizer net, using `<save_dir>/<net_id>.l2l`, and returns a dictionary keyed by the full filename. |

Load behavior:

- Pass the saved `.l2l` file path in the matching network config as `net_path`.
- `net_path` is consumed during network construction by `networks.factory`; it is not a TensorFlow checkpoint restore.
- Rebuild the graph in a fresh default graph and create a new `MetaOptimizer` before loading.
- The repo's CLI convention uses `name.l2l` under the chosen save directory.

Example:

```python
optimizer = meta.MetaOptimizer(net={
    "net": "CoordinateWiseDeepLSTM",
    "net_options": {"layers": (), "initializer": "zeros"},
    "net_path": "<save-dir>/cw.l2l",
})
```

## Workflow notes

- `meta_loss` logs the discovered optimizee and problem variables while building the graph.
- `meta_minimize` is just `meta_loss` plus `tf.train.AdamOptimizer(learning_rate).minimize(...)`.
- `second_derivatives` defaults to `False`; keep it off unless the optimizee graph can support higher-order gradients.
- The unroll body uses a `tf.while_loop` with `parallel_iterations=1` and `swap_memory=True`.
- The returned `fx` is the final loss tensor, not the whole TensorArray of intermediate losses.
