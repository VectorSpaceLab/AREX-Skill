# Filtered Transformation Troubleshooting

## Raw JAX transform rejects a model

Symptom:

```text
TypeError: Argument '<function ...>' of type <class 'function'> is not a valid JAX type
```

Fix: replace the raw transform with an Equinox filtered transform.

```python
compiled = eqx.filter_jit(fn)
grad_fn = eqx.filter_grad(loss_fn)
batched = eqx.filter_vmap(fn)
```

If an external API requires raw JAX transforms, use `eqx.partition` and
`eqx.combine` to move only array leaves across the boundary.

## `filter_grad` returns missing or `None` leaves

`filter_grad` differentiates only inexact array leaves. Integer arrays, booleans,
functions, strings, objects, and static metadata are nondifferentiable.

Checklist:

- Are trainable parameters floating-point or complex arrays?
- Did you use `eqx.is_inexact_array` for optimizer initialization?
- Did `stop_gradient` intentionally remove a parameter from gradients?
- Is the value stored in a static field and therefore outside the dynamic PyTree?

## `filter_pure_callback` output structure mismatch

Symptom: a callback works eagerly but fails under `filter_jit`, or raises a
runtime error after returning a PyTree whose static leaves differ from
`result_shape_dtypes`.

Common causes:

- `result_shape_dtypes` was not passed as the required keyword argument;
- array outputs are not represented by `jax.ShapeDtypeStruct` leaves;
- static sentinel/object leaves returned by the callback do not match the
  declared static structure.

Recovery steps:

1. Define `result_shape_dtypes` with `jax.ShapeDtypeStruct` for every array
   output and the exact expected static leaves for non-arrays.
2. Keep callback side effects out of correctness assumptions; it is a pure
   callback from JAX's perspective.
3. Test the callback both directly and inside a tiny `eqx.filter_jit` wrapper.

## Repeated recompilation

Use:

```python
@eqx.filter_jit
@eqx.debug.assert_max_traces(max_traces=1)
def step(...):
    ...
```

Common causes:

- Static leaves change equality between calls.
- Array shapes or dtypes change.
- Python functions or closures are recreated inside the training loop.
- A model stores transformed callables rather than applying transforms at call
  time.

## Storing `jax.vmap(model)` or `jax.jit(model)` inside a module

Equinox warns when a JAX-transformed callable is assigned as a module field and
its parameters will not be updated correctly.

Prefer:

```python
class Model(eqx.Module):
    layer: eqx.nn.Linear

    def __call__(self, x):
        return jax.vmap(self.layer)(x)
```

or use `eqx.filter_vmap` if the transformed callable itself needs to be a
PyTree.

## `filter_vmap` axes are wrong

Defaults are `in_axes=eqx.if_array(0)` and `out_axes=eqx.if_array(0)`. Non-array
leaves are not batched by default.

Use explicit `in_axes` when only some array leaves are batched:

```python
@eqx.filter_vmap(in_axes=(eqx.if_array(0), None))
def evaluate(model_ensemble, shared_x):
    return model_ensemble(shared_x)
```

If the model was created by vmapping initialization, do not call it directly;
call it inside another `filter_vmap` or unpeel its leading parameter axis.

## `filter_pmap` sees the wrong number of devices

A pmap axis length must match the visible device count. For CPU-only structural
checks, start a fresh process with multiple logical CPU devices before importing
JAX, from the generated skill root. Set `EQUINOX_SKILL_ROOT` to that absolute
path:

```bash
cd "$EQUINOX_SKILL_ROOT" && XLA_FLAGS=--xla_force_host_platform_device_count=2 \
  python scripts/smoke.py --mode transformations --two-cpu-devices
```

For accelerator checks, install and verify the accelerator-specific JAX wheel.
CPU pmap only proves API structure, not device-specific performance or kernels.

## Donation warnings or use-after-donation errors

`filter_jit` donation modes include `"all"`, `"all-except-first"`, warning
variants, and `"none"`. `filter_pmap` donation modes include `"all"`, `"warn"`,
and `"none"`.

Use donation only when the caller will not reuse donated buffers. Keep
`donate="none"` in examples and smoke checks unless memory pressure or compile
behavior is the actual task.

## Custom JVP/VJP tangents do not match

Filtered custom derivative rules still need tangent/cotangent structures that
match differentiable array leaves. If a residual or auxiliary output contains
non-arrays, keep it in the filtered/static path and test with both eager and
`filter_jit` calls.

## `filter_shard` does not show expected sharding

Confirm that:

- the target device mesh and `PartitionSpec` are valid for visible devices;
- `filter_shard` is applied to the array leaves that need sharding;
- a surrounding `filter_jit` does not override or hide the sharding boundary;
- the backend under test is the one you intend to claim.
