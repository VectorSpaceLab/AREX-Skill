---
name: navigation-environment
description: "Operate and validate the GazeboEnv observation, action, reset,
  timing, and reward contract for the ROS/Gazebo Velodyne navigation environment
  without requiring a live simulator."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Navigation environment

Use this skill when a downstream agent needs to reason about the mobile-robot
`GazeboEnv` interface, prepare a compatible observation/action, diagnose a
sensor or ROS integration failure, or check a synthetic transition. This skill
is a distilled contract, not a simulator launcher and not a TD3 training guide.

## Operating contract

- The repository's training configuration uses `environment_dim=20` and four
  robot features, so every observation is a flat numeric vector of length 24.
- The first 20 values are Velodyne distance bins, initialized to 10 and
  updated by the point-cloud callback. The final four values are, in order,
  distance to goal, relative goal heading, linear action, and angular action.
  `reset` returns the two action slots as 0; `step` places the action used for
  that transition in them. There is no separate previous-action history in
  the implementation, so do not invent one.
- The environment-facing action is `[linear_x, angular_z]`: linear is in
  `[0, 1]`, angular is in `[-1, 1]`. `step` publishes these values directly;
  it does not rescale them. A TD3 actor output in `[-1, 1]` therefore needs its
  first component mapped with `(a_linear + 1) / 2` before calling `step`.
- `done` becomes true on a laser collision or a goal hit. A goal hit is
  reported separately as `target=True`; collision and target reward priority
  is target first, then collision.
- Use `scripts/validate_navigation_contract.py` for offline numeric checks.
  It imports no ROS package, starts no process, and is the preferred check for
  state length, action range, point-bin fixtures, and threshold behavior.

## Safe reasoning workflow

1. Confirm the caller has ROS Noetic/Ubuntu 20.04-compatible ROS message and
   Gazebo dependencies, plus Python dependencies used by the environment
   (`numpy` and `squaternion`). A live run additionally needs `roscore`,
   `roslaunch`, Gazebo, and a built catkin workspace with the scenario and
   Velodyne plugin packages. This host-independent skill does not install or
   launch any of them.
2. Treat a relative launch name as relative to the environment module's
   `assets` directory, not the caller's current directory. The repository's
   `multi_robot_scenario.launch` includes the empty TD3 world and spawns model
   `r1`.
3. Validate an observation as 20 finite sensor values followed by four finite
   robot values. Reject 23- or 25-value vectors rather than silently padding or
   truncating them.
4. Validate action-space provenance. If an actor produced `[-1, 1]` for both
   dimensions, transform only the linear component before using this
   environment contract.
5. For a synthetic sensor case, reduce points into the same 20 angular bins,
   compute the minimum distance per bin, and then apply the strict collision
   threshold. Keep simulator verification explicitly unavailable when ROS or
   Gazebo is absent.
6. Interpret `reset` and `step` as ROS-dependent calls. A valid offline vector
   does not prove that odometry, PointCloud2, publishers, or physics services
   are connected.

## Scope boundaries

This skill covers constructor prerequisites and launch resolution, point-cloud
reduction, state/action/reward semantics, reset randomization, ROS interfaces,
and predictable numeric/integration failures. Do not use it to explain TD3
network architecture, replay-buffer behavior, optimizer settings, training
loops, model checkpoints, or installation procedures beyond naming prerequisites.
See the bundled references for the detailed contract and troubleshooting.

## Numeric and evidence notes

The source callback has no explicit finite-value or zero-horizontal-range
 guard. Use the validator's stricter finite-input policy for synthetic data;
never turn NaN or an `acos` domain error into a claimed sensor reading.

## Evidence and verification status

The contract was distilled from the pinned repository's environment module,
launch file, scenario xacro/URDF, Velodyne description and Gazebo plugin, and
training caller. The offline validator is checked with its help/parser path,
self-test, a valid 24-value fixture, invalid 23/25-value fixtures, action-range
mismatches, a synthetic point cloud, and strict threshold cases. No ROS,
Gazebo, `roscore`, `roslaunch`, or catkin runtime is claimed or required here.
