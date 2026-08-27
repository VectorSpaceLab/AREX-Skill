# ALOHA Real-Robot Deployment (external native checkout)

Read this before using the native VLA-Adapter ALOHA scripts in a real
environment. It is a safety/configuration checklist, not permission to run
hardware. The generated skill contains no ALOHA runtime or clients; set
`VLA_ADAPTER_REPO_ROOT` and use `cd <absolute-repo-root>` for native commands.

## Architecture

ALOHA deployment follows a server-client pattern:

1. A CUDA server loads a VLA-Adapter checkpoint and exposes `/act` over MsgPack
   HTTP.
2. A fake client can generate synthetic observations to sanity-check payload
   serialization and action return shape.
3. A real ROS client subscribes to three cameras and bimanual joint states,
   sends observations to the server, and publishes joint commands.

## Default observation/control assumptions

- Cameras: front, left wrist, right wrist.
- Image shape before policy resizing: often 480×640×3 uint8.
- State/action: 14D bimanual joint positions for ALOHA.
- Open-loop action chunk: 25 actions by default.
- Default control frequency: 40Hz.
- `unnorm_key` must match the ALOHA training dataset statistics.

## ROS topic review

Default topic meanings:

| Role | Topic kind |
| --- | --- |
| Front camera | image topic |
| Left/right wrist cameras | image topics |
| Left/right puppet joints | joint-state topics |
| Left/right master commands | joint command topics |
| Optional base odometry/command | odometry and velocity topics |

For a new robot, adapt topic names, action scaling, interpolation, open-loop
steps, and base motion flags in a controlled ROS environment. Do not assume the
repo defaults match a different robot.

## Safety checklist

- Human operator present with emergency stop.
- Robot workspace cleared and task staged.
- Server tested with fake client first.
- `unnorm_key` verified against checkpoint statistics.
- Action dimensions and units verified for the robot.
- Control topic names verified with non-moving or low-risk commands before VLA
  action control.
- Logs enabled and each trial has a stop procedure.

## Stop conditions

Stop immediately if observations desynchronize, action dimensions mismatch,
server returns errors, operator requests stop, or joint commands are outside
safe limits. Debug with fake payloads and logs before resuming.
