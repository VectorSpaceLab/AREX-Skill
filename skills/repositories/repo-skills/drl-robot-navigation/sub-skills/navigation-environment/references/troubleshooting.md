# Navigation environment troubleshooting

Use these diagnoses without claiming a simulator run. First separate static
contract failures (which the bundled validator can check) from ROS/Gazebo
runtime failures (which require the declared prerequisites and a live system).

| Symptom | Likely cause | Safe diagnosis or boundary |
| --- | --- | --- |
| `ImportError` for `rospy`, `sensor_msgs`, or message classes | ROS Python environment is absent or not sourced | Do not import the environment just to check shapes; run the bundled pure-Python validator. This is not simulator verification. |
| `roscore`/`roslaunch` executable not found | ROS runtime is unavailable | Constructor cannot launch; do not replace it with a fake claim of success. |
| launch file does not exist | Relative name was resolved beside the environment module's `assets` directory, or the absolute path is wrong | Check the resolved launch-file contract. Do not assume the process current directory controls it. |
| Gazebo starts but `r1` is absent | `multi_robot_scenario` package, xacro, robot description, or `gazebo_ros spawn_model` failed | Inspect the ROS launch diagnostics in a ROS-capable environment; the offline validator cannot prove model spawning. |
| no `/velodyne_points` messages | Velodyne xacro/plugin is missing, plugin failed to load, topic name differs, or there are no subscribers | The plugin is configured for `/velodyne_points`; verify topic/type and plugin logs in the live system. No live topic check is claimed here. |
| all 20 bins remain `10.0` | callback has not received a message, all points were filtered, or points lie outside the angular gaps | Check callback timing and the z/range/angle filters. `10.0` is also the initial/default cap, not proof of a clear 10-unit corridor. |
| point-cloud callback raises or behaves oddly | zero horizontal magnitude, NaN/Inf coordinates, or `acos` round-off outside `[-1,1]` | The original callback has no explicit guard. Reject non-finite/zero-range synthetic points and use the validator's deterministic fixture rather than hiding the issue. |
| state has 23 or 25 values | wrong `environment_dim`, missing sensor/robot feature, extra batch/metadata value, or manual concatenation error | For this caller require exactly 20 bins + 4 robot values. The validator must reject both lengths. |
| negative linear action or angular value outside `[-1,1]` | actor-space output was passed to the environment without the caller's conversion, or a caller uses the wrong action convention | Convert only actor linear with `(a_linear + 1)/2`; validate the environment action before publishing. `step` performs no clipping or scaling. |
| first `step` fails while reading odometry | no `/r1/odom` callback has populated `last_odom` | Treat it as a missing topic/startup race. Do not substitute a guessed pose in a result report. |
| `wait_for_service` blocks | Gazebo ROS API is not running, physics service names changed, or master is unreachable | Check the four expected service names and ROS master connectivity. A static check cannot time out or repair the service. |
| service call prints a failure but method continues | `velodyne_env.py` catches `rospy.ServiceException` and only prints a message | Mark the transition/reset as runtime-failed; do not interpret the returned vector as evidence that physics advanced. |
| reward is unexpectedly `-100` | strict collision test found `min_laser < 0.35` | Check the minimum across all bins. At exactly `0.35`, collision is false. |
| reward is unexpectedly `100` | distance was strictly below `0.30`; target is checked before collision reward | At exactly `0.30`, target is false. If both flags are true, target reward wins. |
| shaping penalty is missing at close range | `min_laser >= 1` makes `r3=0`, or caller computed reward from a different distance | For the non-terminal branch use `linear/2 - abs(angular)/2 - r3/2`, with `r3=1-min_laser` only below 1. |
| reset loops for a long time | sampled robot/goal/box coordinates repeatedly fail the hard-coded obstacle rectangles or distance filters | This is randomized rejection sampling, not a fixed number of attempts. Do not claim a deterministic seed or termination guarantee. |
| boxes overlap an obstacle or navigation is still blocked | `check_pos` filters box centers only and does not model full footprints or all dynamic interactions | Treat placement as a heuristic scenario randomizer, not a collision-free proof. |
| offline validator rejects a scan with `z=-0.2` | expected: callback keeps only `z > -0.2` | Move the synthetic point above the strict boundary if it is intended to contribute. |

## Runtime boundary

This checkout does not provide ROS/Gazebo executables or ROS Python message
modules. Therefore static inspection, pure-Python numeric validation, and source
provenance are the available evidence. Do not report successful construction,
launch, topic delivery, service timing, or sensor callbacks without a separate
ROS-capable verification record.
