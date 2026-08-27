---
name: extension-patterns
description: "Add and inspect Habitat-Lab registry extensions for tasks,
  sensors, measures, actions, datasets, simulators, and baselines components."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Habitat-Lab Extension Patterns

Use this sub-skill when you need to add, inspect, debug, or review custom Habitat-Lab extension classes that are discovered through `habitat.registry` or `baseline_registry`. It covers registration and config alignment; it does not run environments or train agents.

## Fast Route

- For exact decorator/getter names, ownership boundaries, and config-name alignment, read [references/registry-api.md](references/registry-api.md).
- For recipes for sensors, measures, actions, tasks, datasets, simulators, policies, trainers, storage, updaters, and observation transforms, read [references/extension-patterns.md](references/extension-patterns.md).
- For failure diagnosis around missing keys, duplicate registrations, action spaces, measure dependencies, and transform shapes, read [references/troubleshooting.md](references/troubleshooting.md).
- To safely inspect currently importable registry keys without creating a simulator or `Env`, run `scripts/inspect_registry_extensions.py` from a checkout or installed environment.

## Working Rules

1. Define the extension class in an importable Python module and decorate it with the matching registry decorator.
2. Ensure the module is imported before config construction or before a factory calls `registry.get_*` or `baseline_registry.get_*`.
3. Align every config `type` value with the registry key, not necessarily with the config dictionary key or emitted observation/action UUID.
4. Keep runtime tests narrow: registry lookup, config-node creation, observation/action space compatibility, and shape contracts can be checked without full simulator assets.
5. Escalate full `Env` execution, dataset loading, and training/evaluation to the task/env and baselines sub-skills.

## Common Extension Flow

1. Pick the registry surface: `habitat.registry` for lab runtime components, `baseline_registry` for training/inference components.
2. Pick a stable registry key with `@...register_*(name="...")` when the public config name should differ from the class name.
3. Create or update the matching structured config class so its `type` field equals that registry key.
4. Add the config node under the correct collection, such as `habitat.task.lab_sensors`, `habitat.task.measurements`, `habitat.task.actions`, `habitat.dataset`, `habitat.simulator`, `habitat_baselines.trainer_name`, `habitat_baselines.rl.policy.name`, or `habitat_baselines.rl.agent.type`.
5. Import the module containing the decorator before the lookup site runs.
6. Probe with registry lookups and shape/space checks before attempting asset-backed execution.

## Safe Probe

From this sub-skill directory, run the bundled probe to list registered keys:

```bash
python scripts/inspect_registry_extensions.py --all
```

Useful narrow probes:

```bash
python scripts/inspect_registry_extensions.py --category sensor --category measure
python scripts/inspect_registry_extensions.py --import-module my_project.habitat_extensions --category task_action --category policy
python scripts/inspect_registry_extensions.py --key measure:MyMeasure --key trainer:ppo
```

The script imports registries and optional extension modules, then prints mapping keys. It does not instantiate `Env`, datasets, simulators, trainers, or policies.
