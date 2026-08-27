---
name: setup-and-config
description: "Use this sub-skill to install EverOS, generate and inspect
  configuration, start the server, check health, and run the demo CLI."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# EverOS Setup and Config

Use this sub-skill when a user wants to install EverOS, configure the memory root, start the HTTP service, check capability status, inspect effective settings, or run the local/demo experience.

## Read/run map

- Read [configuration](references/configuration.md) for install commands, root resolution, `everos init`, `everos config show`, server startup, health, and demo modes.
- Read [troubleshooting](references/troubleshooting.md) when import, config, provider, server, or demo errors appear.
- Run [check_everos_install.py](scripts/check_everos_install.py) to inspect an installed package, CLI availability, default templates, and no-lifespan OpenAPI construction without starting a server.

## Core workflow

```bash
python -m pip install everos

everos init --root ~/.everos
$EDITOR ~/.everos/everos.toml

everos config show --root ~/.everos

everos server start --root ~/.everos
curl http://127.0.0.1:8000/health
```

Fill `[llm]` before expecting the normal server to start. Fill `[embedding]` and `[rerank]` before expecting vector/hybrid/agentic search, knowledge write/search, clustering, and backfill behavior. Use `everos demo --plain` before provider setup; use `everos demo --live` only against a running configured server.

## Important decisions

- Use Python 3.12+.
- Keep the same memory root across `init`, `server start`, `config show`, and `cascade` commands.
- Prefer loopback binding (`127.0.0.1`) unless the service is behind an authenticated gateway.
- Use `ENV=DEV` only when the runtime OpenAPI endpoint is needed; the bundled OpenAPI helper can inspect schema without running the server.
- Do not treat optional provider credentials as verified unless the target environment supplies them.

## Common triggers

This sub-skill should handle prompts mentioning EverOS install, `everos init`, `everos.toml`, `ome.toml`, `EVEROS_ROOT`, `everos config show`, `server start`, `/health`, `demo --plain`, `demo --live`, missing API keys, or first-run setup.
