---
name: zenml
description: "Route ZenML repository and package tasks for MLOps pipelines, CLI
  and Client usage, stacks and integrations, server/store internals,
  deployments, agents, and repository maintenance."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# ZenML

Use this repo skill when a task names ZenML or asks about production ML/AI pipelines, `@step`, `@pipeline`, ZenML CLI or `Client`, stacks, integrations, deployers, FastAPI server internals, stores, migrations, resource pools, triggers, model/agent deployment examples, or maintaining this repository.

## Start Here

1. Read [setup and package facts](references/setup-and-package-facts.md) for install modes, optional extras, import checks, CLI entry points, and version-sensitive facts.
2. Read [repo provenance](references/repo-provenance.md) before deciding whether this skill matches a current checkout or should be refreshed.
3. Read [troubleshooting](references/troubleshooting.md) when imports, optional extras, local server setup, Docker/cloud dependencies, CLI/server boundaries, or repository checks fail.
4. Run [check_zenml_environment.py](scripts/check_zenml_environment.py) for a safe import/metadata/CLI probe in the active Python environment.

## Route By Task

- Use [pipeline-authoring](sub-skills/pipeline-authoring/SKILL.md) for user-facing `@step`/`@pipeline` code, artifacts, materializers, settings, caching, retries, hooks, schedules, dynamic pipelines, wait/resume, and local pipeline smoke checks.
- Use [cli-and-client](sub-skills/cli-and-client/SKILL.md) for `zenml` commands, `Client()`, login/connect/init, resource audits, list filters, projects, stacks, secrets, triggers, resource pools, tags, models, and CLI/client coupling fixes.
- Use [stacks-and-integrations](sub-skills/stacks-and-integrations/SKILL.md) for stack components, integration packages, flavors, service connectors, orchestrators, step operators, materializers, artifact stores, container registries, image builders, optional SDK imports, and remote execution backends.
- Use [server-and-stores](sub-skills/server-and-stores/SKILL.md) for FastAPI routers, auth/RBAC, REST endpoints, shared domain models, Zen stores, SQLModel schemas, Alembic migrations, triggers, resource pools, and server deployment troubleshooting.
- Use [deployments-and-agents](sub-skills/deployments-and-agents/SKILL.md) for pipeline deployments, `DeploymentSettings`, `DockerSettings` for serving, model/agent service examples, deployers/model deployers, service discovery, LLM/agent workflow fallbacks, and credential-free deployment smoke patterns.
- Use [maintenance](sub-skills/maintenance/SKILL.md) for repository edits, AGENTS guidance, targeted tests, formatting/linting, docs maintenance, migration checks, dependency updates, CI parity, and PR readiness.

## Install Baseline

ZenML’s base package installs the client, CLI, pipeline authoring APIs, and core abstractions:

```bash
pip install zenml
python -c "import zenml; print(zenml.__version__)"
zenml --help
```

Use narrow extras only when the task needs them: `zenml[local]` for local SQL store support, `zenml[server]` for FastAPI server/local server work, `zenml[dev]` for repository lint/test/docs tooling, and cloud/integration-specific extras only for the selected backend.

## Safety Defaults

- Do not run cloud examples, agent framework matrices, Docker builds, server lifecycle commands, migration upgrades, destructive CLI operations, or provider API calls unless the user explicitly authorizes the environment, credentials, cost, and side effects.
- Treat API keys, server URLs, tokens, secret values, database URLs, and cloud credentials as sensitive; never print secret values.
- Prefer import checks, `--help`, static validation, targeted pytest files, and bundled diagnostic scripts before broad test suites or integration examples.
- Preserve ZenML optional dependency boundaries: base CLI/client imports must not require server, SQL, or integration SDK extras.
