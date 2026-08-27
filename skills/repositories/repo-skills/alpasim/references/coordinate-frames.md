# Coordinate frames and service boundaries

Read before changing trajectories, poses, or gRPC service payloads. AlpaSim
uses active-transform naming and distinguishes the quantity's frame from the
object being described.

- `local`: scenario-fixed ENU inertial frame from NRE.
- `rig`: ego body frame: x forward, y left, z up; origin at the rear axle
  projected to ground.
- `aabb`: body-oriented bounding-box frame with the same orientation convention
  as the rig but a box-center origin.
- `ecef`: WGS84 Earth-centered inertial frame.
- `estimated`/`noised`: the driver's proprioceptive frame; runtime maps driver
  outputs back to the true local frame.

Use names such as `position_object_in_local`,
`pose_local_to_rig`, and `rotation_rig_to_sensor` rather than an unqualified
`position` or `pose`. The code's `A->B` active transform moves a quantity in
frame A using the transform toward B; changing the coordinate notation is the
inverse passive operation.

Service expectations:

- Driver: receives noised history in local, route waypoints in the noised rig
  frame, ground truth in rig; returned trajectories are mapped by runtime.
- Controller: receives current `pose_local_to_rig`, velocities, and a rig-frame
  reference trajectory; returns future local-to-rig poses and estimates.
- Physics and traffic: exchange local-to-AABB transformations.
- Renderer: receives a local-frame rig trajectory, rig-to-sensor calibration,
  and local-to-AABB dynamic actor trajectories.
- Logs: `ActorPoses` store actors in AABB relative to local; metadata preserves
  the rig-to-AABB transform needed for replay.

When a value looks spatially plausible but a service fails, check frame and
active/passive direction before changing units or solver settings. Keep
microsecond timestamps explicit alongside spatial frame names.
