---
name: integrations-mcp-chainlit
description: "Connect Langroid agents to MCP tools, web/search/file tools,
  Chainlit callbacks/UI, HTML logging, and external-service integrations."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# integrations-mcp-chainlit

Use this sub-skill when a Langroid task needs to connect agents to external tools or service-facing integration layers: MCP servers, built-in web/search tools, safe local file tools, Chainlit UI callbacks, HTML task logs, quiet/status output control, or deterministic local smoke checks for those integrations.

## Route before acting

- For Langroid custom `ToolMessage` design, handler signatures, task done sequences, or multi-agent delegation mechanics, route to [`../agents-tasks-tools/SKILL.md`](../agents-tasks-tools/SKILL.md).
- For LLM provider configuration, model names, API gateways, or provider authentication, route to [`../llm-provider-config/SKILL.md`](../llm-provider-config/SKILL.md).
- For RAG ingestion, document parsing, vector stores, or document-chat agents, route to [`../retrieval-doc-chat/SKILL.md`](../retrieval-doc-chat/SKILL.md).
- Stay here for external tool integration wiring, callback/UI integration, search/file tool enablement, MCP transport lifecycle, logging/output controls, and integration troubleshooting.

## Operating map

1. Identify which integration boundary is needed: MCP, search, file tools, Chainlit UI, or logging/output.
2. Load the narrow reference for that boundary:
   - [`references/mcp-workflows.md`](references/mcp-workflows.md) for MCP tool generation, transports, async/decorator choices, and resource forwarding.
   - [`references/search-and-file-tools.md`](references/search-and-file-tools.md) for DuckDuckGo, Tavily, Exa, Google, Seltz, Twitter/X-over-MCP, and local file tools.
   - [`references/chainlit-and-ui.md`](references/chainlit-and-ui.md) for Chainlit callback injection and UI session patterns.
   - [`references/logging-and-output.md`](references/logging-and-output.md) for HTML logs, quiet mode, streaming, and status output.
   - [`references/troubleshooting.md`](references/troubleshooting.md) for common event-loop, credential, subprocess, Chainlit, logging, and quiet-mode failures.
3. Prefer async APIs inside any async app, Chainlit callback, notebook, or test: use `get_tool_async()` / `get_tools_async()` and never wrap them in `asyncio.run()` from a running loop.
4. Keep external-service checks bounded: verify imports, environment variables, local `--help` availability, and schemas before making live network calls. Do not require network for smoke tests.
5. When validating MCP availability without external side effects, run the bundled smoke script:

```bash
python scripts/mcp_tool_smoke.py
```

## Minimal decision table

| Need | Preferred Langroid entry point | Reference |
| --- | --- | --- |
| Build one MCP tool inside async code | `await get_tool_async(server, "tool_name")` | [`references/mcp-workflows.md`](references/mcp-workflows.md) |
| Build all MCP tools | `await get_tools_async(server)` | [`references/mcp-workflows.md`](references/mcp-workflows.md) |
| Customize MCP result formatting | subclass generated tool or use `@mcp_tool` with `handle_async()` | [`references/mcp-workflows.md`](references/mcp-workflows.md) |
| Web search tool | enable `DuckduckgoSearchTool`, `TavilySearchTool`, `ExaSearchTool`, `GoogleSearchTool`, or `SeltzSearchTool` | [`references/search-and-file-tools.md`](references/search-and-file-tools.md) |
| Safe local file read/write/list | `ReadFileTool.create`, `WriteFileTool.create`, `ListDirTool.create` | [`references/search-and-file-tools.md`](references/search-and-file-tools.md) |
| Chainlit UI around an agent/task | `ChainlitAgentCallbacks` or `ChainlitTaskCallbacks` | [`references/chainlit-and-ui.md`](references/chainlit-and-ui.md) |
| Suppress terminal noise or inspect logs | `quiet_mode`, `async_stream_quiet`, `TaskConfig(enable_html_logging=...)` | [`references/logging-and-output.md`](references/logging-and-output.md) |
