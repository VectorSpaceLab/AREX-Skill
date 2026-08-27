---
name: drl-pytorch
description: "Route DRL-Pytorch reinforcement-learning workflows for standalone
  PyTorch Q-learning, DQN-family, PPO, DDPG, TD3, SAC, Atari DQN, and
  Actor-Sharer-Learner scripts."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NO_LICENSE
---

# DRL-Pytorch Repo Skill

Use this skill when a task involves the XinJingHao DRL-Pytorch repository or its standalone PyTorch reinforcement-learning scripts: Q-learning, DQN/DDQN/Dueling DQN, prioritized replay, C51, NoisyNet, PPO, DDPG, TD3, SAC, Atari NoFrameskip DQN, or Actor-Sharer-Learner.

Do not use this skill for Stable-Baselines3, CleanRL, Tianshou, PettingZoo, RLHF packages, or generic RL theory unless the task explicitly needs DRL-Pytorch command/API details.

## First checks

1. Read [repository provenance](references/repo-provenance.md) if you need to decide whether this skill matches a current checkout or should be refreshed.
2. Read [quickstart and environment](references/quickstart-and-environment.md) before installing extras, running smoke checks, or starting training.
3. Use [algorithm index](references/algorithm-index.md) to route by algorithm name, action space, `EnvIdex`, and checkpoint pattern.
4. Use [cross-cutting troubleshooting](references/troubleshooting.md) for CUDA defaults, optional Gymnasium extras, colliding module imports, checkpoints, TensorBoard, or stochastic training failures.

## Choose the sub-skill

| Request signal | Read |
|---|---|
| `Q-learning`, `CliffWalking`, `DQN`, `DDQN`, `Dueling`, `PER`, prioritized replay, `C51`, `NoisyNet`, CartPole, LunarLander discrete | [value-based-discrete-control](sub-skills/value-based-discrete-control/SKILL.md) |
| `PPO`, `DDPG`, `TD3`, `SAC`, actor-critic, policy gradient, Pendulum, LunarLanderContinuous, Humanoid, HalfCheetah, BipedalWalker, continuous control | [policy-and-actor-critic-control](sub-skills/policy-and-actor-critic-control/SKILL.md) |
| Atari, Pong, Enduro, `NoFrameskip`, `AtariNames`, ALE ROMs, OpenCV wrappers, EnvPool, Actor-Sharer-Learner, ASL multiprocessing | [atari-and-asl-workflows](sub-skills/atari-and-asl-workflows/SKILL.md) |

If a task spans multiple algorithms, start with the root algorithm index, then read each owning sub-skill. Keep value-based non-Atari DQN separate from Atari DQN: both use DQN terminology but have different environments, wrappers, dependencies, and checkpoints.

## Repository operating model

DRL-Pytorch is not an installable Python distribution. It is a script collection where each algorithm directory has its own `main.py`, local implementation module, and often a colliding `utils.py`. Commands that run original launchers must be executed from the selected algorithm directory in the user's DRL-Pytorch checkout. Bundled scripts in this skill accept `--repo-root` so diagnostics do not depend on the checkout used to create this skill.

Baseline CPU-safe dependencies for modern workflows are Python 3.11, Gymnasium 0.29.x, NumPy 1.26.x, PyTorch 2.1.x, TensorBoard for `--write True`, and Matplotlib for C51 render helpers. Optional extras include Box2D, MuJoCo, Atari ALE/ROMs/OpenCV, EnvPool, and CUDA acceleration.

## Safe diagnostics

Use the bundled algorithm matrix without a checkout:

```bash
python scripts/drl_pytorch_algorithm_matrix.py --format table
```

Use no-training diagnostics when a DRL-Pytorch checkout is available:

```bash
python scripts/drl_pytorch_safe_smoke.py --repo-root <DRL-Pytorch-checkout> --suite all
```

For narrower checks:

```bash
python scripts/drl_pytorch_safe_smoke.py --repo-root <DRL-Pytorch-checkout> --suite value
python scripts/drl_pytorch_safe_smoke.py --repo-root <DRL-Pytorch-checkout> --suite policy
python scripts/drl_pytorch_safe_smoke.py --repo-root <DRL-Pytorch-checkout> --suite atari
```

The smoke helpers import modules and run tiny CPU object/network checks. They do not train, render, download Atari ROMs, create optional Box2D/MuJoCo/Atari environments, write checkpoints, launch TensorBoard, or start EnvPool workers.

## Training guardrails

- Set `--dvc cpu` or `--device cpu` for CPU-only checks; several launchers default to CUDA.
- Prefer `--Max_train_steps 0 --write False --render False` before any real training when the launcher supports it.
- Install Box2D only for LunarLander/BipedalWalker, MuJoCo only for Humanoid/HalfCheetah, Atari extras/ROMs/OpenCV only for Atari NoFrameskip, and EnvPool only for ASL.
- Treat full training, rendering, checkpoint playback, Atari environment creation, and ASL multiprocessing as user-approved side-effectful work.
- Check checkpoint filename conventions before `--Loadmodel True`; binaries are not bundled in this skill.

## If editing or refreshing

When repository code changes, refresh from source evidence rather than patching this skill by memory. Pay special attention to launcher flags, `EnvIdex` maps, class names, checkpoint naming, optional dependency gates, and repeated local module names.
