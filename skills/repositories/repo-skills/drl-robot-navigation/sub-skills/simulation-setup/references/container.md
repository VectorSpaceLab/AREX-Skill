# Documented Docker alternative

The source README and `dockerfile` describe a ROS Noetic desktop-full image for a headless
training attempt. This is guidance for a human-controlled container run, not an automatic
script and not proof that the simulator works in the current environment.

## What the image does

The Dockerfile:

1. starts from `osrf/ros:noetic-desktop-full`;
2. sets `LIBGL_ALWAYS_SOFTWARE=1`, `GAZEBO_HEADLESS_RENDERING=1`, an empty `DISPLAY`,
   localhost ROS variables, and a Gazebo resource path under the image's workspace;
3. installs Git and pip, then installs Torch, TensorBoard, and squaternion without pinned
   versions;
4. clones the remote `feature/docker_headless_noetic` branch into the image rather than
   copying the inspected source snapshot;
5. sources `/opt/ros/noetic/setup.bash` and runs `catkin_make` (not
   `catkin_make_isolated`) in the cloned workspace; and
6. appends the generated workspace setup to root's `.bashrc` and starts an interactive
   bash shell.

These choices imply network dependence and source/version drift. The project README's
`docker run --rm` also discards files written only inside the container when the session
ends. Use an explicit host volume if model or TensorBoard output must survive, and verify
that the volume does not overwrite the image's built workspace unintentionally.

## Human-controlled sequence

From a directory containing the intended Dockerfile, the documented shape is:

```bash
docker build -t drl_noetic .
docker run --rm -it drl_noetic
```

Inside the container, first confirm the ROS and workspace setup in the current shell. If
using a different image or shell, source them explicitly:

```bash
source /opt/ros/noetic/setup.bash
source <workspace>/devel/setup.bash
```

The README then changes to the project TD3 directory and starts training. That is an
unbounded workload and must be initiated deliberately by the Researcher; this skill never
wraps it in a helper or claims it completed. Similarly, do not turn image building,
`docker run`, `roscore`, or `roslaunch` into an automatic bundled script.

## Headless caveat that must be checked

`GAZEBO_HEADLESS_RENDERING=1`, `DISPLAY=`, and the `gui=false` world default suppress the
Gazebo client in the normal world include, but they do not suppress the unconditional RViz
node in `multi_robot_scenario.launch`. The Dockerfile therefore documents environment
intent, not a guaranteed no-display launch. A user who needs a truly display-less run must
choose or maintain a launch composition that omits RViz and then validate the resulting
sensor/topic contract. Do not claim the documented image is headless-verified merely
because it builds.

The `empty_world.launch` file also states that its `headless` argument is currently
non-functional for the underlying Gazebo behavior. Treat it as an argument-preservation
mechanism rather than a reliable rendering switch.

## Container diagnosis order

1. Confirm `/opt/ros/noetic/setup.bash`, `roscore`, `roslaunch`, `catkin_make`, and
   `gzserver` exist inside the container.
2. Confirm the workspace setup file named by the image actually exists and that
   `rospack find` resolves the scenario and Velodyne packages.
3. Check `ROS_MASTER_URI`, `ROS_HOSTNAME`, `ROS_PORT_SIM`, and
   `GAZEBO_RESOURCE_PATH`; preserve existing resource-path entries when adding the
   scenario launch directory.
4. Before a long training run, use a deliberately bounded startup and inspect the
   `gzserver`, xacro, spawn, plugin, and RViz logs. Confirm `/r1/odom` and
   `/velodyne_points` before handing off to the navigation process.
5. If only RViz fails because `DISPLAY` is empty, classify that as a launch-topology/display
   mismatch, not as evidence that Gazebo or the Velodyne plugin is broken.

The bundled `scripts/check_ros_prerequisites.py` is safe to run inside or outside the
container, but it only checks presence and configuration. The extraction host did not have
ROS Noetic, Gazebo, or ROS message modules, so no container build or native launch result
is available to report.
