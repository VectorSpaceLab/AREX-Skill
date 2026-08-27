---
name: continuous-control
description: "Guides minimalRL DDPG, continuous PPO, and SAC workflows for
  Pendulum-style continuous-action control."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Continuous-Control Workflows

Use this sub-skill when a task asks about minimalRL's continuous-action Pendulum algorithms: DDPG, PPO-Continuous, or SAC.

## Route by task

- **Deterministic actor-critic / DDPG**: read [references/api-reference.md](references/api-reference.md) for `MuNet`, `QNet`, replay, OU noise, and `soft_update`; read [references/workflows.md](references/workflows.md) for action scaling and target updates.
- **Continuous PPO**: use [references/workflows.md](references/workflows.md) for Gaussian rollout/minibatch handling and [references/troubleshooting.md](references/troubleshooting.md) for `mu`, `std`, and log-prob shape issues.
- **Soft Actor-Critic**: use [references/api-reference.md](references/api-reference.md) for `PolicyNet`, twin `QNet`, `calc_target`, and alpha update contracts.
- **Pre-training shape checks**: run [scripts/smoke_continuous_control.py](scripts/smoke_continuous_control.py).

## Do not use this sub-skill for

- Discrete CartPole REINFORCE, actor-critic, PPO, PPO-LSTM, or V-trace policy/value routes; use [../on-policy-discrete/SKILL.md](../on-policy-discrete/SKILL.md).
- DQN, ACER, or V-trace replay/correction debugging; use [../off-policy-value/SKILL.md](../off-policy-value/SKILL.md).
- A2C/A3C multiprocessing; use [../parallel-actor-critic/SKILL.md](../parallel-actor-critic/SKILL.md).

## Quick operating workflow

1. Confirm the environment has continuous actions. The minimalRL continuous scripts assume Pendulum-like observations of length 3 and a one-dimensional action in `[-2, 2]`.
2. Choose the algorithm family:
   - DDPG for deterministic actor plus critic, replay, OU exploration, and soft target updates.
   - Continuous PPO for on-policy Gaussian policy with clipped objective.
   - SAC for stochastic tanh-Gaussian policy, twin critics, entropy temperature update, and replay.
3. Read [references/api-reference.md](references/api-reference.md) before changing tensor shapes or action scaling.
4. Run the smoke helper:

   ```bash
   python sub-skills/continuous-control/scripts/smoke_continuous_control.py --algorithm all
   ```

5. For action range, `log_prob`, state/action concatenation, replay warm-up, or target update failures, read [references/troubleshooting.md](references/troubleshooting.md).

## Bundled runtime files

- [references/api-reference.md](references/api-reference.md) lists source-faithful classes, functions, hyperparameters, tensor/action shapes, and data tuple contracts.
- [references/workflows.md](references/workflows.md) explains DDPG, continuous PPO, and SAC adaptation workflows.
- [references/troubleshooting.md](references/troubleshooting.md) gives actionable fixes for continuous-control failure modes.
- [scripts/smoke_continuous_control.py](scripts/smoke_continuous_control.py) validates representative continuous-control tensors without importing the original repository or running training.
