---
name: gym-pybullet-drones
description: "Use gym-pybullet-drones for PyBullet quadrotor simulation,
  PID/MRAC control examples, Gymnasium PPO hover workflows, and Betaflight SITL
  preflight guidance."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# gym-pybullet-drones

Use this repo skill when a task mentions `gym-pybullet-drones`, PyBullet drone or Crazyflie simulation, Aviary environments, PID/velocity/downwash/MRAC control, Gymnasium hover environments, PPO training/playback, or Betaflight SITL integration.

This skill is self-contained operating guidance for package version `2.2.0`. The original repository examples, tests, and assets were used as evidence, but future agents should use the bundled references and scripts in this skill rather than reopening or executing files from the source checkout.

## Start here

1. Confirm the package is installed in the active Python environment. The repository metadata targets Python `3.12`.
2. Run the bundled import check if installation or Gymnasium registration is uncertain:

   ```bash
   python scripts/check_imports.py
   python scripts/check_imports.py --headless-smoke --env-id hover-aviary-v0
   ```

3. Pick the route below and read the nearest sub-skill before running workflow-specific helpers.
4. Keep `gui=False` / headless mode for automation, CI, containers, or remote servers. Enable GUI, plotting, recording, and full-duration training only after the relevant sub-skill's troubleshooting page says the host can support them.

## Installation and import baseline

For a published install or a local checkout, use a clean Python 3.12 environment and install only the package/runtime dependencies needed for the selected workflow:

```bash
python -m pip install gym-pybullet-drones
# or, for a local checkout you are maintaining:
python -m pip install -e /path/to/gym-pybullet-drones
python -m pip check
```

Minimal package import check:

```python
import gym_pybullet_drones  # registers Gymnasium env IDs
from gym_pybullet_drones.envs import CtrlAviary, VelocityAviary, HoverAviary, MultiHoverAviary
from gym_pybullet_drones.utils.enums import DroneModel, Physics, ObservationType, ActionType
```

The package has no console-script entry points. Use Python imports or the bundled helper scripts below.

## Route map

| Task signal | Read / run |
| --- | --- |
| PID trajectory tracking, `CtrlAviary`, `VelocityAviary`, velocity commands, downwash physics, MRAC, `Logger`, headless control examples | [control-simulation](sub-skills/control-simulation/SKILL.md); helper: `python sub-skills/control-simulation/scripts/run_control_example.py --list` |
| PPO training, short RL smoke tests, `HoverAviary`, `MultiHoverAviary`, `hover-aviary-v0`, `multihover-aviary-v0`, SB3 model save/load/playback | [rl-workflows](sub-skills/rl-workflows/SKILL.md); helper: `python sub-skills/rl-workflows/scripts/run_rl_workflow.py --help` |
| Betaflight SITL, `BetaAviary`, external `betaflight_sitl/bfN` layout, UDP port mapping, `clone_bfs.sh` consequences | [betaflight-sitl](sub-skills/betaflight-sitl/SKILL.md); helper: `python sub-skills/betaflight-sitl/scripts/check_betaflight_layout.py --help` |
| Package layout, registered env IDs, shared enums, dependency/backend notes, logger conventions | [package overview](references/package-overview.md) |
| Install/import, GUI/OpenGL, Gymnasium registration, video conversion, and cross-workflow failures | [troubleshooting](references/troubleshooting.md) |
| Staleness or refresh decision for another checkout | [repo provenance](references/repo-provenance.md) |

## Quick chooser

- If the user says "run the PID example", "velocity control", "downwash", or "MRAC", start with `control-simulation`.
- If the user says "train a hover policy", "play a saved PPO model", or mentions `hover-aviary-v0` / `multihover-aviary-v0`, start with `rl-workflows`.
- If the user says "Betaflight SITL", "BetaAviary", or "check the external drone layout", start with `betaflight-sitl`.
- If the user only needs to know whether the package is installed and registered correctly, run `scripts/check_imports.py` first.

## Operating guardrails

- Required backend for this skill is CPU / generic Python. CUDA is not required for any selected repo-native workflow, even though Torch may use accelerator hardware if the user's environment provides it.
- PyBullet GUI is optional and host-dependent. Prefer `gui=False` for all smoke checks and automated verification.
- `BaseAviary` requires `pyb_freq % ctrl_freq == 0`; use the bundled runners to catch timing mistakes before PyBullet construction.
- Control observations use a 20-value state vector; `Logger.log(...)` expects one 20-value state and one 12-value control vector per drone.
- RL smoke training proves environment/rollout/save/load mechanics, not policy quality. Full PPO training is intentionally not the default.
- Betaflight SITL is an external integration: the package expects prebuilt Betaflight SITL binaries in a local `betaflight_sitl/bfN` layout. The bundled checker is safe; execution wrappers should be run only after those external prerequisites are staged.
- If you need to convert headless PNG recordings into MP4, use the bundled [`scripts/ffmpeg_png2mp4.sh`](scripts/ffmpeg_png2mp4.sh) helper rather than the source repo asset script.
