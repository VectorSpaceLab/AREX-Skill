# Haiku parameters, state, RNG, naming, and hooks API reference

This reference is a self-contained map for public `haiku` APIs commonly imported as `import haiku as hk`. Use it while writing or debugging code that executes inside `hk.transform` or `hk.transform_with_state`.

## Core mental model

Haiku lets you write object-oriented modules, then transforms a Python function into pure `init` and `apply` functions. Direct Haiku APIs are side-effecting inside the transformed function: they collect parameters, mutable state, and RNG-sequence progress into explicit data structures returned from or passed to `init`/`apply`.

Parameter and state trees are nested mappings:

```python
params_or_state = {
    "module_or_scope/path": {
        "leaf_name": array,
    },
    "~": {"top_level_value": array},  # values created outside any Module
}
```

Rules of thumb:

- The first key is a module/name-scope path such as `linear`, `encoder/block_0`, or `outer/affine`.
- The second key is the leaf parameter/state name passed to `hk.get_parameter`, `hk.get_state`, or `hk.set_state`, such as `w`, `b`, `count`, or `mean_ema`.
- Top-level values created inside a transformed function but outside any `hk.Module` are grouped under `"~"`.
- Submodules created in a module constructor are named under `parent/~/child`; submodules created in a non-`__call__` method are named under `parent/~method/child`; submodules created in `__call__` use `parent/child`.

## Module authoring APIs

| API | Signature | Use | Notes |
| --- | --- | --- | --- |
| `hk.Module` | `hk.Module(name: str | None = None)` | Base class for custom Haiku modules. | Instantiate modules only inside a transformed function. Subclasses must call `super().__init__(name=name)` before creating submodules, parameters, or state. Default names are lower-snake-case class names. |
| `module.params_dict()` | no public arguments | Inspect parameters belonging to a module and its known submodules inside a transform. | Returns a flat mapping keyed by fully qualified `module/leaf` strings. Useful for debugging, not usually for model logic. |
| `module.state_dict()` | no public arguments | Inspect state belonging to a module and its known submodules inside a transform. | Same shape as `params_dict`, but for mutable state. |

Minimal custom module pattern:

```python
class MyLinear(hk.Module):
    def __init__(self, output_size: int, name: str | None = None):
        super().__init__(name=name)
        self.output_size = output_size

    def __call__(self, x):
        w = hk.get_parameter(
            "w", [x.shape[-1], self.output_size], x.dtype,
            init=hk.initializers.TruncatedNormal(1.0 / x.shape[-1] ** 0.5),
        )
        b = hk.get_parameter("b", [self.output_size], x.dtype, init=jnp.zeros)
        return x @ w + b
```

## Parameter and state APIs

| API | Signature | Use | Sharp edges |
| --- | --- | --- | --- |
| `hk.get_parameter` | `hk.get_parameter(name, shape, dtype=None, init=None)` | Create during `init` or retrieve during `apply` a trainable value in the current module/scope. | `init` is required for the first creation. Reusing the same name in the same module/scope returns the same object only if shape matches. New parameters cannot be created during `apply`. |
| `hk.get_state` | `hk.get_state(name, shape=None, dtype=jnp.float32, init=None)` | Read mutable non-trainable state, initializing it if missing. | Use only under `hk.transform_with_state`. If the state is missing, both `shape`/`dtype` and `init` are needed. |
| `hk.set_state` | `hk.set_state(name, value)` | Set current mutable state for return from `apply`. | Use only under `hk.transform_with_state`; otherwise state is not part of the pure function contract. |
| `hk.get_params` | `hk.get_params()` | Return a copy of the current parameter mapping inside a transform. | Debugging/introspection helper; avoid making model semantics depend on mutable Python structure. |
| `hk.get_initial_state` | `hk.get_initial_state()` | Return the state that would be returned by `init` or passed into `apply`. | Does not run getters or initializers. Useful for tracing state flow. |
| `hk.get_current_state` | `hk.get_current_state()` | Return the current state after any `set_state` calls so far. | Does not run getters or initializers. Useful for debugging update order. |

State update pattern:

```python
class Counter(hk.Module):
    def __call__(self, x):
        count = hk.get_state("count", shape=[], dtype=jnp.int32, init=jnp.zeros)
        hk.set_state("count", count + 1)
        return x, count
```

Transform such functions with `hk.transform_with_state`, not `hk.transform`.

## RNG APIs

| API | Signature | Use | Notes |
| --- | --- | --- | --- |
| `hk.PRNGSequence` | `hk.PRNGSequence(key_or_seed)` | Python iterator that deterministically splits JAX keys from an integer seed or PRNG key. | Useful outside transformed code for managing init/apply keys, and internally Haiku uses the same concept. `next(seq)` returns a fresh key. |
| `hk.next_rng_key` | `hk.next_rng_key()` | Get one fresh key from the current transformed `init`/`apply` RNG sequence. | Raises if the transformed call received `rng=None`. Also must be called inside a Haiku context. |
| `hk.next_rng_keys` | `hk.next_rng_keys(num)` | Get multiple fresh keys at once. | Returns an array of `num` keys; exact key-array shape depends on the active JAX PRNG representation. |
| `hk.maybe_next_rng_key` | `hk.maybe_next_rng_key()` | Return a fresh key when an RNG sequence exists, otherwise `None`. | Use only for paths where no-RNG behavior is intentionally supported. Do not silently skip randomness if the model requires it. |
| `hk.reserve_rng_keys` | `hk.reserve_rng_keys(num)` | Pre-split keys for code that will request many keys. | Micro-optimization for large stochastic functions; most code does not need it. |
| `hk.with_rng` | `hk.with_rng(key)` | Temporarily replace the active RNG sequence inside a transformed call. | Advanced; useful to isolate a stochastic sub-block from the outer sequence. |
| `hk.maybe_get_rng_sequence_state` | `hk.maybe_get_rng_sequence_state()` | Inspect the internal RNG sequence state, or `None` if no RNG exists. | Rarely needed except for advanced wrappers/checkpointing. |
| `hk.replace_rng_sequence_state` | `hk.replace_rng_sequence_state(state)` | Replace the internal RNG sequence state. | Requires a current RNG sequence; advanced recovery/control-flow utility. |

Required RNG pattern:

```python
def stochastic_forward(x):
    key = hk.next_rng_key()
    return x + 0.01 * jax.random.normal(key, x.shape)

forward = hk.transform(stochastic_forward)
params = forward.init(jax.random.PRNGKey(0), x)
y = forward.apply(params, jax.random.PRNGKey(1), x)
```

Optional RNG pattern:

```python
def maybe_stochastic_forward(x):
    key = hk.maybe_next_rng_key()
    if key is None:
        return x
    return x + 0.01 * jax.random.normal(key, x.shape)
```

## Naming APIs

| API | Signature | Use | Notes |
| --- | --- | --- | --- |
| `hk.current_name` | `hk.current_name()` | Return the current module/name-scope key, or `"~"` at top level. | Debugging helper inside a transform. |
| `hk.name_scope` | `hk.name_scope(name, *, method_name="__call__")` | Prefix new modules, parameters, and state created in the block. | The context manager is single-use and must not start with `/`. Duplicate scopes are auto-numbered like modules. |
| `hk.force_name` | `hk.force_name(name)` | Force an absolute module/scope name, ignoring current context. | Advanced; can intentionally share parameters, but can also create surprising singleton-like reuse. Prefer explicit module reuse first. |
| `hk.name_like` | `hk.name_like(method_name)` | Decorate a module method so submodules are named as if created in another method. | Useful for checkpoint-compatible refactors. Explicitly name submodules to avoid accidental duplicate names. |

Common naming outcomes:

```python
# Top-level explicit scope and module:
with hk.name_scope("outer"):
    y = hk.Linear(3, name="proj")(x)
# params key: "outer/proj" with leaves "w" and "b"

# Inside a module constructor:
class Parent(hk.Module):
    def __init__(self):
        super().__init__()
        self.proj = hk.Linear(3)  # key begins "parent/~/linear"

# Inside Parent.__call__:
# a new hk.Linear(3) would be keyed "parent/linear".
```

## Creator, getter, setter, and method interception APIs

These hooks are advanced. Keep hook bodies small, deterministic, and easy to remove.

| API | Callback shape | Use | Notes |
| --- | --- | --- | --- |
| `hk.custom_creator(creator, *, params=True, state=False)` | `creator(next_creator, shape, dtype, init, context)` | Override creation of new parameters and optionally new state. | Call `next_creator(shape, dtype, init)` unless deliberately replacing creation. `context` includes `full_name`, `module_name`, `name`, original shape/dtype/init, module, and lifted prefix. |
| `hk.custom_getter(getter, *, params=True, state=False)` | `getter(next_getter, value, context)` | Override returned parameter/state values. | Useful for casting, providing external/pretrained values, or logging. Call `next_getter(value)` to continue stacked getters. |
| `hk.custom_setter(setter)` | `setter(next_setter, value, context)` | Override state values as they are set. | Call `next_setter(value)` to continue stacked setters. `context` includes full state name, module, original shape/dtype, and lifted prefix. |
| `hk.intercept_methods(interceptor)` | `interceptor(next_fun, args, kwargs, context)` | Intercept `hk.Module` method calls to modify inputs, outputs, or skip methods. | `context` includes `module`, `method_name`, `orig_method`, and `orig_class`. Call `next_fun(*args, **kwargs)` to continue; `context.orig_method(...)` short-circuits remaining interceptors. |

Example getter for temporary dtype casting:

```python
def bf16_getter(next_getter, value, context):
    del context
    if hasattr(value, "astype"):
        value = value.astype(jnp.bfloat16)
    return next_getter(value)

with hk.custom_getter(bf16_getter):
    y = model(x)
```

Example method interceptor that observes calls without changing behavior:

```python
def log_calls(next_fun, args, kwargs, context):
    print(context.module.module_name, context.method_name)
    return next_fun(*args, **kwargs)

with hk.intercept_methods(log_calls):
    y = model(x)
```
