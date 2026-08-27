---
name: real-robot-operations
description: "Safety-gated real Push-T robot collection, evaluation, sensing,
  shared-memory IO, and real dataset conversion."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Real Robot Operations

Use this sub-skill for UR5 + RealSense + SpaceMouse workflows around real Push-T demo collection, checkpoint evaluation, shared-memory motion/camera IO, timestamp alignment, and raw real-data conversion.

## Route here when
- a task touches live robot preflight, demo capture, evaluation rollout, or real-robot data layout
- you need to reason about `RealEnv`, `RTDEInterpolationController`, `SingleRealsense`, `MultiRealsense`, `Spacemouse`, `SharedMemoryRingBuffer`, or `SharedMemoryQueue`
- you need to convert recorded robot episodes into a training-ready replay buffer or compute real Push-T metrics
- you need to diagnose timestamp, latency, camera, SpaceMouse, or RTDE failures

## Route elsewhere when
- the task is simulation-only training, evaluation, or Hydra workspace composition: use `../training-and-evaluation/`
- the task is generic ReplayBuffer, dataset schema, or sampler work: use `../data-and-replay-buffers/`
- the task is model, policy, checkpoint, or prediction-shape reasoning: use `../policies-and-models/`

## Bundled references
- [Real robot guide](references/real-robot-operations.md)
- [Troubleshooting](references/troubleshooting.md)
- [Prereq checker](scripts/check_real_robot_prereqs.py)

## Operating contract
- Never start the robot, cameras, or `spacenavd` from this skill.
- Treat emergency-stop reachability, camera connection, and SpaceMouse presence as manual safety confirmations.
- Use the bundled prereq checker only for import/executable/service inspection and optional RTDE socket reachability.
- Keep all real-robot commands bounded by the target robot IP, a known output directory, and the exact dataset/checkpoint path.
