# Container and target runtime contract

The checked-in Dockerfile and Makefile describe the source's intended Jetson
runtime. They are evidence, not commands to execute from this skill.

## Jetson L4T and architecture

The Dockerfile is based on:

```text
nvcr.io/nvidia/l4t-pytorch:r32.6.1-pth1.9-py3
```

This is a Jetson Linux for Tegra (L4T) / ARM-oriented image with a pinned
PyTorch base. The SDK bridge and any compiled `lcm_position` executable must
match the target's aarch64 ABI and the Unitree SDK build. An x86 host cannot
run the ARM binary merely because Python and LCM schemas are present. Conversely,
do not replace the L4T image or binary with an x86 build without revalidating
all SDK and driver contracts.

A future deployment record should state target SoC/L4T release, Python/PyTorch
compatibility, LCM version, SDK build, and image digest. The image tag alone is
not a supply-chain or hardware proof.

## Privileged host-network NVIDIA Docker assumptions

The source Makefile's intended controller container assumes all of the
following, each requiring human/administrator approval:

- privileged container access;
- NVIDIA container runtime and working host GPU/driver integration;
- `--net=host` so the controller can use the host's LCM multicast interface;
- a bind mount of the robot-side source/package directory;
- a working directory containing the deployment package;
- an optional long-running container followed by a controller process.

These settings expose host devices and networking and are not safe defaults for
an untrusted image. Do not broaden privileges, change host networking, or run a
container here to test the contract. Verify image provenance and digest before
any approved operator launch.

## ARM, display, and filesystem assumptions

The Makefile passes `DISPLAY`, `QT_X11_NO_MITSHM`, `XAUTHORITY`, and X11 socket
mounts, and the Dockerfile installs OpenCV/GTK-related libraries. These are for
optional visualization/camera paths; headless control should not assume an
available display. X11 mounts and credentials must be reviewed independently.

The container expects the robot package to be visible at the source's mounted
path and the policy/checkpoint directory to exist inside that package. A bind
mount that hides the expected files, a read-only filesystem where logs are
created, or a missing writable log directory can fail after startup. Use a
versioned staged path and confirm disk/log permissions before launch.

## Runtime gates

Mark `BLOCKED_REQUIRED_BACKEND` when any of the following is unknown or absent:

- compatible Jetson/L4T or explicitly validated external host;
- matching aarch64/x86 SDK bridge, generated LCM bindings, and Python `lcm`;
- NVIDIA driver/runtime if the chosen container needs it;
- approved host networking and multicast interface;
- approved privileged-container policy;
- display/X11 requirements for a camera/visual workflow;
- writable, sufficiently large storage with rollback retained.

A container being able to start is not evidence that LCM packets, camera
schemas, policy dimensions, or motor safety are correct. Continue only through
the human gates in [safety](safety.md) and [controller-workflow](controller-workflow.md).
