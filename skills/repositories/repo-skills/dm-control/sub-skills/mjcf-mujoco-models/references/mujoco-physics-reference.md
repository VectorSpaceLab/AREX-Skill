# MuJoCo Physics Reference

This reference covers compiling MJCF into `Physics`, stepping/resetting simulations, using named model/data access, action specs, rendering API calls, and connecting custom physics to `dm_env`-style control loops.

## Choosing a constructor

Use PyMJCF when the model is being created or modified in Python:

```python
from dm_control import mjcf

physics = mjcf.Physics.from_mjcf_model(mjcf_model)
```

`mjcf.Physics` is a subclass of `dm_control.mujoco.Physics`. It compiles the model through generated XML plus `mjcf_model.get_assets()`, and additionally supports `physics.bind(mjcf_element)` for direct PyMJCF element access.

Use raw MuJoCo constructors when the input is already XML, assets, or an MJB binary:

```python
from dm_control import mujoco

physics = mujoco.Physics.from_xml_string(xml_string, assets=None)
physics = mujoco.Physics.from_xml_path("model.xml")
physics = mujoco.Physics.from_binary_path("model.mjb")
```

Constructor notes:

- `from_xml_string(xml_string, assets=None)` accepts an optional `{filename: bytes}` asset mapping. This is the normal bridge from `mjcf_model.to_xml_string()` plus `mjcf_model.get_assets()`.
- `from_xml_path(file_path)` loads XML and file-based assets relative to the XML path through MuJoCo.
- `from_model(model)` wraps an existing low-level `wrapper.MjModel`.
- `reload_from_xml_string`, `reload_from_xml_path`, and `mjcf.Physics.reload_from_mjcf_model` replace the compiled model/data of an existing `Physics`; reacquire named indices or PyMJCF bindings after substantial model changes.

## Resetting and stepping

A typical state edit should happen inside `reset_context()`:

```python
with physics.reset_context():
    physics.named.data.qpos["slide_z"] = 0.1
    # or, for PyMJCF Physics:
    # physics.bind(slide_joint).qpos = 0.1

physics.set_control([0.0] * physics.model.nu)
physics.step()
```

`reset_context()` resets the simulation on entry, yields the `Physics`, and calls `after_reset()` on exit so derived MuJoCo quantities are consistent. For direct control:

- `physics.reset()` resets to the default state or a keyframe when supported.
- `physics.after_reset()` recomputes derived quantities after a manual reset.
- `physics.forward()` recomputes forward dynamics without advancing time.
- `physics.step(nstep=1)` advances one or more MuJoCo steps.
- `physics.set_control(control)` copies controls into `physics.data.ctrl`.
- `physics.time()` and `physics.timestep()` report simulation time and MuJoCo timestep.
- `physics.get_state()` and `physics.set_state(state)` snapshot/restore qpos, qvel, actuator activation, and plugin state when present.
- `physics.copy(share_model=False)` creates a second `Physics`; use `share_model=True` only when shared compiled model ownership is intentional.

## Named model and data access

`physics.model` and `physics.data` expose MuJoCo model/data wrappers. `physics.named` adds name-based indexing for many fields:

```python
# Generalized position by joint name.
physics.named.data.qpos["slide_z"] = 0.05

# Geom world position by geom name and Cartesian column.
z = physics.named.data.geom_xpos["box_geom", "z"]

# Multiple rows and columns.
xy = physics.named.data.geom_xpos[["box_geom", "floor"], ["x", "y"]]

# Model fields are available through named.model.
geom_size = physics.named.model.geom_size["box_geom"]
```

Named indexing fails with `KeyError`, `IndexError`, or `ValueError` when a name, object type, camera id, or axis label does not exist. Validate names after compile with the object counts and known names in `physics.model` / `physics.named` before running a long loop.

For PyMJCF-generated models, prefer `physics.bind(element)` when you still hold the `mjcf.Element` object:

```python
binding = physics.bind(box_geom)
print(binding.xpos)        # derived data for the geom
binding.pos = [0, 0, 0.4]  # writes model geom_pos and marks derived data dirty
print(binding.xpos)        # reading derived data triggers synchronization
```

Bindings can also cover a sequence of same-kind elements:

```python
physics.bind([geom_a, geom_b])["pos", ["x", "z"]] = [[0.1, 0.2], [0.3, 0.4]]
```

Do not pickle or hold long-lived references to synchronizing array wrappers returned by bindings; hold the binding or reacquire it.

## Action specs and controls

`dm_control.mujoco.action_spec(physics)` returns a `dm_env.specs.BoundedArray` for the model's actuators:

```python
from dm_control import mujoco
import numpy as np

spec = mujoco.action_spec(physics)
control = np.zeros(spec.shape, dtype=float)
finite_min = np.where(np.isfinite(spec.minimum), spec.minimum, -1.0)
finite_max = np.where(np.isfinite(spec.maximum), spec.maximum, 1.0)
control = np.clip(control, finite_min, finite_max)
physics.set_control(control)
physics.step()
```

If `physics.model.nu == 0`, the action spec has shape `(0,)`; keep control arrays empty and step passive dynamics.

## Rendering API

`physics.render` is an API-level rendering call. It is optional and requires a working MuJoCo OpenGL backend.

```python
rgb = physics.render(height=240, width=320, camera_id=-1)
depth = physics.render(height=240, width=320, depth=True)
seg = physics.render(height=240, width=320, segmentation=True)
wire = physics.render(render_flag_overrides={"wireframe": True})
```

Arguments:

| Argument | Meaning |
|---|---|
| `height`, `width` | Output image size. Must not exceed the offscreen buffer size. |
| `camera_id` | `-1` for free camera, non-negative index, or fixed camera name. |
| `overlays` | Text overlays for RGB rendering only. |
| `depth=True` | Return a float depth image with shape `(height, width)`. |
| `segmentation=True` | Return int labels with shape `(height, width, 2)`. |
| `scene_option` | Optional MuJoCo scene option wrapper. |
| `render_flag_overrides` | Temporary render flag overrides such as `{"wireframe": True}`. Not allowed with depth or segmentation. |
| `scene_callback` | Callback invoked after scene creation and before rendering. |

Render constraints and gotchas:

- `depth` and `segmentation` cannot both be true.
- `overlays` are not supported with depth or segmentation.
- `render_flag_overrides` are not supported with depth or segmentation.
- Width and height must fit the compiled offscreen buffer. In PyMJCF, set it before compile with `getattr(model.visual, 'global').offwidth` and `.offheight`; after compile inspect `physics.model.vis.global_.offwidth` and `.offheight`.
- `camera_id=-2`, a non-existent fixed camera id, or a missing camera name raises a camera error.
- If rendering fails due to `MUJOCO_GL`, missing display, EGL, GLFW, or OSMesa problems, the model may still be valid. Use non-rendering compile/step as the core validation and route backend work to the rendering sibling skill.

## Custom `dm_env` / `control.Environment` bridge

For a custom environment around raw `Physics`, subclass `dm_control.rl.control.Task` and pass it to `control.Environment`:

```python
from dm_control.rl import control
from dm_env import specs
import numpy as np

class HeightTask(control.Task):
    def initialize_episode(self, physics):
        with physics.reset_context():
            physics.named.data.qpos["slide_z"] = 0.0

    def get_observation(self, physics):
        return {"height": np.asarray([physics.named.data.geom_xpos["box_geom", "z"]])}

    def get_reward(self, physics):
        return float(physics.named.data.geom_xpos["box_geom", "z"] > 0.2)

    def action_spec(self, physics):
        from dm_control import mujoco
        return mujoco.action_spec(physics)

env = control.Environment(physics, HeightTask(), time_limit=5.0, control_timestep=None)
timestep = env.reset()
while not timestep.last():
    action = np.zeros(env.action_spec().shape, dtype=float)
    timestep = env.step(action)
```

Use this bridge for lightweight custom tasks. If the task needs Composer entities, observables, variations, arenas, or lifecycle hooks, route to the Composer sibling skill.

## Validation checklist for a compiled model

1. `physics.model.nq`, `physics.model.nv`, and `physics.model.nu` match the intended state and actuator dimensions.
2. Every downstream name is accessible through `physics.named` or `physics.bind(element)`.
3. `with physics.reset_context():` initial state edits succeed and `physics.forward()` or `after_reset()` leaves derived fields finite.
4. A zero or clipped action from `mujoco.action_spec(physics)` can be applied and stepped.
5. State snapshots via `get_state()` and `set_state()` preserve shape.
6. Rendering, if needed, is checked separately with a known backend and fixed image size.
