---
name: mpc-control
description: "Operate the CPU-side quadruped convex MPC controller, its
  robot/state/command interfaces, gait and FSM runners, policy bridge, and
  compiled solver extension."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# MPC control

Use this skill for low-level, CPU-side control questions: selecting a supported robot or
runner, converting state and commands into 12 joint torques, configuring gaits/FSM
transitions, checking the `mpc_osqp` binding, or diagnosing controller data-shape
failures. Keep Isaac Gym lifecycle and Hydra/RSL-RL training in the linked neighboring
skills rather than reproducing them here.

## Route first

- Read [the API contract](references/api-reference.md) before constructing records or
  calling a runner. It is the source of truth for enum values, array shapes, frame
  conventions, and policy boundaries.
- Follow [the workflow](references/workflows.md) for install/build order, CPU smoke
  checks, gamepad-free operation, and the state-to-torque loop.
- Use [troubleshooting](references/troubleshooting.md) for extension import errors,
  malformed simulator records, unsafe FSM transitions, and policy/checkpoint failures.
- For package installation, compiler/dependency ordering, or backend diagnostics, route
  to [setup-and-diagnostics](../setup-and-diagnostics/SKILL.md).
- For simulator assets, DOF effort mode, rigid-body records, terrains, viewer loops, or
  Isaac Gym availability, route to [isaac-gym-simulation](../isaac-gym-simulation/SKILL.md).
  For policy training/configuration, route to [rl-training](../rl-training/SKILL.md).

## Operating contract

1. Select one of `RobotType.ALIENGO`, `RobotType.A1`, or `RobotType.GO1`, and construct
   `Quadruped(robot_type)`. Do not invent a fourth robot model; Mini Cheetah is not an
   enabled public enum. Preserve the model's four-leg, three-joint-per-leg ordering.
2. Select `ControllerType.FSM`, `ControllerType.MIN`, or `ControllerType.POLICY`.
   `RobotRunnerFSM` adds state transitions, `RobotRunnerMin` calls convex MPC directly,
   and `RobotRunnerPolicy` computes learned MPC weights before entering the FSM.
3. Call `runner.init(robot_type)` once, then call `runner.run(dof_states, body_states,
   commands)` once per control step. Reset between episodes with the runner's `reset()`.
   The result is a NumPy `float32` vector of exactly 12 torques, ordered as four
   consecutive three-joint leg blocks.
4. Keep the input representation consistent. Normal simulator mode uses structured
   DOF/body records; `Parameters.bridge_MPC_to_RL` changes the low-level MPC path to
   numeric arrays, but the policy runner still expects the structured DOF fields.
5. Commands begin with `[x_velocity, y_velocity, yaw_rate]`. Optional MPC weights must
   be nonnegative and have the exact documented length. A zero command is safe input,
   not an implicit request to enter locomotion.
6. Never claim a simulation or RL run is verified on an installation without Isaac Gym.
   CPU imports, model construction, gait arithmetic, and the solver binding are
   separately checkable; RL/simulation remains a required-backend block when that
   closed-source package cannot be imported.

## Controller boundaries

- `DesiredStateCommand` stores velocity/yaw commands and a 13-element MPC weight
  vector. `ConvexMPCLocomotion` chooses the gait, estimates contact/ground state,
  solves for stance forces, and fills swing/stance leg commands.
- `LegController` combines feed-forward force/torque, Cartesian PD, and joint PD through
  each leg Jacobian. `zeroCommand()` must precede each controller call so stale commands
  cannot survive a failed branch; `updateCommand()` is the torque boundary.
- FSM mode starts from `Parameters.control_mode`. In normal operation, recovery stand,
  passive, and locomotion transition through `ControlFSM`; safety checks can redirect
  unsafe locomotion to recovery. Test mode runs the current state without transition
  checks.
- The policy bridge is optional and heavyweight: it imports the RL/policy stack, needs a
  valid checkpoint and CUDA policy runtime, produces 12 scaled nonnegative weights, and
  appends the required thirteenth gravity-placeholder weight before MPC. It is not a
  substitute for the convex-MPC smoke test.

## Verification gate

Run the bundled `scripts/check_mpc_api.py` as a read-only API/extension probe. Treat an
extension import failure as a build/runtime diagnosis, not as evidence that the control
math is wrong. The prepared handoff passed Python 3.8, PyTorch 1.10/CUDA 11.3 on an
A100 allocation, package imports, `rsl_rl`, and `mpc_osqp`; Isaac Gym was unavailable,
so RL/simulation remains an explicit required-backend block. Do not run interactive
native demos or simulator tests as part of a CPU smoke check; they are deferred until
the required Isaac Gym backend is installed and verified. Keep review reports and test
fixtures outside this runtime subtree. Preserve this separation when handing the
controller to another application: API success is not a claim of gait stability, robot
safety, or sim-to-real readiness.
