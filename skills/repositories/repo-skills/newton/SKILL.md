---
name: newton
description: "Use Newton physics engine APIs for robotics simulation, solvers,
  contacts, asset import/export, sensors, viewers, examples, and repository
  maintenance."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Newton repo skill

Use this skill when a task involves Newton, `newton-physics`, the Python `newton` package, Warp-backed physics simulation, robotics/contact/deformable solver workflows, URDF/MJCF/USD import, Newton examples, or Newton repository maintenance.

## Start here

1. Confirm install/backend state with `scripts/check_newton_env.py`.
2. For a tiny public simulation check, run `scripts/newton_smoke.py --device cpu --steps 2`.
3. Route to the focused sub-skill below.
4. If the user is editing Newton source, also read `references/development-maintenance.md`.
5. If behavior depends on version-sensitive details, read `references/repo-provenance.md`.

## Installation and backends

Read `references/install-and-backends.md` before installing optional extras or diagnosing CUDA/RTX/Torch/USD/MuJoCo issues. Base Newton requires `warp-lang`; optional workflows use extras such as `newton[sim]`, `newton[importers]`, `newton[examples]`, `newton[onnx]`, `newton[rtx]`, `newton[torch-cu12]`, `newton[torch-cu13]`, and `newton[notebook]`.

Use CPU for first smoke checks unless the user specifically asks for CUDA, RTX, or Torch behavior. A CPU pass does not prove GPU performance.

## Sub-skill routing

| Task | Read |
| --- | --- |
| Build a model, add bodies/shapes/joints, allocate states/controls/contacts, replicate worlds, or write a minimal simulation loop | `sub-skills/modeling-simulation/SKILL.md` |
| Choose/configure solvers, CollisionPipeline, MuJoCo contacts, SDF/hydroelastic contacts, contact material tuning, or deterministic/GPU solver behavior | `sub-skills/solvers-contacts/SKILL.md` |
| Import URDF/MJCF/USD assets, diagnose optional importer deps, schema resolvers, mesh/remesh/heightfield utilities, or USD/File export artifacts | `sub-skills/asset-import-export/SKILL.md` |
| Use actuators, controllers, IK, `ArticulationView`, robot target layouts, sites for robotics control, or ONNX/Torch policy dependencies | `sub-skills/robotics-control/SKILL.md` |
| Use sensors, viewer backends, recording/replay, example CLI/browser, `--viewer`, `--device`, `--test`, headless visualization, or benchmark flags | `sub-skills/sensors-visualization/SKILL.md` |
| Diagnose cross-cutting install/import/backend or skill-staleness issues | `references/troubleshooting.md`, `references/repo-provenance.md` |
| Edit Newton source, tests, docs, examples, public API, or changelog | `references/development-maintenance.md` |

## Safe public commands

From this generated skill directory:

```bash
python scripts/check_newton_env.py --show-optional
python scripts/newton_smoke.py --device cpu --steps 2
python scripts/list_newton_examples.py --limit 20
```

Against an installed Newton environment, common package commands are:

```bash
python -m newton.examples --list
python -m newton.examples basic_pendulum --viewer null --device cpu --test
```

Use the user's Python environment for these commands. Do not assume this generated skill's construction environment is available.

## Operating rules

- Use public imports: `import newton`, `import warp as wp`, and public submodules such as `newton.solvers`, `newton.sensors`, `newton.viewer`, `newton.utils`, `newton.ik`, and `newton.actuators`.
- Do not import from `newton._src` in user-facing code, docs, examples, or generated answers.
- Set `newton.use_coord_layout_targets = True` before constructing new robotics models that write position targets.
- Treat MuJoCo, USD/importers, RTX, ONNX, Torch, notebooks, and viewer stacks as optional extras; check dependencies before running examples.
- Prefer tiny CPU smokes before long examples, GPU runs, downloads, or visualization.
- Never hide network, credential, external-service, or broad dependency installation behind a helper script.

## Staleness and provenance

`references/repo-provenance.md` records the source commit, package version, evidence paths, and verification summary used to create this skill. Refresh this skill when Newton's public APIs, docs, examples, dependency extras, or solver/importer behavior change.
