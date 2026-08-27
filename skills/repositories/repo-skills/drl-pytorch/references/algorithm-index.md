# Algorithm Index

Read this for a compact map from user intent to DRL-Pytorch algorithm directories, sub-skills, environment indexes, and checkpoint conventions.

## Route by task

| User intent | Sub-skill | Algorithm label | Default safe env | Optional envs |
|---|---|---|---|---|
| Tabular RL baseline | `value-based-discrete-control` | Q-learning | CliffWalking-v0 | none |
| DQN, Double DQN, Dueling DQN | `value-based-discrete-control` | DQN family | CartPole-v1 (`EnvIdex 0`) | LunarLander-v2 (`EnvIdex 1`, Box2D) |
| Prioritized replay | `value-based-discrete-control` | LightPrior PER by default | CartPole-v1 | LunarLander-v2; sum-tree PER if requested; legacy gym0.1x only with older stack |
| Distributional DQN | `value-based-discrete-control` | C51 | CartPole-v1 | LunarLander-v2 |
| NoisyNet exploration | `value-based-discrete-control` | NoisyNet DQN | CartPole-v1 | LunarLander-v2 |
| PPO for discrete actions | `policy-and-actor-critic-control` | PPO-Discrete | CartPole-v1 | LunarLander-v2 |
| PPO for continuous actions | `policy-and-actor-critic-control` | PPO-Continuous | Pendulum-v1 (`EnvIdex 0`) | LunarLanderContinuous-v2, Humanoid-v4, HalfCheetah-v4, BipedalWalker-v3, BipedalWalkerHardcore-v3 |
| DDPG/TD3/SAC continuous | `policy-and-actor-critic-control` | DDPG, TD3, SAC-Continuous | Pendulum-v1 | same continuous-control env map as PPO-Continuous |
| SAC for discrete actions | `policy-and-actor-critic-control` | SAC-Discrete | CartPole-v1 | LunarLander-v2 |
| Atari image DQN | `atari-and-asl-workflows` | Noisy-Duel-DDQN-Atari | no-ROM dummy smoke only | Pong (`EnvIdex 37`), Enduro (`EnvIdex 20`), other Atari names with ALE/ROMs/OpenCV |
| EnvPool Atari framework | `atari-and-asl-workflows` | Actor-Sharer-Learner | import/dummy smoke only | EnvPool Atari `Name[EnvIdex] + "-v5"` training |

## Common environment indexes

### Discrete Gymnasium launchers

| `EnvIdex` | Environment | Notes |
|---:|---|---|
| 0 | `CartPole-v1` | CPU-safe baseline for DQN/PER/C51/NoisyNet/PPO-Discrete/SAC-Discrete. |
| 1 | `LunarLander-v2` | Requires Box2D support. |

### Continuous-control launchers

| `EnvIdex` | Environment | Notes |
|---:|---|---|
| 0 | `Pendulum-v1` | CPU-safe baseline. |
| 1 | `LunarLanderContinuous-v2` | Requires Box2D support. |
| 2 | `Humanoid-v4` | Requires MuJoCo. |
| 3 | `HalfCheetah-v4` | Requires MuJoCo. |
| 4 | `BipedalWalker-v3` | Requires Box2D support. |
| 5 | `BipedalWalkerHardcore-v3` | Requires Box2D support and longer training. |

### Atari indexes

| `EnvIdex` | Atari DQN environment | ASL/EnvPool environment | Notes |
|---:|---|---|---|
| 20 | `EnduroNoFrameskip-v4` | `Enduro-v5` | README pretrained Atari DQN checkpoint example uses Enduro at `ModelIdex 900`. |
| 37 | `PongNoFrameskip-v4` | `Pong-v5` | README pretrained Atari DQN checkpoint example uses Pong at `ModelIdex 700`. |
| 1 | `AlienNoFrameskip-v4` | `Alien-v5` | ASL default is Alien (`EnvIdex 1`). |

Use the Atari/ASL sub-skill for the longer Atari name table and dependency gates.

## Checkpoint and output conventions

- Most launchers write checkpoints under a per-algorithm `model/` directory and logs under `runs/` when `--write True`.
- DQN family: `model/{algo}_{brief_env}_{steps}.pth`, for example `DuelDDQN_CPV1_100.pth`.
- PER LightPrior and modern sum-tree: `model/{algo}_{brief_env}_{steps}.pth`; LightPrior saves thousands, while sum-tree source behavior may use raw step count in older examples.
- C51: `model/{algo}_{brief_env}_{steps}k.pth`, for example `C51_DDQN_CPV1_60k.pth`.
- NoisyNet: `model/{algo}_{brief_env}_{steps}k.pth`, for example `NoisyNetDQN_CPV1_100k.pth`.
- PPO-Discrete: `model/ppo_actor{episode}.pth` and `model/ppo_critic{episode}.pth`.
- PPO/DDPG/TD3/SAC continuous: `model/{brief_env}_actor{timestep}.pth` plus critic/Q-critic files.
- SAC-Discrete: `model/sacd_actor_{timestep}_{brief_env}.pth` and `model/sacd_critic_{timestep}_{brief_env}.pth`.
- Atari DQN: `model/{ExperimentName}_{ModelIdex}k.pth`, where `ExperimentName` includes algorithm flags plus the Atari NoFrameskip environment name.

## Maintain the distinction between labels and paths

This skill uses original directory names as labels so agents can recognize the repository layout in a user's checkout. Runtime helpers and references are bundled under the generated skill tree. Do not create new instructions that link to or depend on the checkout used to generate this skill.
