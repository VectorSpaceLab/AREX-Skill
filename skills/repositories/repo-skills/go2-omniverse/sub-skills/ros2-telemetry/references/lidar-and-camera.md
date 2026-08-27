# Camera and LiDAR surfaces

## Camera

The source creates an IsaacLab camera under each robot's base (or G1 head) with
RGB output, 640×480, 0.1 s update period, and a ROS-style camera offset. A
headless hero capture creates a separate 1920×1080 camera and writes RGB PNGs to
the operator-selected directory.

The older OmniGraph camera stream uses `isaacsim.core.nodes` and
`isaacsim.ros2.bridge`. The modern port deliberately skips that bridge extension
when direct `rclpy` publishing is used, so camera creation and camera ROS
streaming are separate capabilities.

## LiDAR

The bundled Unitree LiDAR specification describes a 128-emitter rotary sensor with
360° azimuth and approximately ±45° elevation. The source has an RTX LiDAR
helper and packs points into `PointCloud2`, but the main loop records LiDAR as
disabled pending the Isaac Sim 5 schema update. Treat LiDAR as optional until a
matching runtime proves the config and annotator path.

## Failure isolation

First prove a flat, headless simulation without cameras or LiDAR. Then enable
camera creation, then capture, and only then investigate ROS camera graphs or
RTX sensor configuration. A sensor extension error should not be diagnosed as
a policy/checkpoint failure.
