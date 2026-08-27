# GazeboEnv API reference

## Constructor and launch resolution

`GazeboEnv(launchfile, environment_dim)` stores the requested sensor dimension,
initializes the robot/goal bookkeeping, fills `velodyne_data` with `10`, builds
angular gaps, launches a ROS master on port `11311`, initializes a ROS node
named `gym`, and launches Gazebo. The constructor is therefore not an offline
object constructor.

For a relative `launchfile`, resolution is:

```text
<directory containing the environment module>/assets/<launchfile>
```

An absolute path is used unchanged. A missing resolved file raises `IOError`
before the `roslaunch` subprocess is started. In the pinned scenario, the
relative name `multi_robot_scenario.launch` includes `empty_world.launch`,
spawns Pioneer model `r1` using `pioneer3dx.gazebo.launch`, and starts RViz.

The constructor then creates:

| Interface | Type or service | Purpose |
| --- | --- | --- |
| `/r1/cmd_vel` | `geometry_msgs/Twist` publisher | direct linear/angular command |
| `gazebo/set_model_state` | `gazebo_msgs/ModelState` publisher | place `r1` and four boxes |
| `/gazebo/unpause_physics` | `std_srvs/Empty` proxy | advance simulation |
| `/gazebo/pause_physics` | `std_srvs/Empty` proxy | stop simulation after a slice |
| `/gazebo/reset_world` | `std_srvs/Empty` proxy | reset world on episode reset |
| `goal_point` | `visualization_msgs/MarkerArray` | goal visualization |
| `linear_velocity` | `visualization_msgs/MarkerArray` | linear command visualization |
| `angular_velocity` | `visualization_msgs/MarkerArray` | angular command visualization |
| `/velodyne_points` | `sensor_msgs/PointCloud2` subscriber | 3-D range observations |
| `/r1/odom` | `nav_msgs/Odometry` subscriber | robot pose and yaw |

The launch and runtime prerequisites are ROS Noetic on Ubuntu 20.04-compatible
systems, a built scenario/Velodyne catkin workspace, Gazebo with the ROS API
plugin, and Python packages used by the module (`numpy`, `squaternion`, and the
ROS Python message modules). `roscore`, `roslaunch`, and Gazebo must be
available at runtime. This contract deliberately does not provide setup
commands.

## Sensor reduction

The repository's main caller passes `environment_dim=20`. The constructor
creates 20 contiguous angular intervals. The first starts at
`-pi/2 - 0.03`; nominal intervals have width `pi/20`; the last ends at
`pi/2 + 0.03`. Each bin uses a lower-inclusive, upper-exclusive test:
`lower <= beta < upper`. The initial value of every bin is `10.0`.

For each `PointCloud2` point `(x, y, z)`, `velodyne_callback`:

1. Keeps it only when `z > -0.2`.
2. Computes horizontal angle using the implementation's x-axis reference:
   `beta = acos(x / sqrt(x*x + y*y)) * sign(y)`.
3. Computes full 3-D distance `sqrt(x*x + y*y + z*z)`.
4. Places the distance in the matching bin and keeps the minimum.
5. Ignores points outside all intervals. Missing bins retain `10.0`.

The bundled Velodyne xacro mounts a VLP-16 on `base_link` at `(0.125, 0,
0.25)`, publishes `/velodyne_points` at 10 Hz, and uses 360 horizontal
samples over approximately `[-1.57, 1.57]`, 16 vertical samples, and a
non-GPU ray plugin in this scenario. The plugin emits x/y/z fields and filters
its configured range before publishing. These sensor details explain the
expected message shape but do not replace a live topic check.

## Observation shape

`reset()` returns:

```text
[bin_0, ..., bin_19, distance, theta, 0.0, 0.0]
```

`step(action)` returns `(state, reward, done, target)`, where `state` is:

```text
[bin_0, ..., bin_19, distance, theta, action[0], action[1]]
```

The use of `np.append` flattens the one-element laser list with the four robot
values, yielding 24 values for `environment_dim=20`. The final two slots are
reset zeros or the action used for the current transition; the environment
does not maintain a distinct previous-action pair. The environment does not
normalize, clip, or replace non-finite input/action values. A missing odometry
message leaves `last_odom` unset and the first `step` then cannot read its
pose; treat that as an integration failure, not as a valid zero pose.

Distance is Euclidean distance in the odometry x/y plane. The goal bearing is
computed from the positive x axis, subtracted from robot yaw, and wrapped by
the implementation into approximately `[-pi, pi]`. The wrap code is not a
substitute for a general angle-normalization utility; preserve its behavior
when reproducing a result.

## Action and transition timing

The environment-facing action is two values:

| Component | Allowed contract | Published field |
| --- | --- | --- |
| `action[0]` | `[0, 1]` linear command | `Twist.linear.x` |
| `action[1]` | `[-1, 1]` angular command | `Twist.angular.z` |

`step` publishes the command and visualization markers, waits for
`/gazebo/unpause_physics`, calls it, sleeps `TIME_DELTA = 0.1` seconds, waits
for `/gazebo/pause_physics`, calls it, and then reads the latest sensor and
odometry callbacks. Service exceptions are printed and do not automatically
abort the method. `reset` follows the reset service with placement, marker
publication, an unpause/sleep/pause slice, and construction of the initial
state.

The actor in the repository produces both components in `[-1, 1]`. Its caller
maps only the first component with `(actor_linear + 1) / 2`; angular is passed
through. Do not infer this conversion from `GazeboEnv.step` itself.
