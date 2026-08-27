# Module and PyTree Workflows

Equinox’s central idea is that models are ordinary PyTrees. Subclassing
`eqx.Module` gives a frozen dataclass whose leaves can be arrays, functions,
other modules, Python scalars, or arbitrary objects.

## Define a simple module

```python
import equinox as eqx
import jax
import jax.numpy as jnp

class Linear(eqx.Module):
    weight: jax.Array
    bias: jax.Array
    name: str = eqx.field(static=True)

    def __init__(self, in_size, out_size, key, name="linear"):
        wkey, bkey = jax.random.split(key)
        self.weight = jax.random.normal(wkey, (out_size, in_size))
        self.bias = jax.random.normal(bkey, (out_size,))
        self.name = name

    def __call__(self, x):
        return self.weight @ x + self.bias
```

Use `static=True` for metadata that should not become a dynamic PyTree leaf.
Do not use it for trainable arrays.

## Field decisions

| Need | Pattern | Notes |
| --- | --- | --- |
| Convert inputs once | `eqx.field(converter=callable)` | Converter runs after `__init__` or dataclass-style `__post_init__`, before `__check_init__`. |
| Exclude metadata from PyTree leaves | `eqx.field(static=True)` | Good for strings, shape tags, bool flags, and small configuration values. |
| Validate invariants | `def __check_init__(self): ...` | Runs after initialization across the class hierarchy; assignment is disallowed. |
| Abstract instance attribute | `foo: eqx.AbstractVar[Array]` | Concrete subclass must provide the field or property. |
| Abstract class attribute | `foo: eqx.AbstractClassVar[...]` | Use for class-level contracts. |
| Wrap callable for tree behavior | `eqx.Partial(fn, *args, **kwargs)` | Similar to `functools.partial`, but a PyTree. |

## Abstract/final pattern

The repo documentation recommends treating every `eqx.Module` subclass as either
abstract or final:

1. Abstract classes declare interfaces with `abc.abstractmethod`,
   `eqx.AbstractVar`, or `eqx.AbstractClassVar`.
2. Final classes provide all fields and the concrete `__init__`.
3. Avoid overriding concrete methods; prefer composition/wrappers.
4. Keep all fields and initialization logic in one class when possible.

This pattern makes JAX-traced model behavior easier to reason about because the
concrete tree structure is explicit.

## Filtering and partitioning

Mixed PyTrees frequently need only their array leaves passed through an optimizer
or raw JAX transform.

```python
import functools as ft

params, static = eqx.partition(model, eqx.is_inexact_array)

@ft.partial(jax.jit, static_argnums=1)  # raw JAX must treat the non-array split as static
def loss(params, static, x, y):
    model = eqx.combine(params, static)
    pred = jax.vmap(model)(x)
    return ((pred - y) ** 2).mean()
```

Use `eqx.is_array` when all JAX/NumPy arrays should be dynamic. Use
`eqx.is_inexact_array` for differentiable floating-point/complex arrays, which
is often the right filter for optimizers. When using raw `jax.jit`, do not pass
the non-array partition as an ordinary dynamic argument; either mark it static
(as above) or use `eqx.filter_jit`/`eqx.filter_grad` instead.

## Model surgery with `tree_at`

`eqx.tree_at(where, pytree, replace=...)` returns a new PyTree with selected
leaves replaced.

Replace the final layer in an MLP:

```python
new_final = eqx.nn.Linear(old_mlp.layers[-1].in_features, out_size, key=key)
new_mlp = eqx.tree_at(lambda m: m.layers[-1], old_mlp, new_final)
```

Replace all linear weights found by a custom selector:

```python
def is_linear(x):
    return isinstance(x, eqx.nn.Linear)

def get_weights(model):
    return [leaf.weight for leaf in jax.tree_util.tree_leaves(model, is_leaf=is_linear)
            if is_linear(leaf)]

new_model = eqx.tree_at(get_weights, model, new_weights)
```

When the replacement is derived from the old value, use `replace_fn=` instead of
precomputing a replacement list.

## Training updates

`eqx.apply_updates(model, updates)` applies an Optax-style update PyTree to a
model PyTree. Pair it with `eqx.filter(model, eqx.is_inexact_array)` for
optimizer initialization.

```python
optim = optax.adam(1e-3)
opt_state = optim.init(eqx.filter(model, eqx.is_inexact_array))

grads = eqx.filter_grad(loss)(model, batch)
updates, opt_state = optim.update(grads, opt_state, model)
model = eqx.apply_updates(model, updates)
```

## Abstract attribute errors

If instantiating a module raises `Can't instantiate abstract class ... with abstract attributes ...` or `... with abstract class attributes ...`, then one or more `AbstractVar` / `AbstractClassVar` annotations are still unresolved.

Fix:

- Make sure every `AbstractVar` is overridden by a concrete field, property, or intentionally class-level value on the final subclass.
- Make sure every `AbstractClassVar` is overridden by concrete annotation/value on the final subclass; prefer a class attribute or `ClassVar` when callers need `type(module).attr`.
- If the attribute is meant to be instance data, keep it as a field on the final class rather than a class variable.
- If the attribute is meant to be shared configuration, use a class attribute or `eqx.field(static=True)` only when it should stay part of the PyTree structure.

## Tree checks and comparisons

| Function | Use |
| --- | --- |
| `eqx.tree_check(pytree)` | Raise when a PyTree has duplicate non-leaf nodes that may imply mistaken sharing. |
| `eqx.tree_equal(a, b, ...)` | Compare PyTrees, including array values; useful for smoke tests and serialization checks. |
| `eqx.tree_flatten_one_level(pytree)` | Inspect exactly one flattening level rather than all leaves. |

Use `tree_check` before training when a model was assembled from reused objects.
If intentional weight tying is needed, use `eqx.nn.Shared` from the
`nn-and-state` sub-skill instead of relying on Python object identity.

## Validation checklist

- Every module field has an annotation.
- Trainable arrays are not static fields.
- Non-array callables or config values are either static or handled with
  filtered transforms.
- Optimizers see only inexact array leaves.
- Model surgery is expressed with `tree_at`, not in-place mutation.
- Structure-sensitive changes are validated with `tree_check` or a focused
  output equality check.
