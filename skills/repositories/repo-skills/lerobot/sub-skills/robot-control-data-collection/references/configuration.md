# Hardware configuration

LeRobot CLIs use draccus nested choice configuration. Use `--help` on the
installed CLI to confirm a field before using it, and keep all device names,
ports, ids, and camera profiles explicit in the run record.

## Common shapes

```text
--robot.type=<registered robot choice>
--robot.id=<stable calibration identity>
--robot.port=<serial path or CAN channel>
--robot.cameras="{name: {type: opencv, index_or_path: 0, width: 640, height: 480, fps: 30}}"
--teleop.type=<registered teleoperator choice>
--teleop.id=<stable calibration identity>
--teleop.port=<serial path, when applicable>
```

Do not use a `--port` field at the root for these CLIs. Bimanual devices use
nested fields such as `--robot.left_arm_config.port`,
`--robot.right_arm_config.port`, and corresponding teleoperator fields. The
exact nested names belong to the selected config class.

`RobotConfig.__post_init__` rejects a robot camera whose `width`, `height`, or
`fps` is unset. A camera configuration outside a robot may allow omitted
values, but a recording plan should always specify them. Keep every camera key
unique. `opencv` accepts an index or path; `intelrealsense` requires a serial
number or name; `reachy2_camera` and `zmq` need manually configured service
parameters.

## Dataset recording fields

`lerobot-record` accepts a required `--dataset.*` block:

| Field | Meaning and gate |
|---|---|
| `repo_id` | Local/HF identifier; require a non-empty task-specific name |
| `single_task` | Short, accurate task description saved with frames |
| `root` | Optional local dataset root; choose and inspect before recording |
| `fps` | Control and dataset cadence; must match camera/control assumptions |
| `episode_time_s` | Maximum recording duration per episode |
| `reset_time_s` | Unrecorded reset phase between episodes |
| `num_episodes` | Number of episodes to retain |
| `video` | Encode camera streams as video when true |
| `push_to_hub` | Upload side effect; set false for local validation |
| `private`, `tags` | Hub publication metadata, only relevant if uploading |
| `resume` | Top-level recording flag; reuse an existing dataset only after schema check |
| `streaming_encoding` | Encode during capture; tune queue/encoder only after cadence is stable |

The script stamps a date-time suffix onto a newly created repo id unless
`--dataset.no_stamp=true`; resume preserves the existing id. Names beginning
with `eval_` are reserved for policy evaluation and are rejected by
`lerobot-record`; use the policy/rollout route for evaluation.

## Type and extra matrix

| Need | Extra(s) to validate |
|---|---|
| Core record/replay/calibration/teleop CLIs | `core_scripts` (dataset + hardware + viz) |
| Serial port enumeration | `hardware`, which includes `pyserial` |
| Feetech SO arms, Koch, LeKiwi, Hope Jr | `feetech`; LeKiwi also uses `pyzmq` |
| Dynamixel OMX | `dynamixel` |
| Damiao/OpenArm | `damiao`; `openarms` is the robot-facing composite |
| Robstride CAN motors | `robstride` |
| reBot B601/Arm 102 | `rebot` |
| Reachy 2 | `reachy2` and a reachable Reachy SDK endpoint |
| Intel RealSense | `intelrealsense` |
| Unitree G1 | `unitree_g1` plus separately installed Unitree SDK; the project composite does not include it automatically |
| Phone teleoperation | `phone`; mobile app/WebXR and same-network gate |
| Gamepad | `gamepad` |
| Visualization | `viz`; use `display_data=false` while diagnosing control |

An import failure from an optional backend is a hard stop for that device, not a
reason to silently choose another transport.

## Preflight order

1. Record OS, Python, LeRobot version, and extras; run safe import/version
   checks.
2. For serial hardware, run `lerobot-find-port` interactively by disconnecting
   only the named bus when prompted; prefer the resulting stable by-id alias
   after verifying it refers to the same device.
3. For cameras, run `lerobot-find-cameras opencv` or
   `lerobot-find-cameras realsense`; discovery may open cameras, so perform it
   only with the workspace safe and no motion permitted.
4. For CAN, inspect the interface and adapter mode. `lerobot-setup-can` has
   setup/test/speed modes; setup changes host networking and test sends motor
   enable/disable frames, so it is a live action and needs a separate gate.
5. Parse the complete command or construct config objects without calling
   `connect`. Compare robot action/observation features with teleoperator
   actions and camera shape/FPS before proceeding.
6. Calibrate the robot and teleoperator under supervision, then verify the
   calibration id/path is the one used by teleop and recording.
