# Hardware overview

This reference records the verified public device names and their conditional
boundaries. A name being registered does not prove that the local SDK, bus,
firmware, power supply, or physical device is present.

## Core abstractions

- `RobotConfig` is a draccus choice registry. Device configurations expose a
  lower-case `type`; common fields are `id` and optional `calibration_dir`.
- `Robot` exposes `observation_features`, `action_features`, `is_connected`,
  `connect(calibrate=True)`, `is_calibrated`, `calibrate`, `configure`,
  `get_observation`, `send_action`, and `disconnect`.
- `TeleoperatorConfig` is a choice registry with `type`, `id`, and optional
  `calibration_dir`. `Teleoperator` exposes `action_features`,
  `feedback_features`, `is_connected`, `connect`, `is_calibrated`,
  `calibrate`, `configure`, `get_action`, `send_feedback`, and `disconnect`.
- `CameraConfig` is a choice registry. Camera configs carry `fps`, `width`,
  and `height`; camera implementations provide discovery, connect, read,
  `async_read`, and disconnect.
- Motor buses share connect/disconnect, scalar and synchronous read/write,
  torque enable/disable, and calibration read/write contracts. A bus may use
  serial, CAN, or a vendor SDK.

All device objects support context-manager cleanup, but live workflows should
still retain a `try/finally` disconnect path.

## Robot types

| `--robot.type` | Transport/family | Install gate or notes |
|---|---|---|
| `so100_follower`, `so101_follower` | Feetech serial bus | `feetech`; identify each arm's serial port |
| `koch_follower` | Feetech serial bus | `feetech`; calibration is device-specific |
| `bi_so_follower` | Two Feetech follower arms | `feetech`; both nested arm ports must be distinct |
| `lekiwi` | Feetech base plus cameras | `lekiwi`; local/wired mode |
| `lekiwi_client` | Network client for a LeKiwi host | `lekiwi`; remote IP and service must be confirmed |
| `omx_follower` | Dynamixel serial bus | `dynamixel`; factory-configured hardware |
| `hope_jr_hand`, `hope_jr_arm` | Feetech serial bus | `hopejr`; optional kinematics/camera fields |
| `reachy2` | Reachy SDK/network | `reachy2`; IP/port and SDK state are live prerequisites |
| `openarm_follower` | Damiao CAN/CAN-FD | `openarms` or `damiao`; Linux only in the documented support |
| `bi_openarm_follower` | Two Damiao CAN arms | `openarms`; four independent interfaces must be mapped safely |
| `rebot_b601_follower` | Damiao CAN through bridge or SocketCAN | `rebot`; adapter and motor IDs must match the arm |
| `bi_rebot_b601_follower` | Two reBot B601 arms | `rebot`; left/right ports and calibration are independent |
| `unitree_g1` | Unitree SDK/network and optional ZMQ camera | `unitree_g1` plus separately installed Unitree SDK |
| `earthrover_mini_plus` | Frodobots SDK service | Confirm the SDK service and URL before use |

`mock_robot` occurs in deterministic tests only. It is not a physical robot
route and must never be reported as hardware validation.

## Teleoperator types

Serial leader families include `so100_leader`, `so101_leader`, `koch_leader`,
`omx_leader`, `openarm_leader`, `openarm_mini`, `rebot_102_leader`, and their
`bi_*` variants. Other registered choices include:

- `keyboard`, `keyboard_ee`, and `keyboard_rover` (global key backend may be
  unavailable on Wayland/headless systems for *teleoperation*);
- `gamepad` (pygame, with optional HID fallback);
- `phone` (iOS HEBI Mobile I/O or Android WebXR, `phone` extra, network access);
- `homunculus_glove` and `homunculus_arm` (serial and calibration);
- `reachy2_teleoperator` (Reachy SDK/network and matching enabled parts);
- `unitree_g1` (remote joystick-only or serial exoskeleton arms).

A recording requires a teleoperator. The recording CLI rejects an omitted
teleoperator; policy deployment belongs to `lerobot-rollout` and the policy
route rather than this route.

## Camera types

- `opencv`: local USB/V4L/DirectShow/AVFoundation-style cameras. Discovery is
  supported; the identifier may be an index or path and can change after
  reconnects.
- `intelrealsense`: RealSense color/depth camera. Discovery and serial/name
  selection are supported; install `intelrealsense` and validate requested
  profiles against the sensor.
- `reachy2_camera`: Reachy camera service. Configure it manually with the
  robot/SDK settings; it is not auto-discovered.
- `zmq`: network camera publisher. Configure server address, port, and camera
  name manually; no local discovery is provided.

`read()` is blocking; `async_read(timeout_ms)` waits for a fresh buffered frame
with a timeout; `read_latest(max_age_ms)` is non-blocking but can reject stale
frames. Camera dimensions and FPS become dataset feature shapes and cadence
constraints, so validate them before enabling torque or motion.

## Motor and transport map

- Feetech uses the `feetech` extra and serial permission/port checks.
- Dynamixel uses `dynamixel` and a serial adapter.
- Damiao uses `damiao`/`openarms` and `python-can`; OpenArm uses Linux
  SocketCAN or SLCAN configuration, often CAN FD with nominal 1 Mbps and data
  5 Mbps defaults in its config.
- Robstride uses `robstride` and `python-can`.
- reBot uses `rebot`, which supplies the Damiao bridge and smart-servo bridge
  packages; `can_adapter` distinguishes a dedicated bridge from SocketCAN.
- LeKiwi additionally uses ZeroMQ for a client/host arrangement.

Do not infer a bus from a product name alone. Confirm the concrete config,
adapter mode, motor model/IDs, bitrate, and installed package before a live
connection.

## Plugin discovery

At CLI startup LeRobot's plugin registration scans installed distributions
whose names begin with `lerobot_robot_`, `lerobot_camera_`,
`lerobot_teleoperator_`, `lerobot_policy_`, or `lerobot_env_`, then imports
matching packages so their choice registrations run. A custom config class
must follow the `SomethingConfig`/`Something` naming convention and register
its lower-case choice. The factory derives the implementation module from the
config module and class name. Check package metadata and importability first;
plugin discovery imports code and is not a device connection, but third-party
imports can still fail or have their own side effects.
