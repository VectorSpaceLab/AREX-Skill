# Filtered Transformation Workflows

Equinox filtered transformations wrap common JAX transforms so they can accept
arbitrary PyTrees. Array-like leaves are traced dynamically; non-array leaves are
handled statically.

## When to choose filtered transforms

Use `eqx.filter_*` when the argument crossing a JAX transform boundary is a
model, optimizer state, callable wrapper, or nested PyTree that may contain
functions, strings, objects, or other non-array values.

```python
@eqx.filter_jit
@eqx.filter_grad
def loss(model, x, y):
    pred = jax.vmap(model)(x)
    return ((pred - y) ** 2).mean()
```

If every argument is already an array-only PyTree, the filtered API is usually a
safe replacement for the raw JAX API.

## Main transform groups

| Transform | Use | Notes |
| --- | --- | --- |
| `filter_jit` | Compile functions or methods over mixed PyTrees. | `donate=` controls buffer donation. `.lower(...).compile()` is available through Equinox wrappers. |
| `filter_grad`, `filter_value_and_grad` | Differentiate with respect to inexact array leaves. | Use `has_aux=True` for auxiliary outputs. |
| `filter_jvp`, `filter_vjp`, `filter_jacfwd`, `filter_jacrev`, `filter_hessian` | Forward/reverse AD and Jacobian/Hessian workflows. | Tangent/cotangent PyTrees must align with dynamic leaves. |
| `filter_custom_jvp`, `filter_custom_vjp` | Custom derivative rules over mixed arguments. | Definition methods mirror JAX custom derivative conventions but include filtered nondifferentiable handling. |
| `filter_vmap` | Vectorize functions returning or accepting PyTrees. | Defaults use `eqx.if_array(0)` for array leaves and `None` for non-array leaves. |
| `filter_pmap` | Parallel-map over devices with mixed PyTrees. | Requires matching device axis shape; CPU multi-device smoke uses host device count flags. |
| `filter_eval_shape`, `filter_make_jaxpr` | Inspect abstract output shape or JAXPR for mixed PyTrees. | Useful before constructing `Shared` or debugging transform boundaries. |
| `filter_checkpoint`, `filter_closure_convert`, `filter_pure_callback`, `filter_shard` | Advanced checkpointing, closure conversion, callback, and sharding workflows. | Use focused smoke tests; route internal primitive work to `internal-advanced`. |

## `filter_jit` pattern

Use `filter_jit` around the whole numerical step, not just the loss, when
training performance matters.

```python
@eqx.filter_jit
def make_step(model, opt_state, x, y):
    loss, grads = eqx.filter_value_and_grad(loss_fn)(model, x, y)
    updates, opt_state = optim.update(grads, opt_state, model)
    model = eqx.apply_updates(model, updates)
    return model, opt_state, loss
```

Set `donate="all-except-first"` or similar only after confirming the caller will
not reuse donated buffers.

## Manual filtering alternative

When a raw JAX API must be used, split the model explicitly.

```python
params, static = eqx.partition(model, eqx.is_array)

@jax.jit
def compiled(params, x):
    model = eqx.combine(params, static)
    return model(x)
```

Use this pattern for `jax.lax.scan`, `cond`, or external APIs that do not know
about Equinox filtered transforms.

## Batched and parallel calls

Most `equinox.nn` layers process one example. For a batch:

```python
y = jax.vmap(model)(x_batch)
```

For an ensemble or a vectorized model PyTree:

```python
@eqx.filter_vmap
def make_model(key):
    return eqx.nn.MLP(2, 1, 16, 2, key=key)

ensemble = make_model(jax.random.split(key, 8))
```

When evaluating each ensemble member on the same input, use `in_axes` to map only
array leaves of the ensemble and not the shared input:

```python
@eqx.filter_vmap(in_axes=(eqx.if_array(0), None))
def evaluate(member, x):
    return member(x)
```

## pmap, callback, and sharding checks

`filter_pmap` mirrors `jax.pmap` while filtering non-array leaves. A CPU smoke
can validate structure when a new Python process exposes multiple CPU devices.
Run it from the generated skill root; set `EQUINOX_SKILL_ROOT` to that absolute
path:

```bash
cd "$EQUINOX_SKILL_ROOT" && XLA_FLAGS=--xla_force_host_platform_device_count=2 \
  python scripts/smoke.py --mode transformations --two-cpu-devices
```

Use real accelerator JAX wheels and device smoke checks for real CUDA/ROCm/MPS
claims.

`filter_pure_callback` lets a JIT region call back into Python with arbitrary
non-array inputs and outputs. Pass `result_shape_dtypes=` as a keyword and make
sure the static part of the returned PyTree exactly matches the declared static
structure.

## Shape/JAXPR inspection

Use `filter_eval_shape` to compare structures without allocating full arrays.
This is especially useful before `eqx.nn.Shared`, where source and destination
leaves must have matching tree structure, shape, and dtype.

```python
source_struct = eqx.filter_eval_shape(get, model)
dest_struct = eqx.filter_eval_shape(where, model)
assert eqx.tree_equal(source_struct, dest_struct) is True
```

Use `filter_make_jaxpr` when the task is to inspect transformed computation
rather than execute it.

## Custom derivatives

Use `filter_custom_jvp` and `filter_custom_vjp` when a function has mixed PyTree
arguments but still needs custom derivative definitions. Keep derivative rules
focused on differentiable array leaves; static metadata should be treated as
nondifferentiable configuration.

Checklist:

- Does the decorated function accept/return PyTrees with non-array leaves?
- Are nondifferentiable leaves excluded from tangent/cotangent construction?
- Does `has_aux=True` match the function output shape?
- Are symbolic zeros handled where the derivative rule expects them?
