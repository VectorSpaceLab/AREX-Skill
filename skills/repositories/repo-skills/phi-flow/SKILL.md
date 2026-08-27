---
name: phi-flow
description: "Routes PhiFlow simulation, geometry, optimization, and
  visualization workflows through focused sub-skills."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# PhiFlow

PhiFlow is a differentiable simulation toolkit for physics, geometry, fields,
scene I/O, visualization, and gradient-based optimization.

Use this root skill as a router, not as a manual. Start with the sub-skill that
matches the user's task, and only read deeper references when the task needs the
verified API details, safe scripts, or troubleshooting notes.

## Start here

- If the user needs to install, import, or inspect backends, use
  [`sub-skills/installation-and-backends/SKILL.md`](sub-skills/installation-and-backends/SKILL.md).
- If the task is about grids, fields, geometries, meshes, scenes, or data I/O,
  use [`sub-skills/core-data-and-geometry/SKILL.md`](sub-skills/core-data-and-geometry/SKILL.md).
- If the task is about advection, diffusion, incompressible flow, waves, FLIP,
  SPH, or other direct PDE steps, use
  [`sub-skills/physics-and-simulation/SKILL.md`](sub-skills/physics-and-simulation/SKILL.md).
- If the task is about gradients, Jacobians, solves, inverse problems, or
  optimization through simulation, use
  [`sub-skills/optimization-and-learning/SKILL.md`](sub-skills/optimization-and-learning/SKILL.md).
- If the task is about plotting, interactive display, controls, or scalar logs,
  use [`sub-skills/visualization-and-ui/SKILL.md`](sub-skills/visualization-and-ui/SKILL.md).

## Install and smoke check

For a local PhiFlow checkout, install the package in that environment with:

```bash
python -m pip install -e .
```

Then run the bundled smoke helper from this skill tree:

```bash
python scripts/check_install.py --show-backends
```

If you only need the published package, `pip install phiflow` is the distribution
name and `phi` is the import name.

`phi.verify()` is the canonical package smoke check. It confirms the minimal
runtime setup and reports the Dash/Plotly status used by the web interface.

## What this root skill covers

PhiFlow's public surface is split across a few distinct workflows:

- `phi.field` and `phi.geom` for grid, field, geometry, mesh, SDF, and scene
  handling.
- `phi.physics` for advection, diffusion, incompressible projection, waves,
  FLIP/PIC coupling, and SPH helpers.
- `phi.math` and the backend integrations for gradients, Jacobians, solves,
  and JIT-compiled differentiable workflows.
- `phi.vis` for plotting, display, scalar log loading, and runtime controls.

## Common entry points

- `from phi.flow import *` for the common simulation/geometry names.
- `from phi.physics import advect, diffuse, fluid, wave, sph` for direct PDE
  work.
- `import phi.vis as vis` for plotting and UI workflows.
- `from phi.field import Scene` for scene-backed data round-trips.

## Read this before staleness checks

If the current checkout looks different from the version this skill was built
from, read [`references/repo-provenance.md`](references/repo-provenance.md)
before reusing the skill or refreshing it.

## Runtime files

- [`references/repo-provenance.md`](references/repo-provenance.md) - source
  snapshot and refresh baseline.
- [`references/repo-routing-metadata.json`](references/repo-routing-metadata.json)
  - router metadata for the live skill registry.
- [`references/troubleshooting.md`](references/troubleshooting.md) - cross-cutting
  install, backend, and stale-doc failures.
- [`scripts/check_install.py`](scripts/check_install.py) - safe import and
  runtime smoke check.
