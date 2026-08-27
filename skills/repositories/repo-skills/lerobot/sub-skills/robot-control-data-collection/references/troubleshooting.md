# Hardware troubleshooting and limits

Preserve the exact command, selected type, port/interface, OS, installed extra,
calibration id, and first error. Stop motion before changing configuration.

## Wrong or missing serial port

**Symptoms:** `Could not connect on port`, timeout, no difference from
`lerobot-find-port`, permission denied, or the wrong arm moves.

1. Stop and disconnect power/torque as appropriate.
2. Rerun `lerobot-find-port` with only the named bus unplugged when prompted;
   zero differences means the device was not detected, and multiple differences
   means the setup is ambiguous.
3. Check cable, power, USB adapter, permissions/group membership, and whether
   another process has the port open. Prefer a stable serial-by-id path after
   confirming its target. Never “fix” a wrong arm by swapping ids or disabling
   safety checks.
4. For SO arms, inspect motor LEDs, 3-pin chain continuity, controller power,
   and the correct voltage variant. Repeated packet errors can be physical.

## Missing SDK or plugin

An informative `ImportError` names the package and install extra when a backend
is absent. Install the exact conditional extra for the chosen type, then rerun
the non-opening environment probe and CLI help. Reachy, reBot, Unitree, Phone,
RealSense, ZeroMQ, CAN, Feetech, Dynamixel, and gamepad backends are not
interchangeable. Unitree's SDK installation and CycloneDDS/system setup are
separate from the LeRobot extra. If a third-party plugin fails during discovery,
inspect its package import in an isolated process and do not continue to live
control.

## Permission, CAN, or network failure

- **Serial:** use OS group/udev policy and verify the port owner; avoid broad
  world-writable permissions. Close competing serial monitors.
- **CAN:** verify the interface exists and is UP, adapter mode matches config,
  nominal/data bitrates match the motor network, and the bus is physically
  terminated. `lerobot-setup-can --mode=setup` changes host networking and
  `--mode=test` sends motor frames; neither is a read-only diagnostic.
- **Reachy/Unitree/LeKiwi/ZMQ:** verify the intended isolated network, IP,
  service/server, port, watchdog and latency. A reachable TCP port does not
  prove robot readiness. Do not expose a control endpoint to an untrusted
  network.

## Calibration failure or mismatch

If calibration says the device is not calibrated, a range is invalid, or the
cached values do not match the motor, stop. Check that the id and calibration
folder identify the same physical device, then recalibrate with the robot
secured. A range with equal min/max is invalid. Do not copy a leader file to a
follower or reuse calibration after changing motor order, firmware, assembly,
side, or bus mapping without verification.

Some devices differ: OMX is shipped factory-configured; reBot records a zero
pose and re-zeros on connection; phone calibration aligns a mobile frame;
Reachy parts/cameras are selected by matching flags; Unitree exoskeleton
calibration is interactive. Report these distinctions rather than applying the
SO-arm sweep procedure universally.

## Camera not found, bad profile, or stale frames

1. Run the matching discovery filter and record identifiers; replugging may
   change OpenCV indices.
2. Check USB bandwidth, permissions, cable, selected serial/name, and whether
   another application owns the device.
3. For RealSense, keep `fps`, `width`, and `height` all set or all unset and
   validate against the camera's supported profiles. Depth uses the color FPS
   and may be nearest-supported rather than exact.
4. For a robot camera, set width, height, and FPS explicitly. A missing field is
   rejected before the robot config is accepted. For Reachy/ZMQ, check service
   name, IP, port, stream type, timeout, and warmup.
5. `read()` can block; `async_read` raises `TimeoutError` when no fresh frame
   arrives; `read_latest` rejects an over-age frame. Stop recording if frames
   are stale or dimensions/FPS differ from dataset features. Do not compensate
   for a missing camera by silently recording a different view.

## Recording cadence or feature mismatch

`record_loop` requires dataset FPS equal to the requested FPS. Reduce camera
load, use an appropriate FOURCC/encoder, adjust image-writer threads, or lower
FPS only in a newly validated plan. Inspect action/observation feature keys,
shapes, units, and task labels before retaining episodes. An interrupted run
should finalize locally; use resume only after its metadata and robot
compatibility pass. A poor cadence report is a data-quality failure, not a
reason to continue collecting.

## Replay or unexpected motion

Treat every replay error as a live safety event. Stop with the physical
emergency stop, isolate power, save logs, and inspect the robot. Check dataset
episode index, action names/units, FPS, calibration, joint limits, start pose,
and robot type before any retry. A mock replay or parser test cannot validate a
real trajectory. Policy rollout errors belong to the policy route after this
hardware handoff.

## Intentional uncertainty

The source and deterministic tests establish config/factory names, lifecycle
contracts, cleanup paths, CLI ownership, and several mocked failure states.
They do not establish that a particular user's motor wiring, voltage, firmware,
CAN termination, SDK release, camera profile, network latency, joint limit, or
emergency-stop hardware is safe. Actual hardware compatibility and safety need
operator and manufacturer evidence. No bundled script opens devices or sends
commands by default.
