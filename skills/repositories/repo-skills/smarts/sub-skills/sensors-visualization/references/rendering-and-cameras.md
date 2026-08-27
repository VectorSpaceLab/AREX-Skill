# Panda3D rendering and camera reference

Rendering is an optional backend. A CPU import, a non-rendered environment,
and a valid `AgentInterface` do not establish that a Panda3D camera can create
images. Keep two checks separate:

- **CPU/non-rendered:** state sensors, lidar configuration, observation types,
  and environment lifecycle can run without the camera extra.
- **software/OpenGL/X11:** grid maps, RGB, occlusion, custom shaders, and
  renderer tests need `camera-obs` dependencies and a usable Panda3D display
  backend. On headless Linux, use a compatible Xvfb invocation or an available
  offscreen backend.

## Install and probe

Install only the package variant needed by the project, for example the
`camera-obs` extra. Its relevant dependencies are Panda3D and the glTF loader.
Do not install packages from a runtime helper or assume CUDA is required.
Run `scripts/check_rendering.py` from the active environment. Its normal mode
checks importability and display hints; `--probe-offscreen` creates and tears
down a bounded SMARTS renderer object. Run it under `xvfb-run -a` when the host
requires X11. A pass means imports or construction worked, not that a map was
loaded, a frame rendered, or a sensor observation had the right pixels.

For the verified inspection baseline, Panda3D 1.10.16 and SMARTS 2.0.1
imported under Xvfb. Full renderer tests were deliberately deferred; never
report them as passed from the import helper.

## Camera configurations

All camera configs describe pixels and world coverage:

```python
from smarts.core.agent_interface import (
    DrivableAreaGridMap, OGM, RGB, OcclusionMap,
)
area = DrivableAreaGridMap(width=64, height=64, resolution=100 / 64)
ogm = OGM(width=64, height=64, resolution=100 / 64)
rgb = RGB(width=64, height=64, resolution=100 / 64)
occlusion = OcclusionMap(width=64, height=64, resolution=100 / 64)
```

The output array dimensions are `(height, width, 1)` for the two grid maps and
`(height, width, 3)` for RGB and custom renders. `OcclusionMap` is represented
as a one-channel visibility array. Each output includes `GridMapMetadata` with
resolution, width, height, camera position, and camera heading. SMARTS flips
rendered images vertically when copying the Panda3D buffer into the
observation. Keep camera sizes small while diagnosing because each image adds
copy and rendering cost to every step.

`occlusion_map` depends on OGM and requires equal width and height; it can add a
surface-noise shader pass. The configuration itself is validated eagerly, so a
missing OGM or dimension mismatch is an interface error, not a runtime display
failure.

## Custom render pipeline

`CustomRender` names a fragment-shader pass and declares a tuple of unique
render dependencies. Supported dependency classes are:

- `CustomRenderVariableDependency(value, variable_name)` for a scalar or a
  short vector passed as a shader uniform;
- `CustomRenderBufferDependency(buffer_dependency_name, variable_name,
  target_actor=...)` for observation/event buffers;
- `CustomRenderCameraDependency(camera_dependency_name, variable_name,
  target_actor=...)` for an existing camera texture and its resolution.

A camera dependency makes both the sampler and a matching
`<variable_name>Resolution` available to the shader. Built-in camera ids
include occupancy, top-down RGB, drivable-area, and occlusion. A custom pass
may also consume a previous named pass. Dependency variable names must be
unique within a pass, and camera dependencies must refer to an attached
sensor when they name a built-in camera. A custom shader file is user input:
check it exists and is readable before constructing the interface; do not copy
or assume a source-checkout shader path.

The internal buffer catalog covers simulation time/step counters, events, ego
state, neighborhood state, waypoint and road-waypoint fields, via points,
lidar rays/points/hits, and signal state. Buffer values are only supplied when
the corresponding observation exists; shader code must tolerate absent data.

## Failure and performance discipline

- If a policy does not use image data, disable all image sensors; SMARTS warns
  in its public guidance that these may significantly slow `step()`.
- Use one small camera first, then add OGM/occlusion/custom passes one at a
  time. A renderer crash after adding a pass is usually a shader dependency,
  display backend, or incompatible input issue.
- Destroy the environment/renderer in `finally` or a context-managed wrapper;
  Panda3D uses process-global display state and resources.
- Do not run full renderer or image-heavy native tests as an import check.
  Candidate renderer tests are valid only after display/software backend
  availability is independently established.
- A remote browser visualization and a local Panda3D camera are different
  paths: one can fail while the other imports successfully.
