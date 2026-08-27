# Locomotion and manipulation troubleshooting

## Unknown manipulation environment name

Symptoms:

- `ValueError`, `KeyError`, or registry lookup failure from `manipulation.load(name)`.
- User provides a name like `reach_site`, `lift_box`, or a suite-style `(domain, task)` pair.

Fix:

```python
from dm_control import manipulation
print(manipulation.ALL)
```

Use an exact name from `manipulation.ALL`, such as `reach_site_features` or `reach_site_vision`. Generic suite `(domain_name, task_name)` loading belongs in `../suite-rl-workflows/SKILL.md`, not this manipulation registry.

## Unknown tag

Symptoms:

- Empty or failing result from `get_environments_by_tag`.
- User asks for a tag other than `features`, `vision`, or `easy`.

Fix:

```python
from dm_control import manipulation
print(manipulation.TAGS)
```

Only call `get_environments_by_tag(tag)` after checking `tag in manipulation.TAGS`. The verified tags are `features`, `vision`, and `easy`.

## Feature/vision confusion

Symptoms:

- A policy expects object coordinates but a `*_vision` task lacks direct prop-pose observations.
- A headless host fails when a `*_vision` task tries to produce camera observations.
- Observation keys differ from expected hand-written code.

Fix:

- Use `*_features` for low-dimensional proprioception, force/torque/touch, and prop-pose features.
- Use `*_vision` for camera observations; direct prop-pose features are disabled in these variants.
- Always inspect `env.observation_spec()` after loading; never hard-code observation keys across feature/vision variants.
- Route MuJoCo/OpenGL, `MUJOCO_GL`, EGL, OSMesa, GLFW, and viewer issues to `../rendering-viewer-assets/SKILL.md`.

## Missing h5py for mocap/reference-pose tasks

Symptoms:

- `ImportError` mentioning `h5py not found` from HDF5 trajectory loading.
- Reference-pose tracking or CMU mocap data code fails before environment construction.

Fix:

Install the public package and HDF5 dependency before using mocap HDF5 loaders:

```bash
pip install dm_control
pip install h5py
```

Mocap/reference-pose workflows can also require large CMU HDF5 data; confirm network and storage budget before triggering a download.

## Missing labmaze or installed assets

Symptoms:

- Maze/corridor example imports fail with `ModuleNotFoundError: labmaze`.
- Environment construction cannot find packaged meshes, textures, XML, or HDF5 files.

Fix:

- Reinstall from a non-editable public package source: `pip install dm_control`.
- For unreleased source installs, use `pip install git+https://github.com/google-deepmind/dm_control.git`.
- Editable installs are not supported for normal use; they can miss generated MuJoCo bindings or package data.
- Do not copy large assets into a skill or project; rely on the installed package resources.

## Expensive demos or accidental downloads

Symptoms:

- A locomotion task takes much longer than suite/manipulation smoke tests.
- CMU tracking tries to download hundreds of megabytes of data.
- Interactive explorer code opens a viewer or blocks in a GUI loop.

Fix:

- Prefer import/spec probes and one-step rollouts before long experiments.
- Avoid mocap tracking constructors until data, network, and runtime budget are explicitly approved.
- Avoid viewer launchers in automated checks; route visualization to the rendering/viewer sub-skill.
- For soccer, start with `WalkerType.BOXHEAD`, small `team_size`, and short `time_limit` before trying humanoid soccer.

## Rendering failures for vision tasks

Symptoms:

- GLFW warning about a missing display.
- EGL/OSMesa initialization errors.
- Camera observations or `physics.render` fail, while non-rendering reset/step works.

Fix:

- Treat CPU simulation as separate from rendering; a non-rendering `*_features` task may still be healthy.
- Choose and verify a rendering backend before using camera observations.
- Headless EGL can work when proper drivers are available; OSMesa and GLFW are optional and may fail on headless hosts.
- Route backend probes and viewer-specific fixes to `../rendering-viewer-assets/SKILL.md`.

## Source tree or editable-install shadowing

Symptoms:

- Import errors about missing `dm_control.mujoco.wrapper.mjbindings` modules such as `constants`.
- Imports work from one directory but fail from an unbuilt source checkout.

Fix:

- Run scripts from a normal project directory where the installed package is imported, not an unbuilt source tree.
- Reinstall non-editably with `pip install dm_control` or `pip install git+https://github.com/google-deepmind/dm_control.git`.
- Do not rely on `pip install -e .` for `dm_control`.
