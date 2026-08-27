# Physical diagnostics and operating order

These procedures are distilled from the historical source artifacts
`real/camera.py`, `calibrate.py`, `touch.py`, `debug.py`, and the real branch of
`robot.py`. The filenames are evidence labels only. They are intentionally
described rather than bundled: every original diagnostic constructs a robot
object or sends URScript, and therefore can move hardware. The runtime graph
cannot execute them.

## Order of operations

1. **Mechanical and controller check:** clear the workcell, inspect tool and
   gripper, confirm the emergency stop and protective limits, and place the
   arm in a known state. Confirm the controller's remote mode and the exact
   UR software version. The source was tested with UR Software 1.8; newer
   versions may need parser changes.
2. **Camera service check:** connect the RealSense with a USB 3.0-compliant
   cable, start the C++ streamer, inspect device/stream startup, and run
   `python <skill-root>/sub-skills/real-robot/scripts/capture_rgbd.py` once,
   where `<skill-root>` is the directory containing the root `SKILL.md`. Check
   exact 1280x720 dimensions, finite intrinsics, positive sensor scale,
   nontrivial RGB, plausible depth, and the trailing-byte probe result.
3. **Network check:** independently check the camera TCP port 50000, UR
   command TCP port 30002, and UR real-time state port 30003. A successful
   camera probe says nothing about either robot port. Use a TCP connect probe
   or `ss`/controller diagnostics, never send arbitrary URScript as a probe.
4. **Calibration check:** validate/backup `camera_pose.txt` and
   `camera_depth_scale.txt`, compare intrinsics and units, and inspect
   checkerboard residuals. If absent/stale, stop and follow calibration.md.
5. **Single supervised motion:** only after explicit operator approval, use a
   reviewed, low-speed one-step workflow. Observe pose, force, tool, and
   gripper state; stop at the first unexpected result.
6. **Only then run application logic:** route model inputs to training and
   geometry to perception-geometry. Start with one bounded action/trial, not
   an unattended training loop.

## Historical diagnostic roles

- `touch.py` displays live color/depth windows. A mouse click is back-projected
  with intrinsics, depth is multiplied by the calibration scalar, the point is
  transformed with `robot.cam_pose`, and `robot.move_to` sends the end effector
  to the selected position. It is a calibration validation motion, not a
  harmless viewer. Use an approved point and a clear path; never leave its
  loop unattended.
- `debug.py` constructs a real `Robot`, opens the gripper, changes speed to
  joint acceleration 1.4 and velocity 1.05, and repeatedly calls `grasp` at a
  hard-coded workspace-derived point. This is destructive/repetitive and must
  not be used as a connectivity test. The commented corner loop also moves
  hardware.
- Historical `calibrate.py` evidence describes grid motion and calibration
  outputs. Do not invoke it from the original checkout; follow
  [calibration.md](calibration.md) and require a separately reviewed external
  calibration application/output directory.
- `robot.py::guarded_move_to` opens both controller sockets, advances in 1 cm
  position increments, reads real-time state, and stops its loop after planar
  force norm exceeds 20 N or an increment exceeds one second. This guard is
  useful evidence for diagnosis but does not cover every primitive, does not
  guarantee a stop packet, and is not safety-rated.
- The real `grasp` primitive computes an angle-axis tool orientation, clamps
  the target z to the workspace floor, sends a scripted approach/open/close
  sequence, reads tool analog state, and conditionally sends the object to a
  fixed bin before returning home. It is a compound motion with no equivalent
  per-centimeter force guard; approve its full path and bin clearance first.
- The real `push` clamps the XY target and a 0.1 m endpoint to workspace
  limits, sends approach/contact/push/retreat/home commands with a tilted
  tool, then polls state until the historical home position. It reports
  success from command completion rather than tactile proof. Treat any
  endpoint or home mismatch as a stop condition.
- `restart_real` is a box-grab/release recovery sequence with several moves
  and gripper actuations. It is not a reset button and should only be invoked
  after an operator has assessed the physical state and approved its full
  path.

## Non-motion probes

Before touching a controller, use the RGB-D helper and ordinary OS/network
inspection. For robot state, an approved controller-side status view is safer
than asking an old parser to interpret an unknown packet. If a source-level
parser test is required, use captured packets offline and assert the expected
primary message type 16, subpackage lengths, and real-time 812-byte packet
before any socket is connected to hardware.

Record host/port, timestamp, software/firmware versions, calibration file
checksums, frame statistics, and the exact first supervised action. Do not
place credentials or live endpoint secrets in a skill, log, or command copied
to an untrusted channel.
