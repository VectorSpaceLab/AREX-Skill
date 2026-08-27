# Custom environments

A custom robosuite environment usually combines:

- a robot setup chosen with `robots`, `base_types`, and `gripper_types`
- a model graph built from `MujocoWorldBase`, `Arena`, `Task`, and `MujocoObject`
- an environment subclass that wires the model into `_load_model`, `_setup_references`, `_setup_observables`, `_reset_internal`, and reward / success logic

## Recommended build order

1. Pick the arena. Use `TableArena` for tabletop tasks or another `Arena` subclass for bins, pegs, wipe, or multi-table layouts.
2. Set the robot base pose from `robot.robot_model.base_xpos_offset[...]` before merging the robot.
3. Create the object models.
4. Compose the final scene with `ManipulationTask`.
5. Validate the model with the bundled compile helper before adding extra observations or reward logic.

## Tiny tabletop scene

```python
import numpy as np
from robosuite.models import MujocoWorldBase
from robosuite.models.arenas import TableArena
from robosuite.models.objects import BoxObject
from robosuite.models.tasks import ManipulationTask

world = MujocoWorldBase()
arena = TableArena(table_full_size=(0.8, 0.8, 0.05))
arena.set_origin([0.0, 0.0, 0.0])

cube = BoxObject(name="cube", size=[0.02, 0.02, 0.02], rgba=[1, 0, 0, 1])
cube.set_pos(arena.table_top_abs - cube.bottom_offset)

task = ManipulationTask(
    mujoco_arena=arena,
    mujoco_robots=[robot.robot_model],
    mujoco_objects=cube,
)
model = task.get_model(mode="mujoco")
```

## Environment subclass sketch

A typical modeling-oriented environment subclass follows the same pattern as `Lift`:

```python
from robosuite.environments.manipulation.manipulation_env import ManipulationEnv
from robosuite.models.arenas import TableArena
from robosuite.models.objects import BoxObject
from robosuite.models.tasks import ManipulationTask
from robosuite.utils.placement_samplers import UniformRandomSampler

class MyLift(ManipulationEnv):
    def _load_model(self):
        super()._load_model()

        self.robots[0].robot_model.set_base_xpos(
            self.robots[0].robot_model.base_xpos_offset["table"](self.table_full_size[0])
        )

        self.arena = TableArena(table_full_size=self.table_full_size, table_friction=self.table_friction)
        self.arena.set_origin([0.0, 0.0, 0.0])

        self.cube = BoxObject(name="cube", size=[0.02, 0.02, 0.02], rgba=[1, 0, 0, 1])
        self.placement_initializer = UniformRandomSampler(
            name="ObjectSampler",
            mujoco_objects=self.cube,
            x_range=[-0.03, 0.03],
            y_range=[-0.03, 0.03],
            reference_pos=self.table_offset,
            z_offset=0.01,
            ensure_valid_placement=True,
        )

        self.model = ManipulationTask(
            mujoco_arena=self.arena,
            mujoco_robots=[robot.robot_model for robot in self.robots],
            mujoco_objects=self.cube,
        )
```

## Placement and reset guidance

- Use `UniformRandomSampler` for one or two objects and `SequentialCompositeSampler` when you need separate table regions.
- Call `reset()` on an injected sampler before reusing it, then re-add the objects you want it to manage.
- In `_reset_internal`, write the sampled joint positions with `sim.data.set_joint_qpos(...)`.
- In `_setup_references`, cache object body IDs with `sim.model.body_name2id(...)` and use them in observables.
- Keep `use_camera_obs` and `has_renderer` off while validating model structure; turn them on only after the MJCF compiles cleanly.

## Robot composition note

If you are checking a robot assembled with `create_composite_robot(name, robot, base=None, grippers=None)`, verify the registered robot name first, then use the same environment pattern above. That keeps robot/base/gripper composition in the controller sub-skill while this sub-skill owns the model wiring.

## When to stop here

If the problem is really about controller gain tuning, action slicing, or end-effector control semantics, stop at the model boundary and hand off to `../controllers`.
