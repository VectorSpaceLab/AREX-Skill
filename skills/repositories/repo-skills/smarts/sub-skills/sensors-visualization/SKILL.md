---
name: sensors-visualization
description: "Configure SMARTS sensor observations, optional Panda3D rendering,
  Envision recording and replay, and safe diagnostics without conflating CPU
  checks with graphics services."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# SMARTS sensors and visualization

Use this route when an agent needs additional SMARTS observations, camera/grid
outputs, custom shader renders, Envision state streaming or replay, or a
read-only check of rendering and replay prerequisites. Keep the simulation
lifecycle and environment creation in `simulation-environments`; use
`cli-integrations` for exact `scl` command syntax. Frontend npm development,
raw media, and long-running servers are outside this route.

## Decide which boundary you are testing

1. Start with a CPU/non-rendered interface when the policy only needs state,
   waypoints, lidar, lane positions, accelerometer, signals, or nearby actors.
2. Treat `drivable_area_grid_map`, `occupancy_grid_map`, `top_down_rgb`, and
   `custom_renders` as software-rendering features. They require the camera
   extra and a usable Panda3D/OpenGL offscreen or X11 display.
3. An `occlusion_map` also requires an occupancy map with identical width and
   height. It is a rendered output, not a CPU-only visibility calculation.
4. Envision is a separate client/server/browser path. A successful SMARTS
   import or Panda3D import does not prove that the server is listening.

Read the linked references before building an interface:

- [sensor-reference.md](references/sensor-reference.md) — configuration
  dataclasses, sensor semantics, and observation contracts.
- [rendering-and-cameras.md](references/rendering-and-cameras.md) — camera
  extras, offscreen rendering, custom shaders, and performance boundaries.
- [envision-and-replay.md](references/envision-and-replay.md) — client/server,
  JSONL recording, replay, and Visdom limits.
- [data-formats.md](references/data-formats.md) — shapes, metadata, and stable
  serialization expectations.
- [troubleshooting.md](references/troubleshooting.md) — failures by install,
  configuration, API misuse, renderer, and service workflow.

## Configure the interface

Use `AgentInterface` with explicit dataclass values when a non-default shape,
range, or lookahead matters. Boolean `True` resolves to the corresponding
config dataclass; `False` disables the sensor. The interface defaults
accelerometer and lane positions on, but leaves most expensive or optional
sensors off. `AgentInterface.from_type(AgentType.Full, ...)` is convenient but
also enables rendered observations and lidar; do not use it as a cheap smoke
interface.

```python
from smarts.core.agent_interface import (
    AgentInterface, Waypoints, NeighborhoodVehicles, RGB, OGM,
)

interface = AgentInterface(
    waypoint_paths=Waypoints(lookahead=32),
    neighborhood_vehicle_states=NeighborhoodVehicles(radius=50),
    top_down_rgb=RGB(width=128, height=128, resolution=100 / 128),
    occupancy_grid_map=OGM(width=128, height=128, resolution=100 / 128),
    action=...,  # select an action type in the environment route
)
```

Before stepping, inspect the environment's per-agent observation space and
confirm that the policy reads only enabled fields. After a step, check `None`
for disabled optional fields and preserve the named observation structures;
do not assume every observation is a flat NumPy array.

## Workflow and checks

- For CPU checks, import `AgentInterface`, construct low-dimensional sensor
  configs, and run a bounded environment test through the sibling lifecycle
  route. This does not require Panda3D.
- For camera checks, run
  [`scripts/check_rendering.py`](scripts/check_rendering.py), preferably under
  `xvfb-run -a`. Use `--probe-offscreen` only for a bounded construction and
  teardown probe; it is not a renderer behavior test.
- For Envision records, use
  [`scripts/inspect_replay_records.py`](scripts/inspect_replay_records.py) on a
  file or directory. It never sends data, starts a server, or modifies files.
- Keep image dimensions and resolution small while diagnosing. Image sensors
  can dominate `step()` time and memory.
- For recording or replay, verify the server endpoint separately and inspect
  the generated JSONL before attempting playback. Use the CLI sibling route
  for command spelling; this skill documents the Python client contract only.

## Verified limits

The prepared SMARTS 2.0.1 environment passed package imports, live interface
and lidar signature inspection, and a Panda3D/SMARTS renderer import smoke
under Xvfb. That is evidence for importability only. Full renderer behavior,
large image observations, Visdom, and a live Envision server remain optional
or unverified. The bundled helpers report these limits rather than claiming a
successful renderer or visualization session.
