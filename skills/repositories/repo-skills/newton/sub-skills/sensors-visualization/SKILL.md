---
name: sensors-visualization
description: "Use Newton sensors, viewer backends, example CLI, recording,
  headless visualization, and debugging routes."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Newton sensors and visualization

Use this sub-skill when a task involves Newton sensors, viewer backends, example CLI/browser usage, headless runs, recording/replay, screenshot/frame capture, visualization troubleshooting, or benchmark/example flags.

## Route here for

- `newton.sensors.SensorContact`, `SensorFrameTransform`, `SensorIMU`, and `SensorTiledCamera`.
- Sensor label matching and extended state/contact attributes.
- `newton.viewer.ViewerNull`, `ViewerFile`, `ViewerUSD`, `ViewerGL`, `ViewerRTX`, `ViewerRerun`, and `ViewerViser`.
- `python -m newton.examples`, `--list`, `--viewer`, `--device`, `--test`, `--num-frames`, `--benchmark`, and `--warp-config`.
- Choosing a headless viewer or persistent artifact output.
- Viewer/logging order, visible worlds, custom overlays, and diagnostic capture.

## Route elsewhere

- Model and state construction details: `../modeling-simulation/SKILL.md`.
- Solver/contact feature selection before visualization: `../solvers-contacts/SKILL.md`.
- URDF/MJCF/USD import and mesh assets: `../asset-import-export/SKILL.md`.
- Robot controllers, IK, target arrays, and actuator/policy dependencies: `../robotics-control/SKILL.md`.

## Read order

1. `references/sensors-viewers-examples.md` for sensor/viewer APIs, example CLI, and headless/persistent output patterns.
2. `references/troubleshooting.md` for missing viewer extras, sensor allocation order, OpenGL/Wayland, Rerun/Viser ports, and CLI errors.
3. `scripts/check_viewer_sensor_apis.py` to inspect public signatures and run a safe `ViewerNull`/example-list diagnostic.

## Default choices

- Use `ViewerNull` for tests, CI, smoke checks, and headless simulations with no visual output.
- Use `ViewerUSD` or `ViewerFile` when the user needs a persistent artifact.
- Use `ViewerGL` only when an OpenGL context is expected; prefer `headless=True` for frame capture.
- Use `ViewerRerun` or `ViewerViser` when a web/timeline workflow is explicitly needed and the optional dependencies/ports are available.
- Use `ViewerRTX` only when RTX/OVRTX dependencies and a suitable NVIDIA GPU are part of the task.

## Safe diagnostic

From this sub-skill directory:

```bash
python scripts/check_viewer_sensor_apis.py --limit 20
```

The script imports public sensor/viewer modules, instantiates `ViewerNull`, and lists installed examples. It does not open a GL window, start servers, download assets, or run a full simulation.
