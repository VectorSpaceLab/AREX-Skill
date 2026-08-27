# Filter and debugging analysis

## KF/EKF state contract

Both the stock `KalmanFilter` and the customization example
`ExtentedKalmanFilter` maintain the four-element column state:

```text
xEst.shape == (4, 1)
state == [x, y, yaw, v]
```

`x` and `y` are world/ESU coordinates, `yaw` is radians inside the filter, and
`v` is metres per second. The covariance matrices are `Q.shape == (4, 4)`,
`R.shape == (3, 3)`, and `PEst.shape == (4, 4)`. `time_step` is the constructor
`dt` value.

Initialize once with scalar values:

```text
run_step_init(x, y, heading, velocity) -> None
```

Then provide the five scalar inputs for every measurement step:

```text
run_step(x, y, heading, velocity, yaw_rate_imu)
  -> (x, y, heading, velocity)
```

The returned values are scalar floats. `heading` is radians and
`yaw_rate_imu` is the IMU yaw rate in radians per second. The GNSS observation
is `[x, y, heading]`; the control input is `[velocity, yaw_rate_imu]`.

The linear KF uses a fixed motion matrix. The extended filter additionally
computes `jacob_f(x, u)` and propagates the covariance with that Jacobian. The
filter-only replacement is contract-compatible when it preserves the
initializer, the two step methods, the four-state shape, and the four-scalar
return order. Do not compare filter values across implementations without
keeping `dt`, units, initial state, covariance, and measurement sequence fixed.

## Manager-level units

The localization manager is the unit-conversion boundary:

1. It converts the noisy speed from km/h to m/s before `run_step`.
2. It converts the vehicle yaw from degrees to radians before
   `run_step_init`/`run_step`.
3. It converts filtered speed back to km/h for `_speed`.
4. It converts filtered yaw back to degrees for the returned
   `carla.Rotation`.

A filter that returns degrees or km/h will look numerically plausible but will
corrupt downstream planning and control. Test units explicitly at the seam.

## LocDebugHelper without a simulator

`LocDebugHelper(config_yaml, actor_id)` stores three tracks and accepts twelve
scalar arguments in `run_step`:

```text
gnss_x, gnss_y, gnss_yaw, gnss_spd,
filter_x, filter_y, filter_yaw, filter_spd,
gt_x, gt_y, gt_yaw, gt_spd
```

The speed tracks are stored after division by 3.6. With one or more samples,
`evaluate()` returns `(figure, report_text)`, where the report contains mean
GNSS and filtered errors for x, y, and yaw. It does not need a CARLA server.
Use `show_animation: false` for automated checks. If a figure is needed, keep
it in memory or save it with a non-interactive backend; do not call
`plt.show()` in a CI or agent run.

Set the plotting backend before importing OpenCDA's plotting helper. In
verification, run the focused EKF, localization-debug, and drive-profile
checks supplied by the repository or recreate the bounded synthetic checks
below with `MPLBACKEND=Agg`. The runtime skill does not depend on those source
check files remaining available.

The repository helper attempts `TkAgg` only when animation is enabled and
catches `ImportError`, but an explicitly headless `Agg` backend plus
`show_animation: false` is the reliable path. Do not depend on a display,
Tk, Qt, or a CARLA server for these diagnostics.

## Bounded synthetic checks

For a filter-only check, instantiate KF and EKF with a small positive `dt`,
initialize both with the same finite state, run one finite measurement, and
assert:

- `xEst` remains `(4, 1)` and `PEst` remains `(4, 4)`;
- the result has four finite scalar values;
- the manager-facing conversion is tested separately if the replacement is
  installed in a localization manager.

For the debug helper, create it with `show_animation: false`, submit one
consistent sample, call `evaluate()`, assert that the returned report is text,
and close the returned figure. This catches shape, unit, and plotting failures
without opening a window. A live manager test is a separate CARLA-backend
case, not a substitute for these deterministic checks.
