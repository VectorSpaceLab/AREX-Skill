# Haiku-aware JAX transform and control-flow wrappers

Haiku modules and direct APIs are side-effecting until wrapped by `hk.transform` or `hk.transform_with_state`. Raw JAX transforms expect pure functions, so raw `jax.vmap`, `jax.lax.scan`, `jax.remat`, and related control flow can mis-handle Haiku's internal params, state, and RNG when used *inside* a transformed function. Use these rules:

- **Outside Haiku**: transform the model first, then apply ordinary JAX transforms to pure `init`/`apply` functions when possible.
- **Inside Haiku**: use Haiku wrappers when the nested function creates/reads parameters, reads/writes state, consumes `hk.next_rng_key`, or calls modules.
- **For mapped parameter axes**: use `hk.lift` or `hk.lift_with_state` with raw JAX transforms on an inner transformed function; `hk.vmap` intentionally keeps Haiku params/state unmapped.
- **For branch/loop initialization**: make parameter/state creation unconditional under `hk.running_init()` when JAX control flow might skip a branch or loop during init.

## Wrapper selection matrix

| Need | Prefer | Key contract | Common pitfalls |
| --- | --- | --- | --- |
| Map examples while sharing Haiku params/state | `hk.vmap(fun, ..., split_rng=...)` | Parameters and state are not mapped. `split_rng` is required and controls whether Haiku RNG keys are broadcast or split per mapped element. | Missing `split_rng`; trying to create mapped parameters during init with `split_rng=True`; all `in_axes` are `None`. |
| Scan a Haiku body over time | `hk.scan(f, init, xs, length=None, reverse=False, unroll=1)` | Equivalent to `jax.lax.scan` but threads Haiku state/RNG. Return `(carry, y)` from the body. | State/parameter structure must be stable; use explicit init path for optional modules. |
| Map a body with state/RNG but no carry | `hk.map(f, xs)` | Equivalent to `jax.lax.map` with Haiku state/RNG threaded. | Raw `jax.lax.map` may leak or silently drop state/RNG side effects. |
| Differentiate a stateful Haiku sub-computation inside a transform | `hk.grad`, `hk.value_and_grad` | Use only when differentiating inside a transformed function and the differentiated function touches Haiku state. | Outside Haiku, use `jax.grad` on pure functions instead. |
| Rematerialize/checkpoint a Haiku sub-computation | `hk.remat(fun, prevent_cse=True, policy=None, static_argnums=())` | Equivalent to `jax.remat` with Haiku state passed through. | Raw `jax.remat` around modules or direct Haiku APIs can cause tracing/state errors. |
| Conditional branch with Haiku effects | `hk.cond(pred, true_fun, false_fun, *operands)` | Branches receive operands and Haiku state is threaded. Branch outputs must have compatible structure. | Branch-specific parameter creation is unsafe unless all branch params are created during init. |
| Multi-way branch with Haiku effects | `hk.switch(index, branches, *operands)` | Equivalent to `jax.lax.switch` with state/RNG. | During init, unconditionally evaluate all branches that create params/state; use switch only at apply. |
| Counted loop | `hk.fori_loop(lower, upper, body_fun, init_val)` | Equivalent to `jax.lax.fori_loop` with Haiku state/RNG in the body. | Body state structure must be stable; lower/upper may be traced. |
| Data-dependent while loop | `hk.while_loop(cond_fun, body_fun, init_val)` | Equivalent to `jax.lax.while_loop` with Haiku state/RNG in the body. | Not supported during init; `cond_fun` cannot call `hk.set_state`, `hk.next_rng_key`, or similar. |
| Shape tracing inside Haiku | `hk.eval_shape(fun, *args, **kwargs)` | Equivalent to `jax.eval_shape`; any changed Haiku state is discarded. | Do not rely on state changes observed only during shape evaluation. |
| Inner transformed function inside outer transform | `hk.lift`, `hk.lift_with_state`, transparent variants | Registers inner `init` params/state into the outer transform. | Name collisions, accidentally closing over outer modules, and unused state updaters. |
| Repeated layer block with separate per-layer params | `hk.layer_stack(num_layers, ...)` | Wraps a function and repeatedly applies it using scan/lift internally; created params are not shared across layers. | Wrapped function restrictions: no varargs, limited kwargs support, input/output structure must match. |

## Rewriting raw `jax.vmap` inside a transformed function

Bad pattern when `per_example` uses modules or direct Haiku APIs:

```python
def f(x):
    linear = hk.Linear(8)
    def per_example(row):
        return jax.nn.relu(linear(row))
    return jax.vmap(per_example)(x)  # raw JAX transform sees Haiku effects
```

Shared-parameter Haiku rewrite:

```python
def f(x):
    linear = hk.Linear(8)
    def per_example(row):
        return jax.nn.relu(linear(row))
    return hk.vmap(per_example, in_axes=0, out_axes=0, split_rng=False)(x)
```

If the mapped body uses `hk.next_rng_key`, choose RNG behavior deliberately:

```python
def f(x):
    def per_example(row):
        noise = jax.random.normal(hk.next_rng_key(), row.shape)
        return row + noise
    # Share keys while initializing parameters; split keys during apply.
    return hk.vmap(per_example, split_rng=not hk.running_init())(x)
```

Use `split_rng=False` for shared RNG/broadcast behavior, such as deterministic shared dropout masks or no RNG use. Use `split_rng=True` at apply time when each mapped element needs distinct keys. Do not use `split_rng=True` during parameter initialization when the mapped function creates shared Haiku parameters; if you need a leading parameter axis for an ensemble, use `hk.lift` with raw `jax.vmap` on an inner transformed function.

## Rewriting raw `jax.lax.scan` inside a transformed function

Bad pattern when the body uses modules, state, or `hk.next_rng_key`:

```python
def sequence_model(xs):
    cell = hk.Linear(16)
    def step(carry, x_t):
        carry = jnp.tanh(cell(x_t) + carry)
        return carry, carry
    return jax.lax.scan(step, jnp.zeros([16]), xs)[1]
```

Haiku rewrite:

```python
def sequence_model(xs):
    cell = hk.Linear(16)
    def step(carry, x_t):
        carry = jnp.tanh(cell(x_t) + carry)
        return carry, carry
    final, ys = hk.scan(step, jnp.zeros([16], xs.dtype), xs)
    return ys, final
```

For stateful bodies, make sure every iteration sees the same state tree. If a body may create state conditionally, create it before the scan or force the creation path during init.

## Gradients and rematerialization inside Haiku

Most training code should differentiate a pure loss built from transformed `apply` functions:

```python
def loss(params, rng, x, y):
    pred = transformed.apply(params, rng, x)
    return jnp.mean((pred - y) ** 2)
grads = jax.grad(loss)(params, rng, x, y)
```

Use `hk.grad` or `hk.value_and_grad` only for the narrower case where a function is differentiated *inside* a transformed function and that inner function updates Haiku state. They mirror `jax.grad`/`jax.value_and_grad` arguments such as `argnums`, `has_aux`, and `holomorphic`, but they also thread Haiku state updates back to the enclosing transform.

Use `hk.remat` instead of `jax.remat` when rematerializing a sub-function that touches Haiku params, state, or RNG. Keep module construction outside the smallest rematted function when practical, and validate both `init` and `apply` because rematerialization changes tracing behavior.

## Control flow with Haiku state

### `hk.cond` and `hk.switch`

Branch functions can use Haiku state/RNG, but all branches must return compatible pytrees. For branches that create modules or state, initialize all possible branches unconditionally:

```python
def f(x, index):
    branches = [hk.Linear(4, name=f"expert_{i}") for i in range(3)]

    def run_branch(i, value):
        return branches[i](value)

    if hk.running_init():
        # Create every expert's parameters even if only one is used at apply.
        for i in range(len(branches)):
            _ = run_branch(i, x)
        return branches[0](x)

    return hk.switch(index, [lambda value, i=i: run_branch(i, value)
                             for i in range(len(branches))], x)
```

Use the same principle for `hk.cond`: create any branch-specific params/state during init, then branch at apply time.

### `hk.while_loop`

`hk.while_loop` cannot run during initialization because Haiku cannot statically know whether the body will run. Use an unconditional body call during init:

```python
def f(x):
    block = hk.Linear(x.shape[-1])
    def body(v):
        return jnp.tanh(block(v))
    if hk.running_init():
        return body(x)
    return hk.while_loop(lambda v: jnp.linalg.norm(v) < 10.0, body, x)
```

`cond_fun` is for pure loop conditions. It must not call `hk.set_state`, `hk.next_rng_key`, or other Haiku side-effect APIs. Put those in `body_fun` instead.

## Nested transforms with `hk.lift*`

Use lifting when an outer transformed function needs to create/register parameters from an inner transformed function, often because raw JAX transforms are applied to the inner pure `init`/`apply`.

- `hk.lift(inner.init, name="...")` registers parameters only; call inside `hk.transform` or `hk.transform_with_state`.
- `hk.lift_with_state(inner.init, name="...")` registers parameters and state; call inside `hk.transform_with_state` and update state with the returned updater.
- `hk.transparent_lift` and `hk.transparent_lift_with_state` do not add an extra name scope; use only when you intentionally want names to match the inner transform and you have checked for collisions.
- `allow_reuse=True` permits reuse of params/state from the outer context, which is useful in some control-flow situations such as lifting inside a scan. Leave it `False` unless reuse is intentional.

Parameter-only sketch for an ensemble with mapped parameter axes:

```python
def make_member(x):
    return hk.Linear(2)(x)

member = hk.without_apply_rng(hk.transform(make_member))

def outer(x, ensemble_size=4):
    init_rngs = hk.next_rng_keys(ensemble_size) if hk.running_init() else None
    init_many = jax.vmap(member.init, in_axes=(0, None))
    lifted_init = hk.lift(init_many, name="ensemble")
    member_params = lifted_init(init_rngs, x)
    apply_many = jax.vmap(member.apply, in_axes=(0, None))
    return apply_many(member_params, x)
```

Stateful sketch:

```python
inner = hk.transform_with_state(inner_stateful_function)

def outer(x):
    lifted_init, updater = hk.lift_with_state(inner.init, name="inner")
    rng = hk.next_rng_key() if hk.running_init() else None
    params, state = lifted_init(rng, x)
    out, new_state = inner.apply(params, state, hk.next_rng_key(), x)
    updater.update(new_state)  # or updater.ignore_update() if state is intentionally unchanged
    return out
```

The state updater must be used once inside the same `hk.transform_with_state` context. If the inner function has no state and you used `hk.lift`, Haiku ignores state updates for you.

## `hk.layer_stack`

`hk.layer_stack(num_layers, with_per_layer_inputs=False, unroll=1, pass_reverse_to_layer_fn=False, transparent=False, transparency_map=None, name=None)` wraps a function and applies it repeatedly. It can reduce compile-time pressure for large repeated blocks while still creating independent parameters for each layer.

Use it when:

- The repeated block is naturally the same Haiku function called `num_layers` times.
- Parameters created inside the block should be distinct for each layer.
- Inputs and outputs have the same pytree structure; with `with_per_layer_inputs=True`, additional inputs have a leading dimension of `num_layers`.

Avoid or redesign when:

- The block needs arbitrary `*args` or unsupported kwargs.
- The block return structure does not match its carry/input structure.
- You need transparent names but do not have a correct `LayerStackTransparencyMapping`; `transparent=True` requires one.

Minimal pattern:

```python
def block(x):
    return jax.nn.relu(hk.Linear(x.shape[-1])(x))

stacked_block = hk.layer_stack(6, name="blocks")(block)
y = stacked_block(x)
```
