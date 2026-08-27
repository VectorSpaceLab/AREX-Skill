# Controller API and operating details

## State, frames, and integration

`VehicleModel` is a planar dynamic bicycle model. Its state has eight entries:

| Index | Name | Meaning |
|---:|---|---|
| 0 | `x` | rig-origin X in the temporary inertial frame |
| 1 | `y` | rig-origin Y in the temporary inertial frame |
| 2 | `yaw` | rig-origin yaw in the temporary inertial frame |
| 3 | `vx_cg` | CG longitudinal velocity in body coordinates, m/s |
| 4 | `vy_cg` | CG lateral velocity in body coordinates, m/s |
| 5 | `yaw_rate` | body yaw rate, rad/s |
| 6 | `steering` | front-wheel steering angle, rad |
| 7 | `accel` | longitudinal acceleration state, m/s² |

The controller interface is:

```python
ControllerInput(
    state: numpy.ndarray,                 # shape (8,)
    reference_trajectory: Trajectory,     # poses in the current rig frame
    timestamp_us: int,
)

ControllerOutput(
    control: numpy.ndarray,               # [steering_cmd, accel_cmd]
    solve_time_ms: float,
    status: str,
)
```

`MPCController` exposes `dt_mpc`, `name`, and `compute_control`. The public
factory is `create_system(log_file, initial_state, controller_config)`, and the
service-side manager is `SystemManager(log_dir, controller_config)`.

The external trajectory/state API uses rig-frame quantities. On a coerced step,
`System` converts rig lateral velocity to CG lateral velocity using the CG offset
and converts the resulting CG state back to rig-frame velocity/acceleration for
responses. The model resets its integrated `(x, y, yaw)` origin before each
relative propagation; this is intentional and does not reset dynamic state.

A model below 5 m/s uses a kinematic low-speed approximation to avoid the
singular dynamic-bicycle equations. At higher speed it uses the dynamic bicycle
model. Longitudinal velocity is clamped non-negative after integration, so this
model does not support reverse motion.

## Config and choice

```python
ControllerConfig(
    mpc_implementation="linear",  # "linear" or "nonlinear"
    n_horizon=20,
    dt_mpc=0.1,
    gains=MPCGains(),
)
```

`MPCGains` weights longitudinal position, lateral position, heading,
acceleration, steering-command changes, and acceleration-command changes. The
tracking terms are disabled before `idx_start_penalty` (default 10). Both
implementations use the same broad objective and actuator limits, but formulate
and solve different problems.

### Linear MPC

`LinearMPC` uses OSQP. It linearizes the dynamics about the current state,
constructs condensed prediction matrices, interpolates reference poses across
`n_horizon + 1` points, and returns the first command from the QP. Its principal
state limits are yaw ±π/2, forward speed 0–40 m/s, steering ±π/4, and
acceleration −8–6 m/s². Command limits are steering −2–2 and acceleration −9–6
in the model's command units. A non-solved OSQP status is returned rather than
silently claiming success.

### Nonlinear MPC

`NonlinearMPC` builds its do_mpc/CasADi model at construction and lazily creates
the solver on the first `compute_control`. It uses collocation with a Radau
scheme, degree 2, one collocation interval, and an IPOPT maximum of 30
iterations. It has explicit state/input bounds and returns a status beginning
with `failed:` if the solver raises. A zero command in that failure path is not
evidence that the trajectory was tracked.

## Service lifecycle and request invariants

The standalone controller server accepts:

```text
--host HOST                 default 0.0.0.0
--port PORT                 default 50051
--log_dir DIRECTORY         default .
--log-level LEVEL           default INFO
--config YAML               optional typed ControllerConfig file
```

The controller service has `start_session`, `run_controller_and_vehicle`, and
`close_session` operations. A session must be registered first. The first run
lazily creates a `System` and logs to `alpasim_controller_<session>.csv` below
the selected log directory. Every subsequent request must match the previous
simulation timestamp. A run request must satisfy all of the following:

- `planned_trajectory_in_rig` is non-empty.
- `future_time_us` is greater than the current state timestamp.
- `pose_reporting_interval_us` is non-negative.
- The current state timestamp agrees with the manager/system trajectory.
- The session UUID exists and has not been closed.

Violations are surfaced as `ValueError`/`KeyError` in the Python manager and as
service errors at the gRPC boundary. Closing an unknown or already closed
session is an error.

## A repeatable controller check

Construct a straight `Trajectory` with monotonically increasing microsecond
timestamps and identity yaw quaternions. Use an 8-element state with a positive
`vx_cg`, call `compute_control`, and assert:

- `control.shape == (2,)`;
- `solve_time_ms` is positive;
- linear status is `solved` or `solved_inaccurate`;
- nonlinear status is `solved` for a successful solver call.

For a positive lateral offset against a straight reference, both implementations
should normally command negative steering. This is a behavioral check, not a
universal sign rule for arbitrary frame conventions.

The native controller cases also exercise the low-speed/high-speed model switch,
vehicle integration, dynamic-state coercion, session lifecycle, and both MPC
implementations.

## Benchmarking

Run the benchmark module from the controller package directory. Use the quick
set for an iteration check; it covers 14 trajectories. The full set covers about
120 trajectories and is a longer performance run:

```bash
python -m benchmark run --quick --output results/linear.json \
    --description "linear baseline"
python -m benchmark run --quick --config controller.yaml \
    --output results/nonlinear.json --description "nonlinear comparison"
python -m benchmark compare results/linear.json results/nonlinear.json \
    --output-dir comparison/
python -m benchmark list --quick
```

A custom YAML is parsed against `ControllerConfig`; unset fields retain their
defaults. Benchmark JSON records per-trajectory pose/reference traces and solve
times, so compare tracking behavior and timing rather than only process exit
status. Full sweeps and interactive plotting are optional and potentially
expensive; do not run them as an unbounded verification step.
