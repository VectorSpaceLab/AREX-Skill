---
name: mcp-and-integrations
description: "Guides agents that connect Pydantic AI agents to MCP, FastMCP,
  A2A, durable execution, capabilities, hooks, Logfire, AG-UI, Vercel AI, and
  web integration surfaces."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# MCP and Integrations

Use this sub-skill when a task connects Pydantic AI agents to external protocols, application runtimes, observability, durable workflow engines, UI adapters, or capability-driven integration bundles rather than defining ordinary Python function tools.

## Read First

- Read [references/mcp-workflows.md](references/mcp-workflows.md) to choose between `MCPToolset`, legacy `MCPServer*`, `MCP` capability native/local selection, FastMCP inputs, agent-inside-MCP-server recipes, resource/prompt access, sampling, and MCP lifecycle management.
- Read [references/capabilities-and-hooks.md](references/capabilities-and-hooks.md) when packaging integrations as `Capability`, `Hooks`, `NativeOrLocalTool`, `WebSearch`, `WebFetch`, `Instrumentation`, or deferred/on-demand workflows with stable capability IDs.
- Read [references/durable-and-ui-integrations.md](references/durable-and-ui-integrations.md) when wrapping agents for Temporal, Prefect, DBOS, Restate/Kitaru-style durable systems, A2A servers, `AGUIAdapter`, `VercelAIAdapter`, `to_web()`, or web UI embedding.
- Read [references/troubleshooting.md](references/troubleshooting.md) to debug optional extras, MCP native-vs-local confusion, capability resume state, hook ordering, Logfire/OTel setup, durable backend services, UI adapter message limits, and credential-bound integrations.
- Run [scripts/integration_import_check.py](scripts/integration_import_check.py) for no-network import and signature diagnostics for optional integration groups before claiming local support for MCP, FastMCP, A2A, Logfire, AG-UI, Vercel AI, durable engines, or web extras.

## Route Elsewhere

- Use `../agent-core/SKILL.md` for basic `Agent` construction, run methods, `AgentSpec`, dependencies, streaming, testing, and message-history continuation.
- Use `../tools-and-toolsets/SKILL.md` for individual Python function tools, `FunctionToolset`, generic wrapper toolsets, approvals, deferred tool mechanics, and tool schema debugging.
- Use `../models-and-providers/SKILL.md` for provider-specific model strings, provider SDK installation, native provider tools that are not MCP-specific, embeddings, fallback models, and provider credentials.
- Use `../outputs-and-messages/SKILL.md` for structured output design, message serialization, multimodal content model details, and UI message persistence that is not adapter-specific.
- Use `../cli-and-apps/SKILL.md` for `pai`, `clai`, `clai web`, command-line flags, and app-launch instructions.

## Decision Guide

- Prefer `pydantic_ai.mcp.MCPToolset` for MCP clients; it is the current full-protocol path built on FastMCP `Client` and accepts URLs, script paths, transports, in-process FastMCP servers, pre-built clients, and multi-server config via `load_mcp_toolsets()`.
- Use `pydantic_ai.capabilities.MCP` when a remote MCP server may be provider-native on models that support native MCP, with a local `MCPToolset` fallback where the `mcp` extra is installed.
- Treat `MCPServerStdio`, `MCPServerSSE`, `MCPServerHTTP`, `MCPServerStreamableHTTP`, `load_mcp_servers()`, and `FastMCPToolset` as compatibility/deprecation surfaces; document migration toward `MCPToolset` in new guidance.
- Use `Capability` or a custom `AbstractCapability` when an integration owns instructions, tools/toolsets, native tools, settings, lifecycle hooks, event/history processing, or deferred loading as one unit.
- Use durable wrappers only when the backend service/runtime is part of the deployment plan; keep model, toolset, MCP, and capability IDs stable before wrapping.
- Use UI adapters for protocol translation and streaming responses, not as a replacement for application authorization, input sanitization, persistence, or provider credential management.

## Safety Defaults

- Do not start MCP servers, ASGI apps, durable workers, browser UIs, or network clients during skill diagnostics unless the user explicitly asks and required services are available.
- Never print API keys, authorization headers, OAuth tokens, backend connection strings, or provider credentials; diagnostic scripts should report only import presence and variable names.
- For local MCP stdio commands, pass explicit `env=` values and a deliberate `cwd=` rather than inheriting the whole process environment by default.
- For deferred capabilities, always set stable explicit `id` values before persisting or replaying message history.
- For UI adapters, keep `manage_system_prompt='server'`, HTTP(S)-only file URLs, and `preserve_file_data=False` unless the frontend is trusted and audited.
