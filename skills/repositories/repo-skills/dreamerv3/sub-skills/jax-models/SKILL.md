---
name: jax-models
description: "Inspect, extend, and debug DreamerV3 neural/JAX internals: Agent,
  RSSM, heads, optimizers, Ninjax state, sharding, and numerics."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# jax-models

Use this sub-skill when the task is about DreamerV3 model internals rather than command-line training recipes, environment/replay plumbing, or operations dashboards. It covers the DreamerV3 Agent, RSSM, encoder/decoder, JAX wrapper, heads/distributions, optimizer stack, Ninjax parameter/state handling, sharding setup, loss metrics, and numerical debugging.

## Read This First

- For architecture, dimensions, data flow, and model-loss behavior, read [references/model-architecture.md](references/model-architecture.md).
- For callable APIs, JAX setup/sharding, Ninjax state contracts, heads/outs/nets/optimizer utilities, and checkpoint methods, read [references/jax-api-reference.md](references/jax-api-reference.md).
- For non-finite outputs, dtype/platform/JIT/preallocation choices, loss localization, checkpoint regex loading, and LayerScan pitfalls, read [references/debugging-numerics.md](references/debugging-numerics.md).
- For symptom-to-action guidance, read [references/troubleshooting.md](references/troubleshooting.md).
- To inspect a DreamerV3 YAML config or built-in config combination without constructing the full Agent, run [scripts/inspect_model_config.py](scripts/inspect_model_config.py).

## Route Here When

- You need to shrink or expand the neural model (`debug`, `size1m`, `size12m`, regex override blocks, RSSM dimensions, head sizes, image encoder/decoder depths).
- You need to understand `dreamerv3.agent.Agent` construction, `policy()`, `train()`, `report()`, `save()`, or `load()` behavior.
- You need to inspect `dreamerv3.rssm.RSSM`, `Encoder`, or `Decoder` shapes, carries, entries, reconstruction outputs, stochastic state, or KL losses.
- You are debugging `embodied.jax.Agent`, `internal.setup()`, sharding meshes, `transform.init/apply()`, Ninjax parameter names, optimizer metrics, or finite-output assertions.
- You see non-finite policy outputs, XLA/JAX errors, PyTree/checkpoint mismatches, action-head shape errors, or `LayerScan` state issues.

Route elsewhere:

- CLI launch commands, config-file composition recipes, and training/evaluation scripts belong to `train-configure`; this sub-skill only covers model-relevant config keys.
- Environment spaces, replay chunks, driver/stream contracts, and dataset flow belong to `embodied-dataflow`.
- Backend installation, Docker/system package repair, logdir hygiene, and plotting/metrics dashboards belong to `results-ops`.

## Quick Workflows

### Inspect a model config safely

From this sub-skill directory or from a copied skill tree:

```bash
python scripts/inspect_model_config.py defaults debug size1m
python scripts/inspect_model_config.py defaults --set jax.platform=cpu --set agent.dyn.rssm.deter=512
python scripts/inspect_model_config.py --config-file path/to/config.yaml
```

Expected output sections include JAX platform/dtype, RSSM dimensions and feature size, encoder/decoder sizes, head/distribution types, loss scales, rollout settings, and warnings. This script parses configs only; it does not create environments, instantiate `Agent`, allocate JAX devices, or run training.

### Shrink a laptop smoke model

1. Use `defaults debug size1m` for a small CPU-oriented smoke, or inspect the exact override result with `scripts/inspect_model_config.py` before launching.
2. Verify the final `agent.dyn.rssm.deter` is divisible by `agent.dyn.rssm.blocks` and `agent.dec.simple.bspace`.
3. Expect checkpoint incompatibility when changing RSSM/head dimensions. Use a new logdir or a carefully chosen `load(..., regex=...)` subset; read [references/debugging-numerics.md](references/debugging-numerics.md#checkpoint-and-pytree-mismatches).

### Localize non-finite outputs or XLA failures

1. Read [references/debugging-numerics.md](references/debugging-numerics.md#finite-policy-output-checks).
2. Reproduce in a fresh process with CPU/debug settings: `jax.platform=cpu`, `jax.debug=True`, `jax.prealloc=False`, and, when needed, `jax.jit=False` or `jax.debug_nans=True`.
3. Use `policy()` finite assertions and training metrics (`loss/*`, `opt/grad_norm`, `dyn_ent`, `rep_ent`, `adv*`, `ent/*`) to locate the component.
4. If the error only appears during checkpoint restore or model-size changes, read the checkpoint section before editing parameter names.

## Core Object Contracts

- `dreamerv3.agent.Agent(obs_space, act_space, config)` returns the `embodied.jax.Agent` wrapper because the base class intercepts construction. The wrapped model is available as `agent.model` on the returned object.
- Policy carry shape is `(enc_carry, dyn_carry, dec_carry, prevact)`. `init_train()` and `init_report()` use the same carry contract as `init_policy()`.
- Model training data must contain observation keys, action keys, extras (`consec`, `stepid`, and optional replay-context entries), plus a JAX seed inserted by `embodied.jax.Agent.stream()` before `train()`/`report()`.
- RSSM feature dictionaries use `deter`, `stoch`, and `logit`. The tensor feature used by heads concatenates `deter` and flattened `stoch`.
- Output heads return `embodied.jax.outs.Output` objects or dictionaries of them. Use `.pred()`, `.loss(target)`, `.sample(seed)`, `.logp(event)`, `.entropy()`, and `.kl(other)` according to [references/jax-api-reference.md](references/jax-api-reference.md#heads-and-output-distributions).

## Validation Hooks Covered

- Native utility candidate: `LayerScan` apply behavior from the repo test suite is distilled into [references/debugging-numerics.md](references/debugging-numerics.md#layerscan-pitfalls).
- Synthetic safe candidate: parsing `defaults debug size1m` with `scripts/inspect_model_config.py` covers small-model and CPU-debug config behavior without constructing the full Agent.
