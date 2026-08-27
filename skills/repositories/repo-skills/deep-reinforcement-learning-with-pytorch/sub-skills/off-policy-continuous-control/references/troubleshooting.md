# Continuous-Control Troubleshooting

Use this reference for DDPG/SAC/TD3 device selection, action bounds, checkpoint playback, Gym deprecations, Box2D, pygame, rendering, and NumPy compatibility.

## CUDA versus CPU device selection

Source pattern:

```python
device = 'cuda' if torch.cuda.is_available() else 'cpu'
```

Implications:

- CUDA is optional. CPU is a valid fallback for inspection, small smokes, and most debugging.
- The scripts allocate models and many tensors on `device`; SAC BipedalWalker also stores replay-buffer tensors on that device.
- If a CUDA checkpoint must run on CPU, patch `torch.load(path)` to `torch.load(path, map_location=device)` or `map_location='cpu'` before `load_state_dict`.
- If CUDA is visible but not desired, set `CUDA_VISIBLE_DEVICES=` for the process or patch the script to force `device = 'cpu'`.
- Do not use a CPU-only import as evidence of GPU performance; it only proves functional compatibility.

Quick diagnostic from this sub-skill:

```bash
python scripts/continuous_control_compat_report.py --env Pendulum-v1
```

## Action normalization and bounds

Symptoms:

- `AssertionError` or Box bound complaints from `env.step(...)`.
- BipedalWalker actions have the wrong shape.
- SAC actions stay in `[-1, 1]` when the environment expects a different Box range.

Checks:

1. Inspect `env.action_space.shape`, `low`, and `high` with the compatibility helper.
2. DDPG/TD3 actors already output `tanh * max_action`; training then clips noise-perturbed actions to `env.action_space.low/high`.
3. SAC variants rely on a normalized action wrapper. On modern Gym, implement:

```python
def action(self, action):
    ...

def reverse_action(self, action):
    ...
```

instead of only legacy `_action` and `_reverse_action` methods. Otherwise `ActionWrapper.step()` can raise `NotImplementedError` or skip the intended scaling.
4. Keep checkpoint env dimensions consistent. Pendulum has a scalar action; BipedalWalker has a 4-D action.

## Deprecated Gym environment IDs

Repo defaults include:

- `Pendulum-v0`
- `BipedalWalker-v2`

Modern substitutes to prefer:

- `Pendulum-v1`
- `BipedalWalker-v3`

If `gym.make(...)` raises `DeprecatedEnv`, update the command-line `--env_name` or script default. Remember that TD3/DDPG checkpoint directories include the env name, so changing the env ID changes the expected path.

If using Gymnasium or newer Gym APIs, adapt old calls:

```python
state = env.reset()
next_state, reward, done, info = env.step(action)
```

into version-aware handling of tuple reset returns and terminated/truncated step returns.

## Checkpoint path and load failures

Common errors:

- `FileNotFoundError` for `.pth` files.
- size mismatch in actor/critic layers.
- CUDA deserialization error on a CPU process.
- successful actor load but missing target or critic files in TD3.

Fix sequence:

1. Identify algorithm and env ID.
2. Use `references/checkpoint-playback.md` to list expected filenames.
3. Print the current working directory before running the script; all source paths are relative.
4. Check whether env modernization changed the checkpoint directory name.
5. Add `map_location=device` to `torch.load` when moving across CPU/CUDA.
6. For SAC single-Q, patch the broken `load()` method before playback.
7. For SAC `test_agent.py`, inspect Q2 file handling; the source can save/load Q2 from the Q1 filename.

Do not treat a missing checkpoint as permission to launch a long training job without a user-approved budget.

## Box2D, pygame, and BipedalWalker

BipedalWalker requires Box2D support in addition to Gym. Failure surfaces include:

- `gym.error.DependencyNotInstalled: box2D is not installed`
- import errors mentioning `Box2D`, `box2d-py`, or `pygame`
- renderer/display errors when calling `env.render()`
- missing shared libraries for SDL/pygame in headless containers

Fix sequence:

1. Run the compatibility helper with `--env BipedalWalker-v3`.
2. Install a compatible Box2D package such as `box2d-py` and pygame in the active environment.
3. Prefer non-rendered smoke checks first; render only after environment creation and one random-action step work.
4. In headless sessions, skip or patch `env.render()` unless a virtual display or compatible pygame backend is configured.

## NumPy deprecated aliases

DDPG and TD3 source loops use `np.float(done)`. NumPy versions that removed deprecated aliases will fail. Replace with:

```python
float(done)
```

or, when a NumPy scalar is required:

```python
np.float64(done)
```

## Argparse boolean and float quirks

Several scripts use `type=bool` for flags such as `--render`, `--load`, or `--seed`. In argparse, passing `--render False` can still evaluate truthy because non-empty strings convert unexpectedly. Prefer omitting the flag for false, passing known true values only when tested, or patching to `action='store_true'`.

Some SAC arguments declare `type=int` for float defaults such as learning rate or gamma. Patch those parser types to `float` before command-line tuning.
