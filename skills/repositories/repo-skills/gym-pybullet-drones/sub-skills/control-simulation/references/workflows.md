# Control Simulation Workflows

This reference distills the package's control examples into self-contained operating recipes. Use the bundled [`../scripts/run_control_example.py`](../scripts/run_control_example.py) runner instead of reopening or executing the original checkout example scripts.

Baseline verified facts for this skill: package version `2.2.0`, Python `3.12.13`, Gymnasium env IDs `ctrl-aviary-v0` and `velocity-aviary-v0`, and headless-capable `CtrlAviary`/`VelocityAviary` constructors matching `BaseAviary`.

## Smoke-first runner usage

The runner wraps PID tracking, velocity control, downwash, and MRAC with safer defaults than the source examples:

- `gui=False`, `plot=False`, `record_video=False`
- short `--duration-sec 1.0`
- validation of `simulation_freq_hz % control_freq_hz`
- output-folder parent creation before `Logger` is initialized
- compact `Logger.save()` output by default, optional source-like CSV export with `--csv`

Typical commands:

```bash
# PID helix/trajectory tracking with CtrlAviary + DSLPIDControl
python scripts/run_control_example.py pid --duration-sec 1 --output-folder /tmp/gpd-control/pid

# Velocity commands with VelocityAviary's internal PID bridge
python scripts/run_control_example.py pid_velocity --duration-sec 1 --output-folder /tmp/gpd-control/velocity

# Two-drone downwash physics using Physics.PYB_DW
python scripts/run_control_example.py downwash --duration-sec 1 --output-folder /tmp/gpd-control/downwash

# MRAC hover/control with CtrlAviary + MRACControl
python scripts/run_control_example.py mrac --duration-sec 1 --output-folder /tmp/gpd-control/mrac

# Run all four wrappers, each in its own subfolder
python scripts/run_control_example.py all --duration-sec 0.5 --output-folder /tmp/gpd-control/all
```

Add `--csv` when you need per-signal CSV files. Add `--plot` only when `matplotlib` can open a window or a compatible backend is configured. Add `--gui` only on a host with a display/OpenGL context.

## PID trajectory tracking

Use PID tracking when the task is "run the PID example", "track a target position trajectory", or "understand `DSLPIDControl`".

Core components:

- `CtrlAviary`: environment where `step(action)` consumes per-drone motor RPMs shaped `(num_drones, 4)`.
- `DSLPIDControl`: computes RPMs from a 20-value drone state, target position, target RPY, optional target velocity, and optional target RPY rates.
- `Logger`: records the observation state and target trajectory for later analysis.

The wrapped PID workflow mirrors the package example: three Crazyflie drones start around a small circle, each tracks a circular XY trajectory at its initial altitude, and the control loop applies the RPMs computed at the previous step. The source defaults are longer and GUI/plot oriented; the bundled runner keeps it headless and short unless you opt in.

Minimal custom-loop shape:

```python
obs, info = env.reset()
action = np.zeros((num_drones, 4))
for i in range(steps):
    obs, reward, terminated, truncated, info = env.step(action)
    for j in range(num_drones):
        action[j], pos_error, yaw_error = ctrl[j].computeControlFromState(
            control_timestep=env.CTRL_TIMESTEP,
            state=obs[j],
            target_pos=target_xyz[j],
            target_rpy=target_rpy[j],
        )
        logger.log(j, i / env.CTRL_FREQ, obs[j], control_target[j])
```

Use `DroneModel.CF2X` or `DroneModel.CF2P` with `DSLPIDControl`. Do not use `DroneModel.RACE` with PID tracking unless you have replaced the controller.

## Velocity control

Use velocity control when the task is "use velocity control", "send velocity commands", or "understand `VelocityAviary`".

`VelocityAviary` keeps the same `BaseAviary` constructor shape but changes the action contract. Each action row is:

```text
[vx_direction, vy_direction, vz_direction, speed_fraction]
```

The first three values define a direction vector; the fourth value is the fraction of `SPEED_LIMIT` to command after `abs(...)`. Internally, the environment uses one `DSLPIDControl` per drone to convert target velocity into motor RPMs while keeping the current yaw.

The wrapped velocity workflow mirrors the package example's four drones and alternating velocity commands. It is the right smoke target for the Gymnasium env ID `velocity-aviary-v0` or direct `VelocityAviary(...)` construction.

Guardrails:

- Keep the action shape `(num_drones, 4)` even though it is not RPMs.
- Use `DroneModel.CF2X` or `DroneModel.CF2P`; the integrated PID bridge is not initialized for `RACE` in the current package.
- A zero direction vector results in zero target velocity, regardless of `speed_fraction`.

## Downwash physics

Use downwash when the task is "understand downwash physics", "run the downwash example", or "compare PyBullet physics variants".

The package exposes downwash through `Physics.PYB_DW` and the combined `Physics.PYB_GND_DRAG_DW`. In `BaseAviary.step(...)`, the downwash model is applied after base rotor forces for each drone when the selected physics mode includes downwash.

Model behavior distilled from `BaseAviary._downwash(...)`:

- For each drone, check every other drone.
- If another drone is above it (`delta_z > 0`) and within 10 m horizontally, apply a negative Z force to the lower drone.
- The force magnitude uses URDF parameters `dw_coeff_1`, `dw_coeff_2`, `dw_coeff_3`, and `prop_radius` with an exponential radial falloff.

The wrapped downwash workflow uses two drones moving along opposite X-Z trajectories with `CtrlAviary`, `Physics.PYB_DW`, and `DSLPIDControl`. Keep `num_drones=2` for the bundled workflow; write a custom loop for larger swarms.

## MRAC control

Use MRAC when the task is "run MRAC", "inspect adaptive control", or "hover with `MRACControl`".

Core components:

- `CtrlAviary`: still receives motor RPM actions.
- `MRACControl`: computes RPMs, position error, and RPY error from the 20-value state and 12-value target signal.
- `control` and `scipy` dependencies: used by `MRACControl` to place poles and solve the Lyapunov equation.

The wrapped MRAC workflow mirrors the package example's single-drone hover target at `z=1`, but can also create simple multi-drone hover targets when `--num-drones` is set. The default MRAC control frequency is `120 Hz`; keep `simulation_freq_hz` divisible by `control_freq_hz`.

Current package model support is `DroneModel.CF2X`, `DroneModel.CF2P`, and `DroneModel.RACE`. Unknown model strings are rejected by the runner before construction.

## Logger and output inspection

The bundled runner always creates the output folder and calls `Logger.save()` unless it exits during validation or environment construction. Expected outputs:

- `save-flight-<timestamp>.npy`: compact NumPy `.npz` payload written by `Logger.save()` containing `timestamps`, `states`, and `controls` arrays.
- `save-flight-<tag>-<timestamp>/...csv`: optional CSV directory when `--csv` is passed.

Important shape facts:

- `Logger.log(...)` accepts `state` with length 20 and `control` with length 12.
- Internally, `states` has shape `(num_drones, 16, T)` because it stores reordered position, velocity, RPY, angular velocity, and four RPM values.
- `controls` has shape `(num_drones, 12, T)` and should contain target position, target velocity or RPY, and remaining target fields as zeros when unused.

To inspect a saved compact log:

```python
import numpy as np
with np.load('/tmp/gpd-control/pid/save-flight-...npy') as data:
    print(data['timestamps'].shape, data['states'].shape, data['controls'].shape)
```

## GUI, headless, and timing choices

- Use headless `--no-gui` (the default) for CI, servers, containers, and smoke checks. PyBullet connects with `p.DIRECT` through `BaseAviary`.
- Use `--gui` only when the host has a display/OpenGL context. When GUI is enabled, `sync(i, start_time, env.CTRL_TIMESTEP)` slows the loop toward wall-clock speed.
- `BaseAviary.render()` is text-only when `gui=False`; use `--render-every N` to sample textual state summaries without flooding logs.
- Keep `simulation_freq_hz` a multiple of `control_freq_hz`; the constructor raises otherwise, and the runner rejects it early with a clear message.

## Native coverage anchors

The wrapped PID, velocity, and downwash smoke flows correspond to the package's own control example tests. MRAC is not part of those tests but is a useful additional headless smoke target because it exercises `MRACControl`, `control`, and `scipy` dependencies.
