# Real-world and hardware workflows

Real-world robot workflows are high-risk. This reference is for planning, static config review, and operator-facing prerequisites. Do **not** recommend live robot motion, controller restarts, calibration changes, or hardware probes unless the user explicitly requests a controlled hardware validation and confirms that a trained operator is present.

## Safety gate before any hardware-affecting action

Require all of the following before suggesting a real-world launch:

- A responsible human operator is physically present, owns the robot session, and has explicit authority to run the task.
- Emergency stop and power-off paths are reachable and tested by the operator before the agent's involvement.
- Workspace is clear; no humans, loose tools, cables, or fragile objects are in the motion envelope.
- Robot IPs, camera serials, gripper devices, ROS/libfranka/vendor SDK versions, and controller node ranks are known.
- The intended target pose/task goal was recorded by a human through the robot's normal teaching/control workflow.
- The config has been statically checked and placeholders are resolved by YAML or node-local environment variables.
- The first dynamic validation is dummy/simulation/read-only where available, not live actuation.

If any item is missing, stop at a planning/checklist response.

## Typical topology

A common real-world RLinf topology is one GPU head/training node plus one or more robot control nodes:

```text
rank 0: GPU head/training node
  actor, rollout, optional reward/API server
rank 1..N: robot control nodes
  env workers and robot controllers
```

The Ray cluster and per-node environment variables are handled by the setup-and-cluster skill. This embodied skill only verifies that:

- `cluster.num_nodes` equals the intended number of joined nodes.
- `component_placement.actor` and `component_placement.rollout` are on GPU-capable nodes.
- `component_placement.env` points to the robot-control node group or to the camera-owning node when cameras are split from controllers.
- `cluster.node_groups[*].hardware.configs[*].node_rank` matches the node ranks in that group.
- Robot hardware fields are either explicitly set or intentionally filled from environment variables before Ray starts.

## Hardware config pattern

A single-arm Franka-style config normally has a GPU node group and a robot node group:

```yaml
cluster:
  num_nodes: 2
  component_placement:
    actor:
      node_group: gpu
      placement: 0
    rollout:
      node_group: gpu
      placement: 0
    env:
      node_group: franka
      placement: 0
    reward:
      node_group: gpu
      placement: 0
  node_groups:
    - label: gpu
      node_ranks: 0
    - label: franka
      node_ranks: 1
      hardware:
        type: Franka
        configs:
          - robot_ip: <ROBOT_IP>
            node_rank: 1
```

For multiple arms, extend `node_ranks`, `placement`, and `hardware.configs` together. A two-arm setup commonly uses `node_ranks: 1-2` for the robot group and `env.placement: 0-1`, with one hardware config per arm.

For split camera/controller arrangements, the env worker may run on the GPU/camera node while a controller rank is configured separately:

```yaml
hardware:
  type: Franka
  configs:
    - robot_ip: <ROBOT_IP>
      node_rank: 0
      camera_type: zed
      camera_serials: [<ZED_SERIAL>]
      gripper_type: robotiq
      gripper_connection: <serial_device>
      controller_node_rank: 1
```

## Environment-variable hardware enumeration

RLinf can fill unset hardware config fields from node-local environment variables named after the upper-case field name:

| YAML field | Environment variable | Notes |
| --- | --- | --- |
| `robot_ip` | `ROBOT_IP` | Identifier for Franka-like hardware. Multiple comma-separated values create/map multiple robot configs. |
| `camera_serials` | `CAMERA_SERIALS` | Comma handling depends on one-vs-many robot enumeration; keep counts aligned. |
| `gripper_connection` | `GRIPPER_CONNECTION` | Serial device for gripper controller when applicable. |
| `robot_url` | `ROBOT_URL` | Identifier pattern for DOSW1-style hardware. |
| `can_interface` | `CAN_INTERFACE` | Identifier pattern for GimArm-style hardware. |

Rules:

- YAML values win over environment variables.
- Variables are read on the node that owns the hardware config.
- Export variables before Ray starts; Ray workers inherit the environment captured at startup.
- `node_rank` and `controller_node_rank` are not filled from environment variables.
- If `configs: []` is used, the robot count is inferred from the identifier variable. Every multi-value variable must provide the same count.

## Real-world model/env families

| Family | Typical policy | Planning fields |
| --- | --- | --- |
| Franka peg insertion / pick-place / charger / cap tightening | CNN, Flow, OpenPI, RLT MLP, async PPO/SAC | `target_ee_pose`, `robot_ip`, camera type/serial, gripper type, demo buffer, success hold steps, action dimension. |
| Dual Franka | OpenPI or CNN/Flow variants | one hardware config per arm, split controller/camera fields, dual-arm action representation, per-arm safety space. |
| XSquare Turtle2 | CNN SAC | vendor controller container, SDK/ROS availability, camera IDs, target pose for success, dummy mode before real motion. |
| DOSW1 / GimArm | collection or real-world RL | vendor connection identifier (`ROBOT_URL`/`CAN_INTERFACE`), controller dependencies, task-specific override config. |
| FrankaSim | CNN/MLP/Flow/OpenVLA-style sim bridge | no live robot, but same state/image/action assumptions as real-world policies; useful for smoke testing. |

## Real-world launch-shape planning

A real-world async launch uses an async embodied training entrypoint rather than the synchronous simulator entrypoint:

```bash
python <async-embodied-training-entrypoint> \
  --config-path <embodied-config-dir> \
  --config-name <realworld_config_name> \
  runner.logger.log_path=<run_log_dir>
```

Before recommending this, verify:

1. The cluster is already up and node count matches `cluster.num_nodes`.
2. The exact Python environment and robot SDKs are available on every node that will own workers.
3. The config has no unresolved placeholders in `hardware`, `override_cfg`, model paths, demo buffers, or reward checkpoints.
4. The operator approves the action policy, target pose, maximum episode steps, and reset behavior.
5. A dummy/non-actuating config or simulation bridge was used for cluster/model plumbing if available.

## Real-world data collection

RLinf supports two embodied data collection styles:

### Episode collection wrapper

For simulator or robot episodes, the `data_collection` block can write `pickle` or `lerobot` output asynchronously:

```yaml
env:
  eval:
    data_collection:
      enabled: true
      save_dir: ${runner.logger.log_path}/collected_data
      export_format: pickle      # or lerobot
      only_success: true
      robot_type: panda
      fps: 10
```

Use `pickle` when the next step is reward-model preprocessing or custom analysis. Use `lerobot` when the next step is VLA SFT or LeRobot-compatible tooling. `only_success: true` reduces disk use but can remove negative examples needed by reward learning.

### Replay-buffer demonstration collection

Real-robot RLPD collection saves successful teleoperated trajectories to a replay buffer. The operator uses a SpaceMouse, GELLO, or vendor device; episodes are counted only when the task succeeds. Planning fields include:

```yaml
runner:
  num_data_episodes: 20
  record_task_description: true
env:
  eval:
    use_spacemouse: true
    use_gello: false
    gello_port: <serial_port_if_used>
    no_gripper: false
    override_cfg:
      target_ee_pose: [x, y, z, rx, ry, rz]
      success_hold_steps: 3
```

The resulting replay buffer stores observation, next observation, action, reward, done/termination/truncation flags, and `intervene_flags` that mark expert data. RLPD configs then point their demo/prior-data field at that buffer.

## Reward model data on real robots

Two real-world reward-data modes are common:

- **Keyboard/manual labels:** collect frames during teleop, label success/failure with operator keys, balance fail/success ratio, and write `train.pt`/`val.pt` directly for ResNet reward training.
- **Fixed-pose labels:** set a target pose and success threshold; collect episodes, save raw `pickle`, then preprocess into reward dataset splits.

Both require the same hardware safety gate as RL training. Manual labels should be reviewed for class imbalance and accidental key presses before model training.

## Real-world troubleshooting triage

- If robot workers fail to start, check node rank, hardware config ownership, and environment capture at Ray start before touching the robot.
- If action dimension errors appear, verify `ROBOT_PLATFORM`, `no_gripper`, gripper type, and whether the policy expects 6-DoF, 7-DoF, dual-arm, or chunked actions.
- If cameras fail, do not move the robot. Verify serial ownership, SDK installation, device permissions, and that the camera-owning node matches env placement.
- If reward/demo buffers look empty, inspect success threshold, `success_hold_steps`, `only_success`, operator interventions, and output directories.
- If a run controls the wrong robot, stop immediately; verify `robot_ip`, comma-separated environment variable ordering, and `node_rank` mapping.
