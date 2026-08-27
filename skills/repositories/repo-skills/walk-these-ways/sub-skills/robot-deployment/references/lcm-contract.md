# LCM message and observation contract

The deployment modules construct LCM with:

```text
udpm://239.255.76.67:7667?ttl=255
```

This is a UDP multicast URL, not a proof of connectivity. A host must have an
approved interface on the robot's `192.168.123.x` network and multicast support.
The read-only network helper reports local facts only; it never enables
multicast, adds a route, changes an IP, or publishes a message.

## Channels and direction

| channel | direction | source contract |
|---|---|---|
| `state_estimator_data` | robot/SDK → estimator | `state_estimator_lcmt` body and IMU state |
| `leg_control_data` | robot/SDK → estimator | `leg_control_data_lcmt` joint state and estimated torque |
| `rc_command` | RC/SDK → estimator | `rc_command_lcmt` sticks, mode, switches |
| `pd_plustau_targets` | controller → SDK/robot | `pd_tau_targets_lcmt` desired joint targets and gains; **actuation boundary** |
| `camera1` … `camera5` | robot camera → estimator | `camera_message_lcmt`, optional raw images |
| `rect_image_front`, `rect_image_bottom`, `rect_image_left`, `rect_image_right`, `rect_image_rear` | robot camera → estimator | `camera_message_rect_wide`, optional rectified images |

The controller subscribes to the first three state channels and, when
`StateEstimator(use_cameras=True)`, to both five-channel camera families. It
publishes the target channel from `LCMAgent.publish_action`; this operating skill
must never call that method or reproduce a publisher.

## State estimator fields

`state_estimator_lcmt` contains:

- `p[3]`, `vWorld[3]`, `vBody[3]`;
- `rpy[3]`, `omegaBody[3]`, `omegaWorld[3]`;
- `quat[4]`, `contact_estimate[4]`;
- `aBody[3]`, `aWorld[3]`;
- `timestamp_us`, `id`, and `robot_id` as 64-bit integers.

The source consumes `rpy` to build a rotation matrix and gravity vector and
uses `contact_estimate > 200` as a Boolean contact state before applying its
contact permutation. It derives smoothed body angular velocity from RPY
history; it does not use every schema field in the policy observation.

`leg_control_data_lcmt` contains `q[12]`, `qd[12]`, `p[12]`, `v[12]`,
`tau_est[12]`, `timestamp_us`, `id`, and `robot_id`. The estimator consumes
`q`, `qd`, and `tau_est`; the remaining fields remain part of the wire contract.

`rc_command_lcmt` contains `mode`, `left_stick[2]`, `right_stick[2]`,
`knobs[2]`, and six switch values: `left_upper_switch`,
`left_lower_left_switch`, `left_lower_right_switch`, `right_upper_switch`,
`right_lower_left_switch`, and `right_lower_right_switch`. The estimator uses
mode, both sticks, and all switch edge/current states. The runner treats the
right-lower-right switch as the R2 calibration/start gate and the
left-lower-left switch as a logging/probing event.

## Target message (document only; never publish here)

`pd_tau_targets_lcmt` contains twelve-element `double` arrays `q_des`,
`qd_des`, `tau_ff`, `kp`, and `kd`, followed by `timestamp_us`, `id`,
`robot_id`, and `se_contactState[4]`. The source sends zero velocity, feedforward
torque, and contact-state arrays, configured PD gains, and an id of `0` (or
`-1` for a hard reset). The target message is the actuation boundary and must
remain behind a human-approved SDK/controller process.

## Camera caveat

Raw `cameraN` payloads are `278400` bytes and are reshaped by the source as
`(3, 200, 464)` then transposed. Rectified wide payloads are `34800` bytes and
are reshaped using the source's `(116, 100, 3)` convention plus flips/transposes.
These shapes and channel names are source-specific. Camera use is optional and
can introduce bandwidth, generated-module, and shape failures; disable or
remove camera-dependent policy inputs rather than guessing a shape.

The repository's `go1_gym_deploy/tests/check_camera_msgs.py` references additional
message modules not present in the checked-in `lcm_types` directory (for
example mask/Vicon types). Treat that test as evidence of an optional generated
module dependency, not as a guaranteed smoke test.

## Architecture distinction

Python LCM schema classes are generated wire bindings, while `lcm_position` is a
compiled SDK-side executable. The same multicast URL and schema do not make an
ARM/aarch64 executable valid on x86, nor do they guarantee ABI compatibility.
Use the matching SDK build and generated modules for the target architecture;
see [container-runtime](container-runtime.md) and
[troubleshooting](troubleshooting.md). Missing LCM runtime or generated modules
is a hard stop, not a reason to publish test data.
