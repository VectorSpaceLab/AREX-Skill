# Troubleshooting matrix

Use the narrowest diagnosis first. Preserve the first error from the failing command and
separate a missing host capability from a source/configuration error. The extraction host
lacked ROS Noetic, Gazebo, roscore, roslaunch, catkin_make, and ROS Python message modules;
full native verification is therefore explicitly unavailable.

## Missing ROS Noetic or catkin commands

**Symptoms:** `/opt/ros/noetic/setup.bash` is absent; `roscore`, `roslaunch`, `rospack`,
`catkin_make_isolated`, or `gzserver` is not found; Python imports of `rospy` or ROS
messages fail.

**Safe path:** stop before building or launching. Use a supported Ubuntu 20.04 host with
ROS Noetic and the required Gazebo ROS packages, or use a deliberately provisioned ROS
Noetic container. Do not attempt to repair a system ROS installation with pip, and do not
claim that the inspection Python environment is a simulator environment. After installing
or entering the supported environment, source `/opt/ros/noetic/setup.bash`, run the static
checker again, and build the workspace manually.

## Workspace package not found

**Symptoms:** `rospack find multi_robot_scenario` or
`rospack find velodyne_description` fails; `roslaunch` reports `package ... not found`.

1. Confirm the command is running in a shell that sourced `/opt/ros/noetic/setup.bash`.
2. Confirm the catkin build completed and produced the workspace setup file.
3. Source the matching workspace setup (`devel_isolated/setup.bash` for the documented
   `catkin_make_isolated` route) in the current shell.
4. Re-run `rospack find` for all three Velodyne/scenario packages.
5. If a vendored package is absent from the source tree or was skipped by the build, fix
   the workspace/package state and rebuild; do not copy a generated setup directory from a
   different checkout.

## Catkin build failure

**Symptoms:** `catkin_make_isolated` stops in CMake or package configuration.

Capture the first failing package and its missing dependency. The scenario package
explicitly declares `xacro`; the launch path also requires installed Gazebo ROS, RViz,
state publisher, joint-state, and spawn packages, while the workspace supplies the
Velodyne description and plugin packages. A successful parse of one launch file does not
prove that the plugin shared library compiled. Fix the supported ROS/Gazebo package set,
then rerun the build from the workspace root. Avoid switching to `catkin_make` merely to
hide an isolated-build error; the Dockerfile and README document different commands and
are not equivalent verification evidence.

## Xacro or package URI failure

**Symptoms:** `xacro` reports an unknown package, include, macro, or file; Gazebo cannot
resolve a mesh; the robot description is empty.

- Validate `rospack find multi_robot_scenario` and `rospack find velodyne_description`
  before inspecting the xacro expansion.
- Verify the active composite chain uses `pioneer3dx.gazebo.launch` and
  `pioneer3dx.xacro`, not the stale `pioneer3dx.urdf.launch` path. The latter refers to
  `multi_robot_tutorial`, which is not the visible package name.
- Check that the Velodyne description package and its `VLP-16.urdf.xacro` are in the
  workspace and built.
- The Pioneer body evidence contains a mesh URI beginning
  `package://gazebo_plugins/test/multi_robot_scenario/...`, which is suspicious relative
  to the visible package. Treat a missing mesh as a source URI fault and report the exact
  URI. Do not silently rewrite the source in this runtime skill.
- Keep `GAZEBO_RESOURCE_PATH` pointed at the scenario launch/resource directory and retain
  existing resource entries. A correct ROS package path does not automatically repair
  Gazebo's world/mesh resource lookup.

## World/resource resolution failure

**Symptoms:** `TD3.world`, materials, or meshes are not found; Gazebo starts and exits
while loading the world.

Check:

```bash
printf '%s\n' "$GAZEBO_RESOURCE_PATH"
rospack find multi_robot_scenario
```

For the documented layout, the scenario launch/resource directory is the `launch`
subdirectory under `multi_robot_scenario`. Set it using the actual workspace root, for
example:

```bash
export GAZEBO_RESOURCE_PATH=<catkin-workspace>/src/multi_robot_scenario/launch${GAZEBO_RESOURCE_PATH:+:$GAZEBO_RESOURCE_PATH}
```

Do not replace a non-empty resource path wholesale if it contains other Gazebo assets.
The path is an environment hint, not a substitute for a successful catkin build.

## Gazebo/RViz display and headless failures

**Symptoms:** `gzserver` appears usable but RViz reports `DISPLAY`/OpenGL errors, or a
container with `DISPLAY=` fails as the composite starts.

The world include defaults `gui=false`, and the Dockerfile requests software/headless
rendering, but the composite launch starts RViz unconditionally. Its `gui` arg is not a
reliable global headless switch. Classify this as a launch-topology/display mismatch.
Use an intentionally maintained launch composition that omits RViz for a no-display run,
then separately confirm the ROS topics and Gazebo services. Do not claim that the
Dockerfile's build or `GAZEBO_HEADLESS_RENDERING=1` proves a headless launch works.

If RViz works but Gazebo rendering is slow, retain software rendering only as a deliberate
container choice and inspect `gzserver` logs. Do not use `killall -9` as routine recovery;
identify the owning launch session and terminate it in an orderly way.

## Velodyne plugin or empty cloud

**Symptoms:** robot spawns without `/velodyne_points`, Gazebo logs a missing `.so`, or the
topic exists but has no messages.

1. Confirm `velodyne_description` and `velodyne_gazebo_plugins` resolve with `rospack`.
2. Confirm the active xacro includes VLP-16 with `gpu:=false`; the expected plugin is
   `libgazebo_ros_velodyne_laser.so`. GPU mode selects another library and is not the
   documented baseline.
3. Inspect the first Gazebo plugin load error and verify that the plugin package was built
   in the current workspace and the workspace setup was re-sourced.
4. Check `rostopic info /velodyne_points` for a subscriber. The vendored plugin activates
   the underlying sensor on demand, so no subscriber can yield no generated cloud.
5. Once messages exist, verify `sensor_msgs/PointCloud2` and fields `x`, `y`, `z` before
   handing data-shape issues to the navigation-environment skill.

The active configuration uses CPU rays, 16 vertical lasers, 360 horizontal samples,
10 Hz, and `/velodyne_points`; changing these can change downstream observation behavior.

## Robot or process lifecycle

**Symptoms:** stale roscore/roslaunch processes, duplicate ROS masters, a respawning
Gazebo server, or a second run cannot bind the master port.

- Use one deliberate master for the local run and keep `ROS_MASTER_URI` and
  `ROS_PORT_SIM` aligned (`http://localhost:11311` and `11311` in the documented setup).
- Check existing processes and the owning launch session before starting another one.
- `respawn_gazebo` defaults to true in `empty_world.launch`; a `gzserver` crash may be
  restarted by roslaunch. Read the original failure before stopping the parent launch.
- Stop a bounded launch session through its controlling terminal or launch lifecycle;
  avoid broad `killall -9` commands that can destroy unrelated ROS jobs. Only use a
  targeted forced termination after orderly shutdown has failed and the user has accepted
  the scope.
- A clean process exit does not prove that topics were ever published. Record startup,
  topic, and service evidence separately.

## Environment variable reconciliation

For a local single-host run, the documented values are:

```text
ROS_HOSTNAME=localhost
ROS_MASTER_URI=http://localhost:11311
ROS_PORT_SIM=11311
GAZEBO_RESOURCE_PATH=<workspace>/src/multi_robot_scenario/launch[:existing entries]
```

`ROS_PORT_SIM` is consumed by this repository's environment startup convention and should
not be changed independently of the roscore/roslaunch port. In multi-host or container/
host networking, do not blindly retain `localhost`: select an address reachable from all
ROS participants and make the master URI, hostname, published interfaces, and Docker
networking agree. The static checker can identify missing or inconsistent values but
cannot prove network reachability.
