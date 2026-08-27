---
name: mjcf-mujoco-models
description: "Build, parse, compose, export, compile, step, inspect, and
  optionally render MJCF/MuJoCo models with dm_control."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# MJCF and MuJoCo Models

Use this sub-skill when a task is about raw MJCF/PyMJCF models or `dm_control.mujoco.Physics`: building XML object models, parsing model files or strings, composing attached models, exporting assets, compiling a `Physics`, stepping/resetting state, named data/model inspection, action specs, or a small render probe.

## Route before working

- Stay here for `dm_control.mjcf.RootElement`, `Element.add/find/find_all`, parser/export helpers, `mjcf.Physics.from_mjcf_model`, `mujoco.Physics.from_xml_string/from_xml_path`, `physics.named`, `reset_context`, `mujoco.action_spec`, and `physics.render` API usage.
- Route custom Composer `Entity`, `Task`, observable, and variation abstractions to [composer-environments](../composer-environments/SKILL.md).
- Route Control Suite benchmark loading, wrappers, and rollout loops to [suite-rl-workflows](../suite-rl-workflows/SKILL.md).
- Route operational OpenGL, viewer, pixel-observation, EGL/OSMesa/GLFW, and Blender-exporter troubleshooting to [rendering-viewer-assets](../rendering-viewer-assets/SKILL.md).

## Installation and runtime guardrails

Install the public package with:

```bash
pip install dm_control
```

For unreleased source installs use:

```bash
pip install git+https://github.com/google-deepmind/dm_control.git
```

Editable installs are not supported; do not rely on a source checkout, local paths, notebooks, or repository tests at runtime. Rendering is optional: CPU model construction, compile, reset, and stepping should work without an OpenGL backend, while `physics.render` depends on a configured MuJoCo GL backend.

## Read or run these bundled files

- Read [references/pymjcf-reference.md](references/pymjcf-reference.md) when creating, parsing, modifying, attaching, namespacing, validating, or exporting MJCF/PyMJCF models.
- Read [references/mujoco-physics-reference.md](references/mujoco-physics-reference.md) when compiling models into `Physics`, stepping/resetting simulations, using named data/model access, deriving action specs, rendering, or wrapping a custom `dm_env` environment.
- Read [references/troubleshooting.md](references/troubleshooting.md) when schema/attribute validation, duplicate names, invalid references, assets, compile failures, render backend selection, or simulation divergence blocks progress.
- Run [scripts/mjcf_smoke_model.py](scripts/mjcf_smoke_model.py) to verify an installed `dm_control` can build a tiny PyMJCF model, compile `mjcf.Physics`, step it, optionally render, and optionally write the generated XML.

## Default operating sequence

1. Choose the level: PyMJCF object model for programmatic construction/composition; raw `mujoco.Physics` constructors for existing XML or MJB models.
2. Build or parse the model; use `dclass` for XML `class`, `getattr(model.visual, 'global')` for keyword child names, and direct `mjcf.Element` references for reference attributes.
3. If composing models, attach a fresh or copied child model, keep the returned attachment frame if joints/inertials are needed, and validate namespaced identifiers after attachment.
4. Compile with `mjcf.Physics.from_mjcf_model(model)` or `mujoco.Physics.from_xml_string(xml, assets=model.get_assets())` before claiming the model is valid.
5. Inspect and control through `physics.named`, `physics.bind(element)` for PyMJCF elements, `reset_context`, `set_control`, `step`, and `mujoco.action_spec`.
6. Treat rendering as an optional probe. If rendering fails but non-rendering compile/step succeeds, preserve the model result and route backend diagnosis to the rendering sibling skill.
