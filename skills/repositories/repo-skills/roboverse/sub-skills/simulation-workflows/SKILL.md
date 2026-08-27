---
name: simulation-workflows
description: "Guides RoboVerse installation, handler selection, scenario
  composition, robot and scene setup, observations, rendering, replay,
  randomization, and safe teleoperation workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Simulation Workflows

Use this route when a request needs a RoboVerse simulation assembled or exercised:
installation and package registration, `ScenarioCfg`, robots, scenes, grounds,
assets, cameras, queries, control, randomization, teleoperation, rendering, or
small trajectory replay. RoboVerse owns reusable content; **MetaSim owns the
scenario/config types, task registry, package discovery, simulator handlers, and
backend implementations**. Keep a core simulator or handler change in MetaSim
rather than duplicating it in RoboVerse.

## Route

1. Read [workflows.md](references/workflows.md) and choose the novice smoke route
   or the expert composition route. Start headless with one environment and one
   backend; do not begin with downloaded USD scenes, a GUI, or parallel rollouts.
2. Run [the bundled environment checker](scripts/check_runtime.py) for the
   selected backend. It performs imports and metadata checks only; it never
   launches a simulator, downloads assets, opens a display, or mutates a scene.
3. Use [api-reference.md](references/api-reference.md) for the exact public
   objects and content roots. Prefer exported config classes and `replace(...)`
   over copying asset files or simulator internals.
4. Apply [troubleshooting.md](references/troubleshooting.md) when an optional
   backend, display, camera, asset, query, randomizer, or teleoperation device
   is unavailable. Separate an import/registration pass from a launched-backend
   pass and report the backend actually exercised.

## Minimum validation

```bash
python scripts/check_runtime.py --backend mujoco
python -c "import metasim, roboverse_pack.robots; print('registration imports ok')"
```

For an actual run, construct the smallest `ScenarioCfg`, call
`get_handler(scenario)`, perform one `get_states(mode="tensor")` or one
`simulate()`/state read, and close the handler in `finally`. A successful import
is not evidence that every simulator is installed or that observations are
numerically equivalent across backends. The prepared evidence covered MetaSim
0.2.0, MuJoCo 3.11.0, Torch 2.13.0+cu130, and an 8-A100 inspection host only;
do not generalize that coverage to Isaac, Genesis, Newton, SAPIEN, PyBullet,
Blender, or MJX.

## Scope guard

Do not automatically invoke asset downloaders, real-asset setup, renderer
launches, display servers, teleoperation devices, or replay-data acquisition.
They are explicit, user-approved follow-up actions. Keep output files in a
user-selected directory and always close handlers/apps after a run.

## Bundled material

- [workflows.md](references/workflows.md): installation, registration,
  ScenarioCfg, control, multi-environment, hybrid, rendering, and expert routes.
- [api-reference.md](references/api-reference.md): component/API tables,
  backend extras, content roots, state conventions, queries, randomization, and
  teleoperation contracts.
- [troubleshooting.md](references/troubleshooting.md): backend, GPU/display,
  asset, camera/query, cleanup, randomization, and teleoperation recovery.
- [scripts/check_runtime.py](scripts/check_runtime.py): deterministic,
  side-effect-free prerequisite and backend probe.
