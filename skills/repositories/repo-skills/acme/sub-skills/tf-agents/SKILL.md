---
name: tf-agents
description: "Select, configure, debug, and adapt Acme TensorFlow/Sonnet agents,
  networks, savers, Launchpad examples, and TF losses."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Acme TensorFlow Agents

Use this sub-skill when the user asks about Acme `acme.agents.tf` algorithms, Sonnet/TensorFlow network construction, TensorFlow learner debugging, Launchpad distributed TF examples, TF losses, or TF saving/snapshotting.

## Route By Task

- Choose or compare TF algorithm families: read [references/agent-catalog.md](references/agent-catalog.md), then run `python scripts/select_tf_agent.py --help` or pass task signals to the selector.
- Build or adapt Sonnet policy, critic, observation, recurrent, Atari, OpenSpiel/legal-action, or offline learner networks: read [references/network-and-saver-workflows.md](references/network-and-saver-workflows.md).
- Add TF checkpoints, snapshots, variable syncing, or learner state handling: read [references/network-and-saver-workflows.md](references/network-and-saver-workflows.md).
- Debug TF optional dependencies, `@tf.function` graph behavior, Sonnet shape/dtype errors, Launchpad flags, OpenSpiel legal-action masks, or Gym/Atari setup: read [references/troubleshooting.md](references/troubleshooting.md).

## Boundaries

- This sub-skill owns TensorFlow/Sonnet algorithms under `acme.agents.tf`, `acme.tf.networks`, `acme.tf.losses`, `acme.tf.savers`, `acme.tf.utils`, and `acme.tf.variable_utils`.
- Route JAX algorithms, Haiku/Optax/RLax patterns, and JAX-only examples to the sibling `jax-agents` sub-skill.
- Route environment loops, wrappers, observers, loggers, and generic Acme agent-loop structure to `core-workflows` unless the question is TF-specific.
- Route Reverb table, adder, dataset iterator, and offline data mechanics to `replay-and-data`; this sub-skill only names the TF agent parameters that consume those objects.

## Quick Defaults

- Use the `dm-acme[tf]` optional dependency set for real TF execution; it pins TensorFlow 2.8.0, TensorFlow Probability 0.15.0, TensorFlow Datasets 4.6.0, Reverb 0.7.2, Launchpad 0.5.2, plus Sonnet and TRFL.
- TF agents usually accept Sonnet modules for `policy_network`, `critic_network`, `observation_network`, or a discrete/recurrent `network`; distributed variants accept factories and expose a Launchpad `build(name=...)` method.
- For Control Suite distributed runs, keep three layers separate: `environment_factory`, `network_factory`, then `lp.launch(program_builder.build(), launch_type=...)` with `--lp_launch_type=local_mt` or `local_mp` for local debugging.
- For learner debugging, temporarily remove or bypass the learner `_step()` `@tf.function` decorator, inspect tensors in eager mode, then restore graph mode after the issue is fixed.

## Bundled Helper

- `scripts/select_tf_agent.py` maps task signals such as `--action-space discrete --setting distributed --needs recurrent` to candidate TF agents and example families without importing TensorFlow.
