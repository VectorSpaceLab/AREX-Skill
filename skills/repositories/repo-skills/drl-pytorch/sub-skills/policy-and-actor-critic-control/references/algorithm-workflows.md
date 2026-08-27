# Policy and Actor-Critic Algorithm Workflows

This reference distills the DRL-Pytorch policy-control launchers into self-contained routing facts and command recipes. The algorithms are standalone script directories: each launcher imports neighboring modules by short names and writes `model/` and `runs/` relative to its current working directory.

Use CPU zero-step commands to validate parser, environment creation, and agent construction before training. Training returns are stochastic and usually require many steps; a zero-step check is not a learning-quality test.

## Action-space routing

| Request/environment | Use these algorithms | Avoid these algorithms | Notes |
|---|---|---|---|
| Discrete actions, `CartPole-v1`, `LunarLander-v2` | PPO-Discrete, SAC-Discrete | DDPG, TD3, PPO-Continuous, SAC-Continuous | Discrete launchers read `env.action_space.n`; continuous agents expect Box actions and vector action dimensions. |
| Continuous actions, `Pendulum-v1` | PPO-Continuous, DDPG, TD3, SAC-Continuous | PPO-Discrete, SAC-Discrete | `Pendulum-v1` is the safest CPU baseline for continuous-control checks. |
| Continuous Box2D tasks, `LunarLanderContinuous-v2`, `BipedalWalker-v3`, `BipedalWalkerHardcore-v3` | PPO-Continuous, DDPG, TD3, SAC-Continuous | Discrete algorithms unless using `LunarLander-v2` | Requires `gymnasium[box2d]`; optional dependency was not part of the minimum CPU verification. |
| MuJoCo tasks, `Humanoid-v4`, `HalfCheetah-v4` | PPO-Continuous, DDPG, TD3, SAC-Continuous | Discrete algorithms | Requires `gymnasium[mujoco]` or compatible MuJoCo installation; optional dependency was not verified in the minimum CPU scope. |
| Maximum stability among off-policy continuous agents | TD3 or SAC-Continuous | DDPG as first choice | DDPG is documented by the repo as hyperparameter-sensitive; TD3 refines DDPG with twin critics and target-policy smoothing. |
| Entropy-regularized discrete control | SAC-Discrete | Continuous SAC | SAC-Discrete uses a categorical policy over action probabilities and optional adaptive entropy alpha. |
| On-policy trajectory updates | PPO-Discrete or PPO-Continuous | DDPG/TD3/SAC replay workflows | PPO stores fixed-length trajectory holders controlled by `--T_horizon`; off-policy algorithms use replay buffers. |

## Environment index maps

### Discrete PPO

| `--EnvIdex` | Environment | Short name in logs/checkpoints | Required action space | Optional dependency |
|---:|---|---|---|---|
| 0 | `CartPole-v1` | `CP-v1` | discrete | base Gymnasium |
| 1 | `LunarLander-v2` | `LLd-v2` | discrete | `gymnasium[box2d]` |

### SAC-Discrete

| `--EnvIdex` | Environment | Short name in logs/checkpoints | Required action space | Optional dependency |
|---:|---|---|---|---|
| 0 | `CartPole-v1` | `CPV1` | discrete | base Gymnasium |
| 1 | `LunarLander-v2` | `LLdV2` | discrete | `gymnasium[box2d]` |

### Continuous PPO, DDPG, TD3, and SAC-Continuous

| `--EnvIdex` | Environment | Short name in logs/checkpoints | Required action space | Optional dependency |
|---:|---|---|---|---|
| 0 | `Pendulum-v1` | `PV1` | continuous Box | base Gymnasium |
| 1 | `LunarLanderContinuous-v2` | `LLdV2` | continuous Box | `gymnasium[box2d]` |
| 2 | `Humanoid-v4` | `Humanv4` | continuous Box | `gymnasium[mujoco]` or MuJoCo |
| 3 | `HalfCheetah-v4` | `HCv4` | continuous Box | `gymnasium[mujoco]` or MuJoCo |
| 4 | `BipedalWalker-v3` | `BWv3` | continuous Box | `gymnasium[box2d]` |
| 5 | `BipedalWalkerHardcore-v3` | `BWHv3` | continuous Box | `gymnasium[box2d]` |

The parser help strings mention `Lch_Cv2`, but the verified code map uses `LunarLanderContinuous-v2` and the short name `LLdV2`.

## CPU-safe command recipes

Run these from the target algorithm directory in a user-supplied checkout. They create the selected Gymnasium environment and agent, then exit without training because `--Max_train_steps 0` makes the training loop condition false. Keep `--write False` to avoid TensorBoard side effects and `--render False` for headless hosts.

```bash
cd "<repo-root>/3.1 PPO-Discrete"
python main.py --dvc cpu --EnvIdex 0 --write False --render False --Max_train_steps 0

cd "<repo-root>/3.2 PPO-Continuous"
python main.py --dvc cpu --EnvIdex 0 --write False --render False --Max_train_steps 0 --Distribution Beta

cd "<repo-root>/4.1 DDPG"
python main.py --dvc cpu --EnvIdex 0 --write False --render False --Max_train_steps 0

cd "<repo-root>/4.2 TD3"
python main.py --dvc cpu --EnvIdex 0 --write False --render False --Max_train_steps 0

cd "<repo-root>/5.1 SAC-Discrete"
python main.py --dvc cpu --EnvIdex 0 --write False --render False --Max_train_steps 0

cd "<repo-root>/5.2 SAC-Continuous"
python main.py --dvc cpu --EnvIdex 0 --write False --render False --Max_train_steps 0
```

For a diagnostic that avoids Gymnasium environment creation entirely and only imports modules/constructs tiny objects, use [../scripts/smoke_policy_control.py](../scripts/smoke_policy_control.py):

```bash
python <skill-tree>/sub-skills/policy-and-actor-critic-control/scripts/smoke_policy_control.py \
  --repo-root <repo-root> --algorithm all
```

## Training and play commands

After a zero-step check succeeds, remove `--Max_train_steps 0` or set a real step budget for training. Use `--dvc cuda` only when the runtime has a CUDA-capable PyTorch build and GPU access.

Examples:

```bash
# Train a short CPU Pendulum TD3 run; increase steps for real learning.
cd "<repo-root>/4.2 TD3"
python main.py --dvc cpu --EnvIdex 0 --Max_train_steps 20000 --write True --render False

# Train SAC-Discrete on CartPole with TensorBoard logging.
cd "<repo-root>/5.1 SAC-Discrete"
python main.py --dvc cpu --EnvIdex 0 --Max_train_steps 20000 --write True --render False

# Play/evaluate an existing PPO-Continuous Pendulum checkpoint.
cd "<repo-root>/3.2 PPO-Continuous"
python main.py --dvc cpu --EnvIdex 0 --render True --Loadmodel True --ModelIdex 100
```

Play mode (`--render True --Loadmodel True`) loops indefinitely and expects matching checkpoint files under that algorithm directory's `model/`. It also requires a display-capable runtime. For headless verification, prefer the smoke script or zero-step commands.

## TensorBoard and output directories

- `--write True` creates a TensorBoard writer and removes any same-named log directory before writing.
- Most continuous algorithms write runs under `runs/{BriefEnvName}<timestamp>`.
- PPO-Discrete writes under `runs/{CP-v1-or-LLd-v2}<timestamp>`.
- SAC-Discrete writes under `runs/SACD_{CPV1-or-LLdV2}<timestamp>`.
- View logs from the algorithm directory with:

```bash
tensorboard --logdir runs
```

## Checkpoint guidance

All checkpoint paths are relative to the algorithm directory and require an existing `model/` directory. Save intervals are step-based, but many continuous/off-policy launchers pass `int(total_steps/1000)` into `save()`, so `ModelIdex` usually means thousands of steps, not raw steps.

| Algorithm | Save/load file pattern | `ModelIdex` interpretation |
|---|---|---|
| PPO-Discrete | `model/ppo_actor{episode}.pth`, `model/ppo_critic{episode}.pth` | Raw `total_steps`; default play index is `300000`. |
| PPO-Continuous | `model/{BriefEnvName}_actor{timestep}.pth`, `model/{BriefEnvName}_q_critic{timestep}.pth` | Thousands of steps from `int(total_steps/1000)`; default parser index is `100`. |
| DDPG | `model/{BriefEnvName}_actor{timestep}.pth`, `model/{BriefEnvName}_q_critic{timestep}.pth` | Thousands of steps; default parser index is `100`. |
| TD3 | `model/{BriefEnvName}_actor{timestep}.pth`, `model/{BriefEnvName}_q_critic{timestep}.pth` | Thousands of steps; default parser index is `30`. |
| SAC-Discrete | `model/sacd_actor_{timestep}_{BriefEnvName}.pth`, `model/sacd_critic_{timestep}_{BriefEnvName}.pth` | Thousands of steps; default parser index is `50`. |
| SAC-Continuous | `model/{BriefEnvName}_actor{timestep}.pth`, `model/{BriefEnvName}_q_critic{timestep}.pth` | Thousands of steps; parser default is `100`, while some README play examples use lower trained-checkpoint indexes. |

## Optional dependency and backend caveats

- Box2D (`gymnasium[box2d]`) is needed for LunarLander and BipedalWalker variants. It was not installed or verified in the minimum CPU scope.
- MuJoCo (`gymnasium[mujoco]` or compatible MuJoCo) is needed for Humanoid and HalfCheetah. It was not installed or verified in the minimum CPU scope.
- CUDA is an acceleration option only. The launchers default to `--dvc cuda`, but CPU-safe commands must explicitly pass `--dvc cpu`.
- Long RL training is stochastic. Passing import, object-construction, or zero-step checks proves wiring compatibility, not final score quality.
