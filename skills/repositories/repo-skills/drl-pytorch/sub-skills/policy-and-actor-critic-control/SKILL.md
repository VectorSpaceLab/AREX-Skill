---
name: policy-and-actor-critic-control
description: "Route DRL-Pytorch PPO, DDPG, TD3, and SAC policy/actor-critic
  workflows for discrete and continuous control."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NO_LICENSE
---

# Policy and Actor-Critic Control

Use this sub-skill when a task is about DRL-Pytorch policy-gradient or actor-critic workflows:

- PPO on discrete or continuous action spaces.
- DDPG, TD3, SAC-Discrete, or SAC-Continuous.
- Continuous-control environments such as Pendulum, LunarLanderContinuous, Humanoid, HalfCheetah, BipedalWalker, or BipedalWalkerHardcore.
- Actor/critic APIs, PPO trajectory holders, off-policy replay buffers, action/reward adapters, checkpoint naming, device flags, TensorBoard, or optional Box2D/MuJoCo/CUDA requirements for these algorithms.

Route tabular Q-learning, DQN/DDQN/Dueling, PER, C51, and NoisyNet questions to the value-based discrete-control sibling. Route Atari NoFrameskip, ROM/license, EnvPool, and Actor-Sharer-Learner questions to the Atari/ASL sibling.

## Operating checklist

1. Classify the target environment action space before choosing an algorithm. Use [references/algorithm-workflows.md](references/algorithm-workflows.md) for action-space routing, `EnvIdex` maps, CPU-safe command recipes, optional dependency gates, play commands, checkpoints, and TensorBoard guidance.
2. Use [references/api-and-cli-reference.md](references/api-and-cli-reference.md) for verified class/function names, CLI flags, actor distributions, adapters, replay/trajectory storage, and checkpoint file patterns.
3. Use [references/troubleshooting.md](references/troubleshooting.md) for CPU/GPU device failures, optional Box2D/MuJoCo errors, `EnvIdex` mismatches, checkpoint lookup problems, tensor-shape issues, and stochastic long-training expectations.
4. For a safe checkout diagnostic, run [scripts/smoke_policy_control.py](scripts/smoke_policy_control.py) with a user-supplied DRL-Pytorch checkout. The script imports policy-control modules and performs tiny CPU object checks only; it does not train, create optional environments, download assets, or require Box2D/MuJoCo.

## Safe defaults

- The DRL-Pytorch launchers default to `--dvc cuda`; use `--dvc cpu` for CPU-only sanity checks.
- Prefer `--Max_train_steps 0 --write False --render False` for parser/env/model construction checks before attempting long training.
- `Pendulum-v1` and `CartPole-v1` are the CPU-safe baseline environments in the prepared minimum scope. Box2D, MuJoCo, and CUDA acceleration are optional and dependency-gated; do not claim them verified unless the current runtime actually checks them.
- Checkpoints and TensorBoard logs are written relative to each algorithm working directory (`model/` and `runs/`). Do not bundle binary checkpoints in this skill.
