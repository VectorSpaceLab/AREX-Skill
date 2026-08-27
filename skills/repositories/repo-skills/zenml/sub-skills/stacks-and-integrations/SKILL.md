---
name: stacks-and-integrations
description: "Register, configure, and extend ZenML stacks, stack components,
  integrations, service connectors, materializers, orchestrators, step
  operators, artifact stores, container registries, image builders, and optional
  dependency boundaries."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# ZenML Stacks and Integrations

Use this sub-skill when a task mentions ZenML stacks, stack components, flavors, integrations, service connectors, materializers, orchestrators, step operators, artifact stores, container registries, image builders, Docker/Podman image builds, remote execution backends, cloud credentials, or missing optional SDK extras.

## Route First

- Read [references/component-patterns.md](references/component-patterns.md) for stack registration, stack validation, component config/settings, service connector use, materializer contracts, and remote image-building requirements.
- Read [references/integration-development.md](references/integration-development.md) before adding or changing an integration package, flavor, orchestrator, step operator, image builder, container registry, artifact store, or optional dependency boundary.
- Read [references/troubleshooting.md](references/troubleshooting.md) when imports, extras, service connectors, stack validation, Docker, image builds, orchestrator IDs, or step-operator lifecycle behavior fail.
- Run [scripts/check_optional_imports.py](scripts/check_optional_imports.py) from an active ZenML checkout before finishing integration flavor changes that may import optional SDKs.

## Boundaries

- Own stack infrastructure and integration authoring/import safety; for using `DockerSettings`, `ResourceSettings`, schedules, materializers, or stack settings inside user pipelines, cross-read [../pipeline-authoring/SKILL.md](../pipeline-authoring/SKILL.md).
- Own component-level and integration-level validation rules; for repository-wide test selection, formatting, linting, documentation, dependency, or CI workflow choices, cross-read [../maintenance/SKILL.md](../maintenance/SKILL.md).
- Use [../cli-and-client/SKILL.md](../cli-and-client/SKILL.md) for CLI/client resource listing, filters, project/server login, and stack-management commands when the task is usage-focused rather than implementation-focused.
- Do not duplicate server/store internals here; route FastAPI, SQLModel, migrations, RBAC, and store schema work to the server/store sub-skill.

## Non-Negotiable ZenML Rules

- Keep optional third-party SDK imports out of integration flavor module top level; config classes in flavor files should use standard library, Pydantic, and ZenML core types only.
- Import implementation classes lazily inside `implementation_class` properties, and use `TYPE_CHECKING` blocks for optional implementation type hints.
- For remote orchestrators and step operators, validate remote artifact stores, container registries, required image builders, and remote server requirements before runtime submission.
- `get_orchestrator_run_id()` must return one stable ID for every step in a pipeline run and a unique ID across different runs; dynamic retry paths must preserve the same orchestration-environment ID.
- New step operators should implement `submit()`, `get_status()`, `wait()`, and `cancel()`; store backend job IDs immediately after submission so polling and cancellation can recover.
