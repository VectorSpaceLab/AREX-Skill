# Module and Tree Troubleshooting

## `TypeError`: missing required fields

An `eqx.Module` is dataclass-like. If no custom `__init__` is defined, the
constructor expects every annotated field. If a custom `__init__` is defined,
you must assign every annotated field yourself.

Fix:

- Compare annotations to assignments in `__init__`.
- Remove assignments to fields that are not annotated.
- Use keyword-only construction if inheritance makes positional arguments hard
  to read.

## `AttributeError`: assigning a field after initialization

Modules are frozen after construction. Perform out-of-place updates with
`eqx.tree_at` or build a new module instance.

```python
model = eqx.tree_at(lambda m: m.layers[-1], model, new_layer)
```

Do not write `model.layers[-1] = new_layer`.

## `Cannot assign methods in __init__`

Storing `self.method` as a PyTree leaf creates a cycle. Use one of these:

```python
class M(eqx.Module):
    @property
    def fn(self):
        return self.method

    def method(self, x):
        return x
```

or store a plain function / separate module that does not close over `self`.

## Static-field confusion

`eqx.field(static=True)` removes a field from the PyTree leaves. It is suitable
for metadata and configuration, not trainable arrays. A static array will not be
updated by gradients and may cause recompilation whenever it changes.

If the problem is only that a plain JAX transform rejected non-array leaves, keep
the model structure and use `eqx.filter_jit`, `eqx.filter_grad`, or
`eqx.partition`/`eqx.combine` instead.

## Abstract attribute errors

If you see `Can't instantiate abstract class ... with abstract attributes ...` or `... with abstract class attributes ...`, then a base class declared `AbstractVar` or `AbstractClassVar` that the final subclass did not fully implement.

Fix:

- Give every `AbstractVar` a concrete field, property, or intentionally class-level value on the final subclass.
- Give every `AbstractClassVar` a concrete annotation/value; prefer a class attribute or `ClassVar` when callers need `type(module).attr`.
- If the attribute should be part of the runtime PyTree, make it a field instead of a class attribute.
- If it should stay as metadata only, use `eqx.field(static=True)` on the concrete field.

## `__post_init__` not running as expected

A user-defined `__init__` overrides dataclass-generated initialization and can
prevent a `__post_init__` pattern from doing what you expect. Prefer
`__check_init__` for invariant checking in Equinox modules.

```python
class Positive(eqx.Module):
    value: int

    def __check_init__(self):
        if self.value <= 0:
            raise ValueError("value must be positive")
```

Do not assign fields inside `__check_init__`.

## Optax sees non-array leaves

Initialize optimizers with a filtered parameter tree:

```python
opt_state = optim.init(eqx.filter(model, eqx.is_inexact_array))
```

If an optimizer update tree contains `None` leaves, `eqx.apply_updates` leaves
those model leaves unchanged.

## Duplicate modules or parameters after construction

Equinox models are PyTrees, not DAGs. Reusing the same Python object in two
positions usually means two value copies, not shared training identity. Run:

```python
eqx.tree_check(model)
```

If intentional tying is needed, use `eqx.nn.Shared` and validate that the shared
replacement has the same structure, shape, and dtype.

## `tree_at` selector errors

`tree_at` selectors must pick leaves or subtrees by structure, not by data-valued
control flow. If the selector depends on array values, compute the target path
outside the transformed function or use a deterministic structural predicate.

Checklist:

- Does `where(model)` return the same structural location every time?
- Are you replacing a single leaf with a value, or multiple leaves with a
  sequence of the same length?
- If using `replace_fn`, does it accept each old selected value?
- If replacing `None`, do you need an `is_leaf` rule?
