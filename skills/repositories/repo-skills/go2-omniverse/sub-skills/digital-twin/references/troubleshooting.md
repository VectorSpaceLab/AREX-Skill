# Digital-twin troubleshooting

## Bridge starts but no `/real_dog/*` topics

Check the two process roles separately: CycloneDDS must receive `/lowstate` on
the selected Jetson Ethernet interface; Fast DDS must publish on the forwarding
interface. Confirm the ROS domain and RMW on each side before touching code. A
changed interface name is more likely than a joint mapping bug.

## Missing message or RMW package

`unitree_go`, `rmw_cyclonedds_cpp`, `rmw_fastrtps_cpp`, or standard message
imports must exist in the external runtime selected for each process. Do not
install them into the Isaac Sim Python environment as a substitute for a
matched Jetson ROS 2 workspace.

## Wrong joints or half-blended pose

Verify the 12-name motor order and that the sim subscriber receives names that
match its articulation. The environment action scale is not a safe place to
compensate for an ordering problem. The fixed playback path writes real joint
state after `env.step`; if the old action-based blend is present, the sim may
show a midpoint between default and real pose.

## Body flips or orientation is wrong

Check that `/real_dog/odom` is present, that SDK WXYZ is converted to ROS XYZW,
and that `twin.apply()` runs after the physics step. The implementation pins
spawn XY/Z because IMU has no absolute position; a rotating but non-translating
body is expected.

## Stale data

The queue deliberately drains to the newest item and drops backlog. If updates
stop, inspect timestamps/log counters and DDS discovery; do not increase queue
size indefinitely or send corrective robot commands automatically.
