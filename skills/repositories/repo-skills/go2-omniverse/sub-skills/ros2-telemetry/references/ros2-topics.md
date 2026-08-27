# Simulated ROS 2 topics

The modern `RobotBaseNode` creates these topics for each robot index `N` with a
small keep-last QoS profile (depth 10):

| Topic | Type | Key details |
|---|---|---|
| `robotN/joint_states` | `sensor_msgs/JointState` | Names are prefixed `robotN/`; positions are read from Isaac articulation data |
| `robotN/foot_force` | `std_msgs/Float32MultiArray` | Four Go2 contact-force Z values; this replaces the legacy custom state message |
| `robotN/point_cloud2` | `sensor_msgs/PointCloud2` | Packed little-endian float32 x/y/z, frame `odom`; LiDAR path is currently disabled in the main loop |
| `robotN/odom` | `nav_msgs/Odometry` | Position and orientation are derived from the simulated root state |
| `robotN/imu` | `sensor_msgs/Imu` | Orientation and linear/angular velocity fields are populated from simulation buffers |
| `/tf` | `tf2_msgs/TFMessage` | Publishes `odom` → `robotN/base_link`; avoids the unavailable `tf2_ros` helper |
| `robotN/cmd_vel` | `geometry_msgs/Twist` input | `linear.x`, `linear.y`, `angular.z` update the policy command |

Use the exact slash convention emitted by the ROS client when querying a graph;
source strings use `robotN/...` while ROS tools often display `/robotN/...`.

## Quaternion and frame rules

Isaac root quaternions are treated as `(w, x, y, z)` in the source. ROS message
fields are assigned as `x=q[1]`, `y=q[2]`, `z=q[3]`, `w=q[0]`. Odom uses frame
`odom` and child frame `robotN/base_link`; IMU uses the robot base frame.

## Multi-robot commands

`robot_amount` creates one command entry and one publisher set per environment.
Keep the numeric index consistent across `robotN/cmd_vel`, telemetry topics, and
frame IDs. A topic from robot 0 must not be assumed to control robot 1.
