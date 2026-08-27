---
name: app-development
description: "Help users author and customize Flower Apps with ServerApp,
  ClientApp, Context, Message, records, and pyproject.toml wiring."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# app-development

Use this sub-skill for Flower App authoring, inspection, and troubleshooting.

## Covers
- `ServerApp`, `ClientApp`, `Context`, `Message`, `RecordDict`, `ArrayRecord`, `ConfigRecord`, `MetricRecord`, and `Array`
- `pyproject.toml` app metadata and `tool.flwr.app.components`
- `flwr new` / `flwr run` app authoring loops
- `Context.run_config`, `Context.node_config`, and `Context.state`
- lifecycle hooks via `lifespan()`
- legacy compatibility and deprecation notes for app wiring

## Does not cover
- strategy internals
- dataset partitioning
- deployment admin
- repo-maintenance commands

## Start here
1. Read [references/workflows.md](references/workflows.md).
2. Check [references/api-reference.md](references/api-reference.md) for exact signatures and routing rules.
3. Use [references/troubleshooting.md](references/troubleshooting.md) for signature, config, and record-type failures.
4. Run `scripts/check_flower_app.py` for a safe pyproject/component validation and tiny runtime smoke.

## Quick routing
- Server orchestration and round entry point: `ServerApp`
- Client message handlers: `ClientApp`
- Runtime settings and node-local data: `Context`
- App payloads: `Message` and `RecordDict`
- Arrays, configs, and metrics: `ArrayRecord`, `ConfigRecord`, `MetricRecord`

## Practical rule of thumb
Keep app objects stateless. Put per-run memory in `context.state`, read run-specific values from `context.run_config`, and read node-specific values from `context.node_config`.
