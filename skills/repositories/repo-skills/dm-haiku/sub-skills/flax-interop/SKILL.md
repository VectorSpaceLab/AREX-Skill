---
name: flax-interop
description: "Use Haiku's optional experimental Flax interop APIs to embed Haiku
  modules in Flax or lift Flax modules inside Haiku."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Flax Interop

Use this sub-skill when a task specifically mixes Haiku with Flax and needs `haiku.experimental.flax` behavior. Treat the APIs here as optional, experimental interop helpers: they are useful for preserving existing Haiku code inside a Flax program, or for calling a Flax `linen.Module` inside a Haiku transform.

## Route by direction

- **Haiku inside Flax:** use `hk.experimental.flax.Module(transformed)` for an `hk.transform`/`hk.transform_with_state` result, or `hk.experimental.flax.Module.create(hk.ModuleClass, *args, **kwargs)` for a Haiku module class.
- **Flax inside Haiku:** call `hk.experimental.flax.lift(flax_module, name="...")` inside an outer `hk.transform` or `hk.transform_with_state` function.
- **Variable inspection/conversion:** use `hk.experimental.flax.flatten_flax_to_haiku(collection)` on one Flax collection such as `variables["params"]`, not on the whole variables dictionary.
- **Generic Flax work:** route out of this sub-skill for ordinary Flax training loops, non-Haiku Flax APIs, or broad migration planning.

## Read or run these bundled files

- Read [references/api-reference.md](references/api-reference.md) for a compact API table, signature shapes, collection mapping rules, and state/RNG semantics.
- Read [references/flax-interop.md](references/flax-interop.md) for copyable recipes that choose between Haiku-in-Flax and Flax-in-Haiku workflows.
- Read [references/troubleshooting.md](references/troubleshooting.md) when optional `flax` imports fail, variable trees look surprising, state does not update, RNG streams fail, or versions are incompatible.
- Run [scripts/haiku_flax_smoke.py](scripts/haiku_flax_smoke.py) to verify the optional Flax dependency and a `Module.create(hk.Linear, ...)` init/apply smoke path on synthetic data.

## Minimal working checks

1. Confirm the dependency path first: `python scripts/haiku_flax_smoke.py --mode module-create`.
2. For Haiku-in-Flax, inspect `variables.keys()` after `mod.init(...)`; expect Flax collections such as `"params"` and, for stateful Haiku, `"state"`.
3. For Flax-in-Haiku, inspect the outer Haiku `params` and `state` returned by `init`; lifted Flax params appear under the explicit `name`, and non-param Flax collections become Haiku state prefixes.
4. If exact initialized values differ between a direct Haiku init path and a Flax-wrapped init path, treat that as expected RNG-splitting behavior unless the same variables are being shared explicitly.
