# Real-robot troubleshooting

Use the sequence below. Stop physical motion first; then diagnose the
service or data boundary. Never turn a timeout into an automatic retry when
the arm's physical state is unknown.

## Camera TCP failures

- **Connection refused on `127.0.0.1:50000`:** the external streamer is not
  running, crashed during SDK startup, or is on another host. Inspect
  `ss -ltnp`, server stdout, USB connection, and device enumeration. Start one
  supervised external server, then rerun the bundled one-shot helper at
  `<skill-root>/sub-skills/real-robot/scripts/capture_rgbd.py`.
- **Timeout or connection reset:** check route/firewall and whether another
  client owns the single listener; inspect server exceptions. Disconnect the
  client and restart the server only after confirming no physical action
  depends on the stream. A TCP connect does not imply a complete frame.
- **Short frame / `unexpected EOF`:** the historical server sent a short
  response, lost the connection, or its dimensions differ from the client.
  The expected 1280x720 payload is 4,608,040 bytes. Do not reshape partial
  data or append a second ping to guess framing; inspect `W`, `H`, pixel
  formats, and server build.
- **Invalid intrinsics or depth scale:** reject the frame. Check that the
  server publishes nine finite float32 values, positive `fx/fy`, and one
  finite positive float scale. Reconnect after the camera has completed its
  30-frame exposure warmup.
- **RGB looks swapped or depth is spatially shifted:** confirm server color
  is RGB8 and depth is aligned to color. Do not repair with a silent BGR
  conversion or geometry transform; that changes the contract.
- **All/most depth is zero or implausible:** check USB 3.0 cable/link speed,
  requested Z16 streams, device/firmware support, lighting/target range, and
  raw-vs-scaled units. Apply the wire scale once and the calibration scalar
  once; a calibration scalar cannot fix a missing stream.

## Streamer build and device failures

- **CMake cannot find OpenGL/GLFW/libusb:** install matching development
  packages through the approved system process, inspect `CMakeCache.txt`, or
  intentionally configure a reviewed non-graphical variant. Do not claim the
  graphical target built when the link step was skipped.
- **Undefined `realsense2` symbols or headers:** the SDK headers and shared
  library are from different versions or the runtime linker cannot find the
  library. Check `pkg-config`/library paths and the executable's dependency
  resolution; rebuild cleanly.
- **No device connected / stream profile error:** check USB 3.0, camera power,
  permissions, SDK/firmware compatibility, and whether another process owns
  the device. The C++ server's requested streams are fixed at 1280x720 RGB8
  and Z16 depth at 30 FPS.
- **Port already in use:** stop the old streamer or select an approved
  deployment variant; the historical executable has no port argument and no
  `SO_REUSEADDR`. Never kill an unknown process on a shared host.
- **Window/OpenGL crash:** treat it as a streamer failure. Inspect GPU/display
  availability and the `window`/GLFW setup; do not assume the TCP buffer is
  still being updated after a rendering exception.

## Calibration and geometry symptoms

- **Missing `<CALIBRATION_OUTPUT_DIR>/camera_pose.txt` or
  `camera_depth_scale.txt`:** stop before any operator-supplied application
  initialization or policy launch. Restore a known-good reviewed backup or
  obtain a separately reviewed external calibration application/output pair.
  This graph cannot execute calibration and must never require the original
  checkout `real/` directory. Do not create identity/one-valued placeholders
  unless explicitly approved as measured commissioning state.
- **Pose loads but clicks/actions land offset, mirrored, or at wrong height:**
  check camera-to-robot convention, checkerboard tool offset/orientation,
  intrinsics, RGB/depth alignment, and whether depth is metres. Validate a
  proper 4x4 rigid pose and apply each depth factor only once. Route formula
  review to [perception-geometry](../../perception-geometry/SKILL.md).
- **Calibration has few detections or high residual:** improve board lighting
  and focus, keep it fixed to the tool, check the `(3,3)` inner-corner setting
  against the physical board, enlarge/spread the grid coverage, and inspect
  each overlay. Recollect; do not hide residuals with an affine transform.
- **Depth is consistently 15–20% too small:** the README notes this historical
  issue for SR300-class cameras and says D400 cameras are less likely to have
  it. Verify the fitted scalar and sensor scale independently; do not import a
  scalar from another camera.

## UR controller/network failures

- **UR TCP refused or hangs:** verify the confirmed controller IP, remote
  control mode, firewall, and ports 30002 (command) / 30003 (real-time).
  Check that no other client owns or saturates the service. Do not send a
  motion command as a port test.
- **Parser assertion/message mismatch:** the source expects primary message
  type 16 and, for the real-time parser, exactly 812 bytes. The README warns
  that later UR software may change packet details. Capture and inspect state
  packets offline; stop and update/revalidate the parser for the controller
  version rather than disabling assertions on live hardware.
- **Arm moves unexpectedly or does not reach the target:** use the emergency
  stop/protective stop, inspect the controller's actual pose and program state,
  and do not issue a second command. Historical `move_to` uses `movel`, default
  tool acceleration 1.2 and velocity 0.25; home uses joint acceleration 8 and
  velocity 3, while calibration/debug lower joint settings. These are not
  safety limits.
- **Guarded move reports contact/timeout:** its software condition is planar
  TCP force norm >20 N or an increment >1 s. Keep the arm stopped, inspect
  contact and the real-time packet, and clear the cause manually. Do not
  simply resume from the next 1 cm increment.
- **Gripper state is wrong:** inspect tool wiring, digital output 8, analog
  input interpretation, and controller program state. `close_gripper` and
  `open_gripper` each connect to 30002 and use digital output 8; the source's
  thresholds are historical and unverified for other grippers.

## Historical-runtime limitations

A bounded current-Python numerical-stack check can validate standalone
helpers. The source artifact has no package metadata and remains a Python
2/early-Python-3 checkout; these facts do not prove that camera streaming, UR
packet parsing, calibration, or full-loop execution works on modern
libraries. Historical source imports were construction evidence only. Keep all
modernization in a separately reviewed adapter and preserve the historical
wire/file contracts when compatibility is required.
