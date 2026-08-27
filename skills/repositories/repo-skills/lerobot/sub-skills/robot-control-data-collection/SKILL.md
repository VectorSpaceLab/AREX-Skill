---
name: robot-control-data-collection
description: "Safely configure, calibrate, teleoperate, record, and replay
  LeRobot-compatible physical robots, motors, cameras, and teleoperators."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Robot control and data collection

Use this route when the task involves a physical LeRobot device, SO-100/SO-101,
LeKiwi, Reachy 2, OMX, OpenArm, reBot, Unitree G1, serial or CAN buses, camera
discovery, calibration, teleoperation, recording, replay, or hardware rollout.
This skill plans and verifies hardware work; it never substitutes for an
operator's emergency-stop procedure.

## Safety boundary

Treat `connect`, `calibrate`, `setup_motors`, camera probing that opens devices,
teleoperation, recording, and replay as side-effecting. Before any such command,
ask for the exact robot, teleoperator, ports/interfaces, workspace, power state,
operator, emergency-stop location, and the user's explicit confirmation to
proceed. The bundled scripts below are dry-run or non-opening probes only.
Never start a policy rollout from this route; send policy selection/checkpoints
to `policy-training-inference`, simulation to `simulation-and-rl`, and async or
network service orchestration to `extensions-and-services`.

## Required inputs and outputs

Collect these inputs before proposing a live command:

- robot type, unique `--robot.id`, port/CAN channel or robot IP, motor variant,
  and whether the device is single or bimanual;
- teleoperator type, id, port/network/phone mode, and whether it needs a
  keyboard, gamepad, SDK, or calibration;
- camera types, identifiers, requested width, height, FPS, color/depth streams,
  and whether each camera is attached to the robot or external;
- OS/backend, installed LeRobot extras, permissions, power supply, network and
  SDK credentials (if any);
- dataset repo id or local root, task text, target FPS, episode/reset duration,
  episode count, video/Hub policy, and replay episode;
- validation target: imports/help only, a mock test, a non-actuating camera
  check, a supervised live teleop, or a supervised recording/replay.

Return a staged plan, exact nested configuration, preflight results, calibration
identity, dataset feature/FPS checks, and an explicit live-action gate.
Separate verified mock behavior from hardware behavior that still needs the
operator's device.

## Route and decide

1. Read [hardware-overview.md](references/hardware-overview.md) to select the
   registered type and conditional extra. If the type is not listed, inspect the
   installed plugin package without importing or actuating it, then route custom
   plugin implementation to `extensions-and-services`.
2. Read [configuration.md](references/configuration.md) and normalize every
   nested `--robot.*`, `--teleop.*`, `--dataset.*`, and camera field. A robot
   camera must have explicit width, height, and FPS; reject incomplete camera
   config before motion.
3. Run the safe package/config probe:
   `python skills/disco/lerobot/sub-skills/robot-control-data-collection/scripts/hardware_environment_probe.py --robot-type <type> --teleop-type <type> --camera-type <type>`.
   From an arbitrary directory, use the bundled script's actual path in the
   installed skill tree. It lists package availability but does not open a bus,
   camera, socket, or robot.
4. Use [safety.md](references/safety.md) to choose the next gate. `--help` is
   safe; port discovery, camera discovery, motor setup, calibration, connection,
   teleop, recording, and replay are progressively more invasive.
5. Use [workflows.md](references/workflows.md) for the selected flow and
   [api-reference.md](references/api-reference.md) for Python-level inspection.
   Stop on any missing required extra, unknown type, mismatched feature, stale
   calibration, wrong port, unsafe workspace, or emergency-stop uncertainty.
6. Diagnose only after preserving the failed command and exact error; use
   [troubleshooting.md](references/troubleshooting.md). Do not repeatedly power
   cycle a faulting arm or bypass a permission, voltage, CAN, or watchdog error.

## Safe command planning

- Build a recording command with
  [record_command_builder.py](scripts/record_command_builder.py). It prints a
  command and preflight checklist only, and defaults Hub upload off.
- Build a replay command with
  [replay_command_builder.py](scripts/replay_command_builder.py). Its output is
  always labeled ACTUATES ROBOT and requires a separate human confirmation in
  the workflow; the script never executes it.
- Use
  [hardware_environment_probe.py](scripts/hardware_environment_probe.py) for
  import/version, OS, optional-backend, and non-opening device-file checks.
- Keep command values quoted, use stable `/dev/serial/by-id/...` names when
  available, and never copy a port from another arm without unplug/replug
  identification.

## Completion criteria

A non-actuating check is complete only when imports/config parsing/help and
script checks pass. A live teleop is complete only after a bounded low-speed
motion check, observed camera frames, operator confirmation, and clean
`disconnect`. A recording is complete only after each retained episode is
saved, its features and FPS match the robot/camera configuration, and the
local dataset can be inspected; Hub upload is a separate credentialed action.
A replay is complete only after the dataset episode is validated, the robot and
workspace are confirmed, the operator is at the emergency stop, and cleanup
runs even on Ctrl-C. Route all policy training, checkpoint, and evaluation
selection to `policy-training-inference` after this handoff.

## Intentional limits

This route does not guess motor IDs, joint limits, CAN wiring, SDK versions,
network reachability, safe poses, camera support profiles, or physical safety
ratings. The reference notes distinguish source-backed configuration contracts
from mock-only tests; actual device behavior remains an operator verification.
