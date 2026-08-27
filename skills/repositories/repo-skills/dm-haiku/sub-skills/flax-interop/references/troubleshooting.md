# Flax Interop Troubleshooting

## Quick diagnosis table

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `ImportError` mentions `haiku.experimental.flax.* features require flax to be installed` | The optional `flax` dependency is absent. | Install a compatible `flax` package in the active Python environment, then rerun `python scripts/haiku_flax_smoke.py --mode module-create`. |
| `Module.create(hk.Linear, ...)` initializes but variable keys look different from a direct Haiku transform | Variables are stored in Flax collection layout; top-level leaves use `"~"`, nested module scopes are nested dictionaries. | Inspect `variables["params"]` directly for Flax layout, or call `flatten_flax_to_haiku(variables["params"])` to see Haiku-style keys. |
| Stateful Haiku wrapped as Flax does not persist updates | Flax `apply` did not mark the `"state"` collection mutable, or returned updates were not merged into the next variables. | Call `out, updates = mod.apply(variables, ..., mutable=["state"])`, then use `variables = {**variables, **updates}` for the next call. |
| Lifted stateful Flax module loses state or returns empty state | The outer Haiku function used `hk.transform` instead of `hk.transform_with_state`, or the returned Haiku state was ignored. | Use `hk.transform_with_state`; keep both `params` and `state` from `init`, then pass and replace `state` on every `apply`. |
| `flax.errors.InvalidRngError` says `rngs` should be a dictionary | A raw JAX key was passed as `rngs` to a lifted Flax module. | Pass a mapping such as `rngs={"dropout": hk.next_rng_key()}` or `rngs={"params": hk.next_rng_key(), "dropout": hk.next_rng_key()}`. |
| Haiku apply randomness fails inside a Flax wrapper | Wrapped Haiku code calls `hk.next_rng_key()` but no Flax `"apply"` RNG stream was supplied. | Call `mod.apply(variables, ..., rngs={"apply": jax.random.PRNGKey(seed)})`. |
| Exact initialized weights differ between direct Haiku and Flax-wrapped Haiku | Haiku and Flax split RNG keys differently. | Compare shapes and outputs using shared variables, not independently initialized arrays. If exact values matter, choose one framework to initialize and convert/share those variables. |
| Interop code breaks after package upgrades | `haiku.experimental.flax` is optional and experimental; Flax/JAX internals can change across versions. | Run the bundled smoke script and a small local init/apply case. If it fails after upgrade, use mutually compatible Haiku, JAX, and Flax versions or isolate the interop boundary behind a small wrapper. |
| `Module.create` cannot expose an alternate Haiku forward method | The helper wraps the Haiku module's `__call__` path only. | Write a small Haiku function that calls the desired method, transform it, then wrap the transformed function with `hkflax.Module(...)` if a Flax module interface is still needed. |
| `lift` is called but no variables appear | The lifted callable was created but not called during the transformed function, or it was called outside a Haiku transform. | Create and call the lifted module inside the function passed to `hk.transform` or `hk.transform_with_state`; inspect the params/state returned by `init`. |

## Missing Flax dependency

Haiku can be installed without Flax. In that case the experimental Flax module path may import as a shim, but accessing interop features raises an `ImportError` explaining that Flax is required. Use a local import check before writing interop-heavy code:

```python
try:
    import flax
    import haiku.experimental.flax as hkflax
    _ = hkflax.Module
except ImportError as err:
    raise RuntimeError("Install the optional flax dependency before using Haiku/Flax interop") from err
```

Prefer a small smoke test over a broad dependency install. The bundled script exercises only JAX, Haiku, Flax, and synthetic arrays.

## Variable collection naming surprises

Interop crosses two naming conventions:

- Flax variables are grouped by collection first, such as `variables["params"]` and `variables["batch_stats"]`.
- Haiku parameter/state trees are two-level dictionaries: `{module_name: {name: value}}`.
- `flatten_flax_to_haiku` joins nested Flax module scopes with `/`.
- Top-level Flax leaves become the Haiku module key `"~"`.
- `lift(..., name="foo")` prefixes outer Haiku keys with `"foo"`; non-param Flax collections become state prefixes such as `"foo/batch_stats/..."` or `"foo/state/..."`.

When debugging, print only collection names, module names, leaf names, shapes, and dtypes rather than full arrays.

## Stateful module caveats

### Haiku state inside a Flax program

A stateful Haiku component wrapped by `hkflax.Module` stores Haiku state in Flax's `"state"` collection. A read-only `apply` can return the old state value, but it will not return persistent updates unless the collection is mutable.

```python
out, updates = mod.apply(variables, x, mutable=["state"])
variables = {**variables, **updates}
```

### Flax mutable collections inside a Haiku program

A lifted Flax module registers non-param collections as Haiku state. If any collection can change during apply, the outer function must use `hk.transform_with_state` and the caller must carry the returned state forward.

```python
net = hk.transform_with_state(forward)
params, state = net.init(rng, x)
y, state = net.apply(params, state, rng, x)
```

## RNG stream rules

- Haiku-in-Flax init uses Flax's `"params"` stream.
- Haiku-in-Flax apply uses Flax's `"apply"` stream when the wrapped Haiku function needs `hk.next_rng_key()`.
- Flax-in-Haiku lifted modules receive Flax-style `rngs={...}` mappings through the lifted callable.
- During outer Haiku init, `lift` can add a `"params"` key from Haiku's RNG sequence if a params key is not supplied.
- Avoid passing a non-dictionary `rngs` value; Flax expects stream names.

## Version compatibility workflow

1. Run `python scripts/haiku_flax_smoke.py --mode module-create`.
2. If import fails, install or repair the optional `flax` dependency first.
3. If import works but init/apply fails, check the installed Haiku, JAX, JAXlib, and Flax versions together; interop depends on all four.
4. Reduce the boundary to a tiny `hk.Linear` or `nn.Dense` synthetic example before debugging full models.
5. Do not depend on private Haiku or Flax modules in downstream code; use only public `haiku`, `haiku.experimental.flax`, `jax`, and `flax.linen` imports.
