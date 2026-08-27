# Control Simulation Troubleshooting

Use this reference when a control simulation fails before changing controllers or physics. Prefer the bundled runner's headless smoke defaults while isolating issues:

```bash
python scripts/run_control_example.py pid --duration-sec 0.5 --output-folder /tmp/gpd-smoke/pid
python scripts/run_control_example.py downwash --duration-sec 0.5 --output-folder /tmp/gpd-smoke/dw
```

## `pybullet` install, build, or import failures

Common symptoms:

- `ModuleNotFoundError: No module named 'pybullet'`
- wheel build errors during install
- C/C++ compiler errors while building `pybullet`
- `ImportError` while importing `gym_pybullet_drones.envs` or constructing an aviary

Actions:

1. Confirm the active environment is the one where `gym-pybullet-drones` is installed.
2. Confirm Python compatibility; this skill is based on package `2.2.0` with Python `3.12.x` support.
3. Reinstall in a clean environment if dependency state is mixed:
   ```bash
   python -m pip install --upgrade pip setuptools wheel
   python -m pip install gym-pybullet-drones
   python - <<'PY'
   import pybullet, gym_pybullet_drones
   print('imports ok')
   PY
   ```
4. On Linux source builds, install a compiler/toolchain before reinstalling. On macOS source builds, PyBullet may need platform-specific compiler flags.
5. If `matplotlib` is the missing import, see the logger section below; `Logger` imports `matplotlib.pyplot` even when plotting is disabled.

## GUI, display, and OpenGL failures

Common symptoms:

- PyBullet cannot connect with `p.GUI`.
- `Failed to create an OpenGL context`.
- The process hangs or crashes on a server/container when `gui=True`.
- `BaseAviary.render()` says graphical rendering requires `gui=True`.

Actions:

1. Rerun headless first:
   ```bash
   python scripts/run_control_example.py pid --no-gui --no-plot --duration-sec 1 --output-folder /tmp/gpd-headless
   ```
2. Only use `--gui` on a host with a working X/Wayland display and OpenGL stack.
3. Keep `--plot` off while debugging GUI; plotting uses `matplotlib` and can fail independently of PyBullet.
4. Remember that `render()` is textual in headless mode. Use `--render-every N` for sampled text output instead of enabling GUI solely for state inspection.
5. If recording in headless mode, expect PNG frame directories rather than GUI MP4 output.

## Invalid action shapes

Common symptoms:

- `IndexError` or reshape errors inside `BaseAviary.step(...)`.
- Drones do not move because action rows are all zeros or velocity directions are zero.
- `VelocityAviary` appears to accept RPMs but motion is wrong.

Rules:

- `CtrlAviary.step(action)` expects shape `(num_drones, 4)` where each row is motor RPMs.
- `VelocityAviary.step(action)` also expects shape `(num_drones, 4)`, but each row is `[vx, vy, vz, speed_fraction]`, not RPMs.
- `Logger.log(...)` expects `state` length 20 and `control` length 12.
- `computeControlFromState(...)` expects one 20-value state vector for a single drone, not the full `(num_drones, 20)` observation array.

Minimal shape check:

```python
obs, _ = env.reset()
action = np.zeros((env.NUM_DRONES, 4))
obs, reward, terminated, truncated, info = env.step(action)
rpm, pos_e, yaw_or_rpy_e = ctrl[0].computeControlFromState(
    env.CTRL_TIMESTEP,
    obs[0],
    target_pos=np.array([0.0, 0.0, 1.0]),
)
```

## Drone model and controller mismatches

Common symptoms:

- `DSLPIDControl requires DroneModel.CF2X or DroneModel.CF2P` followed by process exit.
- `VelocityAviary` raises an attribute error because its internal PID controllers were not initialized.
- MRAC setup fails after passing an unknown or incompatible drone string.

Rules:

- Use `cf2x` or `cf2p` for PID, velocity, and downwash workflows that rely on `DSLPIDControl`.
- Current `MRACControl` supports `cf2x`, `cf2p`, and `racer`.
- The bundled runner rejects `racer` for PID/velocity/downwash and rejects unknown drone strings before constructing the environment.

Examples:

```bash
# Valid PID
python scripts/run_control_example.py pid --drone cf2x --duration-sec 1 --output-folder /tmp/gpd-pid

# Valid MRAC with racer model
python scripts/run_control_example.py mrac --drone racer --duration-sec 1 --output-folder /tmp/gpd-mrac-racer
```

## `ctrl_freq` / `pyb_freq` mismatch

Common symptoms:

- `ValueError: pyb_freq is not divisible by env_freq` from `BaseAviary.__init__()`.
- Control loop timing does not match expected simulation steps.

Rules:

- `pyb_freq` is the low-level PyBullet stepping frequency.
- `ctrl_freq` is the environment/control step frequency.
- `pyb_freq % ctrl_freq` must be zero because `BaseAviary` computes an integer `PYB_STEPS_PER_CTRL`.

Use compatible pairs such as:

| `simulation_freq_hz` | `control_freq_hz` | Notes |
| --- | --- | --- |
| `240` | `48` | Source PID, velocity, and downwash default. |
| `240` | `120` | Source MRAC default. |
| `240` | `240` | One PyBullet step per control step. |

The bundled runner validates this early:

```bash
python scripts/run_control_example.py mrac --simulation-freq-hz 240 --control-freq-hz 50
# exits with a clear divisibility message before constructing PyBullet
```

## Missing `matplotlib`, plotting, or logger output-folder failures

Common symptoms:

- `ModuleNotFoundError: No module named 'matplotlib'` while importing `Logger`.
- Plot window hangs or fails on a headless host.
- `FileNotFoundError` or output directory errors from custom logger paths.
- No CSV files are created even though the compact log exists.

Actions:

1. The package `Logger` imports `matplotlib.pyplot`; install `matplotlib` even if you only save logs.
2. Keep runner default `--no-plot` for smoke checks. Use `--plot` only with a display or configured backend.
3. The bundled runner creates `--output-folder` parents before `Logger` starts. If writing custom code, call `os.makedirs(output_folder, exist_ok=True)` first.
4. Compact logs are saved by default as `save-flight-<timestamp>.npy` containing a NumPy zip payload. Pass `--csv` for source-like CSV directories.
5. If no logs appear, check whether the process exited during validation or environment construction before `logger.save()` ran.

## Excessive runtime or noisy output

The source examples use GUI/plot-friendly defaults and can run for 5-15 seconds while printing state every step. On shared or CI hosts, use the bundled short defaults first:

```bash
python scripts/run_control_example.py all --duration-sec 0.25 --output-folder /tmp/gpd-control-smoke
```

Then increase duration selectively:

```bash
python scripts/run_control_example.py downwash --duration-sec 3 --csv --output-folder /tmp/gpd-downwash-debug
```

To inspect state without flooding logs:

```bash
python scripts/run_control_example.py pid --duration-sec 2 --render-every 24 --output-folder /tmp/gpd-pid-render
```

## Downwash-specific surprises

- Downwash requires `Physics.PYB_DW` or `Physics.PYB_GND_DRAG_DW`; plain `Physics.PYB` does not apply the model.
- The modeled force affects a lower drone only when another drone is above it and horizontally within 10 m.
- Very short smoke runs prove construction/logging, not a physically meaningful downwash comparison. Use longer runs and inspect `z` trajectories when analyzing the effect.

## MRAC-specific failures

Common symptoms:

- Import errors involving `control` or `scipy`.
- A timing mismatch at `120 Hz` control frequency.
- Numerical instability after large timestep changes or aggressive target changes.

Actions:

1. Confirm dependencies import:
   ```bash
   python - <<'PY'
   import control, scipy
   from gym_pybullet_drones.control.MRACControl import MRACControl
   print('mrac deps ok')
   PY
   ```
2. Keep the default MRAC pair `simulation_freq_hz=240`, `control_freq_hz=120` for smoke checks.
3. Start with the bundled hover target before adding aggressive trajectories.
4. Use `cf2x`, `cf2p`, or `racer`; reject unknown strings at the CLI before blaming MRAC internals.

## When to route elsewhere

- PPO training/playback, policy checkpoints, `stable-baselines3`, or `torch` training duration: route to the RL workflow owner.
- Betaflight SITL layout, external Betaflight builds, UDP ports, or `gnome-terminal`: route to the SITL workflow owner.
