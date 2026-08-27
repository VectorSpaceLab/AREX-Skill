---
name: platform-backend
description: "Develop and validate the AutoGPT Platform Python backend, graph
  runtime, blocks, integrations, Prisma data layer, APIs, and backend tooling."
metadata:
  disco-role: operating
disable-model-invocation: true
license: NOASSERTION
---

# Platform Backend

Use this sub-skill for the Python FastAPI backend and shared platform libraries:
REST/WebSocket routes, graph execution, scheduler/executor services, blocks,
provider integrations, workspace/media handling, Prisma schema, model catalog,
backend CLI tools, and Python tests.

## Reference map

- Read [backend architecture](references/backend-architecture.md) to locate
  services, API features, data access, authentication, execution, and storage.
- Read [block development](references/block-development.md) for `Block`,
  `ProviderBuilder`, credential schemas, OAuth/webhooks, media files, and block
  documentation/test contracts.
- Read [API, CLI, and testing](references/api-cli-testing.md) for commands,
  OpenAPI generation, Prisma/migrations, snapshots, model catalog changes, and
  focused validation.
- Read [troubleshooting](references/troubleshooting.md) for dependency,
  service, auth, database, block, and generated-artifact failures.
- Run `python scripts/backend_smoke.py --repo <checkout>` for read-only layout,
  import, and CLI-help checks. It does not start Docker or reset a database.

## Development sequence

1. Work from `autogpt_platform/backend` and use `poetry run` for Python package
   commands. Keep shared-library changes under `autogpt_platform/autogpt_libs`.
2. Identify the owning feature and its nearby tests. Route changes through the
   public API layer, Pydantic models, data functions, and service boundary
   rather than reaching across unrelated features.
3. For an API change, update the route/model, add or revise focused tests, then
   export or fetch OpenAPI before asking the frontend to regenerate hooks.
4. For a block, define schemas and credentials, implement `async run`, provide
   deterministic test input/output or mocks, and test with the block harness.
5. For database changes, review `schema.prisma` and migrations, use the
   dedicated test database path, and never point a reset at a developer's live
   database.

## Useful commands

```bash
cd autogpt_platform/backend
poetry install
poetry run app
poetry run rest
poetry run ws
poetry run pytest path/to/test.py::test_name -xvs
poetry run test
poetry run format
poetry run lint
poetry run prisma migrate deploy
poetry run prisma generate
poetry run gen-prisma-stub
poetry run export-api-schema --output openapi.json --pretty
poetry run cli --help
poetry run oauth-tool --help
```

## High-risk boundaries

- REST and WebSocket startup connects to PostgreSQL and Redis; imports or
  `--help` are safer than starting services.
- Blocks may require API keys, OAuth, external network calls, media storage,
  ClamAV, or provider-specific packages. Prefer mocks and the built-in block
  test contract for local validation.
- Catalog changes are catalog-as-code. Keep model slugs, provider/creator
  references, costs, routing, visibility, and `LLMModel` enum lines consistent;
  use the documented retirement CLI for stored graph migrations.
- Route to [platform-stack](../platform-stack/SKILL.md) for Docker/service
  orchestration and [platform-frontend](../platform-frontend/SKILL.md) for UI
  consumers. Read [workspace/media guidance](references/backend-architecture.md)
  before changing file persistence or `store_media_file()` behavior.
