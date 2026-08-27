# Cross-Cutting Troubleshooting

Use this reference for problems that affect multiple DRL-Pytorch workflows before switching to a sub-skill-specific troubleshooting page.

## Default CUDA fails on a CPU-only runtime

**Symptoms**

- `AssertionError: Torch not compiled with CUDA enabled`
- `RuntimeError: Found no NVIDIA driver`
- command hangs or fails after printing parsed args with `dvc='cuda'`

**Cause**

Many launchers default to CUDA. CPU is a full substitute for import, parser, toy-env, and zero-step sanity checks.

**Recovery**

- For launchers with `--dvc`, pass `--dvc cpu`.
- For Atari DQN, pass `--device cpu`.
- For PER launchers without `--dvc`, use `CUDA_VISIBLE_DEVICES=""` for CPU smoke checks.
- Only claim CUDA verified after the active runtime passes a torch CUDA availability and tiny allocation check.

## Optional Gymnasium environments are missing

**Symptoms**

- `DependencyNotInstalled: Box2D is not installed`
- MuJoCo import errors when selecting Humanoid/HalfCheetah
- Atari ALE/ROM errors when selecting NoFrameskip environments

**Cause**

The base dependency set covers CartPole, Pendulum, and CliffWalking, not every Gymnasium extra.

**Recovery**

- Switch to a base smoke environment (`CartPole-v1`, `Pendulum-v1`, or `CliffWalking-v0`) when validating algorithm code.
- Install only the specific extra required by the selected workflow: Box2D for LunarLander/BipedalWalker, MuJoCo for Humanoid/HalfCheetah, Atari extras and accepted ROMs for NoFrameskip.
- Do not silently download ROMs or install large optional stacks when the user only requested a CPU-safe smoke.

## Imports resolve the wrong sibling module

**Symptoms**

- `ModuleNotFoundError: utils`
- importing one algorithm after another returns classes from the first directory
- a class exists in the source tree but import picks the wrong `DQN.py`, `PPO.py`, or `utils.py`

**Cause**

DRL-Pytorch uses standalone directories with repeated short module names. Python caches modules by short name.

**Recovery**

- Run original launchers from their own algorithm directory in a checkout.
- For diagnostics, use bundled smoke scripts; they isolate `sys.path` and purge colliding module names between algorithms.
- If writing custom inspection code, add only one algorithm directory to `sys.path` at a time and remove colliding module names from `sys.modules` before switching.

## Checkpoint load fails

**Symptoms**

- `FileNotFoundError` for a `.pth` or `.npy` file under `model/`
- loading the wrong actor/critic or Atari checkpoint
- `Missing key(s)` or `Unexpected key(s)` when loading a checkpoint

**Cause**

Checkpoints are relative to the algorithm working directory and filename patterns differ by workflow. Binary checkpoints are not bundled in this skill.

**Recovery**

- Confirm the current working directory is the algorithm directory in the user checkout.
- Match `EnvIdex`, algorithm flags, brief environment names, and `ModelIdex` to the filename pattern in `references/algorithm-index.md` and the owning sub-skill reference.
- Do not mix actor/critic files across DDPG/TD3/SAC/PPO variants.
- Treat pretrained checkpoint playback as a real repo execution task, not a safe smoke, because it reads binary weights and often renders environments.

## TensorBoard or `runs/` issues

**Symptoms**

- `ModuleNotFoundError: tensorboard`
- `runs/` is missing or unexpectedly overwritten
- TensorBoard shows old runs after a new command

**Cause**

`--write True` enables `SummaryWriter`; some launchers delete an existing run path before writing. Q-learning enables writer behavior in source defaults.

**Recovery**

- Install TensorBoard only when logging is requested.
- Use `--write False` for smoke checks.
- Run `tensorboard --logdir runs` from the algorithm directory whose logs you want.
- Warn before deleting or overwriting run directories in a user's checkout.

## Training results are stochastic or slow

**Symptoms**

- reward curves vary by seed;
- quick tests show poor scores;
- Atari/ASL/MuJoCo jobs run for a long time;
- GPU memory or process usage grows during ASL.

**Cause**

The repository implements research training loops with stochastic environments, replay/trajectory buffers, and long default step counts.

**Recovery**

- Use zero-step or bundled diagnostic scripts for validation.
- Set explicit seeds and record hyperparameters for actual training.
- Treat full training, rendering, Atari ROM execution, EnvPool jobs, and benchmark recovery as user-approved expensive actions.
- Evaluate only with the algorithm's own `evaluate_policy` semantics and enough episodes for the requested confidence.
