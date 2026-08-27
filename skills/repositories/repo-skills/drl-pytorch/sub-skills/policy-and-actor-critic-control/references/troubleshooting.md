# Policy-Control Troubleshooting

Use this reference for PPO, DDPG, TD3, SAC-Discrete, and SAC-Continuous failures. Start with CPU-safe zero-step commands and the bundled smoke script before long training.

## Default CUDA on CPU-only runtime

**Symptoms**

- `RuntimeError: Found no NVIDIA driver on your system`.
- `AssertionError: Torch not compiled with CUDA enabled`.
- A launcher fails before training even though the environment is CPU-only.

**Cause**

Every policy-control launcher defaults `--dvc cuda`. Several launchers convert this string to `torch.device` immediately after parsing.

**Recovery**

- Pass `--dvc cpu` explicitly:

```bash
python main.py --dvc cpu --EnvIdex 0 --write False --render False --Max_train_steps 0
```

- Use CUDA only after confirming a CUDA-capable PyTorch build and visible GPU.
- The minimum verified scope is CPU; CUDA acceleration is optional and must not be treated as verified unless checked in the current runtime.

## Optional Box2D missing

**Symptoms**

- Creating `LunarLander-v2`, `LunarLanderContinuous-v2`, `BipedalWalker-v3`, or `BipedalWalkerHardcore-v3` fails.
- Errors mention Box2D, `box2d-py`, `b2World`, SWIG, or missing compiled wheels.

**Cause**

These environments are not part of base Gymnasium. They require the Box2D extra.

**Recovery**

- For a CPU-safe algorithm wiring check, switch to `EnvIdex 0` (`CartPole-v1` for discrete, `Pendulum-v1` for continuous).
- If the task specifically needs Box2D, install a compatible `gymnasium[box2d]` stack in the active runtime and then re-run the desired environment creation check.
- Do not claim Box2D workflows are verified from a Pendulum or CartPole smoke alone.

## Optional MuJoCo missing

**Symptoms**

- `Humanoid-v4` or `HalfCheetah-v4` fails during `gym.make`.
- Errors mention MuJoCo, `mujoco`, XML assets, or environment registration/import failures.

**Cause**

MuJoCo tasks require `gymnasium[mujoco]` or a compatible MuJoCo installation. The minimum CPU scope did not install or verify MuJoCo.

**Recovery**

- Use `EnvIdex 0` (`Pendulum-v1`) for a base continuous-control check.
- Install/check the MuJoCo dependency stack only when the task truly targets Humanoid or HalfCheetah.
- Keep MuJoCo failures dependency-gated rather than treating them as PPO/DDPG/TD3/SAC API failures.

## Wrong `EnvIdex` or action-space mismatch

**Symptoms**

- `AttributeError: 'Discrete' object has no attribute 'shape'`.
- `AttributeError: 'Box' object has no attribute 'n'`.
- Tensor/action shapes do not match after switching an environment.
- A continuous algorithm is asked to run `CartPole-v1`, or a discrete algorithm is asked to run `Pendulum-v1`.

**Cause**

The discrete launchers read `env.action_space.n`; continuous launchers read `env.action_space.shape[0]` and `env.action_space.high[0]`. The same numeric `EnvIdex` means different environments in discrete and continuous directories.

**Recovery**

- Discrete PPO/SAC: use `EnvIdex 0` for `CartPole-v1`, `1` for `LunarLander-v2`.
- Continuous PPO/DDPG/TD3/SAC: use `EnvIdex 0` for `Pendulum-v1`, `1` for `LunarLanderContinuous-v2`, `2` for `Humanoid-v4`, `3` for `HalfCheetah-v4`, `4` for `BipedalWalker-v3`, `5` for `BipedalWalkerHardcore-v3`.
- If the desired environment is not in the launcher's map, adapt the launcher only after checking action-space type and state/action dimensions.

## Checkpoint not found or wrong model index

**Symptoms**

- `FileNotFoundError` for a `.pth` file under `model/`.
- Play mode starts with `--Loadmodel True` but cannot find actor/critic weights.
- A checkpoint exists but the algorithm looks for a differently named file.

**Cause**

Checkpoint names differ by workflow and are relative to the algorithm working directory. Several launchers save `int(total_steps/1000)` while PPO-Discrete saves raw step counts.

**Recovery**

- Run play commands from the same algorithm directory whose `model/` contains the checkpoint.
- Match both actor and critic file names:
  - PPO-Discrete: `ppo_actor{ModelIdex}.pth` and `ppo_critic{ModelIdex}.pth`.
  - PPO-Continuous/DDPG/TD3/SAC-Continuous: `{BriefEnvName}_actor{ModelIdex}.pth` and `{BriefEnvName}_q_critic{ModelIdex}.pth`.
  - SAC-Discrete: `sacd_actor_{ModelIdex}_{BriefEnvName}.pth` and `sacd_critic_{ModelIdex}_{BriefEnvName}.pth`.
- Check whether `ModelIdex` means raw steps or thousands of steps for the chosen algorithm in [algorithm-workflows.md](algorithm-workflows.md).

## Tensor shape and dtype problems

**Symptoms**

- `mat1 and mat2 shapes cannot be multiplied`.
- `Index tensor must have the same number of dimensions as input tensor`.
- Replay-buffer assignment fails for action shape or dtype.
- Continuous action is outside environment bounds.

**Cause**

The agents expect exact state/action conventions:

- PPO-Discrete `select_action` expects a one-dimensional NumPy state and stores integer actions in shape `(T_horizon, 1)`.
- PPO-Continuous stores action vectors and per-action log probabilities with shape `(T_horizon, action_dim)`.
- DDPG/TD3 store environment-scale float action vectors.
- SAC-Discrete stores action indices as long tensors with shape `(max_size, 1)`.
- SAC-Continuous stores normalized actions in `[-1, 1]`; the launcher scales them to environment bounds with `Action_adapter` and maps warmup samples back with `Action_adapter_reverse`.

**Recovery**

- Recompute `state_dim`, `action_dim`, and `max_action` from the selected environment before constructing the agent.
- For continuous agents, keep NumPy action arrays shaped `(action_dim,)`, not scalar floats unless `action_dim == 1` and the code path explicitly accepts it.
- Do not mix utility modules between algorithm directories; each directory owns its own `utils.py`.
- Use the bundled smoke script to isolate imports and catch basic shape issues without training.

## Import collisions between algorithm directories

**Symptoms**

- Importing `PPO`, `SAC`, or `utils` succeeds once but later algorithms use the wrong utility classes.
- `ImportError` or missing attribute errors appear after checking multiple algorithm folders in one Python process.

**Cause**

The repository uses repeated short module names (`utils.py`, `PPO.py`) in sibling directories. Python caches modules by name.

**Recovery**

- Run each algorithm in a separate process or clear cached module names between imports.
- If writing a diagnostic, prepend only the target algorithm directory to `sys.path`, then remove `utils`, `PPO`, `DDPG`, `TD3`, `SACD`, and `SAC` from `sys.modules` after the check.
- The bundled smoke script implements this import isolation.

## Rendering or play hangs

**Symptoms**

- Command appears to run forever.
- Headless display errors occur.
- `--render True` never returns.

**Cause**

The play path is an infinite `while True` loop in each launcher. Rendering also needs a display backend, and `--Loadmodel True` needs existing checkpoints.

**Recovery**

- Do not use render mode for automated smoke checks.
- Use `--render False --Loadmodel False --Max_train_steps 0` for construction checks.
- If interactive play is required, confirm display support and checkpoint files first, then interrupt manually when finished.

## Long stochastic training or unstable scores

**Symptoms**

- Scores vary strongly across seeds.
- DDPG learns slowly or collapses.
- Zero-step checks pass but learning quality is poor.

**Cause**

RL training is stochastic and hyperparameter-sensitive. The repository itself notes DDPG instability and recommends TD3 as a refinement. Zero-step/import checks validate wiring only.

**Recovery**

- Treat `--Max_train_steps 0` as a wiring check, not a performance benchmark.
- For continuous off-policy tasks, prefer TD3 or SAC-Continuous when robustness matters.
- Increase `Max_train_steps` and keep TensorBoard logging for real experiments.
- Use multiple seeds for score claims. The launchers set torch seeds and increment environment reset seeds across episodes, but this does not make training deterministic across all hardware/backends.

## TensorBoard or output-directory surprises

**Symptoms**

- Previous logs disappear.
- Logs are not found from the current shell.
- Checkpoints or runs are created in an unexpected directory.

**Cause**

The launchers create/remove relative `runs/` directories when `--write True`, and create relative `model/` directories for checkpoints. Running from a different working directory changes where files land.

**Recovery**

- Run commands from the intended algorithm directory.
- Keep `--write False` during smoke checks.
- Use `tensorboard --logdir runs` from the algorithm directory that produced the logs.
