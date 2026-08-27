# Quickstart and Installation

## When to read

Read this when you need a fresh robosuite install, a minimal import check, or a safe first environment smoke before choosing a deeper sub-skill.

## Package identity

- Distribution name: `robosuite`
- Import name: `robosuite`
- Verified package version for this skill: `1.5.2`
- Core backend: MuJoCo Python binding (`mujoco>=3.3.0,<3.10` in the package metadata)
- Python support: Python 3 according to package metadata; Python 3.10 was used for skill-time inspection.

## Install paths

### From PyPI

```bash
python -m pip install robosuite
```

### From a local checkout

```bash
python -m pip install -e .
```

The source checkout's `requirements.txt` installs the package editably with `-e .`.

### Optional extras and dependencies

Install only what your workflow needs:

| Need | Extra packages | Notes |
| --- | --- | --- |
| Gymnasium-style wrapper | `gymnasium` | Required by `GymWrapper`; fallback to new enough `gym` may work but Gymnasium is preferred. |
| Demonstration HDF5 inspection/playback | `h5py` | Required by teleoperation demo aggregation and bundled HDF5 helpers. |
| Short video writing | `imageio` plus an FFmpeg backend such as `imageio[ffmpeg]` | Needed for MP4 output. |
| SpaceMouse / DualSense | `hidapi` plus hardware/driver access | Optional and platform-dependent. |
| Extra external robots/models | `robosuite-models` | Optional; the generated skill focuses on built-in robosuite models. |
| Whole-body Mink IK example | `mink==0.0.5` | Optional third-party controller example. |
| USD export | `usd-core`, `pillow`, `tqdm` | Optional; external USD-capable apps may still be required. |
| Isaac / Omniverse rendering | Isaac Sim / Isaac Lab app stack | External-app dependent and not a core verified path. |

## Minimal import check

```bash
python - <<'PY'
import robosuite as suite
print(suite.__version__)
print(sorted(suite.ALL_ENVIRONMENTS)[:5])
print(sorted(suite.ALL_ROBOTS)[:5])
PY
```

Expected behavior: robosuite imports and prints registries. Warnings about missing `macros_private.py`, `robosuite_models`, or `mink` are not fatal for core environment/controller workflows.

## Headless environment smoke

```bash
python - <<'PY'
import numpy as np
import robosuite as suite

env = suite.make(
    "Lift",
    robots="Panda",
    has_renderer=False,
    has_offscreen_renderer=False,
    use_camera_obs=False,
    use_object_obs=True,
)
try:
    obs = env.reset()
    low, high = env.action_spec
    action = np.random.uniform(low, high)
    obs, reward, done, info = env.step(action)
    print("action_dim", env.action_dim)
    print("obs_keys", list(obs)[:8])
    print("reward", reward, "done", done)
finally:
    env.close()
PY
```

Use the root bundled `scripts/check_install.py` when you want this wrapped in a reusable diagnostic helper.

## Offscreen camera smoke

For camera observations on headless Linux, set an appropriate MuJoCo GL backend before Python starts:

```bash
MUJOCO_GL=egl python - <<'PY'
import robosuite as suite

env = suite.make(
    "Lift",
    robots="Panda",
    has_renderer=False,
    has_offscreen_renderer=True,
    use_camera_obs=True,
    camera_names="agentview",
    camera_heights=32,
    camera_widths=32,
)
try:
    obs = env.reset()
    print(obs["agentview_image"].shape)
finally:
    env.close()
PY
```

If `egl` is unavailable, try a software backend such as `MUJOCO_GL=osmesa` if your environment provides it. On-screen viewer paths require a display and are not a substitute for a headless camera smoke.

## Which sub-skill next?

- Use `sub-skills/environments/` for standardized task construction, observation keys, rewards, GymWrapper, and deterministic rollouts.
- Use `sub-skills/controllers/` for controller JSONs, action split maps, robots, grippers, bases, and third-party controller extension.
- Use `sub-skills/teleoperation/` for keyboard/SpaceMouse/DualSense/MJGUI control, DataCollectionWrapper, and demo HDF5 playback.
- Use `sub-skills/rendering/` for camera observations, renderer backends, depth/segmentation, video, domain randomization, and optional USD.
- Use `sub-skills/modeling/` for custom environments, MJCF assets, object/arena/task composition, robot XML validation, and maintainer test selection.
