# Legacy custom interfaces

The repository includes an `ament_cmake` package named `go2_interfaces` with
messages such as `Go2State`, `Go2Cmd`, `Go2Move`, `Go2RpyCmd`, and `IMU`. Its
message definitions and CMake metadata are useful compatibility evidence, but
the modern Isaac Sim/Jazzy port intentionally avoids importing the custom
package.

## Modern replacement

The modern sim publishes foot force as `std_msgs/Float32MultiArray` on
`robotN/foot_force`. Consumers written for `go2_interfaces/Go2State` must either
subscribe to the standard array and update their adapter, or run an explicitly
matched bridge on the Humble side. Do not add a `Go2State` subscription to the
modern sim without building and exposing the package in the same ROS runtime.

## Build boundary

Building the custom messages requires a ROS 2 workspace with `ament_cmake`,
`rosidl_default_generators`, `geometry_msgs`, and generated runtime support.
That workspace is separate from the Isaac Sim Python environment. Verify the
message package with the target ROS distro before using it on a wire.

The current Creator environment had no system `ros2` CLI, so message generation
and wire-level compatibility remain unverified.
