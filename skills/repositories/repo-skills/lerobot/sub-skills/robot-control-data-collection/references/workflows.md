# Hardware workflows

Every workflow has two phases: **plan without side effects**, then a separately
confirmed live phase. A command shown below is a template; replace all
angle-bracket values and confirm the selected config's `--help` output first.

## 1. Prepare and identify devices

1. Install only the needed extra(s), for example `lerobot[feetech]`,
   `lerobot[dynamixel]`, `lerobot[openarms]`, `lerobot[rebot]`,
   `lerobot[intelrealsense]`, `lerobot[reachy2]`, `lerobot[lekiwi]`, or
   `lerobot[phone]`. For Unitree, install the Unitree SDK separately and do
   not claim that `lerobot[unitree_g1]` alone is sufficient.
2. Check CLI parsing without a device: `lerobot-calibrate --help`,
   `lerobot-teleoperate --help`, `lerobot-record --help`,
   `lerobot-replay --help`, `lerobot-find-port --help`, and
   `lerobot-find-cameras --help`. Some older installed wrappers may not expose
   useful help; report that instead of invoking a default.
3. For serial buses, with power off or torque disabled and the arm secured,
   run `lerobot-find-port`. Disconnect only the named bus when prompted, press
   Enter, record the one-port difference, and reconnect. If zero or multiple
   differences appear, stop and repeat with other USB devices removed. Check
   permission/group membership rather than chmod-ing a port as a first choice.
4. For OpenCV or RealSense, use `lerobot-find-cameras opencv` or
   `lerobot-find-cameras realsense` only with no robot motion possible. Record
   the identifier and reported default profile. `reachy2_camera` and `zmq`
   require manual service configuration.
5. For CAN, verify the interface name, adapter type, bitrate, CAN-FD setting,
   and wiring against the hardware manual. `lerobot-setup-can --mode=setup`
   changes host interfaces; `--mode=test` sends motor enable/disable frames;
   both are live operations and require explicit confirmation.

## 2. Configure motor IDs (one-time, live)

Use `lerobot-setup-motors --robot.type=<type> --robot.port=<port>` or the
teleoperator equivalent only when the assembly instructions say the motor is
isolated and the operator can stop power immediately. For SO-100/SO-101,
configure each motor in the prescribed order with only the intended motor
connected; do not guess IDs or run setup on a daisy chain. A setup failure is a
hardware stop: check cabling, power and the selected motor variant before
retrying. OMX is documented as factory-configured and normally does not need
setup.

## 3. Calibrate robot and teleoperator

Use one stable id per physical device and repeat that id in every later command:

```bash
lerobot-calibrate --robot.type=<robot-type> --robot.port=<follower-port> --robot.id=<follower-id>
lerobot-calibrate --teleop.type=<teleop-type> --teleop.port=<leader-port> --teleop.id=<leader-id>
```

For bimanual or network devices, use the exact nested arm/IP fields from
`--help`. The calibration CLI enforces exactly one of `--robot.*` or
`--teleop.*`; it connects with automatic calibration disabled, calls the
interactive device calibration, and disconnects in `finally`.

For SO arms and most Feetech leaders/followers, place all joints near the
middle, confirm at the prompt, then move each joint through its full safe range.
For reBot, place the arm in its documented zero pose; its connection-time
re-zero behavior differs from persistent motor-range calibration. For Phone,
calibration aligns the phone pose with the robot frame and requires the phone
app/browser to be connected. Unitree exoskeleton calibration is interactive and
requires every joint's full range. Never calibrate with a person in the sweep
area or with an unknown emergency-stop state.

## 4. Supervised teleoperation

First run a short, low-speed or bounded-duration session without recording:

```bash
lerobot-teleoperate \
  --robot.type=<robot-type> --robot.id=<follower-id> --robot.port=<follower-port> \
  --teleop.type=<teleop-type> --teleop.id=<leader-id> --teleop.port=<leader-port> \
  --fps=<control-fps>
```

Add the camera map only after camera discovery and feature checks. Use
`--teleop_time_s=<small-duration>` for a bounded smoke run where supported.
Keep `display_data=false` while diagnosing control; visualization is optional
and can add load. Check the arm starts in a known safe pose, action keys match
robot features, the operator can release/disable input, and the loop's cadence
summary is close to its target. Stop on jitter, stale observations, unexpected
torque, a missing camera, or any communication warning.

For Reachy 2, enabled robot parts and teleoperator parts must match. If an
external VR application already sends commands, set the robot's external
command option as documented so LeRobot does not send duplicate commands. For
LeKiwi, confirm host/client IP and watchdog behavior. For Unitree, confirm the
robot server, network latency and controller before physical operation. For
keyboard teleoperation, global input permissions differ from recording control
keys on headless/Wayland sessions.

## 5. Record demonstrations

Use the dry-run builder first, then a confirmed command such as:

```bash
lerobot-record \
  --robot.type=<robot-type> --robot.id=<follower-id> --robot.port=<follower-port> \
  --teleop.type=<teleop-type> --teleop.id=<leader-id> --teleop.port=<leader-port> \
  --dataset.repo_id=<owner/task> --dataset.single_task="<one-sentence task>" \
  --dataset.fps=30 --dataset.num_episodes=<small-count> \
  --dataset.episode_time_s=<seconds> --dataset.reset_time_s=<seconds> \
  --dataset.push_to_hub=false
```

Set `--dataset.fps` to the intended control/data cadence. `record` rejects a
missing teleoperator, builds dataset features from robot features plus
processors, and rejects a robot-camera dataset whose FPS differs from the
requested recording FPS. A newly created id is timestamped unless
`--dataset.no_stamp=true`; `--resume=true` retains the existing id and checks
robot compatibility. Keep upload disabled until local inspection succeeds.

The interactive recording controls are terminal-safe `n`/right-arrow for next,
`r`/left-arrow to discard and re-record, and `q`/Escape to stop. Reset phases
are paced but not recorded. Ctrl-C enters cleanup; verify the dataset is
finalized and both robot and teleoperator disconnect. Inspect frames, camera
sharpness, task labels, action/state features, episode counts, and actual
cadence before training. Route inspection or dataset schema work to
`dataset-workflows`.

## 6. Replay a dataset episode

Replay is physical actuation even though it writes no dataset:

```bash
lerobot-replay \
  --robot.type=<robot-type> --robot.id=<follower-id> --robot.port=<follower-port> \
  --dataset.repo_id=<owner/task> --dataset.episode=<episode-index> \
  --dataset.root=<local-root-if-needed> --dataset.fps=<dataset-fps>
```

Before confirmation, validate that the episode exists, the dataset's action
feature names and units match the selected robot, the dataset FPS is the
intended playback cadence, calibration identity is current, and the workspace
is clear. Place the robot in a known start pose and keep the emergency stop in
hand. Start with the shortest known-safe episode or a bounded local fixture.
The replay implementation connects before sending actions and disconnects in a
`finally` block; a command builder must never call it automatically.
