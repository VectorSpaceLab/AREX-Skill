# Simulation API reference

## When to read this

Read this before constructing a RoboCasa environment or adapting the README Gym
recipe. The facts below are distilled from `robocasa/__init__.py`,
`robocasa/utils/env_utils.py`, `robocasa/wrappers/gym_wrapper.py`, and the
`Kitchen` constructor/source, then checked against the installed package
signatures.

## Compatibility and registration

RoboCasa 1.0.1 performs import-time assertions:

| Component | Required by this release |
|---|---|
| Python | The package metadata declares `>=3`; the public installation recipe uses Python 3.11. |
| NumPy | Exactly `2.2.5` |
| MuJoCo Python package | Exactly `3.3.1` |
| robosuite | `>=1.5.2` |
| Gymnasium | Package dependency; the Gym wrapper uses the Gymnasium API. |

The package imports task classes and registers 374 kitchen environments. Import
also attempts to import the optional `mimicgen` integration; its absence emits a
warning and does not block the core kitchen registry. `import robocasa` is
therefore both the compatibility gate and the registration step. Import it
before calling `gym.make("robocasa/<TaskName>", ...)`.

The Gym wrapper dynamically creates environment IDs for the current robosuite
registered environment set. Prefer a known RoboCasa kitchen ID such as
`robocasa/PickPlaceCounterToCabinet`; inspect the actual Gym registry rather
than assuming every robosuite ID is a kitchen task.

## `create_env`

Verified signature:

```python
create_env(
    env_name,
    robots="PandaOmron",
    camera_names=[
        "robot0_agentview_left",
        "robot0_agentview_right",
        "robot0_eye_in_hand",
    ],
    camera_widths=128,
    camera_heights=128,
    seed=None,
    render_onscreen=False,
    translucent_robot=False,
    split=None,
    obj_instance_split=None,
    generative_textures=None,
    randomize_cameras=False,
    layout_and_style_ids=None,
    layout_ids=None,
    style_ids=None,
    **kwargs,
)
```

The helper loads a composite controller configuration for the selected robot and
calls `robosuite.make`. It supplies these lower-level values itself:

- `has_renderer=render_onscreen`;
- `has_offscreen_renderer=not render_onscreen`;
- `use_camera_obs=not render_onscreen`;
- `ignore_done=True`;
- `use_object_obs=True`;
- camera names, dimensions, seed, split-derived object/layout/style selection,
  and the camera-depth setting.

Because these are explicit entries in the final keyword dictionary, passing
`use_camera_obs` or `has_offscreen_renderer` in `kwargs` raises a duplicate-key
`TypeError` (`dict() got multiple values for keyword argument ...`). The same
construction pattern means callers should not override other helper-owned
keywords such as `ignore_done` through `kwargs`; use the lower-level
`robosuite.make` API only when that control is required.

`camera_depths` is the one special case handled from `kwargs`: the helper removes
it from `kwargs` and forwards it once. It may be a boolean or a per-camera list
as accepted by `Kitchen`.

### Split mapping

`split` is validated before construction. Accepted values are `None`, `"all"`,
`"pretrain"`, and `"target"`; values such as `"test"` are invalid for
`create_env`, even though the Gym wrapper's constructor default is `"test"`.
Pass a supported split explicitly when using `gym.make`.

| `split` | Object instance split | Layout/style selection assigned by helper |
|---|---|---|
| `None` | Leaves `obj_instance_split` unchanged | Leaves explicit `layout_ids`, `style_ids`, or `layout_and_style_ids` unchanged; `Kitchen` defaults to all when those are omitted. |
| `"pretrain"` | `"pretrain"` | `layout_ids=-2`, `style_ids=-2`: the train groups, layouts 11–60 and styles 11–60. |
| `"target"` | `"target"` | `layout_and_style_ids=[(1,1), ..., (10,10)]`; explicit layout/style IDs are cleared. |
| `"all"` | `None` | `layout_ids=-3`, `style_ids=-3`: all layout/style IDs (1–60 before task-specific exclusions). |

The target mapping is a diagonal set of ten `(layout, style)` pairs, not every
combination of the first ten layouts and styles. `Kitchen` filters excluded
layouts/styles for each task after this mapping. For object sampling, the
`Kitchen.sample_object` contract defines `pretrain` as all but the last four
object instances (or the first half, whichever is larger), `target` as the
remainder, and `None` as all available instances in the selected registries.

## `Kitchen` constructor and lifecycle

Verified signature highlights:

```python
Kitchen(
    robots,
    env_configuration="default",
    controller_configs=None,
    gripper_types="default",
    base_types="default",
    initialization_noise="default",
    use_camera_obs=True,
    use_object_obs=True,
    reward_scale=1.0,
    reward_shaping=False,
    placement_initializer=None,
    has_renderer=False,
    has_offscreen_renderer=True,
    render_camera="robot0_agentview_center",
    render_collision_mesh=False,
    render_visual_mesh=True,
    render_gpu_device_id=-1,
    control_freq=20,
    horizon=1000,
    ignore_done=True,
    camera_names="agentview",
    camera_heights=256,
    camera_widths=256,
    camera_depths=False,
    renderer="mjviewer",
    renderer_config=None,
    init_robot_base_ref=None,
    seed=None,
    layout_and_style_ids=None,
    layout_ids=None,
    style_ids=None,
    enable_fixtures=None,
    generative_textures=None,
    obj_registries=("objaverse", "lightwheel"),
    obj_instance_split=None,
    use_distractors=False,
    translucent_robot=False,
    randomize_cameras=False,
    robot_spawn_deviation_pos_x=0.15,
    robot_spawn_deviation_pos_y=0.05,
    robot_spawn_deviation_rot=0.0,
    clutter_mode=0,
    update_fxtr_cfg_dict=None,
    use_cotraining_cameras=False,
    use_novel_instructions=False,
)
```

The base class uses `ignore_done=True` by default and RoboCasa's helper forces
that value. `horizon` is the episode timestep limit only when done handling is
allowed by the lower-level environment. For helper-based bounded experiments,
stop the outer loop after the requested number of steps.

Construction sets up the scene and robot model lazily through the robosuite
lifecycle. A successful `create_env` return proves that Python/controller
construction worked, not that every fixture/object XML needed by `reset()` is
installed. Always close a successfully constructed environment.

## Gymnasium wrapper

`robocasa.wrappers.gym_wrapper` defines `RoboCasaGymEnv` and dynamically creates
classes such as `PickPlaceCounterToCabinet` for IDs of the form
`robocasa/<TaskName>`. Its constructor calls `create_env` and immediately calls
`self.env.reset()`, so `gym.make` is an asset-dependent operation, unlike a
constructor-only probe.

Use the README-shaped recipe:

```python
import gymnasium as gym
import robocasa  # registers the IDs and checks versions
from robocasa.utils.env_utils import run_random_rollouts

env = gym.make(
    "robocasa/PickPlaceCounterToCabinet",
    split="pretrain",
    seed=0,
)
try:
    result = run_random_rollouts(
        env, num_rollouts=3, num_steps=100, video_path="rollouts.mp4"
    )
finally:
    env.close()
```

The wrapper's default `split="test"` is not accepted by `create_env`; pass
`split="pretrain"`, `"target"`, `"all"`, or arrange a corrected wrapper call
before construction.

### Observations

The wrapper remaps the underlying observation into a Gymnasium `spaces.Dict`.
The key converter emits:

- `state.gripper_qpos` from `robot0_gripper_qpos`;
- `state.base_position` and `state.base_rotation` from
  `robot0_base_pos`/`robot0_base_quat`;
- `state.end_effector_position_relative` and
  `state.end_effector_rotation_relative` from the corresponding
  `robot0_base_to_eef_*` observations;
- `video.robot0_agentview_left`, `video.robot0_agentview_right`, and
  `video.robot0_eye_in_hand` for RGB camera frames;
- `annotation.human.task_description`, populated from the episode language
  metadata (often an empty string for the base task metadata).

RGB images are vertically flipped by the wrapper before returning them. When
`enable_render=False`, it substitutes black images for the configured camera
keys. If camera depth is enabled, depth keys are added with shape
`(height, width, 1)` and `float32` values; the mapped RGB image keys also expose
`_image`/`_depth` variants according to the wrapper implementation.

The underlying robosuite environment, rather than this wrapper, is the better
choice for raw observations or custom camera sets. `camera_names` passed to
`create_env` controls the underlying camera observations. The wrapper's
`camera_names` argument is currently replaced by the fixed PandaOmron converter
camera list; do not assume arbitrary wrapper camera names change its remapped
keys.

## Action representations

`convert_action(action)` accepts a flat array-like action and returns a dict:

```python
{
    "action.end_effector_position": action[0:3],
    "action.end_effector_rotation": action[3:6],
    "action.gripper_close": action[6:7],
    "action.base_motion": action[7:11],
    "action.control_mode": action[11:12],
}
```

The input must contain at least 12 ordered values. The returned dict is the
Gym wrapper's action representation; do not pass the flat array directly to
`RoboCasaGymEnv.step`.

The wrapper action space uses `Box` values in `[-1, 1]` with `float32` shapes:

| Key | Shape | Meaning |
|---|---:|---|
| `action.end_effector_position` | `(3,)` | End-effector position command |
| `action.end_effector_rotation` | `(3,)` | End-effector rotation command |
| `action.gripper_close` | `(1,)` | Thresholded at `0.5`; below maps to `-1`, otherwise `+1` |
| `action.base_motion` | `(4,)` | First three values map to base; final value maps to torso |
| `action.control_mode` | `(1,)` | Thresholded at `0.5`; selects base control mode |

The wrapper's `step` converts those keys into the robosuite composite-controller
keys, rejects leftovers with `AssertionError`, concatenates robot actions, and
returns `(observation, sparse_reward, terminated, truncated, info)`. It sets
`truncated=False` and `info["success"]` from the task success check. A missing
key, wrong shape, a NumPy array with an unexpected scalar representation, or a
flat/dict mix should be fixed at the action boundary rather than patched inside
the environment.

## Rendering modes

- `render_onscreen=False` (the helper default) requests no interactive viewer,
  enables off-screen rendering, and enables camera observations.
- `render_onscreen=True` requests the interactive renderer and disables camera
  observations through the helper's fixed flags. It needs a display/viewer
  backend and is not suitable for a generic headless process. Select this on a
  direct `create_env` call; the Gym wrapper passes `render_onscreen=False`
  internally and is not the route for overriding that flag.
- `camera_names` can be a camera name or list; common PandaOmron names are
  `robot0_agentview_left`, `robot0_agentview_right`, and
  `robot0_eye_in_hand`. `camera_widths` and `camera_heights` can be scalar
  dimensions or per-camera lists. `camera_depths` can be a bool or per-camera
  list.
- The helper's `run_random_rollouts` writes frames by calling the underlying
  `env.sim.render(height=512, width=768, camera_name=...)`. The default video
  camera is `robot0_agentview_center`, which must exist in the constructed
  simulation. A video writer requires the imageio/video backend and a writable
  parent directory.

Rendering and reset are external-asset-dependent. Use the diagnostic and
troubleshooting reference to distinguish a missing EGL/display library from a
missing RoboCasa XML/object file.
