---
name: asset-import-export
description: "Use Newton URDF, MJCF, USD, schema resolver, mesh, remesh,
  heightfield, and asset import/export workflows safely."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Newton asset import and export

Use this sub-skill when a task involves loading assets into Newton, converting URDF/MJCF/USD models, diagnosing optional importer dependencies, handling mesh quality/remeshing, using schema resolvers, or preparing scene artifacts for USD/File viewers.

## Route here for

- `ModelBuilder.add_urdf()`, `add_mjcf()`, and `add_usd()` arguments and workflow choices.
- Optional extras for importers, MuJoCo/MJCF, USD schemas, mesh processing, and remeshing.
- USD schema resolver behavior, custom attributes, deformable imports, and returned deformable maps.
- Visual-vs-collider parsing, fixed-joint collapse, self-collision flags, asset path resolvers, and mesh hull limits.
- `newton.utils` mesh validation, solidification, remeshing, heightfield, and texture utilities.
- Export-style artifacts through `ViewerUSD` or file-based viewer routes, before switching to sensor/viewer details.

## Route elsewhere

- Building primitive scenes from scratch: use `../modeling-simulation/SKILL.md`.
- Choosing a solver/contact path for an imported model: use `../solvers-contacts/SKILL.md` after import succeeds.
- Robot controllers, IK, target arrays, and policies: use `../robotics-control/SKILL.md`.
- Live viewers, example CLI, screenshots, Rerun/Viser/RTX details: use `../sensors-visualization/SKILL.md`.

## Read order

1. `references/import-export-workflows.md` for URDF/MJCF/USD decision paths and public signatures.
2. `references/mesh-and-usd-reference.md` for mesh utilities, USD schema resolver notes, and deformable limitations.
3. `references/troubleshooting.md` for optional dependency, path, mesh, and parser failures.
4. `scripts/check_import_extras.py` to check importer/remesh optional modules without loading assets.

## Dependency rule

Base `pip install newton` is enough for primitive model construction and many public APIs. Asset workflows often need extras:

- `newton[sim]` for MuJoCo/MJCF and `SolverMuJoCo` support.
- `newton[importers]` for USD, mesh processing, URI resolution, and schema packages.
- `newton[remesh]` for remeshing utilities.
- `newton[examples]` when running built-in examples that combine importers, viewers, and policy dependencies.

Install the smallest extra that matches the requested format; do not install all extras just to inspect a simple primitive scene.

## Safe diagnostic

From this sub-skill directory:

```bash
python scripts/check_import_extras.py
```

The script reports optional modules and the likely Newton extra that provides each one. It performs no downloads and does not open asset files.
