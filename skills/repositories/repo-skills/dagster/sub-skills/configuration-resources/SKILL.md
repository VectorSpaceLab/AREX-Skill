---
name: configuration-resources
description: "Use this sub-skill when implementing or debugging Dagster Pythonic
  config, RunConfig, ConfigurableResource, EnvVar, resource dependencies,
  ConfigurableIOManager, or test resource wiring."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Configuration Resources

Use this sub-skill to model Dagster runtime configuration and resource wiring with the Python APIs exported by `dagster`.

## Route Here

- Define asset/op config classes with `dagster.Config` or `dagster.PermissiveConfig`.
- Build `dagster.RunConfig` for `materialize`, `execute_in_process`, schedules, sensors, or launch-time resource config.
- Implement resources with `dagster.ConfigurableResource`, `dagster.ResourceDependency`, and resource lifecycle hooks.
- Implement IO managers with `dagster.ConfigurableIOManager` or a configurable IO manager factory.
- Preserve secrets with `dagster.EnvVar` and debug EnvVar resolution.
- Wire resources in tests with `Definitions`, `build_resources`, `build_init_resource_context`, or direct invocation patterns.

## Route Elsewhere

- Asset, op, graph, job, partition, or automation modeling belongs in the `asset-definitions` sub-skill when that sub-skill exists.
- Dagster instance YAML, deployment configuration, daemons, executors, or webserver operations belong in the `deployment-operations` sub-skill when that sub-skill exists.
- Repository maintenance, `ruff`, `pyright`, package layout, or contribution workflow belongs in the `repo-development` sub-skill when that sub-skill exists.

## Fast Path

1. Pick the model: `Config` for strict structured config, `PermissiveConfig` for open-ended extra keys, `ConfigurableResource` for reusable external services, and `ConfigurableIOManager` for persistence behavior.
2. Keep runtime config structured: pass instances through `RunConfig(ops={...}, resources={...})` instead of hand-building nested dicts when Python code owns the launch.
3. Keep secrets deferred: use `EnvVar("NAME")` or `EnvVar.int("NAME")` inside config/resource objects; use `.get_value()` only for explicit non-Dagster runtime reads.
4. For nested resources, declare dependencies as typed fields on the parent resource, using `ResourceDependency[T]` when the nested value is a plain object or function rather than a configurable resource class.
5. In tests, prefer the narrowest execution path that exercises the behavior: instantiate config directly for Pydantic validation, call resource methods for pure behavior, and use `Definitions`/`execute_in_process` when Dagster resource initialization matters.

## References

- Follow `references/api-reference.md` for API shapes, conversion rules, and code templates.
- Follow `references/workflows.md` for implementation and testing workflows.
- Follow `references/troubleshooting.md` for common failures and fixes.
- Run `scripts/check_config_resource_shape.py --help` or the smoke command in the script output when you need a safe local sanity check of config/resource conversion.
