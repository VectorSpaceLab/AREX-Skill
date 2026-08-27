---
name: cli-and-client
description: "Use ZenML from the CLI and Python Client for repository
  initialization, server connection, resource listing,
  project/stack/pipeline/run/secret/trigger/resource-pool/tag/model management,
  and CLI/client coupling fixes."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# CLI and Client

Use this sub-skill when the task mentions ZenML CLI commands, `zenml_cli:cli`, `zenml login`, `zenml init`, `zenml connect`, `zenml project`, `zenml pipeline`, `zenml secret`, `zenml stack`, `zenml trigger`, `zenml resource-pool`, `zenml resource-request`, `zenml tag`, `zenml model`, or Python `Client()` usage.

## When To Read

- Read [references/cli-reference.md](references/cli-reference.md) before changing or using CLI command families, output formats, filters, login/connect behavior, secrets, projects, stacks, triggers, resource pools, tags, models, or list commands.
- Read [references/client-api.md](references/client-api.md) before using `zenml.client.Client`, adding list filters, matching CLI options to Client signatures, or auditing resources programmatically.
- Read [references/troubleshooting.md](references/troubleshooting.md) when debugging `unexpected keyword argument`, missing server extras, auth/login/connect failures, secret redaction concerns, trigger/resource-pool command confusion, or optional integration imports that break CLI help.
- Run [scripts/zenml_cli_help_snapshot.py](scripts/zenml_cli_help_snapshot.py) to capture Click help for `zenml` or one command path without logging in to a server.

## Scope

This sub-skill owns command and Client usage plus CLI development coupling. It does not own deep FastAPI/store internals, stack component implementation, integration flavor authoring, or repository-wide maintenance checks.

## Route Elsewhere

- Use `../server-and-stores/SKILL.md` for REST routers, Zen stores, SQLModel schemas, migrations, RBAC, trigger internals, resource-pool backend behavior, or server dependency wiring.
- Use `../stacks-and-integrations/SKILL.md` for stack component/flavor implementation, optional SDK import boundaries, service connector internals, or integration extras.
- Use `../pipeline-authoring/SKILL.md` for `@pipeline`, `@step`, run configuration, materializers, schedules as pipeline authoring constructs, and execution semantics.
- Use `../maintenance/SKILL.md` for repo formatting, linting, targeted pytest selection, docs upkeep, or CI-equivalent commands.

## Safe Defaults

Prefer `--help`, `list`, `describe`, and `--output=json`/`yaml` for audits. Do not run destructive commands such as `delete`, `clean`, stack mutations, server start/stop, or secret value retrieval unless the user explicitly asks and credentials/config are appropriate. Treat API keys, secret values, auth tokens, server URLs, and generated config files as sensitive user data.
