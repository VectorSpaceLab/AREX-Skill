# Twinbot message mapping

## Joint order

The bridge reads Unitree motor indices in this order:

1. `FR_hip_joint`, `FR_thigh_joint`, `FR_calf_joint`
2. `FL_hip_joint`, `FL_thigh_joint`, `FL_calf_joint`
3. `RR_hip_joint`, `RR_thigh_joint`, `RR_calf_joint`
4. `RL_hip_joint`, `RL_thigh_joint`, `RL_calf_joint`

The sim subscriber builds a name-to-value map and reorders incoming values into
its articulation joint names, using default joint positions and zero velocity
for names absent from a message.

## Orientation and velocity

Unitree IMU quaternion is `(w, x, y, z)`. ROS `Odometry` fields are assigned as
`orientation.w=q[0]`, `x=q[1]`, `y=q[2]`, `z=q[3]`. Gyroscope values populate
`twist.angular`. The subscriber caches both under a lock and writes root pose and
root velocity after the normal policy/physics step.

## Kinematic override

When fresh joint data exists, `write_joint_state_to_sim` overwrites positions
and velocities. When fresh odometry exists and XY pinning is enabled,
`write_root_pose_to_sim` and `write_root_velocity_to_sim` overwrite the base
orientation and angular velocity while preserving the sim spawn position.
This is visual kinematic playback, not a force-level real-robot controller.
