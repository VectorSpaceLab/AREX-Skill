---
name: model-loading
description: "Load, inspect, validate, and lightly simulate Menagerie MJCF XMLs
  with MuJoCo, mujoco.viewer, and robot_descriptions when available."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Model Loading

Use this sub-skill when the task is to open an existing Menagerie XML, resolve
its asset/include dependencies, compile it with MuJoCo, run a short
deterministic smoke step, or compare loader/runtime behavior without editing the
XML itself.

## Route here for

- Directly loading a specific `scene.xml`, `scene_position.xml`, `scene_mjx.xml`,
  `<model>.xml`, or `*_mjx.xml` file.
- Loading a Menagerie model via `robot_descriptions` when the package is
  installed.
- Checking a scene for missing mesh/include errors after files were moved.
- Running a short no-warning compile/step smoke test.
- Checking that expected bodies or actuators exist in the compiled model.

## Do not handle here

- Choosing which Menagerie XML to load or listing model families: route to
  [model-catalog](../model-catalog/).
- Changing XMLs, attaching parts, composing models, or generating variants:
  route to [model-editing](../model-editing/).
- Repo-wide formatting, licensing, gallery, or maintainer checks: route to
  [contribution-maintenance](../contribution-maintenance/).

## Start here

1. Read [references/loading-workflows.md](references/loading-workflows.md) for
   copyable load, viewer, robot_descriptions, and smoke-step recipes.
2. Read [references/api-reference.md](references/api-reference.md) for the
   exact MuJoCo calls, body/actuator lookup helpers, and warning checks used
   here.
3. Use [scripts/smoke_load_model.py](scripts/smoke_load_model.py) to compile,
   assert names/counts, and optionally short-step an XML with deterministic safe
   controls.
4. Read [references/troubleshooting.md](references/troubleshooting.md) when a
   mesh, include, warning, or viewer/runtime error appears.

## Operating rules

1. Prefer `mujoco.MjModel.from_xml_path(...)` for a concrete XML path. Use an
   absolute path when invoking from an arbitrary working directory.
2. Keep the XML and its sibling asset tree together. Relative `include` and
   `mesh` paths are resolved from the XML location, so moving only the XML
   commonly causes missing-mesh or missing-include failures.
3. Use `robot_descriptions` only when the model is published there and the
   package is installed. If the package name is unknown or unavailable, fall
   back to the XML path.
4. Use `python -m mujoco.viewer --mjcf <path>` only in a GUI/OpenGL-capable
   session. On headless hosts, use the smoke script first.
5. For smoke validation, mirror the repo test behavior: compile the XML, step
   briefly with deterministic Halton control noise, and fail if MuJoCo warnings
   remain.
6. If you need to discover models or filenames, leave this sub-skill and route
   to the catalog sub-skill instead of guessing.
