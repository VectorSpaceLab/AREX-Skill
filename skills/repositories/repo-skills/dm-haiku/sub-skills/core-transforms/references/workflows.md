# Core Transform Workflows

## Purpose

Read this reference when you need concrete recipes for using Haiku transforms in a future task. The recipes are intentionally small and self-contained; they use synthetic arrays and public Haiku/JAX APIs only.

## Workflow 1: choose the transform wrapper

Use this decision sequence before writing code:

1. Write the network/loss/utility as an ordinary Python function `f(*args, **kwargs)`. Create Haiku modules inside that function, not at import time.
2. Ask whether `f` reads or writes mutable state. Direct `hk.get_state`/`hk.set_state`, moving averages, and stateful normalization require state.
3. If no state is used, call `f_t = hk.transform(f)`.
4. If state is used, call `f_t = hk.transform_with_state(f)` and design your caller to store and return `state` explicitly.
5. Ask whether the apply path uses Haiku randomness. If no, wrap with `f_t = hk.without_apply_rng(f_t)` to remove apply-time `rng`; do not use this wrapper if apply may call `hk.next_rng_key`, dropout, or sampling.
6. If more than one apply method must share parameters/state, replace single transform with `hk.multi_transform` or `hk.multi_transform_with_state`.

## Workflow 2: implement a stateless transform

```python
import haiku as hk
import jax
import jax.numpy as jnp

def score_fn(x):
    hidden = hk.Linear(4, name="hidden")(x)
    hidden = jax.nn.relu(hidden)
    return hk.Linear(2, name="head")(hidden)

score = hk.without_apply_rng(hk.transform(score_fn))
x = jnp.ones([3, 5])
params = score.init(jax.random.PRNGKey(0), x)
logits = score.apply(params, x)

assert logits.shape == (3, 2)
assert params["hidden"]["w"].shape == (5, 4)
assert params["head"]["w"].shape == (4, 2)
```

Key points:

- The untransformed function is allowed to create modules and parameters because Haiku captures them during `init`.
- The returned `apply` is pure and can be passed to `jax.grad`, `jax.jit`, or similar JAX transforms from outside the Haiku function.
- `without_apply_rng` is safe here because the apply path has no Haiku random-number use.

## Workflow 3: keep the apply RNG when the apply path is stochastic

```python
import haiku as hk
import jax
import jax.numpy as jnp

def stochastic_score(x, is_training):
    x = hk.Linear(4)(x)
    if is_training:
        x = hk.dropout(hk.next_rng_key(), rate=0.5, x=x)
    return hk.Linear(2)(jax.nn.relu(x))

score = hk.transform(stochastic_score)
x = jnp.ones([3, 5])
params = score.init(jax.random.PRNGKey(0), x, is_training=True)
logits = score.apply(params, jax.random.PRNGKey(1), x, is_training=True)
assert logits.shape == (3, 2)
```

Key points:

- `apply(params, rng, ...)` is required when `is_training=True` can execute a stochastic path.
- For a deterministic evaluation path you may pass `None` only if no random operation is executed on that path.
- Do not wrap this transform with `without_apply_rng` unless the wrapped apply will never execute stochastic code.

## Workflow 4: migrate stateful code from `hk.transform` to `hk.transform_with_state`

### Symptom

A function originally wrapped with `hk.transform` starts using state, or a stateful module is added. Haiku reports that state is non-empty or that `hk.{get,set}_state` requires `hk.transform_with_state`.

### Migration steps

1. Change the wrapper:

```python
# Before
forward = hk.transform(forward_fn)

# After
forward = hk.transform_with_state(forward_fn)
```

2. Update initialization:

```python
# Before
params = forward.init(rng, x, is_training=True)

# After
params, state = forward.init(rng, x, is_training=True)
```

3. Update application:

```python
# Before
y = forward.apply(params, rng, x, is_training=True)

# After
y, state = forward.apply(params, state, rng, x, is_training=True)
```

4. Persist the latest `state` next to the latest `params` in training/evaluation loops.
5. If the apply path is deterministic, you may then use `forward = hk.without_apply_rng(forward)` and call `y, state = forward.apply(params, state, x, ...)`.
6. Validate with a tiny shape case and assert that `state` keys/shapes are present before relying on the larger model.

### Minimal migration example

```python
import haiku as hk
import jax
import jax.numpy as jnp

def forward_fn(x):
    count = hk.get_state("count", shape=[], dtype=jnp.int32, init=jnp.zeros)
    hk.set_state("count", count + 1)
    return x + count.astype(x.dtype)

forward = hk.without_apply_rng(hk.transform_with_state(forward_fn))
x = jnp.ones([2, 3])
params, state = forward.init(jax.random.PRNGKey(0), x)
y, state = forward.apply(params, state, x)
assert y.shape == (2, 3)
assert state["~"]["count"].shape == ()
```

## Workflow 5: adapt a stateless transform into a stateful pipeline

Use `hk.with_empty_state` when a larger caller expects `(params, state)` and `(out, state)` but the Haiku function itself has no state.

```python
import haiku as hk
import jax
import jax.numpy as jnp

def forward_fn(x):
    return hk.Linear(2)(x)

forward = hk.with_empty_state(hk.transform(forward_fn))
x = jnp.ones([1, 3])
params, state = forward.init(jax.random.PRNGKey(0), x)
y, state = forward.apply(params, state, None, x)
assert y.shape == (1, 2)
assert not state
```

Use `hk.without_state` in the opposite direction only when you want a guard that the function really has no state:

```python
forward = hk.without_state(hk.transform_with_state(forward_fn))
params = forward.init(jax.random.PRNGKey(0), x)
y = forward.apply(params, None, x)
```

If the function creates state, `without_state` raises instead of silently dropping it.

## Workflow 6: share one initialization across multiple apply methods

Use multi-transform when several methods must share modules or parameters, such as encoder/decoder pieces or model subroutines.

```python
import haiku as hk
import jax
import jax.numpy as jnp

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

    return template, (encode, decode)

model = hk.without_apply_rng(hk.multi_transform(factory))
x = jnp.ones([2, 3])
params = model.init(jax.random.PRNGKey(0), x)
encode, decode = model.apply
z = encode(params, x)
y = decode(params, z)
assert z.shape == (2, 2)
assert y.shape == (2, 4)
```

Checklist:

- The template function must touch every module whose parameters any apply method will need.
- The apply functions can be a tuple, dict, or other pytree; preserve that shape in your calling code.
- For stateful methods, switch to `hk.multi_transform_with_state` and thread state through each method call.
- If methods update shared state, decide on the order of method calls and persist the most recent state.

## Workflow 7: use `hk.running_init()` to initialize conditional parameters

Use `hk.running_init()` sparingly when Python-level conditional code would otherwise initialize only the branch selected during `init` while `apply` may later use a different branch.

```python
import haiku as hk
import jax
import jax.numpy as jnp

def conditional_fn(x, use_left):
    left = hk.Linear(2, name="left")
    right = hk.Linear(2, name="right")

    if hk.running_init():
        _ = left(x)
        _ = right(x)

    return left(x) if use_left else right(x)

conditional = hk.transform(conditional_fn)
x = jnp.ones([1, 3])
params = conditional.init(jax.random.PRNGKey(0), x, True)
y = conditional.apply(params, None, x, False)
assert y.shape == (1, 2)
assert set(params) == {"left", "right"}
```

Notes:

- `hk.running_init()` is valid only inside a transformed function.
- It returns `True` during `init` and `False` during `apply`.
- If the conditional is a JAX control-flow primitive or a JAX transform inside the Haiku function, route to `jax-interop-and-advanced` for Haiku wrappers and lifting guidance.

## Workflow 8: diagnose wrong RNG/state position quickly

When a transformed call fails, classify by signature first:

| Transformed object | Correct apply start | Common wrong call |
| --- | --- | --- |
| `hk.transform(f)` | `apply(params, rng, ...)` | `apply(params, state, rng, ...)` or `apply(params, ...)` before wrapping with `without_apply_rng` |
| `hk.transform_with_state(f)` | `apply(params, state, rng, ...)` | `apply(params, rng, state, ...)` or omitting returned `state` |
| `hk.without_apply_rng(hk.transform(f))` | `apply(params, ...)` | passing `rng=` as a keyword to the wrapper |
| `hk.without_apply_rng(hk.transform_with_state(f))` | `apply(params, state, ...)` | `apply(params, rng, ...)` with the RNG accidentally occupying the state slot |

Concrete recovery:

1. Inspect the wrapper you used.
2. Rewrite the call using the corresponding row above.
3. Prefer positional leading arguments for `params`, `state`, and `rng`.
4. Run a tiny shape check or the bundled smoke script before restoring the call in a larger loop.
