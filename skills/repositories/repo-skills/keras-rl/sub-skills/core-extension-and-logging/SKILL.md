---
name: core-extension-and-logging
description: "Use keras-rl core fit/test lifecycle, processors, callbacks,
  logging, utilities, and environment checks."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# keras-rl Core Extension and Logging

Use this sub-skill when the task is about the shared keras-rl agent lifecycle or cross-cutting extension surfaces rather than a specific algorithm family.

## Read when

- You need to call or debug `Agent.fit(...)`, `Agent.test(...)`, `compile(...)`, callback wiring, `verbose`, `visualize`, `nb_max_episode_steps`, `action_repetition`, or `start_step_policy`.
- You are writing a custom `Processor`, custom `Env`, old-Gym API adapter, multi-input observation processor, reward/action transformer, or whitening normalizer.
- You need training logs, JSON log visualization, model checkpoints, `WandbLogger`, `FileLogger`, `TrainIntervalLogger`, `TestLogger`, or `Visualizer`.
- You need `clone_model`, `clone_optimizer`, `huber_loss`, `WhiteningNormalizer`, or a safe installed-environment compatibility check.

## Route elsewhere

- For DQN, Double DQN, Dueling DQN, SARSA, CEM, replay memory, and discrete policy construction details, use the sibling `discrete-control` sub-skill.
- For DDPG, NAF, actor/critic/value/mu/L model construction, continuous-action random processes, and MuJoCo/Pendulum patterns, use the sibling `continuous-control` sub-skill.

## Use this sub-skill

1. Check the exact shared APIs and callback/log schema in [references/api-reference.md](references/api-reference.md).
2. Follow the applicable lifecycle, processor, logging, visualization, and environment-check workflows in [references/workflows.md](references/workflows.md).
3. If imports, plotting, callbacks, Gym wrappers, or processor shapes fail, use [references/troubleshooting.md](references/troubleshooting.md).
4. To plot a `FileLogger` JSON without relying on the original repository, use [scripts/visualize_keras_rl_log.py](scripts/visualize_keras_rl_log.py).
5. To inspect installed keras-rl/Keras/backend compatibility before agent work, use [scripts/check_keras_rl_env.py](scripts/check_keras_rl_env.py).

## Compatibility note

keras-rl is legacy Keras 2.x code. Prefer a legacy Keras backend and check compatibility before investing in training. A Theano CPU backend is often the safest compile-only route for this package family; TensorFlow-era imports may work while agent construction can still hit legacy symbolic-tensor behavior. Modern `tf.keras`/Keras 3 stacks should be treated as incompatible until proven by a local smoke check.
