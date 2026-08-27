# RocketRide Server Overview

RocketRide is an AI pipeline platform with a multithreaded native engine, visual IDE authoring, Python/TypeScript SDKs, an MCP server, n8n integrations, deployment assets, and a large catalog of pipeline nodes.

Use this overview to orient a task before opening a focused sub-skill. It is intentionally self-contained; path names below are repo-relative locations a future maintainer may encounter in a RocketRide checkout, not links to required runtime dependencies.

## Primary operating surfaces

| Surface | Public purpose | Skill route |
|---|---|---|
| `.pipe` JSON pipelines | Portable pipeline graphs composed of components/providers with config, data-lane input edges, and control/invoke edges. | `sub-skills/pipeline-authoring/` |
| Python SDK package `rocketride` | Async client, CLI, typed schemas, task-token lifecycle, file upload/streaming, events, deploy/database/log/store namespaces. | `sub-skills/sdk-clients/` |
| TypeScript/Node package `rocketride` | Node/browser SDK, CLI, `DataPipe`, generated `.pipe` TypeScript contract, analytics/app SDK exports. | `sub-skills/sdk-clients/` |
| MCP package `rocketride-mcp` | Exposes running RocketRide pipelines as Model Context Protocol tools/resources for assistants. | `sub-skills/mcp-and-integrations/` |
| Node catalog | Service definitions, provider classes, node README/docs generation, optional dependencies, node tests. | `sub-skills/nodes-catalog/` |
| Runtime engine | Native engine process, WebSocket/DAP protocol, `/ping`, observability, Docker/Helm/source build/deployment. | `sub-skills/runtime-deployment/` |
| VS Code extension and apps | Visual pipeline editor, App Builder, connection/deployment settings, shell/remotes. | `sub-skills/ide-and-apps/` |
| Contributor workflow | Builder task registry, docs generation, generated contract files, focused tests and CI troubleshooting. | `sub-skills/development-build-docs/` |

## Key concepts

- A pipeline is a JSON object with `components` (or legacy/alternate `nodes`) and optional root metadata such as `name`, `description`, `version`, `source`, editor viewport, and lock/grid settings.
- Each component has an `id`, `provider`, `config`, optional UI metadata, optional `input` data-lane connections, and optional `control` invoke connections.
- Data lanes move typed outputs from one component to another. Control connections let agents/tools/LLMs/memory be invoked by class type.
- A running pipeline receives a task token. SDK/CLI data operations (`send`, `pipe`, `upload`, `chat`, `status`, `stop`) target that token.
- The engine normally listens on port `5565`; SDKs connect to `/task/service` over WebSocket and can also use Cloud endpoints.
- Provider credentials and external service coordinates should be passed as environment variables and referenced from node config, never committed as literal secrets.

## Package and version baseline

- Monorepo package: `rocketride-server` version `3.3.0`.
- Python SDK distribution/import: `rocketride` version `1.3.0`.
- TypeScript package: `rocketride` version `1.3.0`.
- MCP distribution/import: `rocketride-mcp` / `rocketride_mcp` version `1.2.0`.
- VS Code extension package display name: RocketRide, version `1.2.0`.
- n8n community package: `n8n-nodes-rocketride` version `0.1.0`.

## Common route combinations

- Build a pipeline and run it from Python: `pipeline-authoring` for JSON shape, then `sdk-clients` for `RocketRideClient.use()` and `send()`/`pipe()`.
- Build locally and diagnose connection failures: `runtime-deployment` for engine startup and `/ping`, then `sdk-clients` for URI/auth/token handling.
- Expose a pipeline to an assistant: `mcp-and-integrations` plus `sdk-clients` if the pipeline must first be started by CLI/SDK.
- Add or fix a provider node: `nodes-catalog` for service JSON and generated docs rules, then `development-build-docs` for builder/test/docs commands.
- Fix visual editor or app-builder behavior: `ide-and-apps`; route to `development-build-docs` only for build/test/docs tasks.

## Verification stance

The generated skill verifies CPU/static surfaces: Python SDK and MCP imports, CLI help for the Python SDK, static `.pipe` shape checks, service-definition parsing, and skill link/frontmatter checks. It does not claim live Cloud, provider API, vector database, Docker/Kubernetes, VS Code, n8n, or GPU runtime verification unless a future task explicitly prepares those services and credentials.
