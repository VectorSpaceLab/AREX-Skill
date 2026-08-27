# CleanRL Algorithm Catalog

CleanRL organizes most runnable algorithms as one file per experiment script. Use this catalog to pick the smallest script family that matches the environment, backend, and user goal before building a command.

## Installed Baseline Facts

- Package version inspected: CleanRL `2.0.0b1`.
- Supported Python range from package metadata: `>=3.8,<3.11`.
- Base imports verified during extraction: `cleanrl`, `cleanrl_utils`, `torch`, `gym`, `gymnasium`, `tyro`, and `wandb`.
- Representative CPU help checks passed for `cleanrl/ppo.py`, `cleanrl/dqn.py`, and `cleanrl/c51.py`.
- Optional extras were not installed in the inspection environment; treat optional-backend commands as conditional.

## Family Selection Matrix

| Goal / environment | Preferred scripts | Default envs from script evidence | Extra/backends | Safe smoke candidate |
| --- | --- | --- | --- | --- |
| PPO classic control | `cleanrl/ppo.py` | `CartPole-v1`, `num_envs=4`, `total_timesteps=500000` | base install | `python cleanrl/ppo.py --num-envs 1 --num-steps 64 --total-timesteps 256 --no-cuda` |
| DQN / C51 classic control | `cleanrl/dqn.py`, `cleanrl/c51.py` | `CartPole-v1`, `learning_starts=10000`, `total_timesteps=500000` | base install | `python cleanrl/dqn.py --learning-starts 10 --total-timesteps 16 --buffer-size 10 --batch-size 4 --no-cuda`; same shape works for `c51.py` |
| PQN classic control | `cleanrl/pqn.py` | `CartPole-v1`, `num_envs=4`, `total_timesteps=500000` | base install plus current torch stack | `python cleanrl/pqn.py --num-envs 1 --num-steps 64 --total-timesteps 256 --no-cuda` |
| Atari PPO | `cleanrl/ppo_atari.py`, `cleanrl/ppo_atari_lstm.py`, `cleanrl/ppo_atari_multigpu.py` | `BreakoutNoFrameskip-v4`, `num_envs=8`, `total_timesteps=10000000` | `atari`; multigpu also needs `torchrun`/CUDA topology | `ppo_atari.py --num-envs 1 --num-steps 64 --total-timesteps 256` after ROM/backend setup |
| Atari value methods | `cleanrl/dqn_atari.py`, `cleanrl/c51_atari.py`, `cleanrl/rainbow_atari.py`, `cleanrl/sac_atari.py`, QDagger variants | Breakout or BeamRider NoFrameskip defaults; replay methods often `learning_starts=80000` | `atari`; JAX variants also `jax` | Replay smoke: `--learning-starts 10 --total-timesteps 16 --buffer-size 10 --batch-size 4` after ROM/backend setup |
| JAX classic / continuous | `dqn_jax.py`, `c51_jax.py`, `ddpg_continuous_action_jax.py`, `td3_continuous_action_jax.py` | CartPole for DQN/C51; Hopper for DDPG/TD3 | `jax`, and `mujoco` for continuous | Help-only first; tiny DQN/C51 mirrors classic replay flags if JAX is installed |
| EnvPool Atari PPO/PQN/RND | `ppo_atari_envpool.py`, `ppo_atari_envpool_xla_jax.py`, `ppo_atari_envpool_xla_jax_scan.py`, `ppo_rnd_envpool.py`, `pqn_atari_envpool.py`, `pqn_atari_envpool_lstm.py` | `Breakout-v5` or `MontezumaRevenge-v5`; RND default `total_timesteps=2000000000`, `num_envs=128` | `envpool`; XLA scripts also `jax`; Atari ROM/runtime constraints still apply | Use help checks first; smoke candidates from native tests use `--num-envs 8 --num-steps 6/32 --total-timesteps 256` |
| Continuous control PPO/DDPG/TD3/SAC/RPO | `ppo_continuous_action.py`, `ddpg_continuous_action.py`, `td3_continuous_action.py`, `sac_continuous_action.py`, `rpo_continuous_action.py` | `HalfCheetah-v4` or `Hopper-v4`; RPO default `total_timesteps=8000000` | `mujoco`; `dm_control` for `dm_control/...` env ids | PPO/RPO: `--num-envs 1 --num-steps 64 --total-timesteps 128`; replay methods need `learning_starts` below total timesteps |
| Procgen PPO/PPG | `ppo_procgen.py`, `ppg_procgen.py` | `starpilot`, `num_envs=64`, `total_timesteps=25000000` | `procgen` | Native smoke uses `--num-envs 1 --num-steps 64 --total-timesteps 256 --num-minibatches 2`; PPG adds `--n-iteration 1` |
| PettingZoo multi-agent Atari | `ppo_pettingzoo_ma_atari.py` | `pong_v3`, `num_envs=16`, `total_timesteps=20000000` | `pettingzoo`; multi-agent ALE and SuperSuit | `python cleanrl/ppo_pettingzoo_ma_atari.py --num-steps 32 --num-envs 6 --total-timesteps 256 --cuda False` |
| PPO-TrXL memory tasks | `cleanrl/ppo_trxl/ppo_trxl.py` | `MortarMayhem-Grid-v0`, `num_envs=32`, `total_timesteps=200000000` | `memory_gym` requirements; nested package metadata | Help-only first; reduce `--num-envs`, `--num-steps`, and `--total-timesteps` only after memory-gym is present |
| IsaacGym PPO | `cleanrl/ppo_continuous_action_isaacgym/ppo_continuous_action_isaacgym.py` | `Ant`, `num_envs=4096`, `total_timesteps=30000000` | IsaacGym task stack and usually NVIDIA GPU/CUDA | Do not propose CPU smoke; verify backend availability and route GPU issues to troubleshooting |

## Optional Dependency Matrix

| Extra / dependency set | Scripts that usually need it | Notes |
| --- | --- | --- |
| base install | `ppo.py`, `dqn.py`, `c51.py`, many help checks | Includes torch/gym/gymnasium/tyro/wandb in the inspected setup. |
| `atari` | `*_atari.py`, NoFrameskip envs, Atari QDagger/Rainbow/SAC | Includes ALE/AutoROM/shimmy/opencv; ROM license acceptance may be required before real runs. |
| `jax` | `*_jax.py`, XLA EnvPool scripts | JAX wheels are platform/CUDA-specific; CPU help may still fail if jaxlib is absent or incompatible. |
| `envpool` | `*_envpool*.py`, RND EnvPool, PQN EnvPool | EnvPool uses Gymnasium-style Atari v5 ids such as `Breakout-v5`; combine with JAX for XLA scripts. |
| `mujoco` | continuous control Gymnasium MuJoCo scripts | Required for `Hopper-v4`, `HalfCheetah-v4`, `Ant-v4`, etc.; rendering can need headless OpenGL setup. |
| `dm_control` | `dm_control/...` env ids in RPO/PPO continuous | Requires DM Control plus MuJoCo stack; use only when env id starts with `dm_control/`. |
| `procgen` | `ppo_procgen.py`, `ppg_procgen.py` | Native smoke candidates reduce envs/minibatches heavily. |
| `pettingzoo` | `ppo_pettingzoo_ma_atari.py` | This script uses argparse, not tyro; boolean flags use values such as `--cuda False`. |
| memory-gym requirements | `cleanrl/ppo_trxl/ppo_trxl.py` | Nested PPO-TrXL dependency set includes memory-gym/minigrid/einops; not part of base install. |
| IsaacGym stack | nested IsaacGym PPO script | Treat as specialized GPU simulator setup; not covered by base or standard extras. |

## Algorithm-Specific Gotchas

- Replay-buffer algorithms (`dqn*`, `c51*`, `rainbow_atari.py`, `ddpg*`, `td3*`, `sac*`) often do no learning before `--learning-starts`; tiny runs must lower `--learning-starts` below `--total-timesteps`.
- PPO-style on-policy scripts compute derived batch sizes from `--num-envs * --num-steps`; tiny runs need compatible `--num-minibatches` and `--total-timesteps`.
- Atari `NoFrameskip-v4` scripts and EnvPool `-v5` scripts are not interchangeable; choose the env id family that matches the script.
- `ppo_atari_multigpu.py` expects distributed launch semantics; do not replace `torchrun` with plain Python for actual multi-GPU tests.
- `ppo_rnd_envpool.py` is exploration-heavy and defaults to an enormous timestep budget; never run defaults as a smoke test.
- `rpo_continuous_action.py` is a PPO variant with `rpo_alpha`; smaller alpha values can be useful for selected MuJoCo/DM Control environments, but tuning belongs to experiment operations.
- `ppo_pettingzoo_ma_atari.py` exposes `--capture_video` with an underscore in the source argparse definition, unlike tyro scripts' kebab-case `--capture-video`.
- `--upload-model` depends on `--save-model` behavior and Hugging Face credentials/network; route details to evaluation-and-sharing.

## Evidence-Backed Smoke Shapes

These distilled smoke shapes come from repository-owned native checks, but are written here as self-contained patterns rather than runtime links to source tests:

- Classic control PPO: `--num-envs 1 --num-steps 64 --total-timesteps 256`.
- Classic DQN/C51: lower replay warmup, for example `--learning-starts 200 --total-timesteps 205`, or use the more conservative bundled helper shape.
- Atari PPO: reduce `--num-envs`, `--num-steps`, and `--total-timesteps`; only run after Atari dependencies and ROM setup are complete.
- Atari replay/QDagger/Rainbow/SAC: `--learning-starts 10 --total-timesteps 16 --buffer-size 10 --batch-size 4` after Atari setup.
- Continuous control: Hopper/DM Control smoke commands need MuJoCo or DM Control installed and reduced rollout or replay-start settings.
- Procgen: one env, 64 steps, 256 timesteps, and small minibatch settings; PPG also needs a reduced iteration count.
- EnvPool: 8 envs, small rollout lengths, and 256 timesteps for PPO/RND/XLA scan variants, with EnvPool/JAX installed as needed.
- PettingZoo: 6 envs, 32 steps, and 256 timesteps using argparse boolean syntax.

## Use the Bundled Inspector

Run the inspector when a script is unfamiliar:

```bash
python sub-skills/training-scripts/scripts/inspect_cleanrl_script.py cleanrl/dqn.py --format markdown
```

The inspector parses source with `ast`; it does not import the script or optional extras. Use it to confirm default env ids, tracking flags, save/upload flags, replay settings, and tyro/argparse style before crafting a command.
