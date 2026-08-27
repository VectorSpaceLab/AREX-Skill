# Overview

## Scope

This sub-skill guides future agents working on `@strands-agents/sdk` and the `strands-ts` workspace.

It covers:

- Agent config, invoke, stream, cancellation, snapshots, and direct tool calls
- Zod and JSON-schema tools
- Model providers and streaming event translation
- MCP client/tool loading and task-based tool calls
- Hooks, middleware, interventions, and plugins
- Memory, session, and storage layers
- Sandbox execution helpers
- Telemetry helpers
- Graph and Swarm multi-agent orchestration
- Examples, packaging, and workspace commands

It does **not** cover:

- Python SDK implementation
- docs site authoring or `sourceLinks`
- the docs-search MCP server package

## Top-level shape

- The root package is the public barrel for `@strands-agents/sdk`.
- The Node entry point registers Node-specific defaults before re-exporting the public API.
- Browser-safe code lives behind the default entry point; Node-only setup stays out of the browser path.
- Subpath exports expose provider, multi-agent, telemetry, storage, sandbox, vended tool, vended plugin, and memory-store entry points.
- Examples are standalone projects, not shared app code.
- `strandly` wraps common workspace commands for the monorepo.

## Package shape

- Runtime helpers that are not part of the consumer API live in `dependencies`.
- Anything that crosses an API boundary belongs in `peerDependencies`.
- Optional peers should also appear in `devDependencies` so the workspace can test and type-check them.
- Build, lint, test, and browser tooling stay in `devDependencies`.
- The package export map exposes the root barrel plus provider, orchestration, experimental, telemetry, storage, sandbox, A2A, session, and vended tool / plugin / intervention / memory-store subpaths.
- The published file list is intentionally small; it is a package, not a source checkout.

## The operating model

Remember these core rules while drafting or changing guidance:

- `Agent` is async-only. `invoke()` returns a `Promise`; `stream()` returns an async generator.
- `tool()` accepts either Zod schemas or JSON Schema objects.
- `Model` is the provider contract. Providers transform vendor-specific responses into SDK stream events and SDK error types.
- `McpClient` owns server connection, tool discovery, filtering, and task-based tool invocation.
- Hooks, middleware, interventions, and plugins are separate extension layers with different insertion points.
- `MemoryManager`, `SessionManager`, and `Storage` solve different persistence problems.
- `Sandbox` abstracts command execution and file I/O.
- `Graph` and `Swarm` are different orchestration styles, not interchangeable aliases.

## Environment split

- Node-specific defaults are registered by the Node entry point.
- Browser tests and browser bundles are separate from Node unit tests.
- Provider credential checks are conditional and should stay isolated from offline unit coverage.
- The browser-agent example is for demonstration only and is not a production-safe pattern.

## Evidence base

This skill was distilled from the public SDK barrel, the main provider and orchestration modules, package metadata, the TypeScript conventions guide, the testing and dependency docs, the examples guide, the workspace CLI, and the native candidate map.
