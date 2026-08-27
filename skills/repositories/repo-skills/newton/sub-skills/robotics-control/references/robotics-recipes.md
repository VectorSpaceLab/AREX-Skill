# Robotics-control recipes

These recipes distill common Newton robot-control patterns into self-contained workflows. They assume Newton and Warp are importable and use public APIs only.

## Recipe 1: migrate mixed target layouts to coordinate layout

Use this when position-control code writes to `joint_target_q` and the robot has any free, ball, or distance joint. The safe migration path is:

1. Set the global flag before constructing any model.
2. Write position targets using coordinate indices.
3. Write velocity targets and forces using DOF indices.
4. Prefer `ArticulationView` for batched robot slices instead of manual offsets.

```python
import numpy as np
import warp as wp
import newton

newton.use_coord_layout_targets = True
builder = newton.ModelBuilder()

base = builder.add_link(label="robot/base")
arm = builder.add_link(label="robot/arm")
root_joint = builder.add_joint_free(parent=-1, child=base, label="robot/root")
elbow_joint = builder.add_joint_revolute(parent=base, child=arm, axis=newton.Axis.Z, label="robot/elbow")
builder.add_articulation([root_joint, elbow_joint], label="robot")
model = builder.finalize()
control = model.control()

# Position target: layout-aware coordinate start. The free root has 7 coords;
# the revolute joint has one coordinate after that.
elbow_q_start = int(model.joint_target_q_start.numpy()[elbow_joint])
control.joint_target_q[elbow_q_start] = 0.5

# Velocity target and effort: DOF layout.
elbow_qd_start = int(model.joint_qd_start.numpy()[elbow_joint])
control.joint_target_qd[elbow_qd_start] = 0.0
control.joint_f[elbow_qd_start] = 1.0
```

Migration checklist:

- Replace any `joint_qd_start` indexing of `joint_target_q` with `joint_target_q_start` or `joint_q_start` when `use_coord_layout_targets=True`.
- Keep `joint_target_qd`, `joint_f`, joint limits, axes, and gain arrays on the DOF layout.
- If manually constructing `Actuator(..., pos_indices=...)`, usually omit `target_pos_indices`; under coordinate layout it defaults to `pos_indices`.
- If a model still warns about target layout during `finalize()`, set the flag earlier. Setting it after `ModelBuilder` construction is too late for that builder.

## Recipe 2: select robots in replicated worlds

Use `ArticulationView` when the same policy, controller, or reset logic is applied across many worlds. The pattern below builds two robots per world and selects them with a stable `(world, articulation, dof)` shape.

```python
import re
import numpy as np
import warp as wp
import newton
from newton.selection import ArticulationView

newton.use_coord_layout_targets = True

def make_robot(label: str) -> newton.ModelBuilder:
    b = newton.ModelBuilder()
    root = b.add_link(label=f"{label}/root")
    tip = b.add_link(label=f"{label}/tip")
    j0 = b.add_joint_fixed(parent=-1, child=root, label=f"{label}/fixed_root")
    j1 = b.add_joint_revolute(parent=root, child=tip, axis=newton.Axis.Z, label=f"{label}/elbow")
    b.add_articulation([j0, j1], label=label)
    return b

template_world = newton.ModelBuilder()
template_world.add_builder(make_robot("robot_A"))
template_world.add_builder(make_robot("robot_B"), xform=wp.transform((1.0, 0.0, 0.0), wp.quat_identity()))

scene = newton.ModelBuilder()
scene.replicate(template_world, world_count=3, spacing=(2.0, 0.0, 0.0))
model = scene.finalize(device="cpu")
state = model.state()
control = model.control()

robots = ArticulationView(
    model,
    pattern="robot_*",
    include_joints=re.compile(r"elbow"),
)
q = robots.get_dof_positions(state)      # shape: (3, 2, 1)
forces = robots.get_dof_forces(control)  # shape: (3, 2, 1)

forces_np = forces.numpy()
forces_np[:, :, 0] = 0.25
robots.set_dof_forces(control, forces_np)
```

Label-selection debugging rules:

- `pattern="robot_*"` is a glob, not a regex.
- `re.compile(r"robot_[AB]")` is a regex full match; use `.*` if the desired match is only a substring.
- Articulation patterns match full articulation labels.
- Joint and link filters match final path components such as `elbow`, not necessarily the whole slash-delimited label.
- If labels collide by leaf name, inspect `view.link_labels`, `view.joint_labels`, and `view.shape_labels` to disambiguate.

## Recipe 3: use sites as robot frames or tool markers

Sites are useful for end-effector frames, debug markers, and attachment points. They are stored as shape-like markers with site flags but do not collide and do not contribute mass.

```python
import warp as wp
import newton

builder = newton.ModelBuilder()
base = builder.add_link(label="robot/base")
tool = builder.add_link(label="robot/tool")
j0 = builder.add_joint_fixed(parent=-1, child=base, label="robot/base_fixed")
j1 = builder.add_joint_revolute(parent=base, child=tool, axis=newton.Axis.Z, label="robot/tool_joint")
builder.add_articulation([j0, j1], label="robot")

# Tool center point, visible for debugging but not collidable.
tcp_site = builder.add_site(
    body=tool,
    xform=wp.transform(wp.vec3(0.0, 0.0, 0.1), wp.quat_identity()),
    label="robot/tool/tcp",
    visible=True,
)

# Equivalent marker via a shape helper.
finger_site = builder.add_shape_sphere(
    body=tool,
    radius=0.01,
    as_site=True,
    label="robot/tool/finger_marker",
)
model = builder.finalize()
```

Use the returned site indices or labels in APIs that accept site/shape labels. For sensor-specific update timing, route to the sensors/visualization skill.

## Recipe 4: solve IK then copy into position targets

This pattern solves a small IK batch and writes the result into position-control targets. It uses coordinate layout so `joint_target_q` can receive `joint_q` values directly.

```python
import warp as wp
import newton
import newton.ik as ik

newton.use_coord_layout_targets = True
builder = newton.ModelBuilder()
base = builder.add_link(label="arm/base")
tip = builder.add_link(label="arm/tip")
j0 = builder.add_joint_revolute(parent=-1, child=base, axis=newton.Axis.Z, label="arm/shoulder")
j1 = builder.add_joint_revolute(parent=base, child=tip, axis=newton.Axis.Z, label="arm/elbow")
builder.add_articulation([j0, j1], label="arm")
model = builder.finalize(requires_grad=True)
control = model.control()

n_problems = 1
joint_q = model.joint_q.reshape((n_problems, model.joint_coord_count))
ik_q = wp.empty_like(joint_q)
pos_obj = ik.IKObjectivePosition(
    link_index=tip,
    link_offset=wp.vec3(0.0, 0.0, 0.0),
    target_positions=wp.array([wp.vec3(0.5, 0.0, 0.0)], dtype=wp.vec3),
)
solver = ik.IKSolver(model, n_problems, [pos_obj], optimizer=ik.IKOptimizer.LM)
solver.step(joint_q, ik_q, iterations=40)

# Copy the solved coordinate vector into position targets.
control.joint_target_q.assign(ik_q.flatten())
```

When only part of a robot should follow IK, copy just that coordinate slice into `control.joint_target_q`; leave grippers or other joints on separate target values.

## Recipe 5: add a PD actuator with optional delay and clamping

Use builder registration for normal simulation models. It groups compatible single-DOF actuator calls into vectorized actuators at finalization.

```python
import newton
from newton.actuators import ClampingMaxEffort, ControllerPD

newton.use_coord_layout_targets = True
builder = newton.ModelBuilder()
link = builder.add_link(label="hinge/link")
joint = builder.add_joint_revolute(parent=-1, child=link, axis=newton.Axis.Z, label="hinge/joint")
builder.add_articulation([joint], label="hinge")

builder.add_actuator(
    ControllerPD,
    index=builder.joint_qd_start[joint],
    pos_index=builder.joint_q_start[joint],
    kp=50.0,
    kd=5.0,
    delay_steps=1,
    clamping=[(ClampingMaxEffort, {"max_effort": 20.0})],
)
model = builder.finalize()
state = model.state()
control = model.control()
control.joint_target_q[model.joint_target_q_start.numpy()[joint]] = 0.25

# For manual stepping outside a solver loop, zero output before actuator accumulation.
for actuator in model.actuators:
    control.joint_f.zero_()
    actuator.step(state, control)
```

If using `ControllerPID` or a delayed actuator, create two actuator states and swap them each step.

## Recipe 6: model-based joint impedance for heterogeneous robots

Use `ControllerJointImpedance` when you need model-based compensation and all controlled joints are scalar revolute/prismatic joints. Build a controller model with one articulation per robot type or robot instance, then map the controller DOFs to flat simulation arrays.

```python
import numpy as np
import warp as wp
import newton
from newton import JointTargetMode
from newton.controllers import ControllerJointImpedance

ctrl_builder = newton.ModelBuilder()
# Add scalar-DOF robot articulations to ctrl_builder.

scene_builder = newton.ModelBuilder()
# Add matching scalar-DOF robots to the simulation scene.
for i in range(scene_builder.joint_dof_count):
    scene_builder.joint_target_mode[i] = int(JointTargetMode.EFFORT)
model = scene_builder.finalize()
state = model.state()
control = model.control()
newton.eval_fk(model, model.joint_q, model.joint_qd, state)

robot_count = max(ctrl_builder.articulation_count, 1)
max_dofs = max(1, model.joint_dof_count)
default_indices = wp.array(np.arange(model.joint_dof_count, dtype=np.uint32), dtype=wp.uint32)
controller = ControllerJointImpedance(
    builder=ctrl_builder,
    default_dof_indices=default_indices,
    stiffness=wp.zeros((robot_count, max_dofs), dtype=wp.float32),
    damping=wp.zeros((robot_count, max_dofs), dtype=wp.float32),
    use_gravity_compensation=True,
    use_coriolis_compensation=False,
    use_inertia_decoupling=True,
)
inputs = controller.input()
outputs = controller.output()
inputs.joint_q = state.joint_q
inputs.joint_qd = state.joint_qd
inputs.joint_q_des = wp.zeros_like(state.joint_q)
inputs.joint_qd_des = wp.zeros_like(state.joint_qd)
outputs.joint_f = control.joint_f
controller.step(inputs=inputs, outputs=outputs, dt=1.0 / 60.0)
```

Before using this recipe, verify that `ctrl_builder` is non-empty and contains no free/ball/distance joints. If the scene has multiple robot types, compute `max_dofs` as the largest per-robot scalar DOF count, not the total scene DOF count.

## Recipe 7: optional neural policy dependency check

Use import availability before loading a policy file. This avoids confusing model-load errors when optional packages are not installed.

```python
import importlib.util

has_warp_nn = importlib.util.find_spec("warp_nn.runtime") is not None
has_onnx = importlib.util.find_spec("onnx") is not None
has_torch = importlib.util.find_spec("torch") is not None

if not (has_warp_nn and has_onnx):
    print("ONNX policy validation/inference is unavailable; install the Newton ONNX extra for ONNX policies.")
if not has_torch:
    print("Torch policy inference is unavailable; install a Torch extra only if the workflow needs Torch checkpoints.")
```

ONNX policy examples commonly map policy output actions into `control.joint_target_q` after applying a scale and adding nominal joint positions. With coordinate-layout targets and a floating base, reserve the first seven coordinates for base pose before writing actuated joint targets.
