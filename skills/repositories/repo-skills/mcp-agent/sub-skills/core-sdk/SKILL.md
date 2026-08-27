---
name: core-sdk
description: "Build local mcp-agent apps with MCPApp, Agent, AgentSpec,
  AugmentedLLM, RequestParams, settings, secrets, decorators, and factory
  basics."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# core-sdk

Use this sub-skill when the task is to create, configure, or debug a local `mcp-agent` application using the core Python SDK. It covers `MCPApp`, `Agent`, `AgentSpec`, `AugmentedLLM`, `RequestParams`, programmatic `Settings`, YAML config/secrets, local function tools, human-input hooks, and the basic agent factory helpers.

## Start Here

1. Read `references/api-reference.md` for verified constructor signatures, lifecycle patterns, LLM attachment, provider/model selection, and request parameters.
2. Read `references/configuration.md` when the task involves `mcp_agent.config.yaml`, `mcp_agent.secrets.yaml`, `Settings(...)`, provider keys, or schema validation.
3. Read `references/decorators-and-factory.md` for `@app.tool`, `@app.async_tool`, workflow decorator basics, `AgentSpec`, `create_agent`, `create_llm`, and agent-spec loading.
4. Read `references/troubleshooting.md` when imports, provider extras, secrets, YAML merging, server names, async lifecycle, decorators, or `RequestParams` fail.
5. Run `scripts/check_core_sdk.py --help` to see the credential-free smoke checks; run it before blaming provider credentials or network access.

## Core Workflow

- Create one `MCPApp` per process, preferably with an explicit `Settings` object or explicit config path for deterministic runs.
- Enter `async with app.run() as running_app:` before using app context, configured server registry, logging, token counters, human-input hooks, or workflow decorators that depend on runtime context.
- Define `Agent(name=..., instruction=..., server_names=[...], functions=[...], context=running_app.context)` for local agents; attach a provider implementation with `await agent.attach_llm(...)` only after provider package and credentials are available.
- Use `RequestParams(...)` per generation to set model, model preferences, temperature, token limits, tool filtering, history, iteration count, strict mode, and reasoning effort.
- Keep provider keys in secrets or environment variables; keep reusable server/model defaults in config or programmatic `Settings`.

## Route Elsewhere

- Route workflow pattern selection, routers/orchestrators/parallel/deep workflow design, and durable workflow strategy to sibling `workflow-patterns`.
- Route MCP server exposure, server auth internals, FastMCP deployment, and app-as-server details to sibling `mcp-server-integration`.
- Route CLI commands, cloud deployment, and hosted operations to sibling `cli-cloud-operations`.
- Route Temporal worker operations and production durability to sibling `durable-execution`.
- Route tracing/exporter/provider-wrapper internals to sibling `observability-integrations`.

## Bundled Check

Use the smoke checker for local SDK validation without credentials or network:

```bash
python scripts/check_core_sdk.py
python scripts/check_core_sdk.py --provider openai
```

The default check imports core APIs, constructs programmatic settings, validates local function-tool annotations, registers decorators, creates an `AgentSpec`, and builds `RequestParams`. Provider checks only import the provider wrapper and report whether a key-shaped setting is present; they do not call external services.
