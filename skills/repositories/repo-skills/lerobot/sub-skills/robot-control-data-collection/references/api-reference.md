# Hardware API and CLI reference

## Factories and interfaces

Use these imports for non-actuating config and feature inspection:

```python
from lerobot.cameras import Camera, CameraConfig, make_cameras_from_configs
from lerobot.motors.motors_bus import Motor, MotorCalibration, MotorsBusBase
from lerobot.robots import Robot, RobotConfig, make_robot_from_config
from lerobot.teleoperators import Teleoperator, TeleoperatorConfig, make_teleoperator_from_config
```

The factories choose built-in devices by config `type`, then can resolve a
third-party config through the plugin/device-class convention. Constructing a
config is non-actuating; constructing a device may create calibration
directories but should not be treated as a live check. `connect()` is the
boundary that opens a bus, SDK session, camera, or network channel.

Robot methods and their side effects:

| Method/property | Use | Live gate |
|---|---|---|
| `observation_features` | shape/key contract for observations | no device required |
| `action_features` | action names/shape accepted by `send_action` | no device required |
| `is_connected` | state check | no new connection |
| `connect(calibrate=True)` | open transport and optionally calibrate | **actuates/opens** |
| `is_calibrated` | current calibration state | may reflect cached file |
| `calibrate()` | collect/save hardware-specific calibration | **interactive live** |
| `configure()` | apply runtime motor/control settings | **live** |
| `get_observation()` | read state and cameras | connected live |
| `send_action(action)` | command motors/robot | **actuates** |
| `disconnect()` | release resources, often disable torque | live cleanup |

Teleoperators mirror the lifecycle. Use `get_action()` to read input and
`send_feedback()` only when the implementation supports feedback. Camera
implementations expose `find_cameras()` and `connect(warmup=True)` in addition
to frame reads; `async_read` can time out if the stream is slow or stale.

`ensure_safe_goal_position(goal_present_pos, max_relative_target)` clamps each
target relative to the current position. A scalar applies to every key; a dict
must have exactly the same keys. Treat it as a software limit, not a
substitute for a physical stop or joint-limit review.

## CLI ownership

| Command | Contract |
|---|---|
| `lerobot-find-port` | interactive before/after serial-port difference; no motor command, but requires user unplug/replug |
| `lerobot-find-cameras [opencv|realsense]` | enumerates and may open camera backends; no robot action |
| `lerobot-setup-motors` | changes motor IDs/baudrate on supported devices; live and potentially destructive to configuration |
| `lerobot-setup-can` | host CAN setup or live motor test/speed probe; inspect mode before running |
| `lerobot-calibrate` | exactly one robot or teleoperator; connect without auto-calibration, calibrate, finally disconnect |
| `lerobot-teleoperate` | reads teleoperator actions, reads robot observations, sends actions at configured FPS; no dataset |
| `lerobot-record` | requires robot, teleoperator, and dataset; sends actions and writes episodes; optional Hub upload |
| `lerobot-replay` | reads one dataset episode and sends each action at dataset FPS; no recording, still actuates |
| `lerobot-rollout` | policy-driven rollout/evaluation; route to policy-training-inference |

Use `--help` as a parser-level check. CLI names and registered type names are
not interchangeable: `--robot.type=so101_follower` selects a robot, while
`--teleop.type=so101_leader` selects a teleoperator.

## Feature and cadence checks

Before live recording, compare:

1. robot `observation_features` to camera keys/shapes and the selected
   observation processor;
2. robot `action_features` to teleoperator actions and action processor;
3. dataset feature names and types to both processed dictionaries;
4. camera requested profiles to actual reported width/height/FPS;
5. dataset FPS to the control timer. `record_loop` explicitly rejects a
   dataset FPS different from the requested loop FPS.

When the dataset contains depth, color is an `(H, W, 3)` uint8 feature and depth
is an `(H, W, 1)` uint16 sibling whose values are millimetres; zero depth means
no measurement. Actual RealSense profiles may be adjusted to the nearest
supported mode, so use the connected device's result rather than assuming the
request was honored.

## Test evidence boundaries

Deterministic mock tests exercise config validation, connect/disconnect guards,
teleoperation loop pacing, record/resume, replay cadence, and cleanup without
physical devices. Camera tests also cover invalid profiles, read-before-connect,
cleanup after warmup/config failures, retries, stale/timeout behavior, and
reconnect. These are useful contract evidence only; they do not prove serial,
CAN, SDK, camera optics, workspace, or safety behavior on a live device.
