# Safety and actuation gates

LeRobot's abstractions make physical control uniform, not harmless. Treat every
unknown device state as unsafe until an operator verifies it.

## Gate levels

| Level | Examples | Required action |
|---|---|---|
| 0: static | read bundled docs, inspect config text, `--help`, package probe | no hardware or network opening |
| 1: discovery | serial before/after port identification, camera enumeration, CAN interface status | secure robot, disable motion, operator present |
| 2: configuration | motor ID/baudrate writes, CAN interface setup, SDK/server startup | explicit device/adapter confirmation; know how to cut power |
| 3: calibration | joint sweep, leader zeroing, phone pose calibration | clear sweep volume, low-risk posture, emergency stop ready |
| 4: controlled motion | bounded teleop or short record | low speed/duration, no people in workspace, release/stop path tested |
| 5: trajectory replay/policy rollout | `lerobot-replay`, policy deployment | dataset/policy compatibility, start pose, workspace, emergency stop, explicit final confirmation |

A dry-run command builder never advances a gate. An import or mock test never
advances a gate. Ask for confirmation again if the robot, port, workspace,
operator, calibration, dataset, or policy changes.

## Pre-motion checklist

- Identify the exact robot and teleoperator, including left/right arms and
  bimanual ordering.
- Confirm mechanical fastening, correct motor voltage variant, cabling, adapter,
  CAN-H/CAN-L/GND, power supply, and no loose tools or body parts in the sweep.
- Confirm the stable serial path or CAN interface by discovery; do not use a
  stale `/dev/ttyACM*` or guessed channel.
- Confirm calibration id and file belong to this device and are current.
- Confirm software limits (`max_relative_target`, joint limits, velocity/gains)
  are conservative for the first motion. Software clipping is not a hardware
  emergency stop.
- Test the emergency-stop device and tell the operator the exact stop action.
  Keep power isolation accessible. Have a second observer for a first live run.
- Set a short duration or episode count. Keep Hub upload and external
  visualization off while diagnosing.
- For network hardware, verify the intended IP, isolated network, watchdog,
  server ownership, and latency. Do not expose a control service broadly.

## During and after motion

Start with no-load, low-speed, small-range motion. Watch the arm, motor LEDs,
current/noise, camera frames, cadence report, and log simultaneously. Stop
immediately for unexpected motion, torque, heat, noise, stale frames, repeated
packet errors, watchdog timeouts, a person entering the workspace, or loss of
operator input. Use the physical stop first; Ctrl-C is not guaranteed to stop a
mechanically dangerous motion instantly.

Keep `try/finally` cleanup. LeRobot implementations generally disable torque or
smoothly stop on disconnect according to device config; verify the behavior for
the specific robot rather than changing `disable_torque_on_disconnect` casually.
After a stop, record the last command/error, leave power isolated, inspect the
mechanical state, and only reconnect after the fault is understood.

## Recording and replay safety

Recording sends the teleoperator action before saving the frame, so a dataset
can contain the action actually sent after processing/clipping. Validate
features and cadence before motion. Save locally first with
`--dataset.push_to_hub=false`; upload is separate.

Replay reads actions and sends them to the robot at dataset cadence. Before
confirming replay, verify robot type, calibration, action names/units, episode
index, start pose, limits, workspace, and a recovery plan. Do not use replay as
a “dry run.” Policy-driven physical evaluation is a separate rollout gate.
