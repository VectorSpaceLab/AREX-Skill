# RealSense streamer

The historical streamer is a C++11 executable around librealsense SDK 2.0.
It captures an Intel RealSense D415-class device, aligns depth to color,
updates the fixed TCP frame described in
[camera-protocol.md](camera-protocol.md), and renders both streams in an
OpenGL window. It is a camera service, not a robot service.

## Prerequisites

Obtain system packages and SDK versions through the site's approved process;
this skill does not install them. The source evidence requires:

- librealsense SDK 2.0 with headers and `librealsense2.so`;
- a C++11 compiler and CMake (the historical file requires CMake >= 2.8.9);
- POSIX pthreads and the math library;
- OpenGL development libraries because graphical builds are enabled by
  default;
- GLFW headers and library (`glfw` or `glfw3`), plus libusb development
  libraries on non-Windows systems;
- a RealSense camera and a USB 3.0-compliant cable. A USB-C connector alone
  does not prove USB 3.0 throughput.

The CMake target links `realsense2`, OpenGL/GLFW/libusb where applicable,
`pthread`, and `m`. It sets `-std=c++11` and defaults to Debug. With the
historical graphical option enabled, missing OpenGL is a fatal configure error
and missing GLFW commonly becomes a header/library or link error. The source
also includes its own rendering convenience headers; do not assume that
removes the external GLFW/OpenGL requirements.

## Build and start, guarded

Build in a disposable operator-owned build directory from an approved
streamer source copy; inspect compiler/linker output rather than accepting a
stale executable. The graph does not bundle the streamer:

```bash
cmake -S <STREAMER_ROOT> -B <STREAMER_BUILD>
cmake --build <STREAMER_BUILD>
<STREAMER_BUILD>/realsense
```

`<STREAMER_ROOT>` and `<STREAMER_BUILD>` are external operator paths, not the
original checkout's `realsense/` directory.
The process should print device information, warm up 30 frames, and listen on
TCP port 50000. Keep it supervised. Do not run a second instance until the
first one has exited and the port has been released; the server does not set
`SO_REUSEADDR` and does not provide a configurable port in its command line.
The server accepts one client, sends a latest-frame buffer when pinged, and
returns to accept mode after disconnect.

The capture configuration is fixed at 1280x720, 30 FPS, depth `Z16`, and color
`RGB8`. The streamer enables the RealSense depth/color streams, aligns depth
to color, and obtains color intrinsics plus the sensor's depth scale. The
advanced-mode path may set depth units to 100 micrometers and disparity shift
to 50 when supported; this is hardware/firmware dependent and must be
verified from the startup output. A camera that cannot provide the requested
streams is a service failure, not a reason to guess dimensions.

## Service checks

On the camera host, verify the listener with an operating-system tool such as
`ss -ltnp | grep ':50000'` and inspect the process's stdout for `Listening...`,
`Connected to client.`, device information, and RealSense exceptions. On the
client host, let `<skill-root>` mean the directory containing the root
`SKILL.md`, then use the bundled helper:

```bash
python <skill-root>/sub-skills/real-robot/scripts/capture_rgbd.py \
  --host <CAMERA_HOST> --port 50000 --timeout 5
```

It checks the expected payload without importing the old code and performs a
bounded trailing-byte probe. A successful TCP connection with a short,
trailing, or invalid payload means the service/client dimensions or binary
layout do not match; a peer that stays open through the probe is explicitly
inconclusive about exact framing.

For a remote camera, confirm the camera host's reachable address, route,
firewall rule, and bind policy before changing the client host. The server
binds `INADDR_ANY`, while the client default is loopback only. Do not expose
port 50000 to an untrusted network: the protocol has no authentication,
transport encryption, or request validation beyond a non-empty ping.

If graphical dependencies are unavailable, disabling the graphical CMake
option may remove the OpenGL/GLFW requirement, but this is a deliberate build
variant. Verify that the resulting executable still supplies the same stream
configuration and TCP layout before using it. No such variant was proven by
the inspection run.
