---
name: core-runtime
description: "Start, configure, deploy, inspect, and troubleshoot LangBot core
  runtime boot, Application wiring, config.yaml, health checks, Docker or
  standalone Plugin Runtime and Box modes."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Core Runtime

Use this sub-skill when the task is about getting LangBot running, reasoning
about the boot graph, changing runtime configuration, deployment topology,
startup flags, health/resource reporting, or operational probes.

## Read First

- [references/startup-and-configuration.md](references/startup-and-configuration.md)
  for entry points, `config.yaml`, boot stages, and local startup commands.
- [references/deployment-and-operations.md](references/deployment-and-operations.md)
  for Docker/Compose/Kubernetes, Plugin Runtime, Box Runtime, and resource
  probes.
- [references/troubleshooting.md](references/troubleshooting.md) for startup,
  config, port, dependency, and runtime-service failures.

## Core Facts

- `main.py` delegates to `langbot.__main__.main()`.
- The `langbot` console script accepts `--standalone-runtime`,
  `--standalone-box`, `--debug`, and an operator `migrate --cloud` subcommand.
- First startup generates missing data/config files and initializes the
  database before serving HTTP.
- `BuildAppStage` wires the long-lived `Application` object: managers,
  services, runtime connectors, controllers, storage, telemetry, and task
  management.
- The HTTP controller serves Quart/Hypercorn on `api.port` and mounts MCP at
  `/mcp` after route registration.
- Default local data lives under the current working directory's `data/` when
  running the package or source command.

## Typical Workflows

### Local source startup

```bash
uv sync --dev
uv run main.py
```

If you intentionally installed a local sibling SDK checkout, preserve it with:

```bash
uv run --no-sync main.py
```

Use `--standalone-runtime` when an external Plugin Runtime is already running,
and `--standalone-box` when an external Box Runtime is already running.

### Package startup

```bash
uvx langbot
# or
pip install langbot
langbot --help
langbot
```

### Health check

```bash
curl http://127.0.0.1:5300/healthz
```

Expect `code: 0` plus resource counters. If the route is unavailable, diagnose
boot, port binding, config generation, and dependency installation before
looking at higher-level pipeline behavior.

## Boundaries

- HTTP route auth and MCP tool design belong to `api-mcp-web`.
- Platform message flow, adapters, pipelines, providers, and tools belong to
  `platform-pipeline-provider`.
- Plugin Runtime and Box API details belong to `plugin-box-skills`.
- Database migrations, RAG, vector backends, storage, and tenancy belong to
  `persistence-rag-workspaces`.
- Verification selection belongs to `testing-qa`.

## Validation

Use startup-focused checks before broad suites:

```bash
python scripts/langbot_repo_doctor.py --repo-root /path/to/LangBot
uv run --python 3.12 pytest tests/e2e -q --tb=short
```

Only run long resource probes or cloud soak gates when the task is specifically
about runtime retention, capacity, or production stability.
