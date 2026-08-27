---
name: go2-omniverse
description: "Guides Isaac Sim and IsaacLab workflows for Unitree Go2 and G1
  simulation, ROS 2 telemetry, headless rendering, and the real-robot
  digital-twin bridge."
disable-model-invocation: true
metadata:
  disco-role: operating
license: BSD 2-Clause
---

# go2_omniverse

Use this skill when a task involves the Unitree Go2/G1 digital twins, Isaac Sim
launchers, IsaacLab locomotion playback, simulated ROS 2 topics, headless hero
captures, or the Jetson-to-simulation twinbot bridge.

## Route the request

- **Simulation startup, robot/terrain selection, checkpoints, rendering, or
  capture:** read [`simulation-launch`](sub-skills/simulation-launch/SKILL.md).
- **Simulated topics, message types, QoS, TF/IMU conventions, camera, or LiDAR:**
  read [`ros2-telemetry`](sub-skills/ros2-telemetry/SKILL.md).
- **Real Go2 `/lowstate` forwarding, DDS discovery, IMU alignment, or kinematic
  playback:** read [`digital-twin`](sub-skills/digital-twin/SKILL.md).

For a request spanning routes, start with the launch route, then follow its
cross-link to the telemetry or twinbot route. Read the deeper references only
when the task needs exact flags, topic schemas, or failure recovery.

## Install and stack gate

Use a vendor-supported Isaac Sim 5.0 Python 3.11 environment and install only
the selected runtime components:

```bash
python -m pip install 'isaacsim[all,extscache]==5.0.0.0' \
  --extra-index-url https://pypi.nvidia.com
python -m pip install 'isaaclab==0.54.3'  # use an approved source when available
OMNI_KIT_ACCEPT_EULA=YES python -I -c 'import isaacsim; print("isaacsim import ok")'
```

The primary documented stack is Isaac Sim 5.0 with IsaacLab 0.54.3, Python 3.11,
bundled Jazzy ROS 2, Fast DDS, and an NVIDIA GPU. The repository's required
IsaacLab 0.54.3 distribution was not available during skill construction, so
this skill is a **partial draft**: do not claim a successful repository boot,
IsaacLab API inspection, or native CUDA launcher verification until that exact
runtime is supplied and rechecked.

Do not source a host ROS 2 installation into the Isaac Sim Python process on the
modern route. The launcher must use the Isaac-bundled ROS 2 libraries to avoid
Python ABI and duplicate-typesupport failures. Do not start a real robot, alter
DDS/network configuration, or send robot commands without explicit operator
control.

Run the bundled read-only prerequisite check before attempting a launch:

```bash
python scripts/check_runtime_prereqs.py --isaac-venv "$ISAAC_VENV"
```

The check reports missing packages, GPU visibility, and expected environment
variables; it does not launch Isaac Sim, download assets, or contact a robot.

## Common launch shape

Use the launcher that matches the runtime rather than manually rebuilding its
`PYTHONPATH` and `LD_LIBRARY_PATH` setup:

```bash
bash sub-skills/simulation-launch/scripts/launch_sim.sh \
  --project-root "$PWD" --isaac-venv "$ISAAC_VENV" \
  --robot go2 --robot-amount 1 --terrain flat --headless
bash sub-skills/simulation-launch/scripts/launch_sim.sh \
  --project-root "$PWD" --isaac-venv "$ISAAC_VENV" \
  --robot g1 --robot-amount 1 --headless
```

The bundled launcher adapter sets `OMNI_KIT_ACCEPT_EULA`, `ROS_DISTRO`, and
`RMW_IMPLEMENTATION`, and accepts explicit `--isaac-venv` and
`--isaaclab-path` values. It reproduces the repository launcher's bundled ROS
library discovery without requiring the original launcher file. See the
simulation route for capture, checkpoint, G1 asset, and Isaac 6/Humble details.

## Operational boundaries

- This is an inference/playback and telemetry project, not a verified training
  recipe. Checkpoint files are external runtime inputs and are not bundled here.
- The modern path publishes standard ROS 2 messages and a Float32MultiArray
  foot-force topic; it does not publish the legacy `go2_interfaces/Go2State`
  message. See the telemetry route before writing consumers.
- Twinbot mode mirrors real state into the sim. It is not a claimed learned
  Sim-to-Real control loop and does not provide absolute real-dog position.
- Custom USD environments, VR, Nav2, mixed Humble/Jazzy networking, Isaac 6,
  and full camera/LiDAR runtime behavior are qualified or unverified paths.

Read [`references/troubleshooting.md`](references/troubleshooting.md) for
cross-cutting install/import, ABI, checkpoint, asset, and backend failures. Read
[`references/repo-provenance.md`](references/repo-provenance.md) before deciding
whether this skill matches a newer checkout or needs refreshing.
