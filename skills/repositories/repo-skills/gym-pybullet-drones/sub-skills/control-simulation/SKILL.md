---
name: control-simulation
description: "Operate gym-pybullet-drones headless or GUI control-simulation
  workflows for PID tracking, velocity control, downwash, and MRAC."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Control Simulation

Use this sub-skill when a task asks how to run, modify, or debug classic control simulations in `gym-pybullet-drones`: PID trajectory tracking, velocity-command control, downwash physics, MRAC hover/control, logger output, or PyBullet GUI/headless behavior.

## Route here for

- Running the bundled control example runner for `pid`, `pid_velocity`, `downwash`, or `mrac` with short headless smoke defaults.
- Building custom loops with `BaseAviary`, `CtrlAviary`, `VelocityAviary`, `BaseControl`, `DSLPIDControl`, `MRACControl`, or `CTBRControl`.
- Choosing `DroneModel` and `Physics` values for control examples, including downwash-specific physics.
- Inspecting `Logger` outputs, `sync(...)` behavior, PyBullet client/drone IDs, action shapes, and frequency constraints.
- Troubleshooting `pybullet`, display/OpenGL, logger, action-shape, MRAC model, or timing-mismatch failures in control simulations.

## Do not handle here

- Reinforcement-learning training, PPO playback, `learn.py`, `play.py`, `BaseRLAviary`, `HoverAviary`, or `MultiHoverAviary`; route back to the repo skill or the RL sub-skill when available.
- Betaflight SITL, `BetaAviary`, external Betaflight checkout/builds, UDP port setup, or `beta.py`; route back to the repo skill or the SITL sub-skill when available.
- Broad package installation policy beyond the control-specific `pybullet`/GUI/logger symptoms in this sub-skill.

## Start here

1. Read [workflows](references/workflows.md) to choose the bundled runner mode and understand how each source control workflow was wrapped.
2. Use [API reference](references/api-reference.md) for constructor signatures, action/observation shapes, controller signatures, enum values, logger arrays, and installed-package facts.
3. Use [troubleshooting](references/troubleshooting.md) before changing physics, controller code, or dependency versions.
4. Prefer the bundled runner over the original repository example scripts:

```bash
python scripts/run_control_example.py pid --duration-sec 1 --output-folder /tmp/gpd-pid
python scripts/run_control_example.py pid_velocity --duration-sec 1 --output-folder /tmp/gpd-vel
python scripts/run_control_example.py downwash --duration-sec 1 --output-folder /tmp/gpd-dw
python scripts/run_control_example.py mrac --duration-sec 1 --output-folder /tmp/gpd-mrac
```

The runner defaults to `gui=False`, `plot=False`, `record_video=False`, and short durations so it is safe for headless smoke checks. Add `--gui`, `--plot`, `--record-video`, `--csv`, or longer `--duration-sec` only after the environment supports them.

## Runtime guardrails

- `CtrlAviary` and `VelocityAviary` share the `BaseAviary` constructor shape and can run headless with `gui=False`.
- `BaseAviary` requires `pyb_freq % ctrl_freq == 0`; the bundled runner validates this before constructing the environment.
- `CtrlAviary.step(action)` expects motor RPM actions shaped `(num_drones, 4)`; `VelocityAviary.step(action)` expects velocity commands shaped `(num_drones, 4)` with `[vx, vy, vz, speed_fraction]`.
- `DSLPIDControl` is for `DroneModel.CF2X` or `DroneModel.CF2P`; `MRACControl` supports the current `CF2X`, `CF2P`, and `RACE` drone models.
- `Logger.log(...)` accepts one 20-value state snapshot and one 12-value control target per drone; use its saved arrays or optional CSV export to inspect runs.
