# MPC workflows

## 1. Prepare and smoke-test the CPU path

1. Use [setup-and-diagnostics](../../setup-and-diagnostics/SKILL.md) to create the
   documented Python 3.8 environment, keep PyTorch 1.10 with CUDA 11.3, install the
   package and its `rsl_rl` dependency in a controlled order, and build the local
   `mpc_osqp` extension. Do not let a broad policy dependency silently replace the
   pinned PyTorch build.
2. Run the bundled `scripts/check_mpc_api.py`. It performs imports, enum/model checks,
   shape checks, and a small gait arithmetic check without opening a viewer, reading a
   checkpoint, allocating a simulator, or solving a long trajectory.
3. If the extension is absent or has an ABI error, stop at the diagnostic boundary and
   route the build details back to setup-and-diagnostics. Do not work around the failure
   by silently switching to an undocumented solver.
4. Treat the CPU smoke as successful only when the package imports, all three public
   robot models construct, the expected enum names exist, and the extension's public
   symbols are present. This does not verify simulation or RL.

A minimal application-level setup is:

```python
from MPC_Controller.common.Quadruped import RobotType
from MPC_Controller.robot_runner.RobotRunnerMin import RobotRunnerMin

runner = RobotRunnerMin()
runner.init(RobotType.ALIENGO)
# Supply one valid DOF record, body record, and 3-value command per control tick.
torques = runner.run(dof_states, body_states, commands)
```

The records must obey the [API contract](api-reference.md); placeholder all-zero body
records are useful only for interface inspection and are not a stability test.

## 2. Normal state-to-torque loop

At each control step, in this order:

1. Build `commands = [x_vel, y_vel, yaw_rate]` as numeric scalars, with optional
   13-value nonnegative weights only when using the direct command bridge.
2. Read 12 joint positions/velocities and the trunk quaternion plus world linear/angular
   velocities into the normal structured simulator records.
3. Call `runner.run(...)`. The runner updates `DesiredStateCommand`, updates leg
   kinematics, clears old commands, updates the state estimator, executes either the
   FSM, direct MPC, or policy-to-FSM path, and converts leg commands to a 12-value
   torque vector.
4. Check `np.asarray(torques).shape == (12,)` and finite values before handing the
   result to an effort-mode actuator. Apply the vector every simulator frame; do not
   rely on simulator-side stiffness/damping to retain an effort.
5. On reset, call `runner.reset()` and reinitialize any external contact/body state.

For the normal simulator boundary, DOF fields are `"pos"` and `"vel"`; body fields are
`"pose"["r"]`, `"vel"["linear"]`, and `"vel"["angular"]`. For a numeric RL bridge,
set `Parameters.bridge_MPC_to_RL=True` only when the producer really supplies the
flat `(12, 2)` DOF array and 13-value body sequence described in the API reference.
Do not mix bridge-mode DOFs with the policy runner: policy observations index the
structured `"pos"` and `"vel"` fields.

## 3. Choose mode, gait, and FSM behavior

- Use `RobotRunnerMin` for a low-dependency MPC call without FSM transition logic.
- Use `RobotRunnerFSM` when recovery/passive/locomotion transitions and safety checks
  are part of the application. Set `Parameters.control_mode` to an FSM enum before
  initialization; do not mutate it from an unrelated thread during a control step.
- Use `RobotRunnerPolicy` only after the policy environment/checkpoint/CUDA gates pass.
  The policy changes weights, not the final actuator contract: MPC and the leg
  controller still produce the same 12 torques.
- Set `Parameters.cmpc_gait` to one of the public `GaitType` members. Gamepad input may
  update gait and control mode at runtime; direct applications should update those
  settings explicitly and synchronize them with the control loop.

## 4. Gamepad-free guidance

The interactive launcher accepts `--disable-gamepad`. With that flag, every loop uses
zero velocity/yaw commands and does not update gait or FSM mode from a controller. The
default FSM settings therefore begin in recovery stand, not locomotion. A gamepad-free
application that intentionally enters locomotion must set the desired `Parameters`
values in its own launcher before constructing the runner, keep safety checks enabled,
and provide real state records; zero commands alone do not prove walking behavior.

The launcher still creates a viewer, simulator, assets, and effort-mode actors even when
input is disabled. Therefore this route is unavailable until [isaac-gym-simulation](../../isaac-gym-simulation/SKILL.md)
verifies the closed-source Isaac Gym backend. For a CPU-only check, use the bundled API
probe rather than invoking the interactive launcher.

## 5. Policy handoff boundary

A policy runner receives normal structured DOF/body records, computes a 48-value policy
observation, emits 12 clipped/scaled actions, and appends the zero thirteenth weight
before MPC. The checkpoint is an application input; do not assume a latest-run fallback
is safe or reproducible. If loading fails, report the missing/incompatible checkpoint
and route configuration/checkpoint selection to [rl-training](../../rl-training/SKILL.md).
The policy path's `isaacgym` import and CUDA inference requirement make it a required
backend workflow, not a replacement for the CPU solver smoke.

## Deferred native candidates

Interactive simulator/controller demos, viewer loops, and native simulation tests are
intentionally deferred. They require Isaac Gym and, for gamepad operation, an input
receiver. Do not label them skipped because of a Python API error; label them deferred
or backend-blocked and retain the last successful CPU/API checks.
