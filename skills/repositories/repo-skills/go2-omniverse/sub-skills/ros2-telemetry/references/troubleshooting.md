# ROS 2 telemetry troubleshooting

## ABI and missing packages

`rclpy` shared-object errors, duplicate `rcl_interfaces` assertions, or
`rosidl_typesupport_c` failures usually indicate a host/bundled ROS mismatch.
Use the launcher-managed bundled runtime for Isaac Sim 5 and keep custom
`go2_interfaces` builds in a separately matched ROS workspace.

## Topic/type mismatch

If a consumer cannot deserialize `robotN/foot_force`, inspect the advertised
type: modern code uses `std_msgs/Float32MultiArray`, not `go2_interfaces/Go2State`.
Likewise, query the exact indexed topic for multi-robot scenes rather than
assuming a single `robot0` namespace.

## QoS and frames

A topic may be present but silent when publisher/subscriber QoS is incompatible.
Compare reliability/history/depth before changing message code. Check `odom` →
`robotN/base_link`, IMU frame IDs, and quaternion field ordering before blaming
physics or DDS.

## Optional sensors

Camera and RTX LiDAR failures are independent of the base joint/odom/IMU path.
Disable optional sensors, prove the base telemetry, then re-enable one sensor at
a time. Do not treat the current LiDAR-disabled source path as a verified point
cloud stream.
