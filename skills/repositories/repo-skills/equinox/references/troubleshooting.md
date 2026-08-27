# Equinox Troubleshooting

Use this file for cross-cutting installation, JAX backend, mixed-PyTree, state,
serialization, and debug failures. For workflow-specific fixes, also read the
nearest sub-skill `references/troubleshooting.md`.

## Install and import checks

### Symptom: `ModuleNotFoundError: No module named 'equinox'`

Likely causes:

- Equinox is not installed in the Python environment being used.
- A notebook, service, or test runner is using a different interpreter.
- `jax`/`jaxlib` install failed before Equinox could import.

Fix:

```bash
python -m pip install equinox
python - <<'PY'
import equinox as eqx
import jax
print(eqx.__version__)
print(jax.__version__, jax.default_backend())
PY
```

For a local package checkout, an editable install is normal during development:

```bash
python -m pip install -e .
```

### Symptom: `pip check` reports JAX or NumPy conflicts

Equinox depends on compatible `jax` and `jaxlib`. Make sure the two JAX packages
match and that any accelerator wheel is compatible with the host. This skill’s
core Equinox workflows are CPU-verifiable; do not install GPU JAX just because a
GPU is present unless the downstream task truly needs GPU behavior.

## Mixed PyTrees and JAX transform errors

### Symptom: `TypeError: ... is not a valid JAX type`

This usually means a plain `jax.jit`, `jax.grad`, `jax.vmap`, or `jax.pmap`
received a PyTree with non-array leaves such as Python functions, strings,
objects, booleans, or activation callables.

Fix options:

1. Replace the raw transform with the filtered version:

   ```python
   @eqx.filter_jit
   @eqx.filter_grad
   def loss(model, x, y):
       return ((jax.vmap(model)(x) - y) ** 2).mean()
   ```

2. Manually split and reassemble the model around a raw JAX transform:

   ```python
   params, static = eqx.partition(model, eqx.is_array)

   @jax.jit
   def step(params, x):
       model = eqx.combine(params, static)
       return model(x)
   ```

### Symptom: Optax raises `zeros_like requires ndarray or scalar arguments`

Optax should receive only differentiable floating-point array leaves, not an
entire mixed Equinox model.

Use:

```python
optim.init(eqx.filter(model, eqx.is_inexact_array))
```

or partition the trainable part explicitly.

## Module construction footguns

### Symptom: missing or unexpected field errors during module initialization

`eqx.Module` subclasses are frozen dataclass PyTrees. Every annotated field must
be assigned exactly as expected. If you define a custom `__init__`, assign all
fields yourself.

Checklist:

- Did every annotated field get assigned in `__init__`?
- Did you accidentally assign `self.not_declared = ...`?
- Does a converter or `eqx.field(static=True)` belong on the field?
- Should validation go in `__check_init__` instead of mutating in
  `__post_init__`?

### Symptom: `Cannot assign methods in __init__`

Equinox rejects storing bound methods as fields because it creates cycles in the
PyTree. Use a `@property`, a separate function, or wrap the underlying module
instead.

### Symptom: gradients update a `field(init=False)` or a static field behaves strangely

Equinox modules are still PyTrees. A non-init field can still be a PyTree leaf.
If a value should not be traced or trained, use a static field for metadata or
filter it out of the trainable parameter tree. Do not mark array-valued trainable
parameters static.

## Stateful layer issues

### Symptom: `BatchNorm` raises a `NameError` about `axis_name`

`eqx.nn.BatchNorm` computes batch statistics through `lax.pmean`, so training
calls must occur inside a `jax.vmap` or `jax.pmap` with the same `axis_name` used
when constructing the layer.

Pattern:

```python
batch_norm = eqx.nn.BatchNorm(input_size, axis_name="batch", mode="batch")
# Later: jax.vmap(call_one_example, axis_name="batch")(batch)
```

### Symptom: `Attempted to use old state`

`eqx.nn.State.set` and `State.update` return a new state and invalidate the old
one to catch accidental stale-state reuse.

Always write:

```python
x, state = layer(x, state)
# not: layer(x, old_state) again
```

Clone a state only when you intentionally need to fork it.

### Symptom: dropout or normalization does not switch to inference behavior

Use `eqx.nn.inference_mode(model, value=True)` to return a new PyTree with all
nested `inference` attributes toggled. Set `value=False` to return to training
mode.

## Parallelism and sharding

### Symptom: `filter_pmap` or sharding examples only see one CPU device

JAX must be configured before backend initialization. For CPU smoke tests, run a
new Python process from the generated skill root; set `EQUINOX_SKILL_ROOT` to
that absolute path:

```bash
cd "$EQUINOX_SKILL_ROOT" && XLA_FLAGS=--xla_force_host_platform_device_count=2 \
  python scripts/smoke.py --mode transformations --two-cpu-devices
```

If you need real accelerator semantics, install and verify a matching JAX
accelerator build; a CPU pmap smoke does not prove CUDA/ROCm/MPS behavior.

## Runtime errors and debug output

### Symptom: `eqx.error_if` under JIT produces a long `CpuCallback` error

The error may be wrapped by JAX internals. `eqx.filter_jit` often removes some
boilerplate from the message. To change on-error behavior, set `EQX_ON_ERROR` or
pass `on_error="raise"`, `"breakpoint"`, `"nan"`, or `"off"`.

### Symptom: NaNs appear only during backpropagation

Use `eqx.debug.backward_nan(x, name="...", terminate=True)` around suspected
values. For masked operations such as `jnp.where(x > 0, jnp.log(x), 0)`, use the
"double where" pattern so invalid values are never created on the forward pass.

### Symptom: a function recompiles repeatedly

Wrap it with:

```python
@eqx.filter_jit
@eqx.debug.assert_max_traces(max_traces=1)
def f(...):
    ...
```

When it fails, inspect which static or array-valued argument changed shape,
dtype, or equality.

## Serialization

### Symptom: deserialization fails with a tree path in the error

`tree_deserialise_leaves` needs a like-tree whose structure, array shapes, and
dtypes match the saved serializable leaves. Use the reported path to find the
first incompatible leaf.

Pattern:

```python
eqx.tree_serialise_leaves(path, model)
restored = eqx.tree_deserialise_leaves(path, like_model)
```

Non-array and non-serializable leaves come from the like-tree unless you provide
a custom filter spec.

## Optional and excluded surfaces

- `tqdm` is only needed for `equinox.internal.TqdmProgressMeter`; the text/no-op
  progress meter paths do not require it.
- The repository contains an ONNX helper in `equinox.internal`, but the native
  ONNX test is skipped because of an upstream `tf2onnx` issue. Treat ONNX export
  as intentionally excluded unless the user supplies an explicit, verified ONNX
  environment and acceptance target.
- `equinox.internal.noinline` is documented as tested only on CPU. Do not claim
  accelerator coverage without running an accelerator-specific smoke test.
