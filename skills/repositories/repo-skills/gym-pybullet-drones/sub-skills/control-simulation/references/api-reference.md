# Control API Reference

This reference captures the public API facts needed for control-simulation work without reopening the original repository. Baseline inspection: `gym-pybullet-drones` package version `2.2.0` on Python `3.12.13`; Gymnasium env IDs `ctrl-aviary-v0` and `velocity-aviary-v0` are registered by the package.

## Environment constructors

`CtrlAviary` and `VelocityAviary` are headless-capable and share the same constructor shape inherited from `BaseAviary`, minus `vision_attributes`.

### `BaseAviary(...)`

```python
BaseAviary(
    drone_model=DroneModel.CF2X,
    num_drones=1,
    neighbourhood_radius=np.inf,
    initial_xyzs=None,
    initial_rpys=None,
    physics=Physics.PYB,
    pyb_freq=240,
    ctrl_freq=240,
    gui=False,
    record=False,
    obstacles=False,
    user_debug_gui=True,
    vision_attributes=False,
    output_folder='results',
)
```

Key constructor constraints and side effects:

| Field | Operating note |
| --- | --- |
| `drone_model` | `DroneModel.CF2X`, `DroneModel.CF2P`, or `DroneModel.RACE`; controller compatibility is stricter than environment compatibility. |
| `num_drones` | Drives action/observation shapes. `initial_xyzs` and `initial_rpys` must match `(num_drones, 3)` when provided. |
| `physics` | Selects base PyBullet, explicit dynamics, ground effect, drag, downwash, or combined physics. |
| `pyb_freq`, `ctrl_freq` | `pyb_freq % ctrl_freq == 0` is required. `CTRL_TIMESTEP = 1 / ctrl_freq`. |
| `gui` | `False` connects PyBullet with `DIRECT`; `True` requires display/OpenGL. |
| `record` | With GUI, records MP4 through PyBullet; headless direct mode saves PNG frames under `output_folder`. |
| `output_folder` | Used by environment recording and by `Logger` when passed separately. Ensure parents exist for custom paths. |

### `CtrlAviary(...)`

Same public constructor shape as above except no `vision_attributes` argument. It is a control-oriented environment where:

- `action_space`: `spaces.Box` with shape `(NUM_DRONES, 4)` in RPM units, clipped to `[0, MAX_RPM]`.
- `observation_space`: `spaces.Box` with shape `(NUM_DRONES, 20)`.
- `_computeObs()`: returns a `(NUM_DRONES, 20)` array with one 20-value state vector per drone.
- `_preprocessAction(action)`: clips each row of `action` to valid RPMs.

### `VelocityAviary(...)`

Same public constructor shape as `CtrlAviary`. It is a high-level velocity-command environment where:

- `action_space`: shape `(NUM_DRONES, 4)` with `[vx, vy, vz, speed_fraction]` per drone.
- The first three components are normalized to a direction; the fourth component scales `SPEED_LIMIT` via `abs(speed_fraction)`.
- Internally creates `DSLPIDControl` controllers for Crazyflie models and converts velocity commands into motor RPMs.
- `observation_space` and observations still use `(NUM_DRONES, 20)` state vectors.

## Public `BaseAviary` methods

| Method | Signature | Return/behavior |
| --- | --- | --- |
| `reset` | `reset(seed=None, options=None)` | Returns `(obs, info)` after resetting PyBullet, housekeeping, kinematics, and recording. |
| `step` | `step(action)` | Returns `(obs, reward, terminated, truncated, info)` after preprocessing action and running physics steps. |
| `render` | `render(mode='human', close=False)` | Prints textual state; if `gui=False`, warns that graphical rendering needs `gui=True`. |
| `close` | `close()` | Stops GUI video logging if active and disconnects the PyBullet client. |
| `getPyBulletClient` | `getPyBulletClient()` | Returns the integer PyBullet client ID. |
| `getDroneIds` | `getDroneIds()` | Returns a `(NUM_DRONES,)` array of PyBullet body IDs. |

The 20-value state vector layout returned by `_getDroneStateVector(i)` and exposed in control observations is:

```text
[x, y, z, qx, qy, qz, qw, roll, pitch, yaw,
 vx, vy, vz, wx, wy, wz, rpm0, rpm1, rpm2, rpm3]
```

## Physics enum values

| Enum | Value | Use |
| --- | --- | --- |
| `Physics.PYB` | `"pyb"` | Base PyBullet rotor forces/torques. |
| `Physics.DYN` | `"dyn"` | Explicit dynamics update path. |
| `Physics.PYB_GND` | `"pyb_gnd"` | PyBullet plus ground effect. |
| `Physics.PYB_DRAG` | `"pyb_drag"` | PyBullet plus drag. |
| `Physics.PYB_DW` | `"pyb_dw"` | PyBullet plus downwash; used by the downwash workflow. |
| `Physics.PYB_GND_DRAG_DW` | `"pyb_gnd_drag_dw"` | Combined ground effect, drag, and downwash. |

## Drone model enum values

| Enum | Value | Control compatibility |
| --- | --- | --- |
| `DroneModel.CF2X` | `"cf2x"` | Works with `DSLPIDControl`, `VelocityAviary`, `MRACControl`, and `CtrlAviary`. |
| `DroneModel.CF2P` | `"cf2p"` | Works with `DSLPIDControl`, `VelocityAviary`, `MRACControl`, and `CtrlAviary`. |
| `DroneModel.RACE` | `"racer"` | Environment-compatible and supported by `MRACControl`; not supported by `DSLPIDControl`/`VelocityAviary` in the current package. |

## Controller APIs

### `BaseControl`

```python
BaseControl(drone_model: DroneModel, g: float = 9.8)
```

Public methods:

```python
reset()
computeControlFromState(
    control_timestep,
    state,
    target_pos,
    target_rpy=np.zeros(3),
    target_vel=np.zeros(3),
    target_rpy_rates=np.zeros(3),
)
computeControl(
    control_timestep,
    cur_pos,
    cur_quat,
    cur_vel,
    cur_ang_vel,
    target_pos,
    target_rpy=np.zeros(3),
    target_vel=np.zeros(3),
    target_rpy_rates=np.zeros(3),
)
setPIDCoefficients(...)
```

`computeControlFromState(...)` slices the 20-value `BaseAviary` state into position, quaternion, velocity, and angular velocity, then delegates to `computeControl(...)`.

### `DSLPIDControl`

```python
DSLPIDControl(drone_model: DroneModel, g: float = 9.8)
```

Compatibility and returns:

- Requires `DroneModel.CF2X` or `DroneModel.CF2P`; it prints an error and exits for unsupported models.
- Implements cascaded position and attitude PID control.
- `computeControl(...)` returns `(rpm, pos_e, yaw_error)`.
- `rpm` is a 4-value motor RPM vector.
- `target_rpy_rates` are Euler-angle rates in rad/s for the attitude derivative term, not body-rate commands.

### `MRACControl`

```python
MRACControl(drone_model: DroneModel, g: float = 9.8)
```

Compatibility and returns:

- Supports `DroneModel.CF2X`, `DroneModel.CF2P`, and `DroneModel.RACE` in the current package.
- Uses `control.place(...)` and `scipy.linalg.solve_lyapunov(...)` during setup.
- `computeControl(...)` returns `(rpm, pos_e, rpy_e)`.
- Inputs follow the same `BaseControl.computeControl(...)` signature; targets combine position, RPY, velocity, and RPY rates into a 12-value reference internally.

### `CTBRControl`

```python
CTBRControl(drone_model: DroneModel, g: float = 9.8)
```

`CTBRControl` is a control utility with a `BaseControl`-like interface but it does not subclass `BaseControl`. It asserts vector shapes in `computeControl(...)` and returns a normalized thrust plus body-rate-like commands:

```python
norm_thrust, body_rate_x, body_rate_y, body_rate_z = ctbr.computeControl(...)
```

Its `computeControlFromState(...)` adapts the PyBullet state quaternion into the `transforms3d` ordering it uses internally.

## Logger API

```python
Logger(
    logging_freq_hz: int,
    output_folder: str = 'results',
    num_drones: int = 1,
    duration_sec: int = 0,
    colab: bool = False,
)
```

Public methods:

| Method | Signature | Notes |
| --- | --- | --- |
| `log` | `log(drone: int, timestamp, state, control=np.zeros(12))` | Accepts one 20-value state snapshot and one 12-value control target. |
| `save` | `save()` | Writes `save-flight-<timestamp>.npy` containing `timestamps`, `states`, and `controls` via `np.savez`. |
| `save_as_csv` | `save_as_csv(comment='')` | Writes one CSV directory with per-signal files. |
| `plot` | `plot(pwm=False)` | Uses `matplotlib`; may require a display/backend unless running in a configured notebook path. |

Important storage details:

- `states` is shaped `(num_drones, 16, T)`, not `(num_drones, 20, T)`, because it stores reordered position, velocity, RPY, angular velocity, and RPMs from the 20-value input state.
- `controls` is shaped `(num_drones, 12, T)`.
- If `duration_sec=0`, arrays grow dynamically as `log(...)` is called. If preallocating, pass an integer duration long enough for the run.

## Utility API

```python
sync(i, start_time, timestep)
```

`sync(...)` sleeps only when the loop is ahead of the desired wall-clock schedule. Use it for GUI demonstrations; skip it for headless smoke checks.

```python
str2bool(val)
```

Converts common string values such as `true`, `false`, `1`, and `0` into booleans for argparse-style CLIs.

## Source workflow signatures mirrored by the bundled runner

The package examples expose `run(...)` functions with these argument families. The bundled runner maps these to CLI flags and uses short headless defaults.

| Workflow | Run arguments |
| --- | --- |
| PID | `drone`, `num_drones`, `physics`, `gui`, `record_video`, `plot`, `user_debug_gui`, `obstacles`, `simulation_freq_hz`, `control_freq_hz`, `duration_sec`, `output_folder`, `colab` |
| Velocity | `drone`, `gui`, `record_video`, `plot`, `user_debug_gui`, `obstacles`, `simulation_freq_hz`, `control_freq_hz`, `duration_sec`, `output_folder`, `colab` |
| Downwash | `drone`, `gui`, `record_video`, `simulation_freq_hz`, `control_freq_hz`, `duration_sec`, `output_folder`, `plot`, `colab` |
| MRAC | `drone`, `num_drones`, `physics`, `gui`, `record_video`, `plot`, `user_debug_gui`, `obstacles`, `simulation_freq_hz`, `control_freq_hz`, `duration_sec`, `output_folder`, `colab` |

Prefer the bundled runner for operations; use these signatures only to understand parity with package workflows or to write package-version-specific custom code.
