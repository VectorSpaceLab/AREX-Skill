# Core Transform API Reference

## Purpose

Read this reference to choose the correct Haiku transform wrapper and call the resulting `init` and `apply` functions in the right order. The API facts here are distilled from Haiku's public transform documentation, implementation behavior, behavior tests, and installed signature inspection.

## Transform objects and signatures

| API | Use when | `init` contract | `apply` contract | Return type notes |
| --- | --- | --- | --- | --- |
| `hk.transform(f, *, apply_rng=True)` | `f` uses Haiku modules/parameters but no mutable state. | `params = init(rng, *args, **kwargs)` | `out = apply(params, rng, *args, **kwargs)` | Returns `hk.Transformed(init, apply)`. The `apply_rng` keyword is retained in the signature but `apply_rng=False` is removed; use `hk.without_apply_rng(hk.transform(f))` instead. |
| `hk.transform_with_state(f)` | `f` uses `hk.get_state`, `hk.set_state`, or stateful modules. | `params, state = init(rng, *args, **kwargs)` | `out, new_state = apply(params, state, rng, *args, **kwargs)` | Returns `hk.TransformedWithState(init, apply)`. State has the same nested module/name mapping style as params. |
| `hk.without_apply_rng(transformed)` | The apply path is deterministic and never needs a non-`None` Haiku RNG. | unchanged: `rng` remains first for `init`. | Stateless: `out = apply(params, *args, **kwargs)`. Stateful: `out, new_state = apply(params, state, *args, **kwargs)`. Multi-transform apply functions follow the same removal. | Works for `Transformed`, `TransformedWithState`, `MultiTransformed`, and `MultiTransformedWithState`. It supplies `rng=None` internally during apply. |
| `hk.without_state(transformed_with_state)` | You have a `TransformedWithState` object but the function is actually state-free. | `params = init(rng, *args, **kwargs)` | `out = apply(params, rng, *args, **kwargs)` | Raises if init or apply creates non-empty state. Use `transform_with_state` directly when state is real. |
| `hk.with_empty_state(transformed)` | A stateless transform must match a stateful interface for a uniform pipeline. | `params, state = init(rng, *args, **kwargs)` with empty state. | `out, state = apply(params, state, rng, *args, **kwargs)` with empty state returned. | Does not make the function stateful; it ignores supplied state and returns an empty mapping. |
| `hk.multi_transform(factory)` | Several apply methods share one parameter set and no state. | `params = init(rng, *args, **kwargs)` from the template function. | Each apply function in the returned tree has `out = apply_i(params, rng, *args, **kwargs)`. | `factory()` returns `(template_fn, apply_fn_tree)`. The apply tree can be a tuple, dict, custom pytree, or nested structure. |
| `hk.multi_transform_with_state(factory)` | Several apply methods share parameters and mutable state. | `params, state = init(rng, *args, **kwargs)` from the template function. | Each apply function in the returned tree has `out, new_state = apply_i(params, state, rng, *args, **kwargs)`. | Use when any method or shared module touches state. |
| `hk.running_init()` | Code inside a transformed function must know whether it is running during `init` or `apply`. | Callable only while Haiku transform context is active. | Returns `True` during `init`, `False` during `apply`. | Commonly used to force all conditional parameters/state to be created during init. |

## RNG placement rules

- `rng` is always the first argument to every `init` function.
- For `hk.transform`, `rng` is the second argument to `apply`: `apply(params, rng, ...)`.
- For `hk.transform_with_state`, `rng` is the third argument to `apply`: `apply(params, state, rng, ...)`.
- `rng` may be `None` only when the executed path does not need Haiku random numbers. If an initializer, `hk.next_rng_key`, dropout, or sampling path needs randomness, pass a real JAX PRNG key.
- `hk.without_apply_rng` removes only the apply-time `rng` argument. It does not remove `rng` from `init`.
- If the original function has arguments named `rng` or `state`, call the transformed `apply` positionally for those user arguments. Haiku reserves leading `params`, `state`, and `rng` positions on `apply`.

## State placement rules

- Use `hk.transform` for state-free functions. If state is accidentally created, Haiku raises a non-empty-state error and points to `hk.transform_with_state`.
- Use `hk.transform_with_state` when state exists. Keep the state returned from `init`, pass it into `apply`, then persist the `new_state` returned by `apply`.
- State is a nested mapping like params: module name -> state name -> array/scalar. Use shape inspection before and after apply to confirm expected updates.
- `hk.without_state` is a guard for code that should be state-free; it raises if the function actually creates or updates state.
- `hk.with_empty_state` is an adapter for uniform stateful pipelines; it is not a replacement for real state handling.

## Multi-transform factory contract

A multi-transform factory must create modules once and return two things:

```python
def factory():
    encoder = hk.Linear(2, name="encoder")
    decoder = hk.Linear(4, name="decoder")

    def template(x):
        z = encoder(x)
        return decoder(z)

    def encode(x):
        return encoder(x)

    def decode(z):
        return decoder(z)

    return template, {"encode": encode, "decode": decode}
```

- The template function is used only to initialize the full shared parameter/state set. It should exercise every module/state object that any apply method will need.
- The apply tree defines the public methods. Its structure is preserved; for the dict above use `transformed.apply["encode"](...)` and `transformed.apply["decode"](...)`.
- If a needed module is absent from the template, the corresponding apply method may fail because parameters must be created during `init`, not `apply`.
- For stateful multi-transforms, every method returns `(out, new_state)`; thread the latest state through the next method if methods update shared state.

## Shape and purity validation checklist

Use a tiny input before integrating a transform into a larger training/evaluation loop:

1. Initialize with a deterministic example input and a PRNG key: `params = f.init(key, x, ...)` or `params, state = f.init(key, x, ...)`.
2. Inspect parameter and state shapes, not values, for a stable contract: `jax.tree.map(lambda a: getattr(a, "shape", None), params)`.
3. Apply once and assert output shape and dtype expectations.
4. For stateful apply, assert the returned state has the expected keys/shapes and persist `new_state`.
5. If wrapping with `without_apply_rng`, run the deterministic path once and confirm no missing-RNG error is raised.
6. Apply JAX transforms to `f.init` or `f.apply`, not to the impure function passed into `hk.transform`.

## Minimal stateless call pattern

```python
import haiku as hk
import jax
import jax.numpy as jnp

def forward(x):
    return hk.Linear(3)(x)

forward_t = hk.without_apply_rng(hk.transform(forward))
x = jnp.ones([2, 4])
params = forward_t.init(jax.random.PRNGKey(0), x)
y = forward_t.apply(params, x)
assert y.shape == (2, 3)
```

## Minimal stateful call pattern

```python
import haiku as hk
import jax
import jax.numpy as jnp

def forward(x):
    count = hk.get_state("count", shape=[], dtype=jnp.int32, init=jnp.zeros)
    hk.set_state("count", count + 1)
    return x + count.astype(x.dtype)

forward_t = hk.transform_with_state(forward)
x = jnp.ones([2, 3])
params, state = forward_t.init(jax.random.PRNGKey(0), x)
y, state = forward_t.apply(params, state, None, x)
assert y.shape == (2, 3)
```
