# Diagnostics and Serialization Workflows

This reference covers Equinox utilities that help inspect, validate, save, load,
and debug PyTrees and transformed JAX programs.

## Serialization model

Equinox serialization is leaf-oriented. It stores serializable leaves and uses a
like-tree during loading to restore structure and non-serialized leaves.

```python
import equinox as eqx

# Save serializable leaves.
eqx.tree_serialise_leaves("model.eqx", model)

# Restore into the structure of a fresh or template model.
restored = eqx.tree_deserialise_leaves("model.eqx", like_model)
```

Use a directory path or a binary file object. Use a custom `filter_spec` when you
need to skip or alter how particular leaves are stored.

## Custom filter specs

Default behavior handles arrays and Python scalar-like leaves. For custom
behavior, pass callables that receive the file object and leaf.

```python
def serialise_filter(f, leaf):
    if should_skip(leaf):
        return None
    return eqx.default_serialise_filter_spec(f, leaf)

def deserialise_filter(f, like_leaf):
    if callable(like_leaf):
        return like_leaf
    return eqx.default_deserialise_filter_spec(f, like_leaf)
```

Keep filter specs paired: whatever the serialize side skips or custom-writes must
be compatible with the deserialization side and the like-tree.

## Runtime checks

Use `eqx.error_if` to raise errors inside JAX-transformed computation.

```python
def safe_sqrt(x):
    x = eqx.error_if(x, x < 0, "sqrt input must be nonnegative")
    return jnp.sqrt(x)
```

Use `eqx.branched_error_if` or `eqx.Enumeration` when error messages come from a
set of indexed conditions.

Prefer `EQX_ON_ERROR` for breakpoint-mode debugging. The `on_error=` keyword can
override the mode per call, but `breakpoint` is most reliable when set via the
environment variable because that activates Equinox's JAX workaround. Keep
`raise`/default for correctness checks.

## Debugging NaNs

Forward NaNs are often best found with `JAX_DEBUG_NANS=1`, `jax.debug.print`, and
smaller eager reproductions. Backward-only NaNs are often caused by masked
invalid values. Use `eqx.debug.backward_nan` around suspicious values.

```python
y = eqx.debug.backward_nan(y, name="after_safe_log", terminate=True)
```

For `jnp.where`, use a double-where pattern to avoid creating invalid forward
values that later leak into backward passes.

## Trace-count debugging

Use `assert_max_traces` around compiled functions to catch accidental repeated
compilation.

```python
@eqx.filter_jit
@eqx.debug.assert_max_traces(max_traces=1)
def step(model, batch):
    ...
```

Then inspect which argument changes shape, dtype, or static equality. Static
function objects recreated inside a loop are a common cause.

## Dead-code elimination checks

`eqx.debug.store_dce` and `eqx.debug.inspect_dce` help determine whether values
were removed by JAX/XLA dead-code elimination.

```python
@jax.jit
def f(x):
    a, b = eqx.debug.store_dce((x**2, x + 1), name="step")
    return a

f(1)
eqx.debug.inspect_dce("step")
```

Use this for diagnostic questions, not as normal program control flow. The same
caveat applies to `eqx.error_if` and `eqx.branched_error_if`: if you drop the
returned value, the check itself can be optimized away.

## Pretty printing

`tree_pformat` and `tree_pprint` render modules and PyTrees in a readable format.
They are useful in bug reports, smoke tests, and shape reviews.

```python
print(eqx.tree_pformat(model))
print(eqx.tree_pformat(jax.eval_shape(lambda: model), struct_as_array=True))
```

## Enumerations

`eqx.Enumeration` supports JAX-compatible enum-like values. Enumeration items are
PyTree modules and can participate in transformed control/error paths. Use
`item.error_if(token, pred)` when the runtime error message belongs to an enum
item.

## Progress meters

`equinox.internal` exposes progress meters used by internal loop utilities:
`NoProgressMeter`, `TextProgressMeter`, and `TqdmProgressMeter`. `tqdm` is an
optional dependency for the tqdm-backed meter. Use text/no-op meters in minimal
environments.

## Caches

Use `eqx.clear_caches()` when transform caches need to be reset during debugging,
tests, or after repeatedly constructing dynamic functions. Avoid putting it in a
hot training path unless cache behavior is the problem under investigation.

## ONNX exclusion

The repo exposes an internal `to_onnx` helper, but native evidence marks the ONNX
test skipped because of an upstream `tf2onnx` bug. Do not present ONNX export as
verified Equinox guidance unless the user provides a separate verified ONNX
runtime and acceptance test.
