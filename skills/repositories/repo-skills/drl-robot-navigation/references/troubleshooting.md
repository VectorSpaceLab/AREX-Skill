# Cross-cutting troubleshooting

Read this when a request spans setup, environment, training, and evaluation or
when a failure could be caused by more than one layer. Keep the failure class
separate from policy quality.

## Missing runtime versus bad model

If `roscore`, `roslaunch`, `rospack`, Gazebo, catkin, or ROS message imports are
missing, stop before constructing `GazeboEnv`. This repository is not a Python
package that can be repaired with `pip install`; use a ROS Noetic/Gazebo host or
the documented container route, then run the static prerequisite checker. Do
not report a zero reward or failed policy when the simulator never started.

If Python-only model checks fail, use the TD3 model smoke and replay-buffer
smoke first. A failure there is a model/data-contract problem; a failure after
those checks may still be a simulator integration problem.

## Package and workspace resolution

After a catkin build, source the ROS setup and the generated workspace setup in
the same shell. Run `rospack find` for the scenario and Velodyne packages before
launching. A missing `multi_robot_scenario`, `velodyne_description`, or
`velodyne_gazebo_plugins` package indicates sourcing/build/resource resolution,
not an RL hyperparameter issue. Preserve existing `GAZEBO_RESOURCE_PATH` entries
when adding the scenario launch/resource directory.

## Sensor and state failures

The environment subscribes to absolute `/velodyne_points` and `/r1/odom`, and
uses `/gazebo/pause_physics`, `/gazebo/unpause_physics`, and
`/gazebo/reset_world`. Check topic names, message types, and service readiness
before changing code. An empty or stale point cloud can leave bins at `10`; a
missing odometry callback can make the first `step` fail. Validate the offline
24-value state and action contract, but do not treat it as proof of live ROS
connectivity.

The composite launch uses a CPU ray Velodyne by default. GPU PyTorch availability
does not prove Gazebo GPU-ray support. GPU-ray mode has version-specific range
caveats; select it only deliberately and validate the sensor output.

## Checkpoints and output paths

Training writes `<name>_actor.pth` and `<name>_critic.pth` as state dictionaries,
plus NumPy evaluation history and TensorBoard event files. The evaluator needs
the actor but not the critic. Use the bundled artifact checker before loading;
report missing, symlinked, oversized, corrupt, extra-key, and wrong-shape files
explicitly. Do not silently catch load errors and initialize a random actor.
Keep output directories separate for bounded smoke runs and avoid accidentally
mixing stale `TD3_velodyne` files with a new experiment.

## Timeouts and cleanup

The source training loop can run for millions of steps and the source evaluator
is unbounded. Always set step, episode, wall-clock, and operator-stop bounds for
experiments. If Gazebo or ROS must be stopped, use the host's approved process
management procedure and verify that the ROS master and simulator actually
exited. Do not run broad process-kill commands from an automated helper.
