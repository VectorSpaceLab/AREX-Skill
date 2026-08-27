# Haiku/Flax Interop API Reference

The interop surface lives under `haiku.experimental.flax`. Import it separately so missing optional Flax dependencies produce an obvious failure:

```python
import haiku as hk
import haiku.experimental.flax as hkflax
```

## Direction chooser

| If the host program is... | And the component is... | Use | Result |
| --- | --- | --- | --- |
| Flax/Linen | an `hk.Module` class | `hkflax.Module.create(hk_cls, *args, **kwargs)` | A Flax `linen.Module` exposing `init` and `apply`. |
| Flax/Linen | an `hk.transform` or `hk.transform_with_state` result | `hkflax.Module(transformed)` | A Flax `linen.Module` wrapping that transformed Haiku function. |
| Haiku | a Flax `linen.Module` instance | `hkflax.lift(mod, name="scope")` | A callable that registers Flax params/state into the outer Haiku transform. |
| Either | a Flax collection such as `variables["params"]` | `hkflax.flatten_flax_to_haiku(collection)` | A Haiku-style two-level mapping for inspection or conversion. |

## API details

### `hkflax.Module(transformed, parent=None, name=None)`

A Flax `linen.Module` that runs a Haiku transformed function.

- `transformed` may be an `hk.Transformed` from `hk.transform` or an `hk.TransformedWithState` from `hk.transform_with_state`.
- Stateless `hk.Transformed` values are treated as empty-state transformed functions internally, so the Flax wrapper can use one call path.
- During `init`, the wrapper uses Flax's `"params"` RNG stream to initialize Haiku params/state and stores them into Flax variable collections.
- During `apply`, existing Flax variables are flattened back to Haiku `params` and `state`, the Haiku apply function is called, and changed state is stored back only when the Flax call allows the `"state"` collection to be mutable.
- If the wrapped Haiku apply path calls `hk.next_rng_key()`, call the Flax module with an `"apply"` RNG stream, for example `mod.apply(variables, x, rngs={"apply": key})`.

### `hkflax.Module.create(hk_cls, *init_args, **init_kwargs)`

A convenience constructor that converts a Haiku module class into a Flax `linen.Module`.

- `hk_cls` is a Haiku module class such as `hk.Linear` or a custom `hk.Module` subclass.
- `*init_args` and `**init_kwargs` are passed to the Haiku module constructor, not to the Flax `apply` call.
- The returned Flax module calls the Haiku module's `__call__` method. Multiple Haiku forward methods are not exposed by this helper.
- Stateful Haiku modules work, but the Flax caller must request mutable state on apply: `out, updates = mod.apply(variables, x, mutable=["state"])`, then merge `updates` into the variables used for the next call.

### `hkflax.lift(mod, *, name)`

Lifts a Flax `linen.Module` instance into an outer Haiku transformed function.

- Call `lift` inside a function that is transformed by `hk.transform` or `hk.transform_with_state`.
- `name` is required and prefixes the Flax module's variables in the outer Haiku dictionaries.
- Flax `params` become entries in the outer Haiku `params` dictionary.
- Non-param Flax collections become entries in the outer Haiku `state` dictionary. Use `hk.transform_with_state` when the Flax module owns mutable collections.
- If the lifted Flax module needs RNGs, pass them as a mapping: `mod(x, rngs={"dropout": hk.next_rng_key()})`. Passing a raw key as `rngs` is invalid.
- During outer `init`, if no `"params"` RNG is supplied in `rngs`, Haiku supplies one from the current Haiku RNG sequence when available.

### `hkflax.flatten_flax_to_haiku(collection)`

Converts one Flax collection into Haiku's two-level `{module_name: {name: value}}` shape.

```python
variables = {
    "params": {
        "encoder": {"dense": {"kernel": "K", "bias": "b"}},
        "top_level_weight": "W",
    }
}

hk_params = hkflax.flatten_flax_to_haiku(variables["params"])
assert hk_params == {
    "encoder/dense": {"kernel": "K", "bias": "b"},
    "~": {"top_level_weight": "W"},
}
```

Do not pass a full Flax variables dictionary directly unless you intentionally want collection names such as `"params"` or `"batch_stats"` treated as module names. Convert each collection separately.

## Collection mapping rules

| Direction | Flax shape | Haiku shape |
| --- | --- | --- |
| Flax collection to Haiku | `{"dense": {"kernel": arr}}` | `{"dense": {"kernel": arr}}` |
| Flax nested module to Haiku | `{"parent": {"child": {"w": arr}}}` | `{"parent/child": {"w": arr}}` |
| Flax top-level leaf to Haiku | `{"w": arr}` | `{"~": {"w": arr}}` |
| Haiku-in-Flax params | `hk params {"linear": {"w": arr}}` | stored as Flax `variables["params"]["linear"]["w"]` |
| Haiku-in-Flax state | `hk state {"counter": {"c": arr}}` | stored as Flax `variables["state"]["counter"]["c"]` |
| Flax-in-Haiku params via `lift(..., name="foo")` | Flax `params` collection | Haiku `params` under keys like `"foo/..."` |
| Flax-in-Haiku mutable collections via `lift(..., name="foo")` | Flax collection `"batch_stats"` | Haiku state under keys like `"foo/batch_stats/..."` |

## State and RNG semantics

- **Stateful Haiku inside Flax:** use `mutable=["state"]` on `apply`; update the caller's variable dictionary with the returned state collection before the next apply.
- **Stateful Flax inside Haiku:** use `hk.transform_with_state`; keep and pass the returned Haiku state on every apply.
- **Haiku-in-Flax RNG:** initialization uses Flax's `"params"` RNG; Haiku apply randomness uses Flax's optional `"apply"` RNG stream.
- **Flax-in-Haiku RNG:** pass Flax RNG streams through the lifted module's `rngs={...}` keyword. Use Haiku RNG helpers such as `hk.next_rng_key()` to create those keys inside the outer transform.
- **Initialization equivalence:** Flax and Haiku split RNG keys differently. A Flax-wrapped Haiku module and a directly initialized Haiku transform may have different initial parameter values even when shapes and computation agree.
