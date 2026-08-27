# Core Transform Troubleshooting

## Purpose

Use this reference when a Haiku transform call fails, output/state shapes look wrong, or JAX tracing errors appear around `hk.transform` usage. Start by identifying the wrapper type and then match the symptom below.

## Quick signature diagnostic

| Wrapper | `init` | `apply` before optional wrappers | After `without_apply_rng` |
| --- | --- | --- | --- |
| `hk.transform(f)` | `params = init(rng, *args, **kwargs)` | `out = apply(params, rng, *args, **kwargs)` | `out = apply(params, *args, **kwargs)` |
| `hk.transform_with_state(f)` | `params, state = init(rng, *args, **kwargs)` | `out, state = apply(params, state, rng, *args, **kwargs)` | `out, state = apply(params, state, *args, **kwargs)` |
| `hk.multi_transform(factory)` | `params = init(rng, *args, **kwargs)` | each method: `out = apply_i(params, rng, *args, **kwargs)` | each method: `out = apply_i(params, *args, **kwargs)` |
| `hk.multi_transform_with_state(factory)` | `params, state = init(rng, *args, **kwargs)` | each method: `out, state = apply_i(params, state, rng, *args, **kwargs)` | each method: `out, state = apply_i(params, state, *args, **kwargs)` |

## Wrong `init` RNG argument order

Symptoms:

- Error text includes `Init must be called with an RNG as the first argument`.
- A string, input array, params dict, or state dict was passed as the first `init` argument.

Likely cause:

- `init` was called as if it were the original function, for example `f.init(x)` instead of `f.init(rng, x)`.

Recovery:

1. Call `init` with a JAX key or `None` first: `params = f.init(jax.random.PRNGKey(0), x, ...)`.
2. Use `None` only when every initializer and init-time path is deterministic and no Haiku random key is needed.
3. Remember that `without_apply_rng` does not remove the `init` RNG.
4. Validate by inspecting returned params/state shapes before continuing.

## Wrong stateless apply RNG position

Symptoms:

- Error text includes `Apply must be called with an RNG as the second argument`.
- Output arguments appear shifted; an input array is interpreted as RNG.
- `params argument does not appear valid` can appear if the first argument is not the params mapping.

Likely cause:

- A stateless `hk.transform` apply call was written as `apply(params, x, ...)` without wrapping with `hk.without_apply_rng`.
- A stateful call pattern was used for a stateless transform.

Recovery:

1. For plain `hk.transform`, call `out = f.apply(params, rng, *original_args)`.
2. If apply is deterministic, wrap once: `f = hk.without_apply_rng(hk.transform(fn))`, then call `out = f.apply(params, *original_args)`.
3. Do not pass `rng=` as a keyword to the wrapped apply. Haiku reserves leading names and may ask you to pass user arguments positionally.

## Wrong state/RNG position in stateful apply

Symptoms:

- Error text includes `Apply must be called with an RNG as the third argument`.
- Error text includes `state argument does not appear valid`.
- The state tree is unchanged because the returned `new_state` is ignored.
- A PRNG key accidentally occupies the `state` slot or a state dict occupies the `rng` slot.

Likely cause:

- `hk.transform_with_state` was called with stateless ordering: `apply(params, rng, x)`.
- The caller omitted `state` returned by `init`.
- The caller used `without_apply_rng` but still passed an RNG, shifting original arguments.

Recovery:

1. For plain stateful transform, call `out, state = f.apply(params, state, rng, *original_args)`.
2. For `hk.without_apply_rng(hk.transform_with_state(fn))`, call `out, state = f.apply(params, state, *original_args)`.
3. Persist the returned `state` after every apply call.
4. Run a tiny assertion that checks `state` keys and scalar/array shapes before entering a training loop.

## Using state with `hk.transform`

Symptoms:

- Error text includes `If your transformed function uses hk.{get,set}_state then use hk.transform_with_state`.
- `hk.without_state(...)` raises a non-empty-state error.
- A stateful module such as one maintaining moving averages was added and a formerly stateless call fails.

Likely cause:

- The function creates, reads, or updates mutable state but was wrapped with `hk.transform` or converted through `hk.without_state`.

Recovery:

1. Replace `hk.transform(fn)` with `hk.transform_with_state(fn)`.
2. Change init from `params = f.init(rng, ...)` to `params, state = f.init(rng, ...)`.
3. Change apply from `out = f.apply(params, rng, ...)` to `out, state = f.apply(params, state, rng, ...)`.
4. If the apply path is deterministic, optionally wrap the stateful transform with `hk.without_apply_rng` after migrating state.
5. Route detailed state API design, parameter/state tree naming, and `hk.get_state`/`hk.set_state` initialization rules to sibling sub-skill `params-state-rng`.

## Passing `None` RNG to stochastic apply

Symptoms:

- Error text includes `must pass a non-None PRNGKey`.
- The error appears only on training/stochastic paths, not on deterministic evaluation paths.
- It appears after wrapping with `hk.without_apply_rng` or after passing `None` as the apply RNG.

Likely cause:

- The apply path executes `hk.next_rng_key`, dropout, random sampling, or a module/helper that needs a Haiku RNG.
- `hk.without_apply_rng` supplied `rng=None` internally, which is invalid for the executed path.

Recovery:

1. Remove `hk.without_apply_rng` from stochastic transforms.
2. Call `apply` with a fresh key: `out = f.apply(params, jax.random.PRNGKey(seed), ...)` or `out, state = f.apply(params, state, key, ...)`.
3. Split keys outside the transformed apply when calling repeatedly: `key, apply_key = jax.random.split(key)`.
4. If only evaluation is deterministic, keep one transform with RNG in its signature and pass `None` only to evaluation paths that truly avoid stochastic operations.
5. Route direct RNG-sequence utilities such as `hk.PRNGSequence` and `hk.next_rng_key` usage patterns to `params-state-rng`.

## User arguments named `state` or `rng`

Symptoms:

- Error text says Haiku transform adds leading `params`, `state`, and `rng` arguments and user arguments with the same names must be passed positionally.
- A call like `f.apply(params=None, state=None, rng=None)` fails even when testing a function whose original arguments are named `state` or `rng`.

Likely cause:

- The original function has an argument named `state` or `rng`, which collides with Haiku's leading apply argument names.

Recovery:

1. Prefer renaming user-level arguments to domain-specific names such as `carry`, `sample_key`, or `metadata`.
2. If renaming is not possible, pass those original function arguments positionally after Haiku's leading arguments.
3. Check the wrapper's correct leading signature in the quick diagnostic table before adding keyword arguments.

## Multi-transform missing parameters or state

Symptoms:

- An apply method fails because parameters must be created during `init`, not during `apply`.
- Only one method works; another method needs a module not present in the params tree.
- Stateful multi-method calls lose updates between methods.

Likely cause:

- The multi-transform template did not touch every module/state object used by the apply function tree.
- Stateful methods were called without threading the latest returned state.

Recovery:

1. Edit the factory's template function so it calls every shared module path needed by any apply method.
2. Re-run `params = f.init(rng, example_inputs...)` and inspect that expected module keys exist.
3. For `multi_transform_with_state`, use `out, state = apply_i(params, state, rng, ...)` for each method and pass the returned state to the next stateful method.
4. If no method uses state, prefer `hk.multi_transform` or wrap the stateful version with `hk.without_state` only as a guard.

## Raw JAX transform/control-flow caveats inside transformed functions

Symptoms:

- Error text includes `UnexpectedTracerError` and suggests the Haiku version of a transform.
- Error text warns not to pass an already `jax.jit`, `pmap`, or similar transformed function into `hk.transform`.
- Behavior is hard to reason about when `jax.vmap`, `jax.lax.scan`, `jax.remat`, or other JAX transforms wrap code that creates Haiku modules, state, or RNG inside the untransformed function.

Likely cause:

- JAX transformations require pure functions, but the function passed to `hk.transform` is impure until Haiku returns explicit `init` and `apply` functions.
- Raw JAX transforms/control flow inside the Haiku context can hide parameter/state/RNG effects from Haiku.

Recovery:

1. Do not call `hk.transform(jax.jit(fn))` or similar. Transform first, then apply JAX transforms to `f.init` or `f.apply`.
2. If the JAX transform/control flow is inside the Haiku function, route to `jax-interop-and-advanced` for Haiku wrappers such as `hk.vmap`, `hk.scan`, `hk.grad`, `hk.switch`, lifting, and related caveats.
3. Use `hk.running_init()` only for simple conditional initialization in this sub-skill; advanced JAX control-flow rewrites belong to `jax-interop-and-advanced`.

## `hk.running_init()` outside a transform

Symptoms:

- Error text says `running_init` must be used as part of an `hk.transform`.

Likely cause:

- `hk.running_init()` was called at module import time, in an outer helper, or after `init`/`apply` returned.

Recovery:

1. Move the call inside the function passed to `hk.transform` or `hk.transform_with_state`.
2. Make the conditional create all parameters/state during init and only choose the desired branch during apply.
3. Validate by initializing one branch and applying another branch with a tiny input.
