# Environment workflows

## 1. Install without confusing code readiness with data readiness

Use an isolated Python 3.11 environment when possible. The public installation
recipe is:

```bash
conda create -c conda-forge -n robocasa python=3.11
conda activate robocasa
# Install the public robosuite dependency (the release requires >=1.5.2).
# Then, from a RoboCasa checkout or a released source tree:
pip install -e .
```

RoboCasa's package metadata pins the critical compatibility versions to NumPy
2.2.5 and MuJoCo 3.3.1 and requires the usual simulation/data dependencies,
including Gymnasium, h5py, imageio, OpenCV, and LeRobot 0.3.3. Install
`robosuite` separately because it is an external dependency rather than a
RoboCasa `install_requires` entry. Confirm with:

```bash
python -c 'import robocasa, robosuite, mujoco, numpy, gymnasium; print(robocasa.__version__, robosuite.__version__, mujoco.__version__, numpy.__version__, gymnasium.__version__)'
python path/to/check_install.py --json
```

`import robocasa` must pass the exact MuJoCo/NumPy assertions and the robosuite
minimum-version check. If import fails, fix versions before investigating
assets or rendering.

The public setup sequence also provides:

```bash
python -m robocasa.scripts.setup_macros
python -m robocasa.scripts.download_kitchen_assets
```

The first command creates local macro configuration; the second is an explicit,
interactive download of roughly 10 GB and is not part of a safe diagnostic. Do
not run it merely to check imports. The full fixture/object/texture download is
an opt-in prerequisite for reset, task execution, and complete rendering.

## 2. Safe package/backend/asset diagnosis

From any current working directory, run the bundled helper first:

```bash
python path/to/check_install.py --help
python path/to/check_install.py --json
```

The helper never downloads and reports:

- import status and versions for RoboCasa, robosuite, MuJoCo, NumPy,
  Gymnasium, h5py, and LeRobot;
- whether the optional MimicGen package is present;
- the number of registered kitchen environments when RoboCasa imports;
- representative fixture/object/texture asset checks without claiming that a
  partial tree is complete;
- display, EGL, OSMesa, and `MUJOCO_GL` signals for rendering.

Use `--require-assets` only when a reset is an acceptance requirement. Use
`--probe-constructor` for a bounded constructor-only check; it deliberately does
not call `reset()` or download anything. Constructor success must not be
reported as a complete simulation pass.

## 3. Construct a lower-level environment

Use `create_env` for the RoboCasa convenience defaults and split mapping:

```python
from robocasa.utils.env_utils import create_env

env = create_env(
    env_name="PickPlaceCounterToCabinet",
    robots="PandaOmron",
    split="pretrain",
    seed=0,
    camera_names=[
        "robot0_agentview_left",
        "robot0_agentview_right",
        "robot0_eye_in_hand",
    ],
    camera_widths=128,
    camera_heights=128,
    camera_depths=False,
    horizon=100,
)
try:
    raw_obs = env.reset()  # requires the downloaded task assets
    raw_obs, reward, done, info = env.step(env.action_space.sample())
finally:
    env.close()
```

Do not add `use_camera_obs=False` or `has_offscreen_renderer=False` to this
call. The helper already emits both keys and Python raises a duplicate-key
`TypeError`. To take full control of renderer flags, construct through the
lower-level robosuite API with an explicit controller configuration instead of
trying to override helper-owned values.

For a package/API-only probe when assets are incomplete, avoid reset:

```python
from robocasa.utils.env_utils import create_env

env = create_env("PickPlaceCounterToCabinet", split="pretrain", camera_names=[])
try:
    print(type(env).__name__, env.horizon, env.ignore_done)
finally:
    env.close()
```

This checks controller and environment construction only. The first missing
fixture/object XML during a later reset is an external data failure, not proof
that Python dependencies are broken.

## 4. Use the Gymnasium interface

Import RoboCasa before asking Gymnasium for the ID:

```python
import gymnasium as gym
import robocasa

env = gym.make(
    "robocasa/PickPlaceCounterToCabinet",
    split="pretrain",  # or "target" / "all"
    seed=0,
)
obs, info = env.reset()
try:
    action = env.action_space.sample()
    action["action.base_motion"][:] = 0.0
    obs, reward, terminated, truncated, info = env.step(action)
finally:
    env.close()
```

The wrapper constructor resets the underlying environment immediately. Thus
this recipe needs assets at `gym.make` time, not only at the explicit
`env.reset()`. Its constructor default `split="test"` is incompatible with
`create_env`; always pass a supported split.

Use the exact dict keys and shapes from [api-reference.md](api-reference.md).
For a flat 12-value policy output, call `convert_action` before `step`:

```python
import numpy as np
from robocasa.utils.env_utils import convert_action

flat = np.zeros(12, dtype=np.float32)
action = convert_action(flat)
obs, reward, terminated, truncated, info = env.step(action)
```

Do not pass a flat array to the Gym wrapper, and do not pass a dict containing
raw robosuite keys such as `robot0_right` to the wrapper. A mismatched dict is
rejected after conversion with an unprocessed-actions assertion or a missing
key/shape error.

## 5. Seed and determinism checks

Set `seed=<integer>` in `create_env` or `gym.make` for a repeatable initial
sampling request. Use `seed=None` for an unseeded run. The `Kitchen` source uses
its seeded RNG for layout/style, placements, and related camera randomization;
set `randomize_cameras=False` when comparing camera configuration.

For the Gym wrapper, `reset(seed=n)` replaces the inner environment RNG with
`numpy.random.default_rng(n)` before resetting. It returns the Gymnasium pair
`(observation, info)`. This wrapper-specific reset behavior is distinct from
constructor-time `seed=n`; use one documented convention consistently in a
comparison.

A reduced deterministic probe should:

1. create two copies of one representative task with the same seed;
2. disable camera randomization and use headless, no-camera observations if the
   asset tree supports it;
3. reset both and compare layout/style IDs, fixture/object placement keys and
   positions, and selected observations with a tolerance;
4. close both environments even when the comparison fails.

The repository's `tests/test_env_determinism.py` performs this comparison across
nearly all kitchen environments and additional generated-texture/camera cases.
That full test is deferred native evidence because it is expensive and needs
complete fixture/object assets; it is not a default quick check. A reduced
single-task test is the appropriate acceptance candidate.

## 6. Render and save a bounded random rollout

`run_random_rollouts` requires a Gymnasium environment, samples its action
space, zeros `action.base_motion` to avoid excessive jitter, and returns an
`info` dictionary containing `num_success_rollouts`. Use an explicit parent
folder for video output:

```python
from robocasa.utils.env_utils import run_random_rollouts

result = run_random_rollouts(
    env,
    num_rollouts=2,
    num_steps=50,
    video_path="rollouts/random_probe.mp4",
    camera_name="robot0_agentview_center",
)
print(result["num_success_rollouts"])
```

`num_steps` is the safety bound. The helper stops an individual rollout early
when `info["success"]` is true, but otherwise does not use a model-based
termination policy. The underlying helper sets `ignore_done=True`; keep the
outer bound even if `terminated` is observed.

The helper calls `env.sim.render(height=512, width=768, camera_name=...)` for
video frames. Pick a camera that exists in the constructed model. A bare
filename such as `random_probe.mp4` is unsafe for this helper because it calls
`os.makedirs(os.path.dirname(video_path), ...)`; use `rollouts/random_probe.mp4`
or an absolute path with a parent directory.

For interactive rendering, set `render_onscreen=True` only when a viewer/display
is available. For headless RGB observations, retain the helper default
`render_onscreen=False` and verify the EGL/OSMesa signals first. A renderer
library signal does not prove a reset will work if fixture XML or object meshes
are missing.

## 7. Close and classify results

Always call `close()` in `finally`. Report results in separate categories:

- **package/API ready**: imports, exact gates, signatures, and optionally a
  constructor-only probe passed;
- **reset/step ready**: a representative task reset and step passed with the
  required external XML/object assets;
- **render/video ready**: the selected display/offscreen backend and camera
  produced frames;
- **optional integration ready**: MimicGen, input devices, or dataset playback
  were separately installed and verified.

Never collapse these categories into a single “installed” claim.
