---
name: agent-runtime
description: "Owns Upsonic's core agent execution surface: Agent, Task, Direct,
  graph/runtime primitives, streaming, structured output, and run control."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# agent-runtime

Use this route for the core execution APIs: `Agent`, `Task`, `Direct`, graph/runtime primitives, streaming, structured output, timeouts, partial results, and run control.

## Include

- `Agent` and `Task` orchestration.
- `Direct` for direct model calls without the full agent pipeline.
- Runtime primitives such as `Graph`, run state, context handling, streaming, and cancellation/timeout behavior.
- Structured-output and cache-related runtime behavior when the question is about a task run rather than the provider or storage backend.

## Exclude

- Model/provider selection and credentials → [models-and-providers](../models-and-providers/SKILL.md)
- Tools, MCP, or agent-as-tool wiring → [tools-and-mcp](../tools-and-mcp/SKILL.md)
- Session persistence and chat history → [chat-memory-storage](../chat-memory-storage/SKILL.md)
- Policies, reflection, reliability, tracing, or evals → [quality-safety-governance](../quality-safety-governance/SKILL.md)
- Teams, autonomous agents, prebuilt agents, Ralph, and simulation loops → [teams-autonomous-prebuilt](../teams-autonomous-prebuilt/SKILL.md)

## Start here

- [references/api-reference.md](references/api-reference.md)
- [references/troubleshooting.md](references/troubleshooting.md)
- [scripts/inspect_runtime_api.py](scripts/inspect_runtime_api.py)
