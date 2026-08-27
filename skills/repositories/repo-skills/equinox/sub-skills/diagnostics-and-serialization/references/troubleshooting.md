# Diagnostics and Serialization Troubleshooting

## Deserialization reports a leaf path

`tree_deserialise_leaves` reports the first path where the stored leaf and
like-tree leaf are incompatible. Use that path to check shape, dtype, and tree
structure.

Fix:

- Recreate the like-tree with the same structure as the saved model.
- Keep non-serialized leaves, functions, and objects in the like-tree.
- Match array dtypes and shapes unless a custom deserializer intentionally
  converts them.

## Non-array leaves are not restored from the file

This is normal. The like-tree supplies non-serialized leaves. If a callable or
object changed, update the like-tree before deserializing.

## Runtime error text is noisy under `jax.jit`

JAX may wrap `eqx.error_if` failures in callback or internal-stack text. Try:

```python
@eqx.filter_jit
def f(...):
    ...
```

or set `JAX_TRACEBACK_FILTERING=off` only when internals are needed. Keep the
original user-facing error message short and actionable.

## Need to debug at the exact failing runtime check

Use:

```bash
EQX_ON_ERROR=breakpoint python your_script.py
```

Prefer the environment variable over `on_error="breakpoint"`; the keyword exists
but is less reliable for breakpoint-mode debugging because it bypasses Equinox's
JAX workaround. Do this only in an interactive debugging context.

## NaNs occur only in gradients

A masked invalid value may be created on the forward pass and revealed during
backpropagation. Rewrite masked operations to avoid creating invalid values:

```python
safe_x = jnp.where(x > 0, x, 1)
y = jnp.where(x > 0, jnp.log(safe_x), 0)
```

Add `eqx.debug.backward_nan` around suspected values to print primal and
cotangent context.

## `assert_max_traces` fires

The function was traced more than the allowed count. Common causes:

- input array shape or dtype changes;
- static leaves change equality;
- new Python function/closure objects are created in a loop;
- a model stores JAX-transformed callables as leaves.

Use smaller smoke inputs and print tree summaries with `tree_pformat` to compare
static leaves between calls.

## `inspect_dce` shows `<DCE'd>`

The value was dead-code eliminated. This is expected for values that do not
contribute to outputs. If it should be retained, make it part of the output or a
side effect supported by JAX.

## `error_if` is optimized away

A runtime check can disappear if you ignore the value returned by
`eqx.error_if` or `eqx.branched_error_if`.

Fix:

- Thread the returned PyTree into later computation or assign it back.
- Keep the check inside the JAX-transformed code path you actually execute.
- Use `eqx.debug.store_dce` / `eqx.debug.inspect_dce` if you need to confirm the
  elimination.

## `TqdmProgressMeter` import or output fails

`tqdm` is optional. Install it only if the user needs tqdm progress bars:

```bash
python -m pip install tqdm
```

Use `NoProgressMeter` or `TextProgressMeter` for dependency-minimal workflows.
Remember to call `jax.effects_barrier()` before asserting on asynchronous
callback output in tests.

## ONNX export fails or is unavailable

Treat ONNX as unverified for this generated skill. The repository test for the
internal ONNX helper is skipped due an upstream `tf2onnx` issue. If a user needs
ONNX, require a separate `tf2onnx` environment, a concrete export target, and a
small acceptance case before making claims.
