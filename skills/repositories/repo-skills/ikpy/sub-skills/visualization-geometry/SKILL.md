---
name: visualization-geometry
description: "Use for IKPy transformation-matrix checks, geometry helpers,
  headless 3D chain plots, target and frame overlays, and URDF tree
  visualization; do not use it to build chains, solve FK/IK, or control
  hardware."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Visualization and geometry

Use this sub-skill when a Researcher needs to inspect IKPy transforms or create a
visual diagnostic of a chain without connecting to a robot. Start with the
matrix and shape rules in [the API reference](references/api-reference.md),
then select a procedure from [the workflows](references/workflows.md). Keep
long-running or repeatable plots headless and save them to an explicit local
output path.

## Route by responsibility

- Route chain construction, link selection, forward kinematics, inverse
  kinematics, and joint-vector semantics to `chain-kinematics`.
- Route URDF/MJCF model loading and parser behavior to `robot-model-import`.
  This sub-skill only explains the `get_urdf_tree` visualization utility after
  a model path and root link are already known.
- Use the bundled `scripts/smoke_plot.py` for a dependency and save-path smoke
  check. It uses an inline toy chain and never reads a robot file or talks to
  hardware.
- Treat rendered images and DOT/PDF output as diagnostic evidence, not as a
  motion command, simulator state, or proof that a physical robot is safe.

## Operating sequence

1. Establish whether the requested result is a numeric transform inspection, a
   Matplotlib image, or a Graphviz tree; they have different optional
   dependencies and failure modes.
2. Check matrix dimensions and the RPY multiplication order before rendering.
   Inspect the numeric frame first, then use a plot to make frame placement or
   target error easier to see.
3. In headless environments, select the Matplotlib `Agg` backend before
   importing `ikpy.utils.plot`; call `Chain.plot(..., show=False)` and save the
   retained figure explicitly.
4. For a URDF tree, provide an existing URDF path and an exact root link name;
   inspect the returned DOT/tree objects before asking Graphviz to render.
5. Record output paths, dependency availability, numerical checks, and any
   clipping or convention assumptions in the downstream experiment log.

See:

- [references/api-reference.md](references/api-reference.md) for public
  functions, return shapes, conventions, and optional dependencies.
- [references/workflows.md](references/workflows.md) for transform checks,
  headless plots, target/intermediate-frame overlays, and DOT rendering.
- [references/troubleshooting.md](references/troubleshooting.md) for import,
  backend, shape, plotting, and safety failures.
