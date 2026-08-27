# State, RNG, naming, and hook workflows

These workflows assume `import haiku as hk`, `import jax`, and `import jax.numpy as jnp`. They are written with synthetic arrays so they can be adapted without datasets.

## 1. Build a custom `hk.Module` and predict parameter keys

Use `hk.Module` when you want a reusable object that creates parameters, state, or submodules. Call `super().__init__(name=name)` first, store only static Python configuration on `self`, and create Haiku values inside transformed methods.

```python
class AffineProbe(hk.Module):
    def __init__(self, width: int, name: str | None = None):
        super().__init__(name=name)
        self.width = width

    def __call__(self, x):
        w = hk.get_parameter(
            "w", [x.shape[-1], self.width], x.dtype,
            init=hk.initializers.Constant(0.5),
        )
        b = hk.get_parameter("b", [self.width], x.dtype, init=jnp.zeros)
        return x @ w + b


def forward(x):
    with hk.name_scope("outer"):
        return AffineProbe(2, name="affine")(x)

forward = hk.without_apply_rng(hk.transform(forward))
x = jnp.ones([4, 3])
params = forward.init(jax.random.PRNGKey(0), x)
y = forward.apply(params, x)
```

Expected keys:

```python
assert set(params) == {"outer/affine"}
assert set(params["outer/affine"]) == {"w", "b"}
assert params["outer/affine"]["w"].shape == (3, 2)
assert params["outer/affine"]["b"].shape == (2,)
```

When a second module is created with the same base name in the same scope, Haiku normally appends `_1`, `_2`, and so on. Reusing the same module instance reuses its parameters; creating a new module object creates a new named bundle unless you force sharing.

## 2. Use mutable state with `hk.transform_with_state`

Use state for values that are not optimizer parameters but must persist across calls, such as counters, moving averages, or BatchNorm statistics. State changes are explicit in the transformed function contract.

```python
class Counter(hk.Module):
    def __call__(self, x):
        count = hk.get_state("count", shape=[], dtype=jnp.int32, init=jnp.zeros)
        total = hk.get_state("total", shape=x.shape, dtype=x.dtype, init=jnp.zeros)
        hk.set_state("count", count + 1)
        hk.set_state("total", total + x)
        return x + count.astype(x.dtype)


def forward(x):
    return Counter(name="counter")(x)

forward = hk.transform_with_state(forward)
x = jnp.ones([2, 3])
params, state = forward.init(None, x)
y1, state = forward.apply(params, state, None, x)
y2, state = forward.apply(params, state, None, x)
```

Expected behavior:

- `params` is empty if the module only uses state.
- Initial `state["counter"]["count"]` is `0`.
- After the first apply, `count` is `1`; after the second apply, `count` is `2`.
- `hk.get_state` reads the current value for this call; `hk.set_state` determines the returned updated state.

Do not use `hk.transform` for this workflow. If a function touches state, select `hk.transform_with_state` before debugging anything else.

## 3. Write a required stochastic path

Use `hk.next_rng_key()` when randomness is required for correct semantics, such as dropout, sampling, or stochastic latent variables. The transformed `init` and `apply` calls must receive a non-`None` RNG whenever that line can execute.

```python
def stochastic_forward(x, scale=0.1):
    key = hk.next_rng_key()
    eps = jax.random.normal(key, x.shape)
    return x + scale * eps

forward = hk.transform(stochastic_forward)
x = jnp.zeros([2, 3])
params = forward.init(jax.random.PRNGKey(0), x)
y = forward.apply(params, jax.random.PRNGKey(1), x)
```

For an outside training loop, keep a key in the training state and split before every stochastic apply:

```python
rng = jax.random.PRNGKey(0)
for step in range(num_steps):
    rng, apply_rng = jax.random.split(rng)
    y = forward.apply(params, apply_rng, batch)
```

If two independent random samples are needed in one forward pass, either call `hk.next_rng_key()` twice or use `hk.next_rng_keys(2)`:

```python
k1, k2 = hk.next_rng_keys(2)
z = mean + std * jax.random.normal(k1, mean.shape)
mask = jax.random.bernoulli(k2, keep_prob, x.shape)
```

## 4. Recover from `rng=None` intentionally with `hk.maybe_next_rng_key`

If randomness is optional, code the fallback explicitly. This is useful for a single function that supports deterministic inference without an RNG but stochastic training when an RNG exists.

```python
def optional_noise(x, is_training: bool):
    if not is_training:
        return x
    key = hk.maybe_next_rng_key()
    if key is None:
        # Deterministic fallback. Consider raising instead if training must be stochastic.
        return x
    return x + 0.01 * jax.random.normal(key, x.shape)
```

Use this pattern sparingly. If a caller forgot an RNG for a path that requires randomness, prefer `hk.next_rng_key()` so the failure is loud and points to the missing key.

## 5. Debug duplicate names and intentional parameter sharing

Safe parameter sharing options, from least surprising to most advanced:

1. Reuse the same module instance.
2. Pass explicit unique names to separate module instances when they should not share.
3. Use `hk.force_name(existing_module.module_name)` only when absolute-name sharing is intentional and documented.

Example:

```python
class TwoHeads(hk.Module):
    def __call__(self, x, share: bool):
        head_a = hk.Linear(4, name="head")
        if share:
            head_b = head_a                 # same object, same parameters
        else:
            head_b = hk.Linear(4, name="head_b")
        return head_a(x), head_b(x)
```

Use `hk.force_name` only for compatibility or plumbing cases where the module instance is unavailable but the exact module name is known:

```python
shared = hk.Linear(4, name="proj")
alias = hk.Linear(4, name=hk.force_name(shared.module_name))
```

After using forced names, inspect the parameter tree. If two logical modules now point to the same `params[module_name]` bundle, optimizer updates and checkpoint entries are shared too.

## 6. Preserve checkpoint names during a method refactor

When moving submodule construction out of `__call__`, Haiku changes method-based name prefixes. Use `hk.name_like("__call__")` on the new method if you need old checkpoint keys.

```python
class Encoder(hk.Module):
    @hk.name_like("__call__")
    def encode(self, x):
        return hk.Linear(8, name="proj")(x)  # keeps key like encoder/proj

    def __call__(self, x):
        return self.encode(x)
```

If relying on automatic numbering, explicitly name the moved modules. Otherwise two methods both pretending to be `__call__` can accidentally request the same default `linear` name.

## 7. Use creators, getters, and setters for narrow policy hooks

A custom creator can change initialization or skip storage; a getter can alter values when read; a setter can alter state values when saved. Scope these hooks tightly around the code that needs them.

```python
def zero_creator(next_creator, shape, dtype, init, context):
    del init, context
    return next_creator(shape, dtype, jnp.zeros)


def fp32_getter(next_getter, value, context):
    del context
    if hasattr(value, "astype"):
        value = value.astype(jnp.float32)
    return next_getter(value)


def nonnegative_state(next_setter, value, context):
    del context
    return next_setter(jnp.maximum(value, 0))

with hk.custom_creator(zero_creator), \
     hk.custom_getter(fp32_getter), \
     hk.custom_setter(nonnegative_state):
    y = model(x)
```

Guidelines:

- Always call the `next_*` continuation unless you deliberately short-circuit the hook stack.
- Filter by `context.module_name` and `context.name` instead of applying broad global changes.
- Use `state=True` on `custom_creator` or `custom_getter` only when state should be affected as well as parameters.

## 8. Intercept module methods for diagnostics or localized behavior changes

`hk.intercept_methods` wraps `hk.Module` method calls. It can observe calls, change args/kwargs, change outputs, or skip the underlying method. It is powerful enough to be dangerous; prefer it for diagnostics or temporary compatibility layers.

```python
def log_linear_calls(next_fun, args, kwargs, context):
    if isinstance(context.module, hk.Linear) and context.method_name == "__call__":
        print("calling", context.module.module_name)
    return next_fun(*args, **kwargs)

with hk.intercept_methods(log_linear_calls):
    y = model(x)
```

To modify behavior, call `next_fun(*new_args, **new_kwargs)` after edits. Calling `context.orig_method(...)` bypasses any remaining interceptors, so reserve it for explicit short-circuit behavior.

## 9. Fast tree inspection recipe

When a parameter or state key surprises you, print a shape-only view rather than full arrays:

```python
def shape_tree(tree):
    return jax.tree.map(lambda v: getattr(v, "shape", None), tree)

print(shape_tree(params))
print(shape_tree(state))
```

For stable iteration over Haiku-style trees, use `hk.data_structures.traverse` from the advanced/data-structures sub-skill:

```python
for module_name, leaf_name, value in hk.data_structures.traverse(params):
    print(module_name, leaf_name, value.shape)
```
