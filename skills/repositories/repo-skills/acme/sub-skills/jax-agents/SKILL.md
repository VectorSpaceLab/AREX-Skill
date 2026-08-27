---
name: jax-agents
description: "Select, configure, and adapt Acme JAX agents and JAX experiment workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Acme JAX Agents

Use this sub-skill when the task is to choose, configure, or adapt `acme.agents.jax` algorithms or `acme.jax.experiments` runners for continuous-control, discrete-control, offline RL, imitation, learning-from-demonstrations, model-based, or decentralized multiagent workflows.

## Quick Routing

- Start with [`references/agent-catalog.md`](references/agent-catalog.md) to choose the JAX algorithm family from task signals such as action space, online vs offline data, demonstrations, model-based planning, and multiagent structure.
- Use [`scripts/select_jax_agent.py`](scripts/select_jax_agent.py) for a safe local recommendation helper; it uses only Python standard-library imports and `--help` does not import Acme.
- Use [`references/experiment-workflows.md`](references/experiment-workflows.md) to build `ExperimentConfig` or `OfflineExperimentConfig`, switch between local and Launchpad distributed execution, add evaluators, checkpointing, or offline datasets.
- Use [`references/api-reference.md`](references/api-reference.md) for import paths, config classes, builder classes, network factories, experiment runner signatures, actor utilities, and saving helpers.
- Use [`references/troubleshooting.md`](references/troubleshooting.md) before diagnosing dependency imports, JAX/JAXLIB wheels, Launchpad/Reverb/TF extras, PRNG handling, spec/network mismatches, and expensive examples.

## Boundaries

- Route generic `acme.EnvironmentLoop`, environment wrappers, logging loops, and package-level setup to the Acme core workflows skill.
- Route replay table, adders, dataset iterator, TFDS/RLDS, and Reverb data-pipeline internals to the replay/data skill unless the issue is selecting a JAX builder or offline experiment shape.
- Route TensorFlow agent selection or `acme.agents.tf.*` code to the TF agents skill.
- Do not require users to inspect Acme source docs, examples, or tests at runtime; the API names and workflow patterns needed for JAX agent adaptation are distilled in the bundled references.
