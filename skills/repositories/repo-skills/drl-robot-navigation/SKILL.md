---
name: drl-robot-navigation
description: "Guide ROS/Gazebo Velodyne mobile-robot navigation with the
  DRL-robot-navigation TD3 implementation, including simulator setup,
  environment contracts, bounded training, checkpoints, and policy evaluation."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# DRL robot navigation

Use this repo skill when a task involves the `reiniscimurs/DRL-robot-navigation`
workflow: Deep-RL navigation of a Pioneer 3-DX-style robot in Gazebo, using a
simulated Velodyne PointCloud2 sensor, ROS Noetic, PyTorch TD3, checkpoints, or
TensorBoard. This is a Researcher operating graph, not a general ROS tutorial
and not a replacement for a live simulator.

## Route the request

- **Build, ROS/Gazebo startup, Docker/headless execution, xacro, topics, or
  missing simulator tools:** read [`simulation-setup`](sub-skills/simulation-setup/SKILL.md).
- **Observation length, Velodyne angular bins, action scaling, reset/step,
  collision, goal, or reward semantics:** read
  [`navigation-environment`](sub-skills/navigation-environment/SKILL.md).
- **Actor/critic architecture, replay buffer, TD3 hyperparameters, bounded
  training, checkpoint creation, or TensorBoard:** read
  [`td3-training`](sub-skills/td3-training/SKILL.md).
- **Loading an actor, validating `.pth` files, or running bounded policy
  evaluation:** read
  [`policy-evaluation`](sub-skills/policy-evaluation/SKILL.md).
- **A task spanning setup and execution:** start with `simulation-setup`, then
  hand the state/action contract to `navigation-environment` and the model
  artifact to `td3-training` or `policy-evaluation`.

## Baseline and prerequisites

The public README targets Ubuntu 20.04/ROS Noetic, Python 3.8.10, PyTorch 1.10,
TensorBoard, Gazebo, catkin, xacro, and the ROS packages needed by Gazebo and
RViz. The Python programs also use NumPy and `squaternion`. This repository has
no Python packaging metadata or installable distribution: keep `TD3/` on the
runtime import path and treat ROS as a system/runtime dependency.

For a simulator run, require a built catkin workspace, a running ROS master,
Gazebo ROS services, the Velodyne plugin, `/r1/odom`, `/r1/cmd_vel`, and
`/velodyne_points`. Do not replace the Velodyne topic with a 2-D laser without
also changing and validating the observation contract.

The smallest safe Python checks do not need ROS. Run the bundled helpers from
their own directories or with absolute paths; they do not import the source
training modules:

```bash
python3 sub-skills/navigation-environment/scripts/validate_navigation_contract.py self-test
python3 sub-skills/td3-training/scripts/replay_buffer_smoke.py
python3 sub-skills/td3-training/scripts/td3_model_smoke.py --device cpu
python3 sub-skills/policy-evaluation/scripts/check_policy_artifacts.py --help
```

Use `--check-cuda` only as an optional PyTorch device probe. It does not prove
that Gazebo GPU ray sensing works. Use the setup checker before any launch:

```bash
python3 sub-skills/simulation-setup/scripts/check_ros_prerequisites.py \
  --workspace <catkin-workspace> --json
```

A passing static checker or Python smoke is not a live ROS/Gazebo result. Read
[`references/troubleshooting.md`](references/troubleshooting.md) for the
cross-cutting failure boundary, and [`references/repo-provenance.md`](references/repo-provenance.md)
before deciding whether a checkout has drifted from this graph.

## Safety and reproducibility rules

1. Do not import `train_velodyne_td3.py` or `test_velodyne_td3.py` merely to
   inspect classes: both execute module-level simulator/training behavior.
2. Keep real training and evaluation bounded during development. The source
   defaults to millions of steps and the reference evaluator loops forever.
3. Preserve normalized TD3 actions in replay. Convert only the linear component
   for `GazeboEnv.step`: `[(a[0] + 1) / 2, a[1]]`.
4. Validate a 24-value state, 2-value action, checkpoint dimensions, and live
   topics before attributing a bad score to the policy.
5. Use temporary output directories for smoke runs. Do not run broad `killall`
   cleanup commands or build a network-dependent Docker image without explicit
   approval.
6. Report missing ROS/Gazebo, unavailable services, blocked hardware, skipped
   native cases, and incomplete evaluations as limitations—not as model failure.

## Evidence boundary

The graph was distilled from the pinned repository README, TD3 implementation,
catkin launch/configuration files, and the vendored Velodyne simulator metadata.
The source checkout is evidence, not a runtime dependency. The vendored sensor
package is summarized only to the extent needed to configure and diagnose this
navigation workflow.
