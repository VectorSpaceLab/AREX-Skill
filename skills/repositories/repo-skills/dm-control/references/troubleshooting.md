# Cross-cutting dm_control troubleshooting

## Import fails after an editable install

Symptom:

```text
ImportError: cannot import name 'constants' from partially initialized module 'dm_control.mujoco.wrapper.mjbindings'
```

Likely cause: `dm_control` was installed in editable mode and generated MuJoCo binding files are missing or stale.

Recovery:

1. Uninstall the editable package.
2. Reinstall non-editably with `python -m pip install dm_control` or a non-editable source/Git install.
3. Import from a directory that is not shadowing the package with a local `dm_control/` source tree.
4. Run `check_dm_control_install.py` to confirm `suite`, `mjcf`, `mujoco`, `composer`, and `manipulation` import from the installed package.

## `suite.load` says the domain or task does not exist

Validate names before loading:

```python
from dm_control import suite
print(suite.TASKS_BY_DOMAIN.keys())
print(suite.TASKS_BY_DOMAIN['cartpole'])
```

Use exact domain/task strings. The Control Suite has separate collections such as `ALL_TASKS`, `BENCHMARKING`, `EASY`, `HARD`, `EXTRA`, and reward-visualization subsets.

For Jaco manipulation environments, use `dm_control.manipulation.ALL` and `dm_control.manipulation.TAGS` instead of `suite.TASKS_BY_DOMAIN`.

## Action shape or range errors

Check `env.action_spec()` and create actions with matching shape, dtype, minimum, and maximum:

```python
action_spec = env.action_spec()
action = action_spec.minimum + 0.5 * (action_spec.maximum - action_spec.minimum)
time_step = env.step(action)
```

For normalized `[-1, 1]` agent outputs, use the suite action-scale wrapper rather than clipping manually unless the task already expects normalized controls.

## Reset or step works, but rendering fails

Treat rendering as a separate optional backend problem:

1. Run a CPU reset/step smoke first.
2. If images are required, select an OpenGL backend explicitly.
3. Use `MUJOCO_GL=egl` for headless hardware rendering when compatible drivers are available.
4. Use `MUJOCO_GL=osmesa` only when OSMesa system libraries are installed.
5. Use `MUJOCO_GL=glfw` only with a display/windowing environment.

Route detailed backend diagnosis to `sub-skills/rendering-viewer-assets/`.

## GLFW warning on a headless machine

Symptom:

```text
GLFWError: (65550) b'X11: The DISPLAY environment variable is missing'
```

This often appears when rendering-aware modules import GLFW on a headless host. It does not necessarily break non-rendering simulation. If the task is CPU-only, run a suite reset/step or PyMJCF compile/step smoke and continue. If the task needs pixels or a viewer, switch to EGL/OSMesa or provide a display.

## OSMesa `NoneType` / `glGetError` errors

Symptom:

```text
AttributeError: 'NoneType' object has no attribute 'glGetError'
```

Likely cause: PyOpenGL cannot load a usable OSMesa/OpenGL library. Install the appropriate system OSMesa/GL package or choose EGL on a compatible GPU host.

## `Physics.render` works on one host but not another

Rendering depends on system drivers and dynamic libraries, not only Python packages. Record the requested backend, `MUJOCO_GL`, `MUJOCO_EGL_DEVICE_ID`, display availability, and whether a tiny render probe succeeds. Keep model XML debugging separate from backend debugging: a model can compile and step correctly while rendering fails.

## PyMJCF schema or attribute errors

Common causes:

- Attribute name typo (`poss` instead of `pos`).
- Wrong value length or type for vector attributes.
- Deleting required attributes.
- Using `class` instead of `dclass` in Python.
- Accessing XML keyword elements such as `<global>` with dot syntax instead of `getattr(model.visual, 'global')`.

Route detailed model debugging to `sub-skills/mjcf-mujoco-models/`.

## Composer custom environment errors

Common causes:

- Subclass overrides `__init__` instead of implementing `_build`.
- `root_entity` does not expose an `mjcf_model`.
- `Task.before_step` does not apply controls matching `action_spec`.
- Observables are disabled or named differently due to fully qualified keys.
- Code keeps a stale `environment.physics` proxy after recompilation or close.

Route lifecycle and observable debugging to `sub-skills/composer-environments/`.

## Manipulation/locomotion task confusion

- Manipulation names ending in `_features` expose low-dimensional observations; names ending in `_vision` involve camera observations and can require rendering.
- Locomotion examples may use packaged assets, HDF5 mocap data, `labmaze`, or longer interactive demos. Smoke imports and one reset/step before attempting long rollouts.
- Soccer and humanoid/rodent examples are Composer-backed task families, not Control Suite benchmark tasks.

Route high-level task-family decisions to `sub-skills/locomotion-manipulation/`.

## Blender exporter risks

The Blender exporter is optional and may require installing an add-on into Blender. Do not run installer scripts or mutate a user's Blender configuration without explicit approval. Prefer documentation-only guidance unless the user provides a Blender runtime and asks for exporter setup.
