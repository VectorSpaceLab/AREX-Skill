# Architecture Overview

Read this when a request crosses controller, simulator, and learned-policy
boundaries.

## Data flow

The project has two connected layers:

1. The Isaac Gym side creates one or more robot actors, advances PhysX, and
   exposes DOF and rigid-body state. The RL vectorized environment converts
   refreshed GPU tensors into observations and receives a 12-value action.
2. The controller side consumes commands and structured state, selects a robot
   model and gait/FSM runner, computes convex MPC stance forces and swing
   trajectories, and emits 12 joint torques.
3. In policy mode, `WeightPolicy` maps a learned 12-value action to nonnegative
   MPC weights. `RobotRunnerPolicy` feeds those weights into the controller;
   this remains a policy-to-MPC bridge, not direct position control.

## Route boundaries

- Use `mpc-control` for low-level records, enums, gait/FSM, state estimation,
  solver binding, runner behavior, and torque output.
- Use `isaac-gym-simulation` for gym handles, PhysX settings, URDF/assets,
  terrains, tensor refresh, effort control, viewer/gamepad lifecycle, and
  simulator cleanup.
- Use `rl-training` for Hydra overrides, task YAML, observation/action/reward
  contracts, RSL-RL checkpoints, evaluation, and TensorBoard.
- Use `setup-and-diagnostics` for install order, submodules, extension build,
  optional solvers, CUDA/Isaac Gym readiness, config/asset/checkpoint probes,
  and cross-cutting failures.

## Backend truth

CPU-side controller imports and the compiled `mpc_osqp` binding can be checked
without Isaac Gym. The configured RL and simulation paths require the external
Isaac Gym Preview 4 package and a compatible CUDA runtime. If `isaacgym` cannot
be imported, stop before training, viewer creation, simulator stepping, or
policy deployment and report the missing backend explicitly.

## Scope boundary

The repository demonstrates simulation and a sim-to-real goal, but it does not
provide a verified real-robot deployment workflow. Do not infer hardware safety,
calibration, gait stability, or sim-to-real readiness from package imports or a
successful static configuration check.
