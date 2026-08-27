---
name: tools-and-mcp
description: "Guides agents using CrewAI tools, crewai_tools exports, custom
  BaseTool and CrewStructuredTool patterns, MCP server adapters, tool
  publishing, integrations, optional dependencies, and credential boundaries."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Tools and MCP

Use this sub-skill when work involves official `crewai_tools`, custom CrewAI tools, `BaseTool`, `CrewStructuredTool`, MCP servers, tool publishing, enterprise/action adapters, or deciding which tool path is safe when credentials or optional packages are missing.

## Route First

- For assigning tools to `Agent` or `Task`, kickoff behavior, or crew process design, use [`core-runtime`](../core-runtime/SKILL.md).
- For RAG storage, knowledge sources, vector DB architecture, or embedding setup behind search tools, use [`memory-knowledge-and-rag`](../memory-knowledge-and-rag/SKILL.md).
- For LLM provider keys, model routing, base URLs, or function-calling model compatibility, use [`llm-and-providers`](../llm-and-providers/SKILL.md).
- For root-level CrewAI scenario selection, use the parent [`crewai`](../../SKILL.md) router.

## Workflows

1. Identify whether the user needs a built-in tool export, a custom tool, an MCP integration, or a publishable tool package.
2. Check [`tool-catalog.md`](references/tool-catalog.md) for installed export families, safe local defaults, and categories that usually require network credentials.
3. Use [`custom-tools.md`](references/custom-tools.md) for `BaseTool`, `@tool`, `CrewStructuredTool`, typed output, cache, max-usage, and publishing patterns.
4. Use [`mcp-reference.md`](references/mcp-reference.md) for `Agent(mcps=[...])`, `MCPServerStdio`, `MCPServerHTTP`, `MCPServerSSE`, `MCPServerAdapter`, filtering, timeouts, and cleanup.
5. Use [`optional-dependencies.md`](references/optional-dependencies.md) before instantiating tools that may need extras, SDKs, browser runtimes, API keys, or enterprise tokens.
6. Use [`troubleshooting.md`](references/troubleshooting.md) when tool calls fail from missing credentials, schema validation, path safety, MCP transport issues, or import mistakes.

## Safe Defaults

- Prefer local, deterministic tools such as `FileReadTool`, `DirectoryReadTool`, or a small custom `BaseTool` when API keys are missing.
- Do not instantiate tools that make network, cloud, browser, database, or LLM calls unless the user explicitly provided credentials and approved the side effects.
- Keep secrets in environment variables or runtime config; never place real tokens in tool descriptions, examples, logs, or generated skill content.
- For MCP, prefer the native `mcps` field on `Agent` for normal use and reserve `MCPServerAdapter` for manual lifecycle control.
- Filter MCP tools to the minimum allowed set and document local process, file-system, and remote-server security assumptions.

## Bundled Script

- [`scripts/list_tool_exports.py`](scripts/list_tool_exports.py) safely imports `crewai_tools`, lists exported names and inferred categories, and performs no API, LLM, network, credential, file mutation, or tool-instantiation work.

## Usability Targets

- Choose a safe, keyless tool pattern when a requested search or web tool lacks its third-party API key.
- Migrate a local MCP stdio server configuration into a CrewAI agent with tool filtering, timeout, lifecycle, and security notes.
