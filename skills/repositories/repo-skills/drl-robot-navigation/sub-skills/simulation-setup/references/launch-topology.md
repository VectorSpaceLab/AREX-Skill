# Launch topology and startup contracts

This reference distills the launch and xacro evidence from the source snapshot. Use
package names and placeholders below rather than assuming a particular checkout path.
The source evidence is `TD3/assets/multi_robot_scenario.launch`, the
`multi_robot_scenario/launch` files, and the selected robot and Velodyne xacros.

## Composite path

```text
multi_robot_scenario.launch
├── include multi_robot_scenario/launch/empty_world.launch
│   ├── /use_sim_time = true by default
│   ├── gzserver, physics=ode, world_name=TD3.world
│   └── gzclient only when empty_world's gui argument is true
├── include multi_robot_scenario/launch/pioneer3dx.gazebo.launch
│   ├── robot_name = r1
│   ├── robot position = x 0, y 0, z .01, zero rotation
│   ├── robot_description from pioneer3dx.xacro
│   ├── gazebo_ros/spawn_model from robot_description
│   ├── robot_state_publisher
│   └── joint_state_publisher
└── rviz with pioneer3dx.rviz (unconditional in this composite)
```

The composite declares `gui=false`, but does not pass that argument to its `empty_world`
include. The included world file independently defaults `gui=false`, so the observed
baseline starts `gzserver` without `gzclient`; this declaration is not a general headless
switch. The RViz node has no `if` condition. A display-less run can consequently fail or
hang around RViz even with Gazebo software/headless rendering enabled.

`empty_world.launch` sets `/use_sim_time`, defaults to `TD3.world`, starts `gazebo_ros`
`gzserver` with ODE, and optionally starts `gzclient`. Its `headless` argument is retained
for compatibility but is explicitly documented in the file as non-functional for the
relevant Gazebo behavior. `respawn_gazebo` defaults to true; a server crash can therefore
look like an automatic restart rather than a clean failure.

## Robot expansion

`pioneer3dx.gazebo.launch` evaluates:

```text
$(find xacro)/xacro $(find multi_robot_scenario)/xacro/p3dx/pioneer3dx.xacro
```

The root xacro includes materials, Pioneer body, camera, 2-D laser definitions, and the
vendored `velodyne_description/urdf/VLP-16.urdf.xacro`. The active Pioneer body includes:

- `libgazebo_ros_diff_drive.so`, with `cmd_vel`, `odom`, `odom` frame, `base_link`, and
  wheel joints; the empty robot namespace means the spawned `r1` topics are expected as
  `/r1/cmd_vel` and `/r1/odom` in this repository's running setup;
- a joint-state Gazebo plugin plus ROS state/joint publishers;
- a non-GPU VLP-16 sensor attached to `base_link` at approximately `(0.125, 0, 0.25)`;
- meshes and camera/laser resources.

The xacro calls a Pioneer body mesh path beginning with
`package://gazebo_plugins/test/multi_robot_scenario/meshes/p3dx`. That path is not the
same spelling as the package's normal package URI and is a likely mesh-resolution fault
if the model spawns without visuals or fails during resource lookup. Diagnose package
and URI resolution from logs before changing it; do not silently rewrite source launch or
xacro files in a runtime skill.

## Important alternate path

`multi_robot_scenario/launch/pioneer3dx.urdf.launch` is not used by the composite and
contains a `$(find multi_robot_tutorial)` reference, while the visible package is
`multi_robot_scenario`. Treat it as stale/independent evidence. If a user chooses it,
require a deliberate correction and separately validate its xacro/package dependencies;
do not use its failure to diagnose the composite.

## Package/build graph

The scenario package declares and builds only `xacro` in its package metadata and CMake
file. The actual launch path additionally needs ROS packages for Gazebo, spawning,
state publishers, joint states, and RViz, plus the vendored Velodyne description and
Gazebo plugin packages. The three vendored packages are under the workspace source tree:
`velodyne_description`, `velodyne_gazebo_plugins`, and `velodyne_simulator` (the latter
is a package wrapper). The plugin package compiles a Gazebo ROS sensor plugin; package
presence alone does not prove the shared library was built or loadable.

After a successful build, source both setup layers in a new shell and use:

```bash
rospack find multi_robot_scenario
rospack find velodyne_description
rospack find velodyne_gazebo_plugins
```

If one fails, fix sourcing or the catkin build before investigating Gazebo world physics.

## Expected live interfaces

The startup dependencies needed by the navigation process are:

| Interface | Expected value | Owner |
|---|---|---|
| ROS master | `http://localhost:11311` in the documented local setup | roscore/ROS env |
| Drive command | `/r1/cmd_vel` (`geometry_msgs/Twist`) | Pioneer diff drive |
| Odometry | `/r1/odom` (`nav_msgs/Odometry`) | Pioneer diff drive |
| Point cloud | `/velodyne_points` (`sensor_msgs/PointCloud2`) | VLP-16 plugin |
| Reset | `/gazebo/reset_world` | Gazebo ROS |
| Physics | `/gazebo/pause_physics`, `/gazebo/unpause_physics` | Gazebo ROS |
| State setting | `gazebo/set_model_state` | Gazebo ROS |

Check live interfaces only after a user intentionally starts a bounded simulator session;
static prerequisite checks cannot establish them. Topic/state and reward semantics belong
to the navigation-environment skill.
