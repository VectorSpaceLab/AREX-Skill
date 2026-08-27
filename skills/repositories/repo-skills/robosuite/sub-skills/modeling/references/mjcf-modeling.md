# MJCF modeling

This reference collects the MJCF pieces you will use most often when building robosuite model graphs.

## Core APIs

| API | Use | Notes |
| --- | --- | --- |
| `MujocoWorldBase` | Root MJCF world container | Provides a base world, timestep setup, `merge(...)`, and `get_model(...)`. |
| `Arena` / `TableArena` | Workspace geometry | `TableArena.table_top_abs` gives the absolute tabletop height for placement. |
| `Task` / `ManipulationTask` | Compose arena, robots, and objects | Use this when the scene should become an environment-ready task. |
| `MujocoObject` | Common object interface | Exposes `get_obj()`, `bottom_offset`, `top_offset`, and `horizontal_radius`. |
| `MujocoXMLObject` | XML-backed object | Expects the object subtree and placement sites described below. |
| `MujocoGeneratedObject` | Procedural object base | Implement `sanity_check()` and `_get_object_subtree()`. |
| `CustomMaterial` | Texture / material helper | Handy for custom appearances and shared texture names. |
| `new_body`, `new_geom`, `new_joint`, `new_site` | Low-level MJCF builders | These come from `robosuite.utils.mjcf_utils`. |
| `xml_path_completion` | Resolve asset XML paths | Keeps package asset references portable. |
| `array_to_string`, `string_to_array` | Format MJCF attributes | Use them when writing numeric XML attributes. |

## Object XML conventions

A `MujocoXMLObject` needs a predictable object subtree so robosuite can place it and reason about its size:

- a top-level body named `object`
- a `bottom_site` at the lowest contact point
- a `top_site` at the highest contact point
- a `horizontal_radius_site` on the x-y footprint used for spacing checks

Minimal shape:

```xml
<mujoco model="my_object">
  <worldbody>
    <body>
      <body name="object">
        <geom name="main" type="box" size="0.02 0.02 0.02"/>
      </body>
      <site name="bottom_site" pos="0 0 -0.02" rgba="0 0 0 0" size="0.005"/>
      <site name="top_site" pos="0 0 0.02" rgba="0 0 0 0" size="0.005"/>
      <site name="horizontal_radius_site" pos="0.03 0 0" rgba="0 0 0 0" size="0.005"/>
    </body>
  </worldbody>
</mujoco>
```

Those sites drive:

- `bottom_offset` for placing an object on a surface
- `top_offset` for stacking another object on top
- `horizontal_radius` for collision-aware spacing

## Prefixing and composition

- `MujocoModel.correct_naming(...)` and `add_prefix(...)` keep merged models from colliding on names.
- `exclude_from_prefixing(...)` is where a subclass keeps shared names unprefixed.
- `MujocoXML.merge(...)` combines worldbody, actuator, sensor, tendon, equality, and contact content.
- `Task.merge_arena(...)`, `Task.merge_robot(...)`, and `Task.merge_objects(...)` build the final scene graph.

## Tiny object / world example

```python
from robosuite.models import MujocoWorldBase
from robosuite.models.arenas import TableArena
from robosuite.models.objects import BallObject

world = MujocoWorldBase()
arena = TableArena()
arena.set_origin([0.0, 0.0, 0.0])
world.merge(arena)

ball = BallObject(name="ball", size=[0.04], rgba=[0.0, 0.5, 0.5, 1.0])
ball.set_pos(arena.table_top_abs - ball.bottom_offset)
world.merge_assets(ball)
world.worldbody.append(ball.get_obj())

model = world.get_model(mode="mujoco")
```

## Validation steps

1. Load the XML with MuJoCo before you wire it into a new environment.
2. Keep temporary compiled copies in the same directory as the source XML so relative asset paths still resolve.
3. Save the compiled result to a new file and inspect the output for missing mesh, inertia, or joint errors.
4. If a robot or gripper asset changed, verify the end-effector mount bodies and joint names with the bundled robot checker.

## Robot and gripper asset notes

- `RobotModel.set_base_xpos(...)` and `base_xpos_offset[...]` are the usual way to position a robot for a specific arena.
- `ManipulatorModel.eef_name` is the public end-effector mount map; keep it aligned with the robot XML and gripper attachment point.
- `GripperModel` exposes `format_action(...)`, `dof`, `init_qpos`, and the important site / geom names needed by the rest of the stack.
- If you build a composite robot with `create_composite_robot(name, robot, base=None, grippers=None)`, treat the returned class name as a first-class registry entry and verify it the same way as any other registered robot.

## Low-level authoring checklist

- Use `xml_path_completion(...)` for asset paths instead of hard-coding checkout-relative file names.
- Keep mesh scales, density, friction, and inertial values explicit enough for MuJoCo to compile.
- Use `MujocoGeneratedObject.sanity_check()` to reject invalid sizes early.
- Prefer the bundled compile helper for the final round-trip instead of relying only on a viewer.
