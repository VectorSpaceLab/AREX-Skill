# Built-in Environment Troubleshooting

Use this reference to classify failures by environment family, dependency extra, registry state, and render mode before changing agent code or installing broad extras.

## Quick Triage

```python
import gymnasium as gym

env_id = "LunarLander-v3"
try:
    spec = gym.spec(env_id)
except Exception as exc:
    print("not registered", type(exc).__name__, exc)
else:
    print("registered", spec.id, spec.entry_point, spec.kwargs)
    try:
        env = gym.make(env_id)
        obs, info = env.reset(seed=0)
        obs, reward, terminated, truncated, info = env.step(env.action_space.sample())
        env.close()
        print("make/reset/step ok")
    except Exception as exc:
        print("registered but cannot run", type(exc).__name__, exc)
```

Interpretation:

- Not registered: wrong ID, missing namespace/plugin registration, or a third-party package has not been imported/installed.
- Registered but cannot run: optional backend dependency, ROM/license, renderer, or compatibility placeholder problem.
- Runs without rendering but fails with `human` or `rgb_array`: renderer/display/media dependency problem, not necessarily an environment logic problem.

## Env ID and Registry Problems

Symptoms:

- `NameNotFound`, `NamespaceNotFound`, or similar errors from `gym.spec(...)` / `gym.make(...)`.
- Old IDs such as `Taxi-v3` fail when current registry has `Taxi-v4`.
- `ALE/...` IDs missing in a base install.

Fixes:

- Use `gym.pprint_registry()` or `sorted(gym.registry)` to inspect actual IDs.
- Use exact versioned IDs such as `CartPole-v1`, `Taxi-v4`, `LunarLander-v3`, and `Ant-v5`.
- Include namespaces exactly, such as `tabular/Blackjack-v0`, `phys2d/CartPole-v1`, or plugin-provided `ALE/...` IDs.
- For third-party packages, install/import the package that registers its envs before calling `gym.make(...)`.

## Missing `pygame` for Rendering

Typical families:

- Classic Control `human` / `rgb_array` rendering.
- Toy Text graphical rendering.
- Box2D rendering.
- Some JAX/phys2d rendering surfaces.

Symptoms:

- `DependencyNotInstalled` mentioning `pygame` or `pygame-ce`.
- Rendering fails only when `render_mode` is set.

Fixes:

- Classic Control rendering: `pip install "gymnasium[classic-control]"`.
- Toy Text rendering: `pip install "gymnasium[toy-text]"`.
- Box2D rendering: install Box2D extra as described below.
- In headless CI, prefer `render_mode="rgb_array"` and set `SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy` when needed.

## Box2D Failures

Symptoms:

- `DependencyNotInstalled` mentioning Box2D.
- Build errors around SWIG when installing Box2D bindings.
- `LunarLander-v3`, `BipedalWalker-v3`, or `CarRacing-v3` spec exists but `gym.make(...)` fails.

Fixes:

```bash
pip install swig
pip install "gymnasium[box2d]"
```

Notes:

- Verify with `gym.spec("LunarLander-v3")` first, then one non-rendered reset/step.
- Add rendering only after the backend imports successfully.
- Do not install MuJoCo or Atari extras for Box2D failures.

## MuJoCo Failures

Symptoms:

- `DependencyNotInstalled: MuJoCo is not installed`.
- OpenGL/window errors when rendering.
- `v2` or `v3` MuJoCo IDs raise an import error about `gymnasium-robotics`.
- Continuous-action shape errors during `step()`.

Fixes:

```bash
pip install "gymnasium[mujoco]"
```

Rendering backend examples:

```bash
MUJOCO_GL=egl python your_script.py
MUJOCO_GL=osmesa python your_script.py
```

Notes:

- Prefer `v5` IDs for new work, such as `Ant-v5` or `HalfCheetah-v5`.
- Use `v4` only when a benchmark or saved result requires it.
- `v2`/`v3` compatibility placeholders point to `gymnasium-robotics` because they depended on older `mujoco-py` behavior.
- Match continuous action shapes exactly; route detailed action-space shape debugging to `../spaces-data/SKILL.md`.

## Atari/ALE and ROM Failures

Symptoms:

- `gym.spec("ALE/Pong-v5")` fails in a base install.
- ALE package imports but a game fails because the ROM is missing.
- License/ROM acceptance errors.

Fixes:

```bash
pip install "gymnasium[atari]"
```

Then follow the installed ALE package's ROM and license process. Keep these as separate checks:

1. Python package installed and importable.
2. ALE environments registered in Gymnasium.
3. Specific ROM available and licensed.
4. Render/preprocessing mode supported for the chosen env.

Notes:

- Base Gymnasium verified without ALE IDs registered, so missing `ALE/...` IDs are expected until the Atari plugin is installed and registered.
- Atari preprocessing wrappers and video recording may require additional dependencies; route wrapper/recording details to `../wrappers-recording/SKILL.md`.

## Missing `moviepy` or Video Helpers

Symptoms:

- Importing or using video helpers fails with `moviepy is not installed`.
- `RecordVideo` setup fails after the environment itself works.

Fix:

```bash
pip install "gymnasium[other]"
```

Notes:

- `moviepy` is not needed for ordinary `env.render()` calls.
- `RecordVideo` needs an image-returning render mode such as `rgb_array`; route ordering and trigger details to `../wrappers-recording/SKILL.md`.

## Old Gym Compatibility Placeholders

Symptoms:

- `GymV21Environment-v0` or `GymV26Environment-v0` raises an import error saying to install `shimmy[gym-v21]` or `shimmy[gym-v26]`.
- Old Gym code returns `(obs, reward, done, info)` or calls `env.seed(...)`.

Fixes:

```bash
pip install "shimmy[gym-v21]"
pip install "shimmy[gym-v26]"
```

- Use Shimmy only for compatibility with old Gym environments.
- For migrating user code to Gymnasium's current API, route to `../environment-api/SKILL.md`.

## Action Mask Misuse

Symptoms:

- `KeyError: 'action_mask'` on a discrete environment.
- Masked policy uses a stale mask after stepping.
- Code assumes masks come from `action_space` rather than `info`.

Fixes:

- Use `mask = info.get("action_mask")` unless the environment is known to expose masks.
- Refresh the mask after every `step()`.
- For Taxi, `env.action_space.sample(mask)` is the simplest valid random-action path.
- Fall back to normal sampling or a task-specific validity check when no mask is present.

## Decision Checklist

Before installing or changing code, answer:

1. Is the ID registered exactly as written?
2. Is the failure at `gym.spec`, `gym.make`, `reset/step`, `render`, or video recording?
3. Which family owns the ID: Classic Control, Toy Text, Box2D, MuJoCo, Atari/ALE, tabular, phys2d, or third-party?
4. What is the smallest extra for that family?
5. Is the requested feature actually recording/vectorization/custom env/space design rather than built-in environment selection?
