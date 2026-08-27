---
name: typescript-sdk
description: "Routes Memori TypeScript/Node SDK, request scopes, storage, and
  native binding workflows."
metadata:
  disco-role: operating
disable-model-invocation: true
license: NOASSERTION
---

# TypeScript SDK

Use this sub-skill for the `@memorilabs/memori` package, Node request scopes,
TS storage setup, CLI checks, and native-binding troubleshooting.

## Use when

- The request mentions `@memorilabs/memori`, `MemoriRequestScope`, `forRequest`,
  Node peer dependencies, or the TS CLI.
- The user is wiring Memori into a Node backend or a TypeScript app.
- The task is about TypeScript runtime details, not Python-only APIs.

## Read first

- `references/typescript-api-reference.md` for constructors and methods.
- `references/typescript-recipes.md` for cloud and BYODB patterns.
- `references/native-bindings.md` for platform and native-load notes.
- `references/troubleshooting.md` for version, peer-dep, and scope issues.
- `scripts/check_memori_ts_package.mjs` for a safe package-check helper.

## What this sub-skill owns

- `Memori`, `MemoriRequestScope`, and `forRequest(...)`.
- Storage manager and dialect setup in the Node package.
- CLI/package metadata checks and native-load caveats.
- Request-scope identity isolation guidance for concurrent servers.

## What it does not own

- Python cloud, CLI, or MCP guidance: use `cli-and-cloud`.
- Python BYODB setup: use `byodb-storage`.
- Python provider registration: use `llm-integration`.
- Python recall/search or native embedding behavior: use `memory-and-search`.

## Safe first check

Run the bundled package check before suggesting a Node runtime change:

```bash
node scripts/check_memori_ts_package.mjs
```

That helper only reads local package metadata and source layout; it does not
install dependencies or contact a remote service.
