# Workflow Map

This map helps route broad Isaac Lab requests to the right sub-skill and bundled helper.

| User request | Primary owner | Bundled helper | Typical validation |
| --- | --- | --- | --- |
| Launch simulation, choose physics or renderer backends, or reason about `AppLauncher` | `simulation-core` | `sub-skills/simulation-core/scripts/inspect_simulation_api.py` | Inspect signatures and run a tiny config smoke |
| Use robot or sensor configs from `isaaclab_assets` | `assets-and-sensors` | `sub-skills/assets-and-sensors/scripts/list_assets_catalog.py` | Print the catalog and confirm the expected configs are exported |
| List tasks, inspect presets, or parse task configs | `tasks-and-presets` | `sub-skills/tasks-and-presets/scripts/list_task_presets.py` | Show tasks plus preset groups for a known environment |
| Train or play RL agents | `rl-training` | `sub-skills/rl-training/scripts/inspect_rl_dispatch.py` | Build a safe command skeleton and confirm the selector syntax |
| Collect demonstrations or set up teleoperation / XR | `imitation-and-teleop` | `sub-skills/imitation-and-teleop/scripts/inspect_imitation_workflow.py` | Check the phase, device family, and prerequisite hints |
| Work on docs, tests, packaging, changelog fragments, or repo maintenance | `tooling-and-deployment` | `sub-skills/tooling-and-deployment/scripts/inspect_repo_maintenance.py` | Check version metadata and verify the maintenance commands |

## Routing rules

- Start with the root skill for installation, wrapper commands, and broad orientation.
- Move to a focused sub-skill as soon as the user request names a concrete workflow.
- Use the bundled helper scripts when you need a safe command skeleton or a fast import summary.
- Prefer the narrowest sub-skill that can answer the request without reopening the original checkout.
