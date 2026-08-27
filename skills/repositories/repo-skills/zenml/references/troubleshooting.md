# ZenML Cross-Cutting Troubleshooting

Use this reference before broadening installs, running integration examples, or changing multiple ZenML layers.

## Import Or Install Fails

Symptoms:

- `ModuleNotFoundError: zenml`.
- Import succeeds from a checkout but package metadata is missing.
- CLI help fails after adding integration or server imports.
- `pip check` reports incompatible dependencies.

Actions:

1. Run `python scripts/check_zenml_environment.py --json` to distinguish import, package metadata, and CLI entry-point failures.
2. Install the narrowest package variant for the task: base `zenml`, `zenml[local]`, `zenml[server]`, `zenml[dev]`, or a specific integration/connector extra.
3. If a module-level import of FastAPI, SQLModel, or an optional integration SDK broke base CLI/client behavior, route to the relevant sub-skill and move that import behind a dependency check, method-local import, or `TYPE_CHECKING` block.
4. Run `python -m pip check` after dependency changes.

## Optional Dependency Boundaries Break

Common ZenML boundaries:

- CLI and client code should not import from `zenml.zen_server`.
- Client/core/integration code should not import SQL schemas or `SqlZenStore` directly; use shared models, `Client`, or `Client().zen_store` only when intentionally lower-level.
- Integration flavor files must not import optional SDKs at module top level.
- Server code can import inside `zen_server`, but endpoints should keep authorization, entitlement/RBAC, store operations, and wrappers aligned.

Use [stacks-and-integrations](../sub-skills/stacks-and-integrations/SKILL.md) for optional SDK/import issues and [server-and-stores](../sub-skills/server-and-stores/SKILL.md) for server/store boundaries.

## CLI Or Client Filter Errors

Symptom:

```text
TypeError: list_pipeline_runs() got an unexpected keyword argument 'new_field'
```

Likely cause: a filter model field was exposed to Click via `@list_options(...)`, but the `Client` list method signature or filter instantiation was not updated.

Actions:

1. Read [cli-and-client troubleshooting](../sub-skills/cli-and-client/references/troubleshooting.md).
2. Update the filter model, `Client` method signature, and `Client` filter model construction together.
3. If the field should not be a CLI option, add it to the filter model’s `CLI_EXCLUDE_FIELDS`.
4. Add a targeted CLI/client test instead of relying on full-suite coverage.

## Pipeline Runtime Behavior Looks Wrong

Symptoms:

- Cache hit skipped a step hook.
- A custom materializer is not selected.
- Dynamic pipeline creates duplicate child runs.
- Docker/resource settings appear ignored.

Actions:

- Use [pipeline-authoring](../sub-skills/pipeline-authoring/SKILL.md) for decorator/settings/materializer/dynamic behavior.
- Remember cache hits skip step execution and step hooks; retries can execute hooks per attempt.
- Name multi-output artifacts before assigning per-output materializers.
- For dynamic child pipelines, keep child keys and call order stable across retries/resume.
- Check whether the active orchestrator/deployer supports the specific Docker/resource setting.

## Deployment Or Agent Examples Need External Resources

Symptoms:

- Missing `OPENAI_API_KEY`, provider SDK, Docker daemon, cloud credentials, remote artifact store, or container registry.
- LLM/agent examples fall back to deterministic responses.
- Service URL is local when the user expected cloud, or cloud when the user expected localhost.

Actions:

- Treat missing credentials/network/services as skipped or fallback, not as success or skill failure.
- Validate `DeploymentSettings` and `DockerSettings` separately before deploying.
- Use [deployments-and-agents](../sub-skills/deployments-and-agents/SKILL.md) for service/agent adaptation and [stacks-and-integrations](../sub-skills/stacks-and-integrations/SKILL.md) for deployer/image/registry/connector setup.
- Ask before using paid APIs, cloud accounts, Docker builds, service lifecycle operations, or network downloads.

## Server, Models, Stores, Or Migrations Drift

Symptoms:

- REST response shape changed but models/schemas/tests did not.
- Trigger/resource-pool behavior changed in one layer only.
- Alembic reports diverging branches.
- Older clients cannot parse newer server responses.

Actions:

1. Read [server-and-stores](../sub-skills/server-and-stores/SKILL.md).
2. Trace changes across domain models, filters, client signatures, CLI options, server routers, store methods, SQL schemas, migrations, tests, and docs.
3. Add optional fields before removing/renaming fields; preserve rolling compatibility when possible.
4. Run the bundled migration branch check or the repository script in an active checkout with dev/local dependencies installed.

## Repository Checks Are Too Broad Or Mutating

Actions:

- Use [maintenance](../sub-skills/maintenance/SKILL.md) to select targeted checks.
- Avoid running the full test suite locally; use focused `pytest tests/unit/...` or explicit integration tests only when relevant and safe.
- Treat Docker/server provisioning, docs serving, migration replay, cloud integration tests, and agent framework matrices as expensive or mutating unless authorized.
