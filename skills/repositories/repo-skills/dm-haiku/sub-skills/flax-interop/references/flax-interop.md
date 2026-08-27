# Flax Interop Workflows

Use these recipes only for Haiku/Flax boundary tasks. Keep ordinary Flax model design, Flax optimizers, datasets, and training loops in Flax-oriented guidance outside this Haiku repo skill.

## 1. Choose the interop direction

Ask which framework owns the outer program:

- If the outer program is **Flax** and you need to call Haiku code, use `hk.experimental.flax.Module` or `Module.create`.
- If the outer program is **Haiku** and you need to call a Flax `linen.Module`, use `hk.experimental.flax.lift` inside the outer Haiku transform.
- If the task only asks to inspect or translate variable trees, use `flatten_flax_to_haiku` on one Flax collection at a time.

## 2. Convert `hk.Linear` to a Flax module and inspect collections

This is the smallest Haiku-in-Flax path and mirrors the bundled smoke script.

```python
import jax
import jax.numpy as jnp
import haiku as hk
import haiku.experimental.flax as hkflax

x = jnp.ones([2, 3])
rng = jax.random.PRNGKey(0)

# Constructor args after hk.Linear are passed to hk.Linear(...).
mod = hkflax.Module.create(hk.Linear, 4, name="projection")
variables = mod.init(rng, x)
y = mod.apply(variables, x)

print(variables.keys())            # usually: dict_keys(['params'])
print(variables["params"].keys())  # usually includes: 'projection'
assert y.shape == (2, 4)
```

For inspection in Haiku's tree shape:

```python
hk_params = hkflax.flatten_flax_to_haiku(variables["params"])
for module_name, named_values in hk_params.items():
    print(module_name, sorted(named_values))
```

Expected `hk.Linear` parameter names are `"w"` and, when bias is enabled, `"b"`.

## 3. Wrap an already transformed Haiku function for Flax

Use this when the Haiku component is already expressed as a transformed function rather than a module class.

```python
import jax
import jax.numpy as jnp
import haiku as hk
import haiku.experimental.flax as hkflax


def forward(x):
    x = hk.Linear(8, name="hidden")(x)
    return jax.nn.relu(x)

haiku_forward = hk.transform(forward)
flax_mod = hkflax.Module(haiku_forward)

x = jnp.ones([1, 5])
variables = flax_mod.init(jax.random.PRNGKey(0), x)
y = flax_mod.apply(variables, x)
assert y.shape == (1, 8)
```

If `forward` uses `hk.next_rng_key()` during apply, provide a Flax `"apply"` stream:

```python
y = flax_mod.apply(variables, x, rngs={"apply": jax.random.PRNGKey(1)})
```

## 4. Handle stateful Haiku inside Flax

Stateful Haiku modules and functions can be wrapped, but the Flax caller must make the `"state"` collection mutable during apply and carry the updated collection forward.

```python
import jax
import jax.numpy as jnp
import haiku as hk
import haiku.experimental.flax as hkflax


def counter_forward():
    c = hk.get_state("count", [], init=jnp.zeros)
    hk.set_state("count", c + 1)
    return c

counter = hkflax.Module(hk.transform_with_state(counter_forward))
variables = counter.init(jax.random.PRNGKey(0))

for expected in range(3):
    out, updates = counter.apply(variables, mutable=["state"])
    assert int(out) == expected
    variables = {**variables, **updates}
```

Without `mutable=["state"]`, a Flax apply call can read state but will not return state updates for the next call.

## 5. Lift a simple Flax module into a Haiku transform

This is the smallest Flax-in-Haiku path.

```python
import flax.linen as nn
import jax
import jax.numpy as jnp
import haiku as hk
import haiku.experimental.flax as hkflax


def forward(x):
    dense = hkflax.lift(nn.Dense(4), name="flax_dense")
    x = dense(x)
    return hk.Linear(2, name="haiku_head")(jax.nn.relu(x))

net = hk.transform(forward)
x = jnp.ones([2, 3])
params = net.init(jax.random.PRNGKey(0), x)
y = net.apply(params, None, x)

assert y.shape == (2, 2)
assert "flax_dense/~" in params
assert set(params["flax_dense/~"]) == {"kernel", "bias"}
```

Use this pattern when the Haiku transform should own the combined parameter tree and optimizer state.

## 6. Lift a stateful Flax module into Haiku

When the Flax module owns non-param collections, the outer Haiku function must be transformed with state.

```python
import flax.linen as nn
import jax
import jax.numpy as jnp
import haiku as hk
import haiku.experimental.flax as hkflax


class FlaxCounter(nn.Module):
    @nn.compact
    def __call__(self):
        if self.is_initializing():
            self.put_variable("state", "count", jnp.zeros([], jnp.float32))
            return jnp.zeros([], jnp.float32)
        c = self.get_variable("state", "count")
        self.put_variable("state", "count", c + 1)
        return c


def forward():
    counter = hkflax.lift(FlaxCounter(), name="flax_counter")
    return counter()

net = hk.transform_with_state(forward)
params, state = net.init(jax.random.PRNGKey(0))

for expected in range(3):
    out, state = net.apply(params, state, None)
    assert int(out) == expected
```

The Flax `"state"` collection appears in the Haiku state tree under the lifting name, for example `"flax_counter/state/~"`.

## 7. Pass RNG streams through a lifted Flax module

Lifted Flax modules expect Flax-style RNG stream names. Pass `rngs` as a mapping, and create keys from Haiku's current RNG sequence when inside the transform.

```python
class UsesDropout(nn.Module):
    @nn.compact
    def __call__(self, x, *, train: bool):
        return nn.Dropout(rate=0.5)(x, deterministic=not train)


def forward(x, *, train: bool):
    dropout = hkflax.lift(UsesDropout(), name="flax_dropout")
    return dropout(x, train=train, rngs={"dropout": hk.next_rng_key()})

net = hk.transform(forward)
x = jnp.ones([4, 8])
params = net.init(jax.random.PRNGKey(0), x, train=True)
y = net.apply(params, jax.random.PRNGKey(1), x, train=True)
```

Do not pass `rngs=jax.random.PRNGKey(...)`; `rngs` must be a dictionary mapping stream names to keys.

## 8. Variable conversion checklist

When moving or comparing variables across the boundary:

1. Convert each Flax collection separately: `flatten_flax_to_haiku(variables["params"])`, `flatten_flax_to_haiku(variables["batch_stats"])`, and so on.
2. Expect top-level Flax leaves to become the Haiku module name `"~"`.
3. Expect nested Flax paths to be joined with `/` in Haiku keys.
4. For `lift`, expect the explicit lift name to prefix the outer Haiku keys.
5. Do not require exact equality between independent Haiku and Flax initializations unless both sides use the same variable values; RNG splitting differs.
