# Environment Wrappers

## When to read

Read this when a task involves Gym ids, Atari preprocessing, vectorized environments, frame stacking, normalization, time-limit handling, or optional simulator packages.

## `make_env` behavior

`make_env(env_id, seed, rank, log_dir, allow_early_resets)` returns a thunk that creates one Gym environment and applies wrappers:

- `dm.<domain>.<task>` ids route to DeepMind Control Suite through `dmc2gym.make(domain_name=domain, task_name=task)` and `ClipAction`.
- Other ids route to `gym.make(env_id)`.
- Atari environments receive `NoopResetEnv`, `MaxAndSkipEnv`, optional `EpisodicLifeEnv`, `FireResetEnv`, `WarpFrame(84, 84)`, `ClipRewardEnv`, and channel-first transposition.
- TimeLimit environments receive `TimeLimitMask`, which adds `info["bad_transition"] = True` when an episode ends due to the time limit.
- If `log_dir` is not `None`, each worker gets a monitor file under `<log_dir>/<rank>`.

## `make_vec_envs` behavior

`make_vec_envs(env_name, seed, num_processes, gamma, log_dir, device, allow_early_resets, num_frame_stack=None)` builds a vectorized environment:

- `SubprocVecEnv` is used when `num_processes > 1`; otherwise `DummyVecEnv` is used.
- Vector observation spaces (`len(shape) == 1`) are wrapped with `VecNormalize`; reward normalization uses `gamma` when provided.
- `VecPyTorch` converts NumPy observations and rewards to torch tensors.
- Image observations are frame-stacked. If `num_frame_stack` is omitted and the observation is 3D, four frames are stacked.

## Observation/action expectations

- `Policy` uses `CNNBase` for 3D observations and `MLPBase` for 1D observations.
- Non-Atari pixel observations with 3D shapes raise `NotImplementedError` unless a custom wrapper converts them into the Atari-style channel-first workflow.
- Discrete action spaces use categorical distributions; continuous Box action spaces use diagonal Gaussians.
- GAIL in the training loop asserts vector observations, so do not combine `--gail` with Atari/image observations without code changes.

## Optional environment families

| Environment family | Signals | Extra requirements / cautions |
| --- | --- | --- |
| Atari | ids such as `PongNoFrameskip-v4` | Needs Gym Atari/ALE/ROM support compatible with the chosen Gym version. |
| MuJoCo | ids such as `Reacher-v2`, `HalfCheetah-v2` | Needs MuJoCo runtime/license/package support for the Gym version; use `--use-proper-time-limits`. |
| PyBullet | ids containing Bullet or PyBullet environments | Needs `pybullet`/`pybullet_envs`; some Gym versions break old `pybullet_envs` registry assumptions. |
| DeepMind Control Suite | `dm.<domain>.<task>` | Needs `dm_control` and `dmc2gym`; the wrapper uses `ClipAction`. |

## Validation without expensive runs

Use safe checks before launching training:

```bash
python main.py --help
python enjoy.py --help
python scripts/build_training_command.py --preset mujoco-ppo --env-name Reacher-v2 --no-cuda
```

Then, if the user explicitly wants execution, start with very small `--num-env-steps`, one process for continuous-control debugging, and a disposable log directory.
