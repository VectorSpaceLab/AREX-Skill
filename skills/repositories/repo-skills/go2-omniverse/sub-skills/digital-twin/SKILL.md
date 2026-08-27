---
name: digital-twin
description: "Guides the real Go2 LowState to Jetson to Isaac Sim twinbot
  bridge, DDS discovery, IMU/joint mapping, and kinematic playback diagnosis."
disable-model-invocation: true
metadata:
  disco-role: operating
license: BSD 2-Clause
---

# Digital twin

Use this route when a physical Go2 should drive a simulated Go2, when
`/real_dog/joint_states` or `/real_dog/odom` is missing, or when the simulated
robot has incorrect joint pose/orientation. The sim-side launch is the bundled
simulation adapter with `--twinbot`; do not rely on an unbundled source launcher.

## Topology

The bridge has two operator-controlled processes: a CycloneDDS reader on the
Jetson subscribes to Unitree `/lowstate`; a FastDDS publisher forwards standard
`JointState` and `Odometry` messages to the Isaac host. The Isaac process then
uses `TwinbotSubscriber` to overwrite joint state and root pose after each
physics step. The bridge and sim must be diagnosed as separate sides.

## Safe workflow

1. Read [`references/twinbot-workflow.md`](references/twinbot-workflow.md) and
   confirm the Jetson ROS 2 Humble/Unitree SDK environment, Ethernet interface,
   Wi-Fi discovery, RMW choices, and operator permissions.
2. Run the bundled bridge helper without `--run` first; its default is a
   configuration-only dry run. Use `--run` only on the Jetson with the required
   packages and robot-side authorization.
3. Confirm `/real_dog/joint_states` and `/real_dog/odom` before starting the sim
   with `--twinbot`.
4. If joints are wrong, use the exact motor order and name mapping in
   [`references/message-mapping.md`](references/message-mapping.md). If the body
   flips or is half-blended, check IMU odometry and the post-step kinematic
   override before changing gains.

Read [`references/troubleshooting.md`](references/troubleshooting.md) for DDS,
queue, message, quaternion, and stale-data failures. This route never performs
SSH, changes network configuration, or sends commands to a real robot by itself.

## Limits and verification

Twinbot is visual real-to-sim playback, not a claimed learned Sim-to-Real loop.
The current implementation pins sim XY/Z at spawn because IMU data has no
absolute position. IsaacLab 0.54.3 and the Jetson runtime were unavailable
when this skill was built; no live bridge or full sim verification is claimed.
