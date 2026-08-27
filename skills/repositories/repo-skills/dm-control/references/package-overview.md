# dm_control package overview

`dm_control` is a Python package for MuJoCo-based physics simulation and reinforcement-learning environments. It combines ready-made task collections with lower-level model and environment-construction APIs.

## Public component map

| Component | Main entry points | Use it for | Route |
|---|---|---|---|
| Control Suite | `dm_control.suite.load`, `suite.build_environment`, `suite.ALL_TASKS`, `suite.BENCHMARKING`, `suite.TASKS_BY_DOMAIN` | benchmark-style single-agent continuous-control tasks with `dm_env` reset/step loops | `sub-skills/suite-rl-workflows/` |
| RL control interface | `dm_control.rl.control.Environment`, `Task`, `Physics`, `flatten_observation` | implementing or reasoning about the `dm_env.Environment` loop used by suite tasks | `sub-skills/suite-rl-workflows/` or `sub-skills/mjcf-mujoco-models/` |
| MuJoCo bindings wrapper | `dm_control.mujoco.Physics`, `mujoco.action_spec`, `Physics.render`, `physics.named` | compiling XML strings/files, stepping simulation, named model/data access, rendering frames | `sub-skills/mjcf-mujoco-models/` |
| PyMJCF | `dm_control.mjcf.RootElement`, `from_path`, `from_xml_string`, `export_with_assets`, `mjcf.Physics.from_mjcf_model` | programmatic MJCF creation, parsing, composition, asset export, and compilation | `sub-skills/mjcf-mujoco-models/` |
| Composer | `dm_control.composer.Entity`, `Task`, `Environment`, `Observables`, `@composer.observable`, variation helpers | building custom environments from entities, arenas, observables, hooks, and randomized task logic | `sub-skills/composer-environments/` |
| Manipulation | `dm_control.manipulation.ALL`, `TAGS`, `get_environments_by_tag`, `load` | built-in Jaco/prop manipulation environments with feature or vision observations | `sub-skills/locomotion-manipulation/` |
| Locomotion | locomotion examples, walkers, arenas, tasks, soccer, mocap/reference-pose modules | advanced Composer-backed locomotion and multi-agent task families | `sub-skills/locomotion-manipulation/` |
| Rendering/viewer | `Physics.render`, `viewer.launch`, `_render` backends, suite pixel wrapper, `MUJOCO_GL` | offscreen images, pixel observations, GUI viewer, backend selection, camera APIs | `sub-skills/rendering-viewer-assets/` |
| Blender exporter | `dm_control.blender.mujoco_exporter` package | optional MuJoCo asset export from Blender | `sub-skills/rendering-viewer-assets/` |

## Common task-routing examples

- "Load `cartpole/swingup` and step random actions" -> `suite-rl-workflows`.
- "Why does `suite.load('foo','bar')` fail?" -> `suite-rl-workflows` troubleshooting and task registry checks.
- "Build a MuJoCo XML model in Python and compile it" -> `mjcf-mujoco-models`.
- "Attach two MJCF models and keep names unique" -> `mjcf-mujoco-models` PyMJCF reference.
- "Create a custom task with observables and randomized initial state" -> `composer-environments`.
- "Use a Jaco reaching task with feature observations" -> `locomotion-manipulation` manipulation reference.
- "Render pixels on a headless server" -> `rendering-viewer-assets` backend probe and troubleshooting.
- "Launch a viewer with a policy" -> `rendering-viewer-assets` viewer template; only launch when GUI availability is explicit.

## Workflow boundaries

- `suite` and `manipulation` loaders return ready-made `dm_env`-style environments. Use them when the user wants an existing task.
- PyMJCF and `dm_control.mujoco` are lower-level model/simulation APIs. Use them when the user asks about XML, assets, named indexing, compilation, stepping, or frame rendering.
- Composer is the abstraction layer for custom environments. Use it when the user needs new entities, task hooks, observables, randomization, or composition.
- Locomotion/soccer/manipulation are higher-level task families built on Composer. Use them for selecting or adapting existing task families; route to Composer only when the user needs new task/entity code.
- Rendering spans several layers. `Physics.render` can render any compiled model, pixel wrappers add images to observations, and `viewer.launch` opens a GUI. Backend validation belongs with `rendering-viewer-assets`.

## Verified package facts to rely on

- Distribution/import package: `dm_control`.
- Version baseline for this skill: `1.0.44`.
- Python requirement: `>=3.9` from package metadata.
- The installed package exposes 51 Control Suite tasks and 25 manipulation tasks at the skill baseline.
- CPU MuJoCo simulation is sufficient for core suite reset/step and PyMJCF compile/step workflows.
- Rendering is optional but backend-sensitive; EGL worked in the construction environment, while OSMesa and GLFW were unavailable there for system/display reasons.

## When not to use this skill

- Use a generic RL algorithm or training-framework skill when the user asks to implement PPO/SAC/DDPG training itself and only uses dm_control as an environment source.
- Use a MuJoCo-only skill, if available, when the user works directly with the standalone `mujoco` package and not dm_control's suite, PyMJCF, Composer, or wrappers.
- Use repository-maintenance guidance when the task is to modify dm_control source, regenerate bindings, change packaging, or contribute tests; this runtime skill is for operating the package as a user.
