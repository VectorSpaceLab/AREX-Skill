---
name: jax-agent-training
description: "Build and debug public single-agent skrl 2.1.0
  reinforcement-learning workflows with JAX, Flax, Optax, JAX models, memories,
  resources, agents, trainers, checkpoints, and evaluation."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# JAX single-agent training

Use this branch when the requested workflow is a **single-agent** skrl 2.1.0
workflow backed by JAX/Flax/Optax: A2C, CEM, DDPG, DDQN, DQN, PPO, RPO, SAC,
or TD3. It covers model definition, parameter/state initialization, JAX
resources and trainer composition, device and PRNG choices, and the boundary
between training, checkpointing, and evaluation.

## Route before building

1. Select JAX installation and backend policy in
   [framework selection](../../references/framework-selection.md); do not infer
   CUDA support from a CPU import. JAX's `jaxlib` build and the available
   `jax.devices()` determine the usable accelerator.
2. For Gymnasium/Gym, vectorization, simulator loaders, or `wrap_env`, use
   [environment integration](../environment-integration/SKILL.md). This skill
   assumes the environment is already wrapped and exposes the relevant spaces
   and device.
3. For IPPO/MAPPO, simultaneous scopes, or Runner/YAML component mapping, use
   [multi-agent and Runner](../multi-agent-and-runner/SKILL.md).
4. Read [algorithm and component selection](references/algorithm-and-component-selection.md)
   to select model keys, mixins, memory type, and the algorithm configuration.
5. Follow [the workflow/API contract](references/workflow-and-api.md), then use
   [JAX troubleshooting](references/troubleshooting.md) when a construction,
   initialization, device, or checkpoint check fails.

## Minimal construction order

For a normal single-agent build, keep this order:

1. Install the desired JAX/JAXLIB variant first, then install `skrl[jax]`. The
   package extra supplies JAX, JAXLIB, Flax, and Optax requirements, but the
   public installation guidance warns that installing JAX first avoids
   accidentally retaining its CPU build.
2. Wrap the environment and take `observation_space`, optional `state_space`,
   `action_space`, `num_envs`, and `device` from that wrapper.
3. Define Flax models as `Mixin, Model` classes. Call `Model.__init__` before
   the mixin constructor; give every custom constructor argument a default.
   Implement Flax `__call__(inputs, role)` and return `(output, {})` or
   `(output, extra_outputs)`.
4. Call `model.init_state_dict(role=<agent-model-key>)` for **every** model
   before constructing or using the agent. If needed, pass explicit sampled
   `inputs` and a JAX PRNG `key`; otherwise initialization samples each
   declared space using the model device and `config.jax.key`.
5. Create `RandomMemory` for rollouts or replay data when the algorithm needs
   memory. Instantiate the algorithm's `*_CFG`, set experiment/resource fields,
   and construct the JAX agent with the exact model dictionary keys.
6. Construct `SequentialTrainer` for the ordinary loop or `StepTrainer` when
   the caller owns one-step train/eval iteration. Call the trainer only after
   the component/init smoke passes; this branch's bundled script deliberately
   does not train.
7. During evaluation, use the agent checkpoint rather than only a raw model
   when optimizers or preprocessors matter. Set logging/checkpoint intervals
   to zero for a no-output evaluation smoke.

## Bundled safe check

From the generated skill root, run:

```bash
python sub-skills/jax-agent-training/scripts/jax_ppo_components.py --help
python sub-skills/jax-agent-training/scripts/jax_ppo_components.py
```

The helper constructs a small CPU Pendulum PPO stack, initializes Flax state,
creates the JAX memory and PPO agent, initializes a sequential trainer, and
performs one model action/value-shape check. It does **not** call `train()` or
`eval()`, download anything, import a source checkout, create checkpoints, or
write persistent output.

## Scope boundary

This branch does not own generic framework routing, environment installation or
wrapping, Torch/Warp APIs, IPPO/MAPPO, Runner YAML, or external simulator
execution. Keep those decisions in the linked sibling/root skills. See the
[root troubleshooting guide](../../references/troubleshooting.md) for
cross-framework failures and the sibling skills for their own framework or
multi-agent contracts.

## Evidence basis

Claims in this branch are distilled from the public skrl 2.1.0 JAX package APIs,
JAX model/agent/resource documentation, the maintained Gymnasium Pendulum PPO
construction example, JAX configuration tests, JAX model-instantiator tests,
and the installed public signatures. The exact evidence map and unresolved
backend limits are recorded in the branch handoff outside this runtime tree.
