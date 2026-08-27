# Package Overview

## Purpose

Read this when you need a compact map of `gym-pybullet-drones` package entry points, registered Gymnasium IDs, shared enums, dependencies, and cross-workflow conventions before choosing a sub-skill.

## Package baseline

| Fact | Value / operating note |
| --- | --- |
| Distribution | `gym-pybullet-drones` |
| Baseline version | `2.2.0` |
| Import root | `gym_pybullet_drones` |
| Python support evidence | project metadata targets Python `^3.12`; CI uses Python `3.12` |
| License | MIT |
| Console-script CLI | none in current package metadata |
| Required workflow backend | CPU / generic Python runtime; GUI and Torch CUDA are optional host capabilities, not required skill gates |

Runtime dependencies are declared in package metadata and include `pybullet`, `gymnasium`, `stable-baselines3`, `torch`, `numpy`, `scipy`, `matplotlib`, `pillow`, `transforms3d`, `control`, and `pytest`.

## Package layout

| Import or directory | Role |
| --- | --- |
| `gym_pybullet_drones.__init__` | Registers Gymnasium env IDs when imported. |
| `gym_pybullet_drones.envs` | Environment classes: `BaseAviary`, `CtrlAviary`, `VelocityAviary`, `BaseRLAviary`, `HoverAviary`, `MultiHoverAviary`, `BetaAviary`. |
| `gym_pybullet_drones.control` | Controllers: `BaseControl`, `DSLPIDControl`, `MRACControl`, `CTBRControl`. |
| `gym_pybullet_drones.utils` | `Logger`, enums, `sync`, and argparse boolean parsing. |
| `gym_pybullet_drones.examples` | Source example workflows that this skill wraps with bundled helper scripts. |
| Package `assets` | URDFs, Betaflight trajectory/config assets, and source helper scripts used as construction evidence. |

## Registered Gymnasium environments

Import `gym_pybullet_drones` before calling `gym.spec(...)` or `gym.make(...)`.

| Env ID | Entry point | Skill route |
| --- | --- | --- |
| `ctrl-aviary-v0` | `gym_pybullet_drones.envs:CtrlAviary` | `control-simulation` |
| `velocity-aviary-v0` | `gym_pybullet_drones.envs:VelocityAviary` | `control-simulation` |
| `hover-aviary-v0` | `gym_pybullet_drones.envs:HoverAviary` | `rl-workflows` |
| `multihover-aviary-v0` | `gym_pybullet_drones.envs:MultiHoverAviary` | `rl-workflows` |

Minimal registration check:

```python
import gymnasium as gym
import gym_pybullet_drones
print(gym.spec("hover-aviary-v0").entry_point)
```

Use the root `scripts/check_imports.py` helper when you need this check as an automated command.

## Shared enums

| Enum | Values | Notes |
| --- | --- | --- |
| `DroneModel` | `CF2X="cf2x"`, `CF2P="cf2p"`, `RACE="racer"` | Controllers support different subsets; check the owning sub-skill before changing models. |
| `Physics` | `PYB`, `DYN`, `PYB_GND`, `PYB_DRAG`, `PYB_DW`, `PYB_GND_DRAG_DW` | Downwash workflows require `PYB_DW` or the combined variant. |
| `ObservationType` | `KIN`, `RGB`, `DEP`, `ALL` | RL defaults use `KIN`; vision modes are heavier and image-based. |
| `ActionType` | `RPM`, `PID`, `VEL`, `ONE_D_RPM`, `ONE_D_PID` | RL defaults use `ONE_D_RPM`; control envs generally consume `(num_drones, 4)` rows. |
| `ImageType` | `RGB`, `DEP`, `SEG`, `BW` | Used by internal image export helpers when recording or vision observations are enabled. |

## Shared environment pattern

All Aviary environments follow the Gymnasium `reset`/`step`/`close` shape:

```python
import numpy as np
from gym_pybullet_drones.envs.CtrlAviary import CtrlAviary

env = CtrlAviary(gui=False, record=False)
try:
    obs, info = env.reset(seed=0, options={})
    action = np.zeros((env.NUM_DRONES, 4), dtype=np.float32)
    obs, reward, terminated, truncated, info = env.step(action)
finally:
    env.close()
```

Common constructor guardrails:

- `pyb_freq` must be divisible by `ctrl_freq`.
- `initial_xyzs` and `initial_rpys` must match `(num_drones, 3)` when supplied.
- `gui=True` uses PyBullet's GUI path and needs a display/OpenGL context.
- `record=True` with `gui=False` writes PNG frames; use the bundled `scripts/ffmpeg_png2mp4.sh` helper if MP4 conversion is needed.

## Shared logging pattern

`Logger(logging_freq_hz, output_folder="results", num_drones=1, duration_sec=0, colab=False)` stores simulation traces. `Logger.log(drone, timestamp, state, control=np.zeros(12))` expects a 20-value state vector and a 12-value control target. `Logger.save()` writes a compact NumPy archive; `Logger.save_as_csv(comment)` writes source-like per-signal CSV files.

Use sub-skill helpers for workflow execution because they create output folders, keep smoke durations short, and keep GUI/plotting disabled by default.
