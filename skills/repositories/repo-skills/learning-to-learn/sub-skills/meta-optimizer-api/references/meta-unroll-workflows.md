# Meta optimizer unroll workflows

Use these patterns when building, training, saving, or debugging `MetaOptimizer` graphs.

## 1) Build a tiny deterministic graph

Prefer the smallest possible problem and a zero-initialized coordinatewise net when you need a smoke test.

```python
problem = problems.simple()
optimizer = meta.MetaOptimizer(
    net={
        "net": "CoordinateWiseDeepLSTM",
        "net_options": {"layers": (), "initializer": "zeros"},
    }
)
meta_step = optimizer.meta_minimize(problem, len_unroll=2, learning_rate=1e-2)
```

What to inspect immediately:

- `meta_step.fx` should be a scalar tensor.
- `meta_step.x` should hold the final optimizee variables.
- `meta_step.reset` and `meta_step.update` should both be runnable op lists.

If you only need the unrolled loss and do not want to train the meta-optimizer, use `meta_loss(...)` instead of `meta_minimize(...)`.

## 2) Canonical epoch loop

The safe sequence is:

1. Run `reset` once at the beginning of each new epoch or task.
2. For each unroll step, evaluate the loss and run `update`.
3. If training the meta-optimizer, also run `step` each unroll.

```python
reset_op = tf.group(*meta_step.reset)
update_op = tf.group(*meta_step.update)

with tf.Session() as sess:
    sess.run(tf.global_variables_initializer())
    for epoch in range(num_epochs):
        sess.run(reset_op)
        for _ in range(num_unrolls):
            loss_value, x_value, _, _ = sess.run(
                [meta_step.fx, meta_step.x, update_op, meta_step.step]
            )
```

Why this order matters:

- `reset` reinitializes the live optimizee variables and the optimizer state.
- `update` copies the final unrolled state back into the live variables so the next unroll continues from the right place.
- `step` updates the meta-optimizer weights using the unrolled meta-loss.

If you skip `update`, the outer meta-optimizer may train, but the optimizee state will not advance correctly.

## 3) Save/load roundtrip

Save from the session that has already built and initialized the optimizer nets.

```python
save_map = optimizer.save(sess, path=save_dir)
saved_path = next(iter(save_map))
```

Then rebuild the graph in a fresh default graph and point the matching network config at the saved `.l2l` file.

```python
reloaded = meta.MetaOptimizer(net={
    "net": "CoordinateWiseDeepLSTM",
    "net_options": {"layers": (), "initializer": "zeros"},
    "net_path": saved_path,
})
reloaded_step = reloaded.meta_minimize(problem, len_unroll=2, learning_rate=1e-2)
```

Use this pattern when you want to validate that the save path, file naming, and initializer loading are all consistent.

## 4) Debug a variable-assignment mismatch

When `net_assignments` fails, work in this order:

1. Print the optimizee variable names discovered by `meta_loss`.
2. Compare them with the assignment names you supplied.
3. Remove the `:0` suffix if you copied names from TensorFlow tensors.
4. Check that the network ids in `net_assignments` exist in the constructor config.
5. If a variable appears in multiple assignments, remember that updates are accumulated in list order.

A quick example of the expected naming style:

- `x_0`
- `x_1`
- `conv/w`
- `mlp/linear_0/b`

## 5) Debug a side-effectful `make_loss`

If graph construction behaves differently on the first and second call, the loss callable is probably doing too much work.

Move these actions outside `make_loss`:

- dataset downloads
- queue creation
- queue runner registration
- random-data setup that should happen once
- any mutation that should not repeat during unrolling

Keep `make_loss` limited to graph wiring and return a scalar TensorFlow loss.
