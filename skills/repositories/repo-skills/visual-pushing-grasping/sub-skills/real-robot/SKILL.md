---
name: real-robot
description: "Route guarded UR5 and RealSense physical workflows for Visual
  Pushing and Grasping: TCP RGB-D capture, camera-server setup, calibration,
  touch/debug diagnostics, and safety-first failure recovery."
disable-model-invocation: true
metadata:
  disco-role: operating
license: BSD 2-Clause
---

# Real robot

Use this route for an operator-supplied physical UR5 and Intel RealSense path.
It documents historical integration contracts; it is not a robot driver and it
never connects to a controller or starts a camera service automatically.

## Hard safety boundary

**Before any operation that can move the arm or actuate the gripper:**

1. Put the UR5 in a known, supervised state, keep the emergency stop reachable,
   clear people/tools/objects from the workspace, and confirm the controller is
   in the intended remote-control mode. Do not rely on this skill or source
   evidence as a safety-rated control system.
2. Confirm the controller host, TCP/real-time ports, workspace limits, tool,
   checkerboard offset, and home pose with the operator. The host must be
   `<operator-approved-controller-host>`; retain command port `30002` and
   real-time port `30003`. Never copy a historical lab address into a live
   setup.
3. Start and test the camera service first. Run the bundled motion-free helper
   and inspect RGB-D statistics before enabling a robot connection.
4. Back up and inspect calibration outputs. Missing or stale calibration is a
   stop condition, not a reason to guess a pose.
5. Only after those checks, explicitly approve a separately reviewed physical
   application workflow. The runtime graph bundles no motion controller,
   calibration application, touch/debug loop, or UR5 driver.

Use a physical emergency stop for unsafe motion or communication failure; a
historical force check is only a software precaution and is not a substitute
for controller protective stop or an operator.

## Runnable camera helper and route

Let `<skill-root>` mean the directory containing the root `SKILL.md`. For a
one-shot camera probe, read [camera-protocol.md](references/camera-protocol.md)
and run the bundled helper:

```shell
python <skill-root>/sub-skills/real-robot/scripts/capture_rgbd.py --help
python <skill-root>/sub-skills/real-robot/scripts/capture_rgbd.py \
  --host <CAMERA_HOST> --port 50000 --timeout 5
```

`<CAMERA_HOST>` is operator-supplied. The helper performs only a bounded TCP
frame check; it does not import the historical checkout, send UR commands,
perform calibration, or write robot state. A successful camera probe says
nothing about controller connectivity.

- For building/starting a camera server, read
  [realsense-streamer.md](references/realsense-streamer.md); its build and
  service are external operator actions.
- For calibration contracts and output validation, read
  [calibration.md](references/calibration.md).
- For service ordering and guarded diagnostics, read
  [diagnostics.md](references/diagnostics.md).
- For symptoms and recovery, read [troubleshooting.md](references/troubleshooting.md).
- For projection and heightmaps, hand off to
  [perception-geometry](../perception-geometry/SKILL.md).
- For a policy loop, hand off to [training](../training/SKILL.md).

## Calibration execution boundary

**This graph cannot execute calibration.** It supplies the math and file
contract only. Require an operator-supplied, separately reviewed calibration
application and an operator-supplied output directory, for example
`<CALIBRATION_APP_ROOT>` and `<CALIBRATION_OUTPUT_DIR>`. Review the motion plan,
controller host, checkerboard setup, workspace, abort plan, and output files
before any run. Never require, invoke, or assume the original checkout's
`real/` directory; it is source evidence only.

The historical source labels `calibrate.py`, `real/camera.py`, `touch.py`,
`debug.py`, and `robot.py` may explain provenance, but no user instruction
should run them from the original checkout. The separately reviewed calibration
application must produce the required outputs under `<CALIBRATION_OUTPUT_DIR>`:

- `camera_pose.txt`: a 4x4 camera-to-robot homogeneous matrix, finite with a
  proper rigid rotation and metres for translation;
- `camera_depth_scale.txt`: one finite positive dimensionless scalar applied
  after wire depth conversion.

Keep the math/file contract: the pose maps camera points to robot coordinates;
the wire `uint16` scale is applied once to obtain metres, then the fitted
calibration scalar is applied once. Validate exact shapes, finite values,
proper rotation, homogeneous final row, positive scale, residual/RMSE, and
checkerboard coverage. Preserve old outputs before replacing them. Do not use
identity or one-valued placeholders without explicit measured commissioning
approval.

## Historical defaults and guarded order

The historical contract uses controller host
`<operator-approved-controller-host>`, command TCP port `30002`, and real-time
state port `30003`. Verify the actual host with the operator. The real workspace
is `x=[0.3,0.748]`, `y=[-0.224,0.224]`, `z=[-0.255,-0.1]` metres; calibration
uses a different reviewed grid in [calibration.md](references/calibration.md).

The camera client defaults to `127.0.0.1:50000`, historical RGB-D size
1280x720, and a 4 KiB receive chunk. Start the external RealSense server on
the camera host, validate one frame with the bundled helper, then verify the
controller ports independently. Do not infer robot connectivity from camera
connectivity. Supervise the first approved low-speed, single-step action and
do not launch an unattended loop.

Historical packet layouts, home joints, speed values, force threshold, and UR
software notes are evidence for a separately reviewed adapter, not safety
limits or runtime guarantees. Preserve the parser and output contracts when
an operator undertakes compatibility work.

## Scope and verification boundary

The bundled helper performs only TCP connect, ping, exact-byte read, bounded
trailing-byte probe, and payload validation. Build, live capture, calibration,
touch, debug, and motion remain external, explicit, and supervised. Never link
this skill to checkout paths, machine-local environments, or review artifacts.
Treat calibration state and raw frames as deployment data owned by the operator.
