---
name: assets-and-sensors
description: "Use assets-and-sensors for IsaacLab asset catalogs, robot and
  sensor configs, articulation setup, and asset/sensor customization workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Assets and Sensors

Use this sub-skill when the task is about ready-made robot or sensor configs, custom asset definitions, or sensor setup inside Isaac Lab scenes.

## Route here for

- Choosing a preconfigured robot or sensor from `isaaclab_assets`.
- Writing or editing `ArticulationCfg`, `RigidObjectCfg`, or sensor config objects.
- Adding cameras, ray casters, contact sensors, or frame transformers to a robot.
- Understanding actuator models, initial state setup, or asset/sensor data access.
- Inspecting the asset catalog without opening the original checkout.

## Use other subskills for

- Launching the simulation app or choosing the runtime backend: `../simulation-core/SKILL.md`.
- Task registration, preset selectors, or environment discovery: `../tasks-and-presets/SKILL.md`.
- RL train/play or checkpoint handling: `../rl-training/SKILL.md`.

## Working references

- `references/asset-catalog.md`
- `references/robot-and-sensor-configs.md`
- `references/troubleshooting.md`
- `scripts/list_assets_catalog.py`

## Acceptance checks

- Name a valid catalog entry or config family for the requested robot or sensor.
- Explain the key config fields that matter for the requested asset or sensor.
- Use the bundled helper to confirm the exported catalog names when needed.
