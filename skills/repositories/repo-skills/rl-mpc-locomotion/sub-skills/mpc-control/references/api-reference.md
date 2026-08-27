# CPU MPC API reference

This reference describes the public Python-facing contracts recovered from the controller.
The implementation uses `numpy.float32` (`DTYPE`) for most numeric state and command
arrays. Unless stated otherwise, a column vector is shaped `(3, 1)` and a four-leg
collection is ordered leg `0, 1, 2, 3`, with three joints per leg.

## Enums and robot models

Import `RobotType` from `MPC_Controller.common.Quadruped` and the other enums from
`MPC_Controller.utils`:

```python
RobotType.ALIENGO, RobotType.A1, RobotType.GO1
ControllerType.FSM, ControllerType.MIN, ControllerType.POLICY
GaitType.TROT, GaitType.WALK, GaitType.BOUND
FSM_StateName.PASSIVE, FSM_StateName.LOCOMOTION, FSM_StateName.RECOVERY_STAND
FSM_OperatingMode.TEST, FSM_OperatingMode.NORMAL, FSM_OperatingMode.TRANSITIONING
```

The numeric enum values are `RobotType` auto-values 1/2/3; `GaitType` values are TROT
`0`, BOUND `1`, and WALK `6`; FSM state values are PASSIVE `0`, LOCOMOTION `4`, and
RECOVERY_STAND `6`. `Quadruped(robot_type)` rejects unsupported values. Its three
available model contracts are:

| model | abad length | hip/knee length | body mass | nominal height |
| --- | ---: | ---: | ---: | ---: |
| ALIENGO | 0.083 m | 0.25 / 0.25 m | 18.082 kg | 0.35 m |
| A1 | 0.08505 m | 0.2 / 0.2 m | 25.5 kg | 0.26 m |
| GO1 | 0.08 m | 0.213 / 0.213 m | 10.408 kg | 0.26 m |

Each model has four friction coefficients, all `0.4`, a body name of `trunk`, and a
13-element default MPC weight vector. `getHipLocation(leg: int)` returns `(3, 1)` and
only accepts leg indices `0..3`. Geometry, mass, inertia, and weight values are model
parameters, not interchangeable tuning defaults.

## Parameters and commands

`Parameters` is a class of class-level settings. Important defaults are:

- `controller_dt = 0.01` seconds, `cmpc_gait = GaitType.TROT`,
  `cmpc_alpha = 1e-5`, `cmpc_solver_type = 2`, and `cmpc_py_solver = 1`.
- `bridge_MPC_to_RL = False`, `control_mode = RECOVERY_STAND`,
  `operatingMode = NORMAL`, and `FSM_check_safety = True` by default.
- `flat_ground = False`; non-flat mode estimates a ground normal from contacted feet.
- `MPC_param_scale` and `MPC_param_const` map policy outputs into 12 MPC weights:
  the resulting ranges are `[1, 9]` for the first three, `[30, 70]` for the next
  three, and `[0, 2]` for each of the last six.

Use `DesiredStateCommand()` and
`updateCommand(commands, _weight=None)`. `commands[0:3]` are scalar forward/lateral
velocity and yaw-rate commands. With no `_weight`, extra command entries must be
exactly 13 nonnegative values. With `_weight`, the supplied iterable must contain
exactly 12 nonnegative values; the method appends `0.0` as the thirteenth weight. The
stored result is `mpc_weights`; `reset()` clears commands and weights.

## State, leg, and torque records

`ControlFSMData` is a structured record containing `_quadruped`, `_stateEstimator`,
`_legController`, and `_desiredStateCommand`. A controller data assembly must populate
all four before calling `ConvexMPCLocomotion.initialize()` or `ControlFSM`.

`StateEstimator.update(body_states)` fills a `StateEstimate` with position, world/body
linear velocity, world/body angular velocity, quaternion orientation, rotation matrix,
RPY vectors, ground normals, and `ground_R_body_frame`. The estimator also exposes
`setContactPhase(phase)`, `getResult()`, and `reset()`.

- Normal simulator mode expects `body_states["pose"]["r"]` as quaternion
  `(x, y, z, w)`, `body_states["vel"]["linear"]` as three values, and
  `body_states["vel"]["angular"]` as three values. Position is not read by the
  estimator update; height is initialized/updated from the quadruped and feet.
- With `bridge_MPC_to_RL=True`, `body_states` is a flat sequence with orientation at
  indices `3:7`, world linear velocity at `7:10`, and world angular velocity at
  `10:13`. The first three values are not consumed by this update path.
- Contact phase is a `(4, 1)`-compatible truthy array. In non-flat mode, four recent
  contact foot positions are used to estimate a normalized ground plane; avoid calling
  that estimator with no initialized contact history.

`LegController` owns four `LegControllerData` and four `LegControllerCommand` records.
Each leg's `q`, `qd`, `p`, and `v` are `(3, 1)`; its Jacobian `J` is `(3, 3)`. A command
contains `(3, 1)` `tauFeedForward`, `forceFeedForward`, `qDes`, `qdDes`, `pDes`, and
`vDes`, plus `(3, 3)` Cartesian/joint `kp` and `kd` matrices. The lifecycle is:

```python
leg_controller.updateData(dof_states)
leg_controller.zeroCommand()
# controller fills command records
leg_torques = leg_controller.updateCommand()  # float32 shape (12,)
```

Normal `dof_states` is a structured record with `"pos"` and `"vel"` arrays containing
12 joint values. Bridge mode instead expects a numeric `(12, 2)`-compatible array,
where columns `0` and `1` are position and velocity. The torque calculation is
`tauFeedForward + J.T @ (forceFeedForward + Cartesian_PD) + joint_PD` for each leg,
then concatenation into the four three-joint blocks.

## Gait and swing contracts

`OffsetDurationGait(nSegment, offset, durations, name)` takes four-element offsets and
durations in MPC segments. Call `setIterations(iterationsPerMPC, currentIteration)`
before `getContactState()` or `getSwingState()`. These return `(4, 1)` phase values;
`getMpcTable()` returns a flattened horizon contact table of length `nSegment * 4`.
`getCurrentSwingTime(dtMPC, leg)` and `getCurrentStanceTime(dtMPC, leg)` return seconds.
The convex controller uses a fixed horizon of 10 and constructs trotting, bounding,
pronking, pacing, galloping, walking, and trot-running schedules internally. The public
`GaitType` enum intentionally exposes only TROT, WALK, and BOUND.

`FootSwingTrajectory` accepts `(3, 1)` initial/final positions through
`setInitialPosition()` and `setFinalPosition()`, a scalar height through `setHeight()`,
and computes with `computeSwingTrajectoryBezier(phase: float, swingTime: float)`. Phase
is expected in `[0, 1]`; `getPosition()`, `getVelocity()`, and `getAcceleration()` each
return `(3, 1)` arrays.

## Convex MPC and solver extension

`ConvexMPCLocomotion(_dt: float, _iterationsBetweenMPC: int)` has a fixed horizon length
of 10 and computes `dtMPC = _dt * _iterationsBetweenMPC`. Call `initialize(data)` once
per controller reset. It constructs the compiled solver with the selected robot mass,
inertia, four legs, horizon 10, `dtMPC`, `cmpc_alpha`, and `mpc_osqp.QPOASES`. Call
`run(data)` at each control step; it fills leg force/Cartesian commands and returns no
torque itself. The caller obtains torques from `LegController.updateCommand()`.

The optional compiled module `mpc_osqp` must expose `ConvexMpc`, `QPSolverName`,
`OSQP`, `QPOASES`, and `TEST` (the current binding reports `TEST == 42`). Its public
binding is equivalent to:

```python
solver = mpc_osqp.ConvexMpc(
    mass, inertia, num_legs, planning_horizon, timestep, alpha, mpc_osqp.QPOASES
)
forces = solver.compute_contact_forces(
    qp_weights, com_position, com_velocity, com_roll_pitch_yaw,
    ground_normal_vec, com_angular_velocity, foot_contact_states,
    foot_positions_body_frame, foot_friction_coeffs, desired_com_position,
    desired_com_velocity, desired_com_roll_pitch_yaw,
    desired_com_angular_velocity,
)  # sequence of 12 force values for four legs
solver.reset_solver()
```

The force call takes 13 flat sequences: weight state is 13 values, each 3-vector is
three values, contact states cover the horizon and four legs, foot positions cover four
feet in body frame, and friction covers four feet. The exact horizon/table sizes must
match the solver instance. The binding is CPU-side C++/pybind11 code; no Isaac Gym
import is needed for this API, but the compiled extension must match the active Python
3.8/ABI and native build.

## Runners and policy bridge

All runners expose `init(robotType)`, `reset()`, and
`run(dof_states, body_states, commands) -> np.ndarray(12,)`.

- `RobotRunnerMin` assembles `ControlFSMData`, initializes `ConvexMPCLocomotion`, and
  calls MPC directly. It is the smallest end-to-end CPU controller boundary.
- `RobotRunnerFSM` assembles the same records and delegates to `ControlFSM`, whose
  states are PASSIVE, RECOVERY_STAND, and LOCOMOTION. In NORMAL mode, `Parameters` and
  safety checks select transitions; in TEST mode, the current state runs directly.
- `RobotRunnerPolicy(checkpoint=None)` additionally constructs `WeightPolicy`. Its
  policy observation is 48 values: scaled body linear/angular velocity, projected
  gravity, three scaled commands, 12 joint positions, 12 joint velocities, and the
  previous 12 actions. It emits 12 actions/weights, which are passed as `_weight` to
  `DesiredStateCommand`. This runner uses normal structured DOF records and requires
  the RL policy stack, CUDA policy execution, and a valid checkpoint; route those
  prerequisites to the RL and simulation skills.
