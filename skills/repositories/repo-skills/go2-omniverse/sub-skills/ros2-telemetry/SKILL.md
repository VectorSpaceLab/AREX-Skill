---
name: ros2-telemetry
description: "Explains and diagnoses the go2_omniverse simulated ROS 2 topic
  contracts, message conversions, bundled runtime boundaries, and sensor
  caveats."
disable-model-invocation: true
metadata:
  disco-role: operating
license: BSD 2-Clause
---

# ROS 2 telemetry

Use this route for topic names/types, TF and quaternion conventions, `cmd_vel`,
QoS, custom interface compatibility, camera/LiDAR, or ROS graph diagnostics.

## Route by message surface

- Simulated per-robot data and command input: read
  [`references/ros2-topics.md`](references/ros2-topics.md).
- A consumer expects `go2_interfaces` messages: read
  [`references/legacy-interfaces.md`](references/legacy-interfaces.md) before
  changing a subscriber.
- Camera/LiDAR or sensor extension errors: read
  [`references/lidar-and-camera.md`](references/lidar-and-camera.md).
- `/real_dog/*`, Jetson LowState, or DDS interface discovery: route to
  [`digital-twin`](../digital-twin/SKILL.md), not this route.

## Safe diagnostic order

1. Confirm the simulation launcher and bundled ROS runtime are the same version;
   do not mix system Jazzy Python 3.12 libraries with Isaac Python 3.11.
2. Inspect topic names/types and QoS on the running graph before changing code.
3. Check frame IDs and quaternion order at the message boundary.
4. Only then debug camera/LiDAR extensions or custom interface builds.

Use the topic references to generate commands for an operator, but do not start
or mutate a ROS graph during a static skill check. The local Creator environment
had no `ros2` CLI and no live graph, so live topic verification remains pending.

Read [`references/troubleshooting.md`](references/troubleshooting.md) for ABI,
message-package, QoS, and optional sensor recovery.
