---
name: simulation-core
description: "Use simulation-core for Isaac Lab AppLauncher, SimulationCfg,
  backend selection, visualizer modes, and core simulation startup workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Simulation Core

Use this sub-skill when the task is about launching Isaac Lab simulation, selecting physics or renderer backends, configuring headless or streamed runs, or reasoning about `AppLauncher`, `SimulationCfg`, `PhysicsCfg`, `RendererCfg`, and `SettingsManager`.

## Route here for

- Launching an app with `AppLauncher` or a simulation-aware Python entrypoint.
- Choosing `PhysxCfg`, `NewtonCfg`, or `OvPhysxCfg` for the active physics backend.
- Setting `--device`, `--visualizer`, `--enable_cameras`, `--livestream`, or `--experience`.
- Understanding how `SimulationCfg` and visualizer config objects interact.
- Debugging Kit-vs-kitless compatibility and launcher environment variables.
- Inspecting the core simulation API without opening the original checkout.

## Use other subskills for

- Ready-made robots, sensor catalogs, or custom asset configs: `../assets-and-sensors/SKILL.md`.
- Task registration, preset selection, or environment listing: `../tasks-and-presets/SKILL.md`.
- RL train/play or checkpoint handling: `../rl-training/SKILL.md`.

## Working references

- `references/api-reference.md`
- `references/workflows.md`
- `references/troubleshooting.md`
- `scripts/inspect_simulation_api.py`

## Acceptance checks

- Explain which backend or visualizer combination is valid for the requested run.
- Use the bundled helper or a tiny config smoke to confirm the API shape.
- Keep launcher advice aligned with the current `./isaaclab.sh --help` contract and the bundled reference.
