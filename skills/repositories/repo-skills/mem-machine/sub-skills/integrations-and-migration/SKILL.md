---
name: integrations-and-migration
description: "Use MemMachine framework integrations and migration tooling for
  LangGraph, LangChain, LlamaIndex, CrewAI, AWS Strands, OpenClaw, Dify, n8n,
  FastGPT, example agents, and ChatGPT/export imports."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Integrations And Migration

Use this sub-skill when a task asks to connect MemMachine to an agent framework
or platform, adapt an example memory-powered agent, or migrate conversation
exports into MemMachine. Common signals include LangGraph, LangChain,
LlamaIndex, CrewAI, AWS Strands, OpenClaw, Dify, n8n, FastGPT, simple chatbot,
OpenAI/Qwen examples, ChatGPT export, OpenAI export, LoCoMo, and conversation
history import.

## Route Within This Sub-skill

- Read [framework-integrations.md](references/framework-integrations.md) for
  integration patterns, prerequisites, validation checks, and route selection
  across supported frameworks/platforms.
- Read [migration-tools.md](references/migration-tools.md) for ChatGPT/export
  migration planning, local dry-runs, upload prerequisites, and duplicate/rate
  limit handling.
- Read [troubleshooting.md](references/troubleshooting.md) for missing framework
  packages, server/auth errors, malformed export files, duplicate memories, and
  unsafe live operations.
- Run [chatgpt_export_probe.py](scripts/chatgpt_export_probe.py) to inspect a
  local export JSON shape without uploading anything.

## Integration Decision Flow

1. Identify the host framework/platform and whether it uses Python, TypeScript,
   HTTP, plugin manifests, or MCP.
2. Confirm a MemMachine API server or cloud endpoint exists and the user can
   provide project context and auth.
3. Pick the lightest integration path:
   - Python app code: Python SDK or framework wrapper.
   - LangGraph graph: `MemMachineTools` or add/search tool factories.
   - Tool-capable local clients: MCP stdio/HTTP.
   - Browser/no-code platforms: platform-specific plugin or REST integration.
   - Node/TypeScript app: TypeScript REST client.
4. Start with read-only health/config checks; run add/search only after writes
   are approved.

## Migration Decision Flow

1. Run a local-only export probe.
2. Decide what memories should be imported and which metadata should separate
   user/session/source.
3. Create or confirm the target MemMachine project.
4. Upload in small batches with retry/rate-limit handling.
5. Verify with targeted searches and counts.
6. Record duplicate/skipped/failed rows without exposing private conversation
   content unnecessarily.

## Cross-links

- Use [python-sdk-and-cli](../python-sdk-and-cli/SKILL.md) for Python SDK method
  details, CLI command flags, filters, and LangGraph helper signatures.
- Use [server-configuration-and-memory-engines](../server-configuration-and-memory-engines/SKILL.md)
  for self-hosted server, storage, provider, REST, and MCP configuration.
- Use [typescript-rest-client](../typescript-rest-client/SKILL.md) for Node/TS
  package usage and TypeScript app examples.

## Safety Rules

- Do not run provider-backed example agents, no-code plugin actions, or live
  memory uploads without explicit endpoint, credentials, target project, and
  side-effect approval.
- Do not paste private conversation export contents into answers. Summarize
  counts, schema problems, and redacted examples.
- Treat benchmark/evaluation scripts as reference-only unless the user has
  provided datasets, services, provider credentials, and runtime budget.
