---
name: simulation-setup
description: "Prepare and diagnose the ROS Noetic, Gazebo, catkin, launch, and
  Velodyne runtime used by DRL-robot-navigation without claiming unavailable
  native simulator verification."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Simulation setup

Use this skill when a Researcher must make the ROS/Gazebo simulator available, understand
how the repository starts it, or diagnose a startup, package, resource, sensor, display, or
process-lifecycle failure. This is an operating guide, not a training or reward guide.

## Contract and limits

- Target baseline: ROS Noetic on Ubuntu 20.04, with the Python/PyTorch versions stated by
'the project README. The simulator also depends on Gazebo ROS packages and a catkin toolchain.
- The normal build is `catkin_make_isolated` from the workspace root. Source the ROS and
workspace setup files in every shell that uses `roslaunch`, `rospack`, or Gazebo.
- The composite launch is the repository's `TD3/assets/multi_robot_scenario.launch`; its
resolved package launch files and sensor xacro are summarized in
`references/launch-topology.md`.
- Full ROS/Gazebo/roscore/roslaunch/catkin native verification was unavailable in the
extraction environment. The bundled checker is static and safe: it never starts ROS,
Gazebo, Docker, xacro, or a long-lived process. Do not report native runtime success from
its output.
- Do not silently change launch files, substitute a 2-D laser for the Velodyne topic, or
claim that a headless Docker build is a verified workaround. Route navigation state,
reward, TD3, and policy behavior to the sibling skills.

## First response to a setup request

1. Identify the execution boundary: a supported Ubuntu/ROS host, a ROS Noetic container,
   or a host without ROS. Ask for a supported provisioned environment when `/opt/ros/noetic`
   and the ROS commands are absent; do not fake them with pip packages.
2. Run the bundled, read-only check from this skill directory:

   ```bash
   python3 scripts/check_ros_prerequisites.py --workspace <catkin-workspace>
   ```

   Add `--json` for machine-readable diagnostics. It checks command presence, the ROS
   prefix, workspace paths, and environment values; it does not launch anything.
3. In a shell intended for the run, source the installed ROS setup and then the workspace
   setup (the latter is produced only after a successful build):

   ```bash
   source /opt/ros/noetic/setup.bash
   cd <catkin-workspace>
   source devel_isolated/setup.bash
   ```

   Keep `ROS_MASTER_URI`, `ROS_HOSTNAME`, and the simulator port consistent across every
   shell. If the ROS prefix is missing, follow the safe path in `references/troubleshooting.md`.
4. Configure the resource path before Gazebo resolves `TD3.world` and mesh assets. Preserve
   any existing entries rather than replacing them:

   ```bash
   export ROS_HOSTNAME=localhost
   export ROS_MASTER_URI=http://localhost:11311
   export ROS_PORT_SIM=11311
   export GAZEBO_RESOURCE_PATH=<catkin-workspace>/src/multi_robot_scenario/launch${GAZEBO_RESOURCE_PATH:+:$GAZEBO_RESOURCE_PATH}
   ```

5. Build manually from the workspace root when the prerequisites are present:

   ```bash
   catkin_make_isolated
   ```

   Review the first package or dependency failure; do not paper over it by copying
   generated `devel*` files from another machine.

## Startup topology and expected contracts

- `multi_robot_scenario.launch` includes `empty_world.launch`, which starts `gzserver`
  with `TD3.world`, then includes `pioneer3dx.gazebo.launch` for model `r1` at the origin.
- The robot launch expands `pioneer3dx.xacro`, spawns `r1`, and starts robot/joint state
  publishers. The xacro wires the diff-drive plugin (`/r1/cmd_vel`, `/r1/odom`) and the
  CPU Velodyne VLP-16 (`/velodyne_points`).
- The composite also starts RViz unconditionally using `pioneer3dx.rviz`; its `gui` arg
  does not disable that RViz node. A display-less Docker shell therefore needs an
  explicitly headless-safe launch choice; the documented Docker path is not native
  verification and is not automatically repaired by this skill.
- Confirm package resolution before debugging Gazebo:

  ```bash
  rospack find multi_robot_scenario
  rospack find velodyne_description
  rospack find velodyne_gazebo_plugins
  ```

  The standalone `pioneer3dx.urdf.launch` contains a stale `multi_robot_tutorial` package
  reference and is not the composite path. Prefer the composite topology unless a user
  intentionally maintains a corrected standalone launch.

## Velodyne readiness

The robot's VLP-16 macro uses CPU ray mode (`gpu:=false`), 16 vertical lasers, 360
horizontal samples, 10 Hz, horizontal angles `[-1.57, 1.57]`, and topic `/velodyne_points`.
The plugin emits `sensor_msgs/PointCloud2` with `x`, `y`, `z`, `intensity`, `ring`, and
`time` fields. The environment subscribes to the absolute topic and therefore will not
receive data from an arbitrary remapped or 2-D laser topic. The plugin activates sensor
production when it has a subscriber, so check the subscriber and topic before treating an
empty cloud as a Gazebo failure. See `references/velodyne-sensor.md` for a diagnostic order.

## Headless/container guidance

The README documents `docker build -t drl_noetic .`, an interactive `docker run`, and
starting training inside the container. The Dockerfile sets software rendering,
`GAZEBO_HEADLESS_RENDERING=1`, an empty `DISPLAY`, ROS localhost values, and a launch
resource path, then clones a named remote branch and builds with `catkin_make`. Treat this
as a reproducible starting point only: it performs a network-dependent build, follows a
branch rather than this snapshot, has no persistence with `--rm`, and the composite still
contains an unconditional RViz node. Read `references/container.md` before using it.
Do not add an automatic Docker build/run helper or an infinite training/launch script.

## Handoff and evidence

Report which checks passed, which are missing, and whether the result is host or container
based. Keep these separate:

- static prerequisites and package/path evidence;
- successful catkin build and generated setup file;
- actual roscore/roslaunch/Gazebo startup;
- live `/velodyne_points`, `/r1/odom`, and Gazebo service evidence.

The current source snapshot supports the first category and documents the others, but the
available environment did not support the final three. Use the troubleshooting reference
for xacro/package errors, missing resources, Gazebo/RViz display problems, plugin loading,
and orderly shutdown. If the request is about observation binning, reward, action scaling,
or TD3 parameters, hand it to the corresponding sibling sub-skill instead of expanding
this one.
