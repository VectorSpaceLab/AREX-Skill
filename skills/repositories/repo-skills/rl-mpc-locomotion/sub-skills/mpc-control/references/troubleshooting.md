# MPC troubleshooting

## `mpc_osqp` cannot import

**Symptoms:** `ModuleNotFoundError`, an undefined native symbol, an ABI/version error, or
the controller prints that the package must be installed. `ConvexMPCLocomotion` imports
the extension at module import time and exits the process if that import fails, so probe
`mpc_osqp` before importing the high-level locomotion class.

**Recovery:**

1. Run `scripts/check_mpc_api.py` and record the interpreter version, extension import
   exception, and missing public symbol without attempting simulation.
2. Route compiler, Eigen/OSQP/qpOASES, pybind11, and editable-install ordering to
   [setup-and-diagnostics](../../setup-and-diagnostics/SKILL.md). Rebuild in the active
   Python 3.8 environment rather than copying a binary from another interpreter or
   platform.
3. Confirm the binding exposes `ConvexMpc`, `QPSolverName`, `OSQP`, and `QPOASES`.
   `TEST == 42` is a useful identity check, not a solver-quality benchmark.
4. Retry the API probe. If it passes but the high-level class fails, report the next
   import traceback; do not claim a controller run.

Do not edit or vendor solver implementation internals as an operational workaround.
The public dependency is the compiled binding and its supported build process.

## Wrong input representation or shape

**Symptoms:** missing `"pos"`/`"vel"` fields, indexing errors at body quaternion or
velocity fields, broadcasting errors, or a torque result that is not length 12.

**Recovery:**

- In normal mode, use structured DOF arrays with 12 `"pos"` and 12 `"vel"` values and
  structured body values for quaternion `(x, y, z, w)`, linear velocity, and angular
  velocity. Keep the four legs in the same 3-joint order used by the robot model.
- In bridge mode, use a numeric DOF array with position/velocity columns and a flat
  body sequence whose consumed orientation/velocity slices are exactly `3:7`, `7:10`,
  and `10:13`. Set the bridge flag before constructing the runner.
- Do not pass bridge-mode DOFs to `RobotRunnerPolicy`; its observation code reads the
  structured fields. Do not pass a policy action as a three-value velocity command.
- Assert finite values and `(12,)` torque shape at the actuator boundary. A successful
  shape assertion does not establish safe physical behavior.

## Command or weight rejection

**Symptoms:** assertion failures in `DesiredStateCommand.updateCommand`, unexpected
weight dimensions, or policy/MPC behavior that changes abruptly when commands are
extended.

**Recovery:**

- Keep the first three entries as `[x_velocity, y_velocity, yaw_rate]`.
- For direct extended commands, provide exactly 13 nonnegative entries total. For the
  policy overload, provide exactly 12 nonnegative weights; the controller appends the
  thirteenth zero placeholder.
- Use `DesiredStateCommand.reset()` on episode/controller reset. Do not reuse a stale
  policy weight array after changing robot type.
- Remember that zero velocity commands leave the default FSM mode in recovery stand;
  they do not select locomotion or a gait.

## Gait phase, contact, or solver instability

**Symptoms:** all legs appear in swing/stance unexpectedly, a contact table has the
wrong length, a ground-normal calculation produces invalid values, or forces become
non-finite.

**Recovery:**

1. Call `setIterations(iterationsPerMPC, currentIteration)` before reading gait phases.
   Verify four offsets/durations and a horizon table length of `10 * 4` for the built-in
   convex controller.
2. Start the controller with a reset and let the first run initialize four contact-foot
   positions. In non-flat mode, do not request a ground-plane fit before contact history
   exists or when no feet are marked in contact.
3. Check the model's friction vector, body mass/inertia, body height, and foot positions;
   do not combine parameters from different robot types.
4. Keep `cmpc_alpha` at or below the implementation's guarded value (`1e-5`) unless a
   controlled experiment explicitly justifies a change. If the solver returns invalid
   forces, stop before applying torques and collect finite-value diagnostics.

The bundled probe checks interfaces and gait arithmetic only; it does not certify a
stable physical trajectory.

## FSM does not enter locomotion or falls back to recovery

**Symptoms:** a no-gamepad launch remains in recovery, a requested transition is ignored,
or `Parameters.locomotionUnsafe` is raised.

**Recovery:**

- Confirm `Parameters.control_mode` is set to `FSM_StateName.LOCOMOTION` before FSM
  initialization and that `operatingMode` is `NORMAL` when transition checks are wanted.
- In `TEST` mode, the current state runs without transition checks; it is not a safety
  bypass for arbitrary data. In normal mode, roll/pitch and leg-position checks can force
  a recovery transition.
- Check signs and frames: the estimator expects quaternion `(x, y, z, w)`, body-frame
  velocities are derived from the estimator rotation, and leg `p[2]` should not be above
  the hip for the safety check.
- Keep all safety checks enabled for a first application run. Do not fake gamepad events
  from a CPU-only harness; that behavior belongs to the simulator launcher.

## Policy runner fails while MIN/FSM works

**Symptoms:** importing or constructing `RobotRunnerPolicy` fails, checkpoint loading
falls back unexpectedly, CUDA inference fails, or policy observations have wrong values.

**Recovery:**

1. Confirm the CPU `RobotRunnerMin` API probe succeeds first. This separates MPC/solver
   failures from the policy stack.
2. Route Isaac Gym, Hydra, RSL-RL, CUDA device, and checkpoint resolution to
   [rl-training](../../rl-training/SKILL.md) and [isaac-gym-simulation](../../isaac-gym-simulation/SKILL.md).
3. Supply a checkpoint explicitly and verify its task/model matches the selected robot.
   A policy has 48 observation inputs and emits 12 actions; a missing or mismatched
   checkpoint must not be silently treated as a valid policy.
4. If Isaac Gym is unavailable, record policy/simulation as a required-backend block and
   continue with the CPU solver/API checks only.

## Isaac Gym or interactive input is unavailable

The controller's CPU modules and compiled solver can be checked independently. The
interactive launcher, policy import, simulator state producer, viewer, terrains, and
native interactive candidates require the closed-source Isaac Gym package; gamepad mode
also requires an input device. An A100 and CUDA-enabled PyTorch do not substitute for
that package. Route installation to [isaac-gym-simulation](../../isaac-gym-simulation/SKILL.md)
and report the backend as blocked until `import isaacgym` and a minimal simulator probe
pass.
