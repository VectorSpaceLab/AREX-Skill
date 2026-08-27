# Actuators, controllers, selection, and IK

This reference summarizes Newton robotics-control APIs that are intended for public use. Import from `newton` and its public submodules; do not reach into private implementation modules.

## Public import surface

```python
import re

import numpy as np
import warp as wp

import newton
from newton import JointTargetMode
from newton.actuators import (
    Actuator,
    ClampingDCMotor,
    ClampingMaxEffort,
    ClampingPositionBased,
    ControllerPD,
    ControllerPID,
    Delay,
)
from newton.controllers import ControllerJointImpedance, ControllerJointImpedanceModelFree
from newton.ik import (
    IKJacobianType,
    IKObjectiveJointLimit,
    IKObjectivePosition,
    IKObjectiveRotation,
    IKOptimizer,
    IKSampler,
    IKSolver,
)
from newton.selection import ArticulationView
```

Primary installed signatures observed for Newton 1.6 development builds:

- `ControllerPD(kp, kd, const_effort=None)`
- `ControllerPID(kp, ki, kd, integral_max, const_effort=None)`
- `Actuator(indices, controller, delay=None, clamping=None, pos_indices=None, target_pos_indices=None, effort_indices=None, state_pos_attr="joint_q", state_vel_attr="joint_qd", control_target_pos_attr="joint_target_q", control_target_vel_attr="joint_target_qd", control_feedforward_attr="joint_act", control_output_attr="joint_f", control_computed_output_attr=None, requires_grad=False)`
- `ControllerJointImpedance(builder, *, default_dof_indices, stiffness, damping, use_gravity_compensation=True, use_coriolis_compensation=True, use_inertia_decoupling=True, has_qdd_feedforward=False, joint_q_idx=None, joint_qd_idx=None, joint_q_des_idx=None, joint_qd_des_idx=None, joint_qdd_idx=None, joint_f_idx=None, device=None, requires_grad=False)`
- `IKObjectivePosition(link_index, link_offset, target_positions, weight=1.0)`
- `IKObjectiveRotation(link_index, link_offset_rotation, target_rotations, canonicalize_quat_err=True, weight=1.0)`
- `IKSolver(model, n_problems, objectives, *, optimizer=IKOptimizer.LM, jacobian_mode=IKJacobianType.AUTODIFF, sampler=IKSampler.NONE, n_seeds=1, noise_std=0.1, rng_seed=12345, joint_dof_mask=None, ...)`
- `ArticulationView(model, pattern, *, include_joints=None, exclude_joints=None, include_links=None, exclude_links=None, include_joint_types=None, exclude_joint_types=None, include_loop_closing_joints=False, verbose=None)`

Run the bundled `scripts/check_robotics_apis.py` to confirm these names and signatures against the installed Newton package in the current environment.

## Target-control arrays and coordinate layout

Newton separates position targets, velocity targets, feedforward actuator inputs, and direct effort:

- `Control.joint_target_q`: joint position targets [m or rad].
- `Control.joint_target_qd`: joint velocity targets [m/s or rad/s].
- `Control.joint_act`: feedforward actuator input consumed by some controller paths.
- `Control.joint_f`: generalized forces/torques [N or N·m].

For new robotics code, opt in to the coordinate-layout target array before building any model:

```python
import newton

newton.use_coord_layout_targets = True
builder = newton.ModelBuilder()
# build joints/articulations, then finalize
model = builder.finalize()
control = model.control()
```

With `use_coord_layout_targets = True`, `control.joint_target_q` matches `state.joint_q` and has shape `(model.joint_coord_count,)`; use `model.joint_q_start` or the layout-aware `model.joint_target_q_start` for position targets. `control.joint_target_qd` and `control.joint_f` always use the DOF/velocity layout `(model.joint_dof_count,)`, indexed by `model.joint_qd_start`.

This matters for robots containing free, ball, or distance joints: their coordinate counts differ from their DOF counts, so old code that indexes position targets with DOF starts can silently shift every downstream target.

## Actuator pipeline

Actuators compute and accumulate effort into a caller-provided control array. The per-step order is:

1. Optional `Delay` reads delayed command inputs.
2. A `Controller` computes raw effort.
3. Zero or more `Clamping` stages bound the effort.
4. The result is scatter-added into `control.joint_f` or another configured output attribute.
5. Stateful controller and delay buffers are updated.

The caller must zero the output force array before stepping actuators when multiple actuator calls accumulate into the same target.

### Registering an actuator on a builder

```python
import warp as wp
import newton
from newton.actuators import ClampingMaxEffort, ControllerPD

newton.use_coord_layout_targets = True
builder = newton.ModelBuilder()
link = builder.add_link()
joint = builder.add_joint_revolute(parent=-1, child=link, axis=newton.Axis.Z)
builder.add_articulation([joint], label="arm")

# Velocity/force-space DOF index; for revolute/prismatic joints this is one scalar.
dof_index = builder.joint_qd_start[joint]
builder.add_actuator(
    ControllerPD,
    index=dof_index,
    kp=100.0,
    kd=10.0,
    delay_steps=2,
    clamping=[(ClampingMaxEffort, {"max_effort": 50.0})],
)
model = builder.finalize()
```

`ModelBuilder.add_actuator()` is for one SISO actuator DOF at a time. Repeated calls with compatible controller/clamping settings are grouped into vectorized `Actuator` instances during `finalize()`.

### Manual actuator construction

Manual construction is useful outside a full Newton model or for tests:

```python
import types
import warp as wp
from newton.actuators import Actuator, ClampingMaxEffort, ControllerPD, Delay

indices = wp.array([0], dtype=wp.uint32)
actuator = Actuator(
    indices=indices,
    controller=ControllerPD(
        kp=wp.array([100.0], dtype=wp.float32),
        kd=wp.array([10.0], dtype=wp.float32),
    ),
    delay=Delay(delay_steps=wp.array([1], dtype=wp.int32), max_delay=1),
    clamping=[ClampingMaxEffort(max_effort=wp.array([50.0], dtype=wp.float32))],
)

sim_state = types.SimpleNamespace(
    joint_q=wp.array([0.0], dtype=wp.float32),
    joint_qd=wp.array([0.0], dtype=wp.float32),
)
sim_control = types.SimpleNamespace(
    joint_target_q=wp.array([1.0], dtype=wp.float32),
    joint_target_qd=wp.array([0.0], dtype=wp.float32),
    joint_act=None,
    joint_f=wp.zeros(1, dtype=wp.float32),
)
state_a = actuator.state()
state_b = actuator.state()
sim_control.joint_f.zero_()
actuator.step(sim_state, sim_control, state_a, state_b, dt=0.01)
```

Stateful actuators include delayed actuators, `ControllerPID`, and neural controllers with history or recurrent state. Use two state buffers and swap them after every step. Stateless actuators, such as plain `ControllerPD` without delay, can be stepped without explicit state buffers.

## Neural actuator and policy checkpoints

Neural actuator controllers support two backend families:

- ONNX `.onnx` checkpoints use the Warp-NN runtime and the ONNX parser. In package terms this corresponds to the `onnx` optional dependency set.
- Torch `.pt2`, `.pt`, and `.pth`-style checkpoints use PyTorch. In package terms this corresponds to a Torch optional dependency set chosen for the user's CUDA/Python environment.

Do not instantiate a neural policy controller until the checkpoint file and optional backend are known to exist. For diagnosis, prefer import-availability checks first; the bundled script reports `warp_nn.runtime`, `onnx`, and `torch` without loading models.

## Joint-space impedance controllers

`ControllerJointImpedance` computes model-based joint-space impedance torques for a batch of robots. It creates an internal controller model from a `ModelBuilder`, computes forward kinematics and optional mass/gravity/Coriolis terms, then scatters torques into a flat output array.

Important constraints:

- The controller builder must contain at least one articulation.
- Only scalar revolute/prismatic joints and zero-DOF fixed joints are supported by `ControllerJointImpedance`; free, ball, distance, and other multi-coordinate joints are not valid for the PD error term.
- `default_dof_indices` maps concatenated per-robot controller DOFs into the flat simulation arrays. Its length must equal the sum of DOFs over all controller-builder articulations.
- `stiffness` and `damping` are `(robot_count, max_dofs)` arrays. Padding columns for shorter robots are ignored.
- Pass `stiffness=None` and/or `damping=None` when gains should be read from `controller.input()` buffers at each step instead of baked at construction.

Minimal control wiring pattern:

```python
import numpy as np
import warp as wp
import newton
from newton.controllers import ControllerJointImpedance

# ctrl_builder and scene_builder must describe matching scalar-DOF robots.
ctrl_builder = newton.ModelBuilder()
# ... add one or more revolute/prismatic/fixed-joint articulations ...

scene_builder = newton.ModelBuilder()
# ... add the same robot topology to the simulated scene ...
model = scene_builder.finalize()
state = model.state()
control = model.control()
newton.eval_fk(model, model.joint_q, model.joint_qd, state)

total_dofs = model.joint_dof_count
default_idx = wp.array(np.arange(total_dofs, dtype=np.uint32), dtype=wp.uint32)
controller = ControllerJointImpedance(
    builder=ctrl_builder,
    default_dof_indices=default_idx,
    stiffness=wp.zeros((ctrl_builder.articulation_count, total_dofs), dtype=wp.float32),
    damping=wp.zeros((ctrl_builder.articulation_count, total_dofs), dtype=wp.float32),
)
inputs = controller.input()
outputs = controller.output()
outputs.joint_f = control.joint_f
inputs.joint_q = state.joint_q
inputs.joint_qd = state.joint_qd
inputs.joint_q_des = control.joint_target_q
inputs.joint_qd_des = control.joint_target_qd
controller.step(inputs=inputs, outputs=outputs, dt=1.0 / 60.0)
```

If the controller is used in graph-captured GPU execution, bind the live input/output arrays before capture so recorded operations use stable buffer addresses.

## ArticulationView for robot batches

`ArticulationView` selects articulations by label and exposes stable tensor-shaped views of links, joints, DOFs, root state, and selected model/control/state attributes.

Selection rules:

- `pattern` matches full articulation labels.
- `include_joints`, `exclude_joints`, `include_links`, and `exclude_links` match final label path components for strings and regexes.
- Ordinary strings are glob patterns using `*` and `?`.
- A compiled `re.Pattern` uses regular-expression full matching. Add `.*` explicitly for substring regex matching.
- Integer selector lists select explicit indices; keep them unique and sorted ascending.
- A view cannot mix global articulations with per-world articulations.
- Replicated worlds must have a constant articulation count per world for a single view.

Common view methods:

- `get_dof_positions(source)` / `set_dof_positions(target, values, mask=None)`
- `get_dof_velocities(source)` / `set_dof_velocities(target, values, mask=None)`
- `get_dof_forces(control)` / `set_dof_forces(control, values, mask=None)`
- `get_root_transforms(source)` / `set_root_transforms(target, values, mask=None)`
- `get_link_transforms(source)` / `get_link_velocities(source)`
- `get_attribute(name, source)` / `set_attribute(name, target, values, mask=None)`
- `eval_fk(target, mask=None)`, `eval_jacobian(state, ...)`, and inverse-dynamics helpers
- `get_actuator_parameter(...)` / `set_actuator_parameter(...)` for actuator component arrays

Returned arrays are shaped around world and articulation axes; for example, selected DOF positions are shaped like `(world_count, count_per_world, joint_coord_count_for_view)`.

## Sites for robotics control

Sites are non-colliding, zero-mass shape markers. Use them for tool-center points, target frames, debugging markers, spatial tendon routing, or sensor attachment points. They do not participate in collisions and do not affect body inertia.

Create a site directly:

```python
import warp as wp
import newton

builder = newton.ModelBuilder()
body = builder.add_body(mass=1.0)
tcp_site = builder.add_site(
    body=body,
    xform=wp.transform(wp.vec3(0.0, 0.0, 0.2), wp.quat_identity()),
    label="tool_center",
    visible=True,
)
```

Or use a shape method with `as_site=True`:

```python
marker = builder.add_shape_sphere(
    body=body,
    radius=0.02,
    as_site=True,
    label="gripper_tip_marker",
)
```

Use label selectors to find site-backed shapes when a downstream API accepts site/shape labels. Route detailed sensor-update questions to the sensors/visualization skill.

## Inverse kinematics workflow

Newton's IK system is batched. Each objective stores target arrays sized by the base problem count, and `IKSolver` can expand each problem into multiple candidate seeds.

Minimal batched IK pattern:

```python
import warp as wp
import newton
import newton.ik as ik

model = builder.finalize(requires_grad=True)
n_problems = 1
ee_link_index = 0  # choose the body/link index to constrain

target_positions = wp.array([wp.vec3(0.4, 0.2, 0.5)], dtype=wp.vec3)
target_rotations = wp.array([wp.vec4(0.0, 0.0, 0.0, 1.0)], dtype=wp.vec4)

pos_obj = ik.IKObjectivePosition(
    link_index=ee_link_index,
    link_offset=wp.vec3(0.0, 0.0, 0.0),
    target_positions=target_positions,
)
rot_obj = ik.IKObjectiveRotation(
    link_index=ee_link_index,
    link_offset_rotation=wp.quat_identity(),
    target_rotations=target_rotations,
)
limit_obj = ik.IKObjectiveJointLimit(
    joint_limit_lower=model.joint_limit_lower,
    joint_limit_upper=model.joint_limit_upper,
    weight=0.1,
)

joint_q = model.joint_q.reshape((n_problems, model.joint_coord_count))
out_q = wp.empty_like(joint_q)
solver = ik.IKSolver(
    model=model,
    n_problems=n_problems,
    objectives=[pos_obj, rot_obj, limit_obj],
    optimizer=ik.IKOptimizer.LM,
    jacobian_mode=ik.IKJacobianType.AUTODIFF,
)
solver.step(joint_q, out_q, iterations=50, step_size=1.0)
```

Shape contract reminders:

- `joint_q_in` and `joint_q_out` must be 2-D arrays shaped `(n_problems, model.joint_coord_count)`.
- `IKObjectivePosition.target_positions` is a `wp.array[wp.vec3]` with length `n_problems`.
- `IKObjectiveRotation.target_rotations` is a `wp.array[wp.vec4]` with length `n_problems`; quaternions are stored as `(x, y, z, w)`.
- `joint_dof_mask` is a model-wide boolean array shaped `(model.joint_dof_count,)`, supported by the LM optimizer with `sampler=IKSampler.NONE`.
- Free/ball/distance quaternion-integrated joints must be masked all-or-nothing when using `joint_dof_mask`.
- If `sampler=IKSampler.NONE`, `n_seeds` must be `1`.

To update targets frame-by-frame, call `pos_obj.set_target_position(problem_idx, wp.vec3(...))`, `pos_obj.set_target_positions(new_positions)`, `rot_obj.set_target_rotation(problem_idx, wp.vec4(...))`, or `rot_obj.set_target_rotations(new_rotations)` after the solver has assigned objective batch layout.
