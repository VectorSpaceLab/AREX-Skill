# Twinbot workflow

## Two-host topology

1. **Physical Go2 → Jetson:** Unitree `/lowstate` arrives on the Jetson's
   Ethernet side through CycloneDDS and the Unitree ROS 2 message package.
2. **Jetson → Isaac host:** the bridge's second process publishes standard
   `sensor_msgs/JointState` and `nav_msgs/Odometry` with Fast DDS over the
   operator's Wi-Fi/LAN side.
3. **Isaac host:** the bundled simulation adapter starts the Go2 sim with
   `--twinbot`; the subscriber applies the most recent joint and IMU state after
   each physics step.

Keep `RMW_IMPLEMENTATION=rmw_fastrtps_cpp` on the sim-side path. On the Jetson,
CycloneDDS is restricted to the selected physical interface for the reader and
Fast DDS is allowed to select the forwarding interface for the publisher.

## Ordered startup

- Confirm the Jetson has ROS 2 Humble, `unitree_go`, both RMW implementations,
  and operator-approved access to the physical robot.
- Run the bundled bridge in its default dry-run mode first. Then run it with
  `--run` on the Jetson; do not use the command on a host without its external
  message packages and interface configuration.
- On the sim host, confirm `/real_dog/joint_states` and `/real_dog/odom` are
  visible before starting the bundled simulation adapter with `--twinbot
  --headless` and the Go2 selection.
- Look for the subscriber-ready signal and then verify that the simulated dog
  follows the latest joint/orientation data. Stop the bridge and sim using the
  operator's normal process controls.

## Network assumptions

Keep ROS domain and Fast DDS discovery settings aligned across the forwarding
side. The two RMWs do not discover one another directly; the bridge is the
intentional boundary. Do not change interface names, firewall rules, DDS XML,
or robot commands automatically.
