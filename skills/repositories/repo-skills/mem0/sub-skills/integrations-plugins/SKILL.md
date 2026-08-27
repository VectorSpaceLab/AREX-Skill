---
name: integrations-plugins
description: "Use Mem0 framework, agent, and editor integrations: Vercel AI SDK
  provider, MCP/plugin setup for Claude Code, Cursor, Codex, OpenCode,
  Antigravity, OpenClaw, Pi Agent, lifecycle hooks, slash commands, and
  framework cookbooks."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# integrations-plugins

Use this sub-skill when a task mentions Mem0, `mem0ai`, a memory layer, persistent agent memory, Vercel AI SDK memory, `@mem0/vercel-ai-provider`, `createMem0`, MCP setup, Claude Code/Cursor/Codex/OpenCode/Antigravity plugins, OpenClaw memory, Pi Agent memory, slash commands, lifecycle hooks, framework agents, or cookbook-style integration work.

## Route First

- Use this sub-skill for integration package setup, provider wrapping, framework routes, MCP server config, plugin install choices, lifecycle hooks, slash commands, OpenClaw, Pi Agent, and agent/editor troubleshooting.
- Use [Vercel AI Provider](references/vercel-ai-provider.md) for `createMem0`, `addMemories`, `retrieveMemories`, `getMemories`, `searchMemories`, AI SDK v6 routes, streaming, tool calls, sources, file prompts, and user scoping.
- Use [Editor and Agent Plugins](references/editor-agent-plugins.md) for Claude Code/Cowork, Cursor, Codex, OpenCode, Antigravity, OpenClaw, Pi Agent, MCP-only vs full-plugin installs, hook behavior, slash commands, and duplicate registration checks.
- Use [Framework Integrations](references/framework-integrations.md) for LangChain, LangGraph, LlamaIndex, CrewAI, AutoGen, Agno, OpenAI Agents SDK, Google ADK, and similar retrieve-generate-store patterns.
- Use [Troubleshooting](references/troubleshooting.md) for install/import, environment variables, duplicate tools, unsupported package versions, plugin hook failures, MCP auth, memory scope, and workflow-specific failures.

## Sibling Boundaries

- Route direct Python/TypeScript SDK CRUD/search, `MemoryClient`, `Memory`, async clients, filters, exports, and feedback to `../sdk-memory/SKILL.md`.
- Route OSS provider, vector store, embedder, LLM, reranker, graph-memory, Qdrant/PGVector dimensions, and optional dependency selection to `../provider-configuration/SKILL.md`.
- Route terminal-only Mem0 CLI workflows, `mem0 init/add/search/list`, agent JSON output, and CLI import/export to `../cli-memory/SKILL.md`.
- Route self-hosted Mem0 server, Docker Compose, REST deployment, OpenMemory API/UI/MCP hosting, auth, migrations, and operational backups to `../self-hosted-openmemory/SKILL.md`.

## Fast Decision Tree

1. Vercel/Next.js route or AI SDK model wrapper? Use `createMem0` from `@mem0/vercel-ai-provider` v3.0.0 with AI SDK v6 and preserve stable `user_id` or equivalent entity scope.
2. Claude/Cursor/Codex/OpenCode/Antigravity request? Decide between full plugin and MCP-only. Full plugin gives hooks/skills; MCP-only gives memory tools only.
3. Duplicate or missing agent tools? Inspect config first with `python scripts/validate_mcp_config.py`; do not add a second `mem0` server blindly.
4. OpenClaw or Pi Agent? Use the plugin-native memory backend/extension and its own command set; do not replace those workflows with generic SDK snippets unless the task asks for custom app code.
5. LangChain/LangGraph/LlamaIndex/CrewAI/Agents framework? Keep the framework’s agent runner intact and add Mem0 as a scoped memory layer around retrieval and storage.

## Bundled Scripts

- `python scripts/validate_mcp_config.py --help` explains read-only MCP/plugin config checks for Claude, Cursor, Codex, OpenCode, and generic JSON/TOML config files.
- `node scripts/check_vercel_mem0_usage.mjs --help` statically checks TypeScript/JavaScript files for Mem0 Vercel provider imports, `createMem0` usage, user scoping, API key patterns, and unsupported AI SDK hints.

## Working Rules

- Never print or hardcode real `MEM0_API_KEY`, provider API keys, MCP bearer tokens, or personal memory contents.
- Prefer environment variables and config templates; redact secret values in diagnostics.
- Treat hook installers, auto-capture scripts, and plugin setup commands as side-effectful. Use the bundled validators before proposing config edits.
- Do not tell future agents to run original repo examples, tests, or plugin scripts. Use the bundled references and scripts here.
- Confirm destructive memory operations, global-scope deletes, hook rewrites, and project-wide plugin config changes before acting.
