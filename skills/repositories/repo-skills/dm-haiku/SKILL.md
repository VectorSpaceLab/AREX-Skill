---
name: dm-haiku
description: "Use DeepMind dm-haiku as a JAX neural-network library for
  transforms, modules, state/RNG, layers, advanced JAX interop, and optional
  Flax interop."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# dm-haiku

Use this repo skill when a task involves the `dm-haiku` Python package, usually imported as `import haiku as hk`, or when a JAX neural-network workflow needs Haiku's object-oriented modules plus pure `init`/`apply` functions.

Haiku is in maintenance mode: it remains useful for existing Haiku code and research checkouts, but new greenfield projects may be better served by Flax. Do not present Haiku as a full training framework: it provides module, parameter, state, RNG, transform, and model-building utilities that compose with JAX, optimizers, datasets, checkpointing, and accelerators from other libraries.

## Quick install and smoke check

1. Install a JAX build that matches the target machine first. CPU JAX is enough for API work; GPU/TPU execution requires the appropriate JAX backend package for that machine.
2. Install Haiku:

   ```bash
   python -m pip install -U dm-haiku
   ```

3. For optional Flax interop, also install Flax:

   ```bash
   python -m pip install -U flax
   ```

4. Run the bundled checker from this skill directory if import or backend state is uncertain:

   ```bash
   python scripts/check_haiku_env.py
   python scripts/check_haiku_env.py --require-flax
   ```

The checker imports `haiku`, `jax`, and optionally `flax`, runs a tiny `hk.Linear` transform, reports JAX backend/devices, and does not download data or train.

## Route by task

- Use [sub-skills/core-transforms/SKILL.md](sub-skills/core-transforms/SKILL.md) when choosing `hk.transform`, `hk.transform_with_state`, `hk.without_apply_rng`, `hk.multi_transform`, or diagnosing `init`/`apply` signatures.
- Use [sub-skills/params-state-rng/SKILL.md](sub-skills/params-state-rng/SKILL.md) when writing `hk.Module` subclasses, direct `hk.get_parameter` / `hk.get_state` / `hk.set_state` code, RNG flows, module naming, or creators/getters/interceptors.
- Use [sub-skills/modules-and-networks/SKILL.md](sub-skills/modules-and-networks/SKILL.md) when building or debugging Haiku layers, normalization, attention, recurrent cores, `hk.nets` models, or no-download model smoke tests.
- Use [sub-skills/jax-interop-and-advanced/SKILL.md](sub-skills/jax-interop-and-advanced/SKILL.md) when Haiku code interacts with `vmap`, `scan`, `grad`, control flow, nested transforms/lifting, parameter tree utilities, mixed precision, summaries, or visualization.
- Use [sub-skills/flax-interop/SKILL.md](sub-skills/flax-interop/SKILL.md) when mixing Haiku with Flax through `hk.experimental.flax` APIs.

## Root references and helper

- Read [references/troubleshooting.md](references/troubleshooting.md) for install/import, JAX backend, optional dependency, version, example dependency, and maintenance-mode issues that cut across sub-skills.
- Read [references/repo-provenance.md](references/repo-provenance.md) before deciding whether this skill is current for a checkout or should be refreshed.
- `references/repo-routing-metadata.json` contains structured router metadata for managed repo-skill import.
- Run [scripts/check_haiku_env.py](scripts/check_haiku_env.py) as the shared environment/import checker before deeper sub-skill smoke scripts.

## Operating pattern

For most Haiku tasks, work in this order:

1. Pick the transform boundary first: stateless `hk.transform`, stateful `hk.transform_with_state`, or multi-transform. See `core-transforms`.
2. Build module code inside the transformed function. Keep `hk.Module` construction, `hk.get_parameter`, `hk.get_state`, and `hk.next_rng_key` inside Haiku contexts. See `params-state-rng`.
3. Choose modules/networks and validate with synthetic arrays before adding optimizers, datasets, large examples, or distributed JAX. See `modules-and-networks`.
4. If raw JAX transforms appear inside a Haiku-transformed function, switch to Haiku wrappers or lift nested transforms deliberately. See `jax-interop-and-advanced`.
5. Treat Flax interop as optional and explicit. Verify the `flax` dependency and variable collection mapping before mixing codebases. See `flax-interop`.

## Common boundaries

- Haiku does not own optimizers, checkpoint formats, dataset loaders, training launchers, or accelerator installation. Bring those from JAX/Optax/Orbax/TFDS or the user's own stack.
- Full public examples often require external datasets, TensorFlow/TFDS, Optax, RL libraries, or long training. This skill distills their Haiku model patterns into bundled no-download scripts and references; do not require the original checkout for runtime use.
- GPU warnings from JAX usually mean the installed JAX backend is CPU-only. That does not invalidate Haiku API work, but it does mean accelerator performance has not been verified.
- If a task is about editing the `dm-haiku` repository source itself rather than using Haiku as a package, first decide whether a maintainer/repository-development skill is more appropriate; this skill is optimized for package usage.
