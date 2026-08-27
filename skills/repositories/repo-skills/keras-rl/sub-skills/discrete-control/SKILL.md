---
name: discrete-control
description: "Build, configure, troubleshoot, and lightly verify discrete-action
  keras-rl DQN, Double/Dueling DQN, SARSA, CEM, memories, policies, and
  Atari-style processor concepts."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# discrete-control

## Read when

Use this sub-skill for keras-rl workflows with **discrete action spaces** and language such as DQN, Double DQN, dueling DQN, SARSA, CEM, CartPole, Atari processor, `SequentialMemory`, `EpisodeParameterMemory`, `EpsGreedyQPolicy`, or `BoltzmannQPolicy`.

## What this sub-skill owns

- Building and compiling `DQNAgent`, including `enable_double_dqn=True` and `enable_dueling_network=True` with `dueling_type` `avg`, `max`, or `naive`.
- Building and compiling `SARSAAgent` without replay memory.
- Building and compiling `CEMAgent` with `EpisodeParameterMemory` and `compile()` without an optimizer.
- Choosing `SequentialMemory`, `EpisodeParameterMemory`, and common discrete exploration policies.
- Discrete-agent compile/build smoke checks with the bundled helper script.
- Atari DQN preprocessing concepts as reference-only guidance; this sub-skill does not provide a full Atari runner.

## Route elsewhere

- Shared `Agent.fit`/`Agent.test` lifecycle details, callback wiring, `Processor` base-class implementation depth, `FileLogger`, `WandbLogger`, and log visualization belong to the `core-extension-and-logging` sub-skill.
- DDPG, NAF, actor/critic models, random processes, MuJoCo, Pendulum, and continuous action spaces belong to the `continuous-control` sub-skill.

## Backend stance

keras-rl is legacy Keras 2.x code. Prefer a Keras-2-compatible backend stack and run a compile-only smoke check before spending time on training. Some TensorFlow-backed legacy stacks fail when keras-rl inspects symbolic model outputs; if that happens, switch to a compatible legacy backend or patch the compatibility issue before using DQN-style agents.

## Quick operating route

1. Determine `nb_actions` from the environment's discrete action space.
2. Build a Keras model whose final output has **exactly `nb_actions` units**. For replay-memory agents, include the memory window in the model input shape.
3. Pick the agent family:
   - DQN / Double DQN / Dueling DQN: `DQNAgent` + `SequentialMemory`.
   - SARSA: `SARSAAgent` with no replay memory argument.
   - CEM: `CEMAgent` + `EpisodeParameterMemory`.
4. Compile before any `fit`, `test`, `load_weights`/target-network usage, or smoke action checks.
5. Run the bundled compile/build helper with `--agent all` or the specific agent before training.

## Runtime references and helpers

- [API reference](references/api-reference.md): constructors, compile signatures, memory/policy parameters, and gotchas.
- [Workflows](references/workflows.md): build/compile recipes for DQN, Double DQN, Dueling DQN, SARSA, and CEM.
- [Atari and processors](references/atari-and-processors.md): reference-only Atari preprocessing and processor concepts.
- [Troubleshooting](references/troubleshooting.md): shape, compile, backend, memory, Atari, callbacks, and Gym compatibility failures.
- [Build discrete agents smoke helper](scripts/build_discrete_agents_smoke.py): safe compile/build-only helper with optional tiny training disabled by default.
