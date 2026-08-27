---
name: "simulation-rendering"
description: "Use for MuJoCo model loading, simulation state and time
  inspection, headless or onscreen rendering, camera/output configuration, and
  viewer/display diagnostics; route environment catalog, XML editing/IK, MJX
  acceleration, and training elsewhere."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Simulation and rendering

Use this sub-skill when the task concerns the MuJoCo model/data handles behind a
MyoSuite environment, rendering pixels or depth, selecting cameras, preserving
or restoring simulator state, or diagnosing a viewer/display failure. It covers
the base MuJoCo backend in MyoSuite 2.x. It does **not** teach task selection,
XML mutation or IK, MJX/JAX acceleration, or RL training.

## Route first

- Choose [environment workflows](../environments/SKILL.md) for registry lookup,
task configuration, reset/step semantics, or environment-specific observation
and reward behavior.
- Choose [model editing and kinematics](../model-editing-kinematics/SKILL.md)
for XML changes, `MjSpec` editing, site/body edits as a modeling operation, or
IK.
- Choose [MJX acceleration](../mjx-acceleration/SKILL.md) for JAX, MJX, CUDA,
batching, or accelerator performance.
- Choose [training integration](../training-integration/SKILL.md) for policies,
learners, checkpoints, or long-running experiments.

## Fast decision: which rendering path?

1. **Headless or CI:** load `mujoco.MjModel`/`mujoco.MjData`, step with
   `mujoco.mj_step`, and use `MJRenderer.render_offscreen(...)`, or run the
   bundled safe checker:
   `python scripts/check_mujoco_xml.py --help`.
2. **A window is explicitly wanted:** `env.mj_render()` delegates to
   `env.mj_renderer.render_to_window()`, which creates a native passive viewer
   on first use. This is display-dependent and is not verification ground truth.
3. **Raw XML diagnosis:** run
   `python scripts/check_mujoco_xml.py --xml MODEL.xml --render none` first.
   It loads and steps without creating a viewer. Add `--render offscreen` only
   when pixel output is required.

Never use `myosuite.utils.examine_sim` as a headless check: its documented
workflow calls `mujoco.viewer.launch(...)` and is intentionally onscreen. Its
safe native candidate is `python -m myosuite.utils.examine_sim --help` only.

## Environment rendering contract

```python
from myosuite.utils import gym

env = gym.make("myoElbowPose1D6MRandom-v0")
env.reset(seed=1234)
frame = env.mj_renderer.render_offscreen(
    width=320, height=240, camera_id=-1, rgb=True
)
env.close()
```

- `env.mj_model` is the compiled `mujoco.MjModel`; `env.mj_data` is its live
  `mujoco.MjData`. The base environment constructs `env.mj_renderer` as an
  `MJRenderer` for those handles.
- `camera_id=-1` means MuJoCo's free camera. A named camera string or numeric
  camera id selects a model camera. Use a model camera name only after checking
  that it exists; a missing name is a model/rendering error, not a display fix.
- `render_offscreen` returns an RGB `numpy` array for the default call. The
  detailed return matrix for RGB/depth/segmentation is in
  [rendering-api.md](references/rendering-api.md).
- `env.mj_render()` is deliberately different: it opens/synchronizes a window
  and returns no frame. Do not call it in a server, CI job, or headless synthetic
  case.
- `env.viewer_setup(distance=..., azimuth=..., elevation=..., lookat=...,
  render_actuator=..., render_tendon=...)` stores free-camera and visualization
  settings for the next window or offscreen scene. Camera/output details and
  the distance adjustment are documented in [rendering-api.md](references/rendering-api.md).

## Deterministic headless rollout

For a raw model, the safe contract is:

```bash
python scripts/check_mujoco_xml.py \
  --xml MODEL.xml --render offscreen --frames 8 \
  --width 320 --height 240 --output-dir ./mujoco-check
```

The command never calls `mujoco.viewer` or `launch_passive`. It prints model
sizes, steps the requested number of frames, and writes one binary PPM image per
rendered frame under the supplied output directory (for example,
`mujoco-check/frame-0000.ppm`). `--render none` is the default and creates no
output directory. The script accepts optional comma-separated `--qpos` and
`--ctrl`; it validates their lengths before applying them. See the script's
`--help` output for the complete input/output contract.

For a policy/environment rollout, use `MujocoEnv.examine_policy_new` only when
its policy API is already available. Its supported `render` values are
`"onscreen"`, `"offscreen"`, and `"none"`; offscreen mode accumulates RGB
frames and writes an MP4 per episode through `imageio`. Set an explicit
`output_dir`, `filename`, `frame_size`, and finite `horizon`. The safe raw-model
script is preferred for a small, dependency-light rendering check.

## State and time workflow

- `env.dt` is `env.mj_model.opt.timestep * env.frame_skip`.
- `env.time` reads the observed simulation data time
  (`env.obsd_mj_data.time`), so compare it with `env.mj_data.time` only when the
  environment uses the same observed and ground-truth model.
- `env.get_env_state()` returns copied `time`, `qpos`, `qvel`, optional `act`,
  optional mocap position/quaternion, optional site position/quaternion, and
  body position/quaternion arrays.
- Save the returned dictionary before a branch, then call
  `env.set_env_state(state)` to restore the base state. The method updates both
  ground-truth and observed data where present and performs a MuJoCo step to
  refresh derived state; treat restoration as a simulator-state operation, not
  as a byte-for-byte snapshot of every internal buffer.
- `env.reset(...)` establishes the task's initial state. After changing raw
  `qpos`/`qvel`, use `mujoco.mj_forward(model, data)` before inspecting derived
  positions or rendering. Do not edit model arrays merely to move a body unless
  the task is explicitly a model-editing task.

## Visual observations

Visual observations are opt-in. Call `env.get_obs(update_exteroception=True)`
or `env.get_visuals(...)` when the environment has configured `visual_keys`.
Supported key forms are `rgb:CAMERA:HxW:1d`, `rgb:CAMERA:HxW:2d`, and optional
encoder forms such as `r3m18`, `r3m34`, `r3m50`, `rrl`, or `vc1` when their
optional encoder dependencies are installed. A matching `d:` key requests
depth alongside the RGB key. `get_obs()` does not refresh exteroception by
default, and `env_info["visual_dict"]` may therefore be empty or stale unless
visuals were explicitly updated at the current simulation time.

## Backend and safety boundary

Base MuJoCo model loading, stepping, state inspection, and the `MJRenderer`
offscreen path are CPU/base-package capabilities, subject to a usable graphics
backend for pixel rendering. Onscreen viewing additionally requires a display
and native viewer support. MJX/JAX/CUDA is optional and is not established by
an offscreen CPU check; route it to the MJX sub-skill and report it separately.

Before reporting success, check the actual artifact: model load/step succeeded,
rendered arrays have the requested dimensions, and every requested output file
exists and is non-empty. For failure symptoms and recovery branches, use
[troubleshooting.md](references/troubleshooting.md).