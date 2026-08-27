---
name: continuous-control
description: "Build, configure, troubleshoot, and lightly verify
  continuous-action keras-rl DDPG and NAF workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# continuous-control

Use this sub-skill when a task involves continuous-action keras-rl agents: DDPG, NAF/CDQN, actor-critic wiring, `critic_action_input`, value/mu/L model construction, `OrnsteinUhlenbeckProcess`, `GaussianWhiteNoiseProcess`, Pendulum-style control, or MuJoCo caveats.

## Route here for

- DDPG actor/critic model construction and `DDPGAgent.compile([actor_optimizer, critic_optimizer])` setup.
- NAF/CDQN `V_model`, `mu_model`, `L_model`, `covariance_mode`, and continuous-action assumptions.
- Replay memory and action-noise sizing as they affect continuous agents.
- Safe compile-only checks for installed keras-rl continuous-agent wiring.
- Pendulum-style Gym tasks and reference-only MuJoCo adaptations.

## Route elsewhere

- DQN, Double/Dueling DQN, SARSA, or CEM discrete-action recipes: use `discrete-control`.
- The shared `Agent.fit`/`Agent.test` lifecycle, custom `Processor` base classes, callbacks, logging, or visualization helpers: use `core-extension-and-logging`.

## Use these bundled resources

1. [API reference](references/api-reference.md) — constructor signatures, model shape contracts, random processes, and memory notes.
2. [Workflows](references/workflows.md) — DDPG and NAF build recipes, compile smoke usage, Pendulum guidance, and MuJoCo caveats.
3. [Troubleshooting](references/troubleshooting.md) — shape, optimizer, covariance, backend, Gym, MuJoCo, and weight-file failures.
4. [Continuous-agent smoke script](scripts/build_continuous_agents_smoke.py) — compile/build-only helper for DDPG and NAF from an installed keras-rl package.

## Operating notes

- Treat keras-rl as legacy standalone Keras 2.x code. Prefer a legacy Keras backend and check package compatibility before assuming modern TensorFlow/Keras behavior.
- Keep continuous-action examples bounded: compile/build smokes are safe; long training, display rendering, MuJoCo setup, and weight persistence are opt-in user tasks.
- For any continuous Gym environment, first extract `nb_actions` from a one-dimensional continuous action space and keep every actor/mu/random-process output shaped `(nb_actions,)` per action sample.
