# Installation and backend guide

## Install commands

Preferred public release install:

```bash
python -m pip install dm_control
```

Unreleased upstream install:

```bash
python -m pip install git+https://github.com/google-deepmind/dm_control.git
```

Do not use `pip install -e` for normal dm_control usage. The package generates legacy MuJoCo binding files during installation; editable installs can produce import errors such as partially initialized `dm_control.mujoco.wrapper.mjbindings` modules.

## Minimum import smoke

```bash
python - <<'PY'
from importlib.metadata import version
from dm_control import suite, mjcf, mujoco, composer, manipulation
print('dm_control', version('dm_control'))
print('suite tasks', len(suite.ALL_TASKS))
print('manipulation tasks', len(manipulation.ALL))
print('mjcf RootElement', mjcf.RootElement)
print('mujoco Physics', mujoco.Physics)
print('composer Environment', composer.Environment)
PY
```

If this fails before any rendering call, fix installation or dependency resolution before debugging environment code.

## Core dependencies

The package metadata requires runtime packages including `absl-py`, `dm-env`, `dm-tree`, `glfw`, `labmaze`, `lxml`, `mujoco >= 3.11.0`, `numpy`, `protobuf`, `pyopengl`, `pyparsing`, `requests`, `scipy`, `setuptools`, and `tqdm`. Some locomotion/mocap workflows and native tests use `h5py`; test workflows use `pytest`, `mock`, and `pillow`.

Avoid installing every development dependency unless the task is explicitly about repository maintenance or broad native test execution.

## Backend model

`dm_control` has two distinct backend concerns:

1. **MuJoCo simulation**: CPU simulation is enough for loading most environments, compiling models, stepping physics, querying specs, and running non-rendering tests.
2. **OpenGL rendering**: images, cameras, pixel observations, and the GUI viewer require an OpenGL backend.

Rendering backend choice is controlled by `MUJOCO_GL`:

| Backend | When to use | Requirements | Common failure |
|---|---|---|---|
| unset/default | quick local trials | dm_control tries GLFW, then EGL, then OSMesa | default may pick GLFW and warn/fail on headless hosts |
| `glfw` | interactive viewer on a workstation | windowing display plus GLFW/GLEW libraries | `DISPLAY` missing or context not initialized |
| `egl` | headless hardware rendering | EGL-capable GPU driver; optional `MUJOCO_EGL_DEVICE_ID` | driver/device mismatch or missing EGL platform support |
| `osmesa` | software rendering without GPU | system OSMesa/GL libraries visible to PyOpenGL | `NoneType`/`glGetError` or missing GL library |

Example headless probe with the bundled root helper:

```bash
python scripts/check_dm_control_install.py --render --backend egl
```

For deeper backend diagnostics, use the rendering sub-skill's [render backend probe](../sub-skills/rendering-viewer-assets/scripts/render_backend_probe.py).

## Suggested validation order

1. Verify installation and package metadata.
2. Import `suite`, `mjcf`, `mujoco`, `composer`, and `manipulation`.
3. Load and reset one CPU suite task such as `cartpole/balance`.
4. Build and compile one tiny PyMJCF model.
5. Only if images/viewer are required, run a rendering backend probe.
6. Only if using manipulation/locomotion, list task registries and smoke one small feature task.
7. Only if using Blender exporter, confirm the user accepts Blender add-on installation or use documentation-only guidance.

## Backend caveats for future agents

- A GLFW warning during import on a headless host does not prove simulation is broken. Confirm with a CPU reset/step smoke before changing package installs.
- Pixel observations and `visualize_reward=True` may compile/step successfully but fail when the first frame is rendered.
- `MUJOCO_EGL_DEVICE_ID` selects an EGL device for headless hardware rendering; it is not a CUDA device selector for an RL algorithm.
- OSMesa support usually depends on system libraries, not just Python wheels.
- The viewer is intentionally interactive. Do not launch it in non-interactive automation unless the user explicitly requests a GUI run.
- The Blender exporter is not part of the minimum dm_control environment. It depends on Blender's Python/runtime and can mutate a user add-on installation.
