---
name: dm-control
description: "Use DeepMind dm_control for MuJoCo simulation, Control Suite
  environments, PyMJCF models, Composer tasks, rendering, and high-level
  locomotion/manipulation workflows."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# dm-control

Use this repo skill when a task involves Google's `dm_control` package: DeepMind Control Suite environments, MuJoCo simulation through `dm_control.mujoco`, PyMJCF model construction, Composer custom tasks, locomotion/manipulation task families, pixel observations, viewer launchers, or rendering backend troubleshooting.

## First checks

- Install public releases with `pip install dm_control`; install unreleased source with `pip install git+https://github.com/google-deepmind/dm_control.git`.
- Do **not** use editable installs for normal use. `dm_control` generates legacy MuJoCo bindings during installation, and editable installs can leave `dm_control.mujoco.wrapper.mjbindings` partially initialized.
- Run [scripts/check_dm_control_install.py](scripts/check_dm_control_install.py) for an installed-package smoke check that imports core modules, loads one Control Suite task, builds a tiny PyMJCF model, and optionally probes rendering.
- Run [scripts/list_dm_control_tasks.py](scripts/list_dm_control_tasks.py) to list installed Control Suite and manipulation task registries before choosing names.
- Read [references/installation-and-backends.md](references/installation-and-backends.md) when a task needs installation, MuJoCo/OpenGL backend selection, optional rendering, or Blender exporter constraints.
- Read [references/package-overview.md](references/package-overview.md) for the component map, API entry points, and how the sub-skills fit together.
- Read [references/troubleshooting.md](references/troubleshooting.md) for cross-cutting install/import, task selection, backend, and package-data failures.

## Route by task

| User task | Read next |
|---|---|
| Load a Control Suite benchmark, step an environment, inspect action/observation specs, use wrappers, or create a random rollout | [suite-rl-workflows](sub-skills/suite-rl-workflows/SKILL.md) |
| Build, parse, compose, export, compile, step, or inspect a MuJoCo/MJCF model with PyMJCF or `dm_control.mujoco.Physics` | [mjcf-mujoco-models](sub-skills/mjcf-mujoco-models/SKILL.md) |
| Create a custom Composer `Entity`, `Task`, observable, variation, arena, robot, or `composer.Environment` | [composer-environments](sub-skills/composer-environments/SKILL.md) |
| Use high-level locomotion, soccer, walker, mocap, prop, or manipulation task families | [locomotion-manipulation](sub-skills/locomotion-manipulation/SKILL.md) |
| Render frames, use pixel observations, launch the viewer, choose `MUJOCO_GL`, diagnose headless OpenGL, or reason about the Blender exporter | [rendering-viewer-assets](sub-skills/rendering-viewer-assets/SKILL.md) |

## Operating defaults

1. Prefer installed-package imports over source-tree assumptions. The public distribution name and import package are both `dm_control`.
2. Start from CPU/non-rendering simulation unless the user explicitly needs images, camera observations, a viewer, EGL, OSMesa, GLFW, or Blender export.
3. Validate task names from registries before loading them: `suite.TASKS_BY_DOMAIN`, `suite.ALL_TASKS`, `manipulation.ALL`, and `manipulation.TAGS`.
4. For RL loops, use `dm_env.TimeStep` semantics: reset first, sample actions within `action_spec()`, step until `time_step.last()`, and inspect `reward`, `discount`, and observation keys.
5. For custom environments, decide whether the request is a ready-made task selection problem (`suite` / manipulation / locomotion) or a model/task-construction problem (`mjcf` / Composer).
6. Keep rendering failures separate from simulation failures. A Control Suite task can reset/step correctly even when GLFW warns that `DISPLAY` is missing; only pixel/render/viewer tasks require backend fixes.
7. When using cameras or pixel wrappers on headless Linux, try `MUJOCO_GL=egl` first when a compatible NVIDIA/EGL stack is available; use OSMesa only when system OSMesa libraries are installed; use GLFW only with a display.
8. Treat `dm_control.blender.mujoco_exporter` as optional and system-mutating: it requires Blender, and add-on installation should be an explicit user choice.

## Minimal smoke snippets

```python
from dm_control import suite
import numpy as np

env = suite.load('cartpole', 'balance')
time_step = env.reset()
action_spec = env.action_spec()
action = np.zeros(action_spec.shape, dtype=action_spec.dtype)
time_step = env.step(action)
print(time_step.reward, time_step.discount, time_step.observation.keys())
```

```python
from dm_control import mjcf

model = mjcf.RootElement(model='smoke')
model.worldbody.add('geom', name='floor', type='plane', size=[1, 1, 0.1])
physics = mjcf.Physics.from_mjcf_model(model)
physics.step()
print(physics.model.nbody, physics.data.time)
```

## Verification notes

- Safe native verification should prefer small CPU cases first: Control Suite registry/loading, PyMJCF model compilation, MuJoCo named access/math, Composer environment reset/step, and manipulation registry tasks.
- Rendering native checks are backend-specific. Use the bundled render probe before asserting pixel observations or viewer behavior.
- Long locomotion, mocap, soccer, GUI, Blender, benchmark-scale, or data-download workflows should be treated as optional or documentation-backed unless the user provides runtime budget and dependencies.
