# Control, Ensembling, And Safety

## Step Lifecycle And Action Repetition

The agent starts with `step = -1`. Each `run_step` increments the counter. On
the first call it initializes a GPS route planner from `_global_plan`, creates a
full-brake control as a safe initial value, and marks itself initialized.

The configured `action_repeat` is **2** because LiDAR runs at half the 20 Hz
simulation frame rate. On steps where:

```text
step % action_repeat == 1
```

the agent propagates its GPS buffer with the previous control and returns that
same control without a network forward. On the other steps it preprocesses
sensors, runs the ensemble, creates a new control, updates the GPS buffer, and
returns it. Preserve this relationship between LiDAR cadence and action repeat;
setting it to 1 changes both inference cadence and the units used by stuck
thresholds.

## Forward Dispatch

The runtime dispatches one forward call per ensemble member:

- `transFuser`: image, LiDAR input, target point, target raster, velocity, plus
  debug/stuck metadata;
- `late_fusion`: image, LiDAR input, target point, target raster, velocity;
- `geometric_fusion`: the above plus CUDA int64 BEV/camera correspondence
  tensors;
- `latentTF`: image, dummy zero LiDAR-like tensor, target point, target raster,
  and velocity.

An unsupported string is intended to fail with the list of four valid
backbones. Validate before model construction because the source's error branch
uses an invalid string-raise form in Python 3.

## Waypoint Ensemble And Box NMS

Each network produces a waypoint tensor and zero or more rotated object boxes.
The agent:

1. averages waypoints across all checkpoint models;
2. transforms each configured test-time rotation back to local coordinates;
3. median-reduces rotations on CUDA (only 0° is configured, so this adds no
   diversity by default);
4. flattens boxes across networks and applies polygon-IoU NMS at threshold
   `0.2`;
5. stores the retained boxes in a one-frame buffer.

The object head first filters detections below confidence `0.3`. Runtime NMS
sorts confidence ascending, repeatedly keeps the highest-confidence box, and
removes boxes whose polygon IoU with it exceeds the threshold. Boxes are used
by the latent safety check; waypoint averaging drives normal control.

NMS relies on valid polygons. Degenerate or self-intersecting box corners can
cause invalid union/intersection behavior; diagnose object decoding and
coordinate conversion rather than lowering the threshold blindly.

## PID Conversion

The first ensemble network owns the PID-controller state, but the waypoints it
receives are the ensemble mean. The controller first converts waypoints from
LiDAR coordinates back toward vehicle coordinates by adding the LiDAR X offset
`1.3` to every waypoint X.

### Desired Speed And Brake

Using the first two predicted points:

```text
desired_speed = norm(waypoint[0] - waypoint[1]) * 2
```

When the agent is in forced stuck recovery, desired speed is replaced with
`4.0 m/s` (14.4 km/h). Brake is requested if either:

- desired speed is below `0.4 m/s`; or
- current speed divided by desired speed exceeds `1.1`.

The speed PID uses `Kp=5.0`, `Ki=0.5`, `Kd=1.0`, and a 20-sample error window.
Its nonnegative speed error is capped at `0.25`, throttle is clipped to
`[0, 0.75]`, and throttle is set to zero when braking.

### Steering

The steering aim is the midpoint of the first two waypoints. Normalized angle
error is:

```text
degrees(atan2(aim_y, aim_x)) / 90
```

Angle error is forced to zero when speed is below `0.01 m/s` or braking, which
prevents integral accumulation while stopped. The turn PID uses `Kp=1.25`,
`Ki=0.75`, `Kd=0.3`, and a 20-sample window; output steer is clipped to
`[-1, 1]`.

When braking or in forced recovery, steer is multiplied by `0.5`. On the first
forced-move frame steer is explicitly zero. The resulting values populate
`carla.VehicleControl.steer`, `.throttle`, and `.brake`.

## Stuck Detection And Forced Move

The detector increments on every newly computed-control step when speed is
below `0.1 m/s`. It resets `stuck_detector` and `forced_move` when speed is
above `0.1 m/s` and the agent is not currently in the stuck state.

Defaults are scaled by `action_repeat=2`:

```text
stuck_threshold = 1100 / 2 = 550 processed steps
creep_duration  =   30 / 2 =  15 processed steps
```

Because processed control steps occur at half the 20 Hz simulation rate, the
threshold represents about 55 seconds and the nominal creep window about 1.5
seconds. Forced movement starts only when `stuck_detector > stuck_threshold`
and continues while `forced_move < creep_duration`.

During forced movement:

- PID desired speed is forced to 4.0 m/s;
- steering is damped, with zero steering on the first forced frame;
- the front safety check is enabled before allowing the creep control;
- `forced_move` increments once per newly computed-control step.

Do not shorten the stuck threshold without reevaluating traffic-wait behavior.
The emergency controller intentionally lets the car remain stopped behind an
obstacle instead of forcing it into occupied space.

## Emergency Safety Check

`use_lidar_safe_check` is enabled by default, but its emergency override is
applied only while `is_stuck` is true.

### LiDAR-Fusion Backbones

The raw cloud is copied and Y is inverted. Points are retained only inside this
axis-aligned region:

| Axis | Lower bound | Upper bound |
| --- | ---: | ---: |
| Z | -2.0 | -1.05 |
| Y | -3.0 | 0.0 |
| X | -1.066 | 1.066 |

Any point in this filtered safety box marks an emergency stop.

### Latent Image-Only Backbone

Without LiDAR, retained predicted boxes are checked against a CARLA oriented
safety bounding box in front of the ego vehicle. Its longitudinal center uses a
speed-dependent braking-distance approximation:

```text
braking_distance = ((speed_mps * 3.6) / 10)^2 / 2
safety_x = clip(braking_distance + 1, 2, 4)
```

The standard ego extents are approximately `[2.451, 1.064, 0.755]`. Candidate
boxes are converted to CARLA oriented boxes, and a separating-axis test checks
for intersection. The one-frame post-NMS box buffer means this is perception
conditioned, not equivalent to physical LiDAR occupancy.

### Override

When an obstacle is detected during stuck recovery, the override keeps the
computed steer but sets throttle to `0.0` and brake to true. It intentionally
does not clear the stuck counter; if traffic remains in front, the agent waits
rather than defeating the obstacle check.

## Safety Interpretation

- The front safety check is an emergency guard for forced unblocking, not a
  general collision-avoidance controller on every frame.
- PID output quality depends on valid waypoint scale and coordinates. A bad
  checkpoint or target transform can still produce bounded but unsafe control.
- `strict=False` checkpoint loading must not be treated as safety validation.
- Static config checks cannot prove perception, route following, PID tuning, or
  emergency stopping. Those claims require the external CARLA 0.9.10.1 runtime
  and controlled simulator tests.
