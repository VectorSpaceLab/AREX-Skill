---
name: extension-and-control
description: "This skill guides users through IR-SIM registry extensions,
  external state ownership, and keyboard or Matplotlib control integration."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Extension and control

Use this route when a task involves a custom individual or group behavior,
kinematics or map-generator registration, an external state owner, keyboard or
mouse input, or a controller boundary such as a CBF/QP wrapper. Keep ordinary
YAML scene authoring in [scene-configuration](../scene-configuration/SKILL.md),
the simulation lifecycle in
[simulation-environments](../simulation-environments/SKILL.md), sensor/map
consumption in [sensing-and-mapping](../sensing-and-mapping/SKILL.md), and
built-in behavior or planner selection in
[navigation-and-planning](../navigation-and-planning/SKILL.md).

## Start safely

1. Install the base distribution and verify the import before adding optional
   input or solver packages:

   ```bash
   python -m pip install ir-sim
   python -c "import irsim; print(irsim.__version__)"
   ```

2. Decide who owns state. Use normal `internal` stepping for IR-SIM kinematics,
   behaviors, or an action supplied to `env.step(action)`. Use `external`
   stepping when another simulator/controller supplies every object's state and
   velocity; follow [the external sequence](references/external-control.md).
3. Load custom behavior modules explicitly with
   `env.load_behavior("module_name")` after the module is importable on
   `sys.path`. The loader reinitializes registered individual and group class
   handlers; it does not make a file importable by filename alone.
4. Run the bundled, headless registration check from the sub-skill directory:

   ```bash
   python scripts/custom_behavior_smoke.py
   ```

   It uses process-local registries and in-memory fixtures; it does not open a
   GUI or require `pynput`, `pyrvo`, or a QP solver. Check its parser without
   running it with `python scripts/custom_behavior_smoke.py --help`.

## Choose the extension contract

- Per-object, group, stateful, or map/kinematics registration: read
  [custom behaviors and registries](references/custom-behaviors.md).
- Caller-supplied states, velocity ownership, refresh ordering, or CBF/QP
  integration boundaries: read [external control](references/external-control.md).
- Interactive keyboard, MPL fallback, mouse zoom/clicks, and headless limits:
  read [GUI control](references/gui-control.md).
- Import, duplicate-key, dimension, stale-cache, and backend recovery: read
  [troubleshooting](references/troubleshooting.md).

## Non-negotiable checks

- Registry keys are exact `(kinematics, name)` pairs. Register the behavior for
  the kinematics used by the YAML object and return an action with that
  kinematics' action dimension; a behavior name alone is not portable.
- Do not register over a built-in or previously imported custom key. The
  behavior decorators reject duplicate keys with `ValueError`; kinematics
  registration also rejects a different class under the same normalized key.
  Use an isolated process or unique test names for experiments.
- A custom map generator must be imported before the YAML map is built. Its
  non-empty `name`, `yaml_param_names`, constructor, and `_build_grid()` define
  the YAML-facing contract; the framework injects grid `width` and `height`
  and computes them from `resolution`.
- In external mode, update state **and** velocity, then call `env.step()` with
  no action. Do not mix `env.step(action=...)` with external state ownership.
  Use `env.refresh()` when a direct state mutation must be observable before a
  step; never mutate private state fields as a shortcut.
- Treat live keyboard input, OS global hooks, and external CBF/QP solvers as
  integration surfaces. Validate their mocked/headless paths first and report
  optional or unverified dependencies rather than claiming a live test.

The helper and references are self-contained runtime material. The source
checkout, usage scripts, native tests, and private inspection environment are
evidence only and are not runtime dependencies.
