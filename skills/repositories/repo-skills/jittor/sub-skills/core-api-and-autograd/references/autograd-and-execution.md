# Autograd and execution

This reference explains the parts of Jittor that most often confuse users after the API surface itself is known: lazy execution, gradient extraction, sync boundaries, and state update style.

## Lazy execution model

Jittor builds computation lazily and usually executes only when you ask for a concrete value.

Use one of these actions to force work to happen:

- `var.data`
- `var.numpy()`
- `var.sync()`
- `jt.sync_all()`

If you are localizing a failure, temporarily switch to eager-style debugging:

```python
with jt.flag_scope(lazy_execution=0, trace_py_var=3):
    ...
```

That usually makes the first failing op easier to identify than the default lazy trace.

## Gradients

`jt.grad(loss, targets)` expects a scalar loss. In practice:

1. Compute the forward pass.
2. Reduce the objective to one scalar.
3. Call `jt.grad`.
4. Update the parameters or inspect the returned gradients.

Common manual-update pattern:

```python
ps = model.parameters()
loss = ((model(x) - y) ** 2).mean()
gs = jt.grad(loss, ps)
for p, g in zip(ps, gs):
    p -= 0.1 * g
```

Use a scope such as `jt.no_grad()` when you do not want the update step itself to build a new training graph.

## State and execution hygiene

- `Module.execute` is the user-facing forward path.
- `Module.train()` and `Module.eval()` control runtime behavior for layers that care about training mode.
- Keep long-lived Python references to a minimum if you are trying to release memory between iterations.
- `jt.clean()` and `jt.gc()` are useful in tests and short diagnostics, but they do not replace correct graph ownership.

## When to inspect the graph rather than the math

Look at execution and state ownership first when:

- a loss value never changes,
- the graph keeps growing between iterations,
- a parameter looks frozen,
- or the same code works only after a reload.

Those are usually ownership or synchronization problems, not math problems.

## Good debugging order

1. Confirm shapes and dtypes.
2. Run the code under `lazy_execution=0`.
3. Add `trace_py_var=3` if the failure site is still unclear.
4. Add `JT_CHECK_NAN=1` if the symptom is numeric corruption.
5. Once the bug is understood, return to the normal lazy path for performance.