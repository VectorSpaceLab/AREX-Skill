---
name: deployments-and-agents
description: "Build, adapt, validate, and troubleshoot ZenML pipeline
  deployments, model or agent services, DeploymentSettings, DockerSettings
  packaging, deployer selection, service discovery, and credential-free ML or
  LLM workflow smoke patterns."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# ZenML Deployments and Agents

Use this sub-skill when a task mentions ZenML pipeline deployments, deployed HTTP services, real-time inference, serving ML models, deployed agents, LLM or agent examples, `DeploymentSettings`, deployment `DockerSettings`, deployers, model deployers, services, dashboard/static UI files, deployment invocation, or credential-free adaptation of production examples.

## Route First

1. Read [Agent and deployment workflows](references/agent-and-deployment-workflows.md) to choose between pipeline deployments, model-deployer/service workflows, agent examples, deterministic fallbacks, and production-readiness checks.
2. Read [Deployment settings](references/deployment-settings.md) before editing `DeploymentSettings`, `DockerSettings`, CORS, secure headers, endpoint paths, dashboard files, app extensions, or deployer-specific settings.
3. Read [Troubleshooting](references/troubleshooting.md) before running examples, changing stack/deployer configuration, debugging local-vs-remote behavior, or interpreting missing API keys, Docker, registries, services, and cloud credentials.
4. Run [validate_deployment_settings.py](scripts/validate_deployment_settings.py) with `--example` or `--json <settings.json>` for safe schema-level validation without deploying anything.

## Boundary Rules

- Own example-backed production model, agent, and service workflows; pipeline deployments; `DeploymentSettings`; deployer/model-deployer/service usage; HTTP invocation shape; embedded UI patterns; credential-free smoke adaptation; and deployment-specific troubleshooting.
- Route low-level stack component implementation, integration flavor imports, service connectors, image builders, container registries, Docker daemon/backend issues, and cloud component registration to [stacks-and-integrations](../stacks-and-integrations/SKILL.md).
- Route basic `@step`, `@pipeline`, artifacts, materializers, schedules, hooks as authoring primitives, and local pipeline semantics to [pipeline-authoring](../pipeline-authoring/SKILL.md).
- Route FastAPI server/store internals, REST routers, SQLModel schemas, migrations, RBAC, triggers, and server dependency wiring to [server-and-stores](../server-and-stores/SKILL.md).
- Route CLI/client resource audits, `zenml deployment list/describe/invoke` command behavior, login/connect, filters, secrets, and project/stack listing to [cli-and-client](../cli-and-client/SKILL.md).
- Route repository test selection, formatting, linting, docs maintenance, and CI-equivalent checks to [maintenance](../maintenance/SKILL.md).

## Working Pattern

- Classify the serving target first: pipeline deployment for a long-running HTTP service, batch/snapshot execution for one-off work, or legacy/specialized model deployer only when an integration explicitly requires model-server semantics.
- Make deployable pipelines accept explicit JSON-serializable parameters with defaults, return JSON-serializable outputs or stable artifacts, and keep heavyweight models/resources loaded through startup hooks or deployment-service state.
- Keep agent workflows credential-aware: use deterministic fallbacks, stubs, or skipped branches when API keys, network, LLM providers, Docker, services, or cloud credentials are unavailable.
- Treat `DeploymentSettings` as ASGI application configuration and `DockerSettings` as image/runtime packaging; validate both before changing stack/deployer infrastructure.
- Prefer local, credential-free checks first: static code review, `py_compile`, settings validation, import checks, and small synthetic payloads. Deploy, invoke, start services, build images, or call LLMs only after the user explicitly authorizes the environment and credentials.

## Safe Validation

- `python scripts/validate_deployment_settings.py --help` shows supported validation modes.
- `python scripts/validate_deployment_settings.py --example` prints and validates a tiny, credential-free deployment plus Docker settings payload.
- `python scripts/validate_deployment_settings.py --json deployment_settings.json` validates a user-supplied JSON payload containing `deployment` and/or `docker` settings without loading source hooks, running pipelines, starting servers, using Docker, or reading credentials.
