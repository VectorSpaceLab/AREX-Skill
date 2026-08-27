---
name: agent-core
description: "Use AtomicAgent, AgentConfig, BaseIOSchema, ChatHistory,
  SystemPromptGenerator, hooks, token counting, and multimodal content to build
  typed Atomic Agents."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Agent Core

Use this subskill when a task is about building or debugging the core Atomic Agents framework API: typed schemas, agent construction, history, prompts, streaming, async calls, hooks, multimodal content, or token counting.

## Read first

- `references/api-reference.md` for the public classes, signatures, and object relationships.
- `references/workflows.md` for quickstart, memory, streaming, and context-provider recipes.
- `references/troubleshooting.md` for docstring, client-wrapper, history, role, and trimming failures.
- `scripts/agent_core_smoke.py` for a safe offline smoke check.

## Owns

- `AtomicAgent` and `AgentConfig` construction.
- `BaseIOSchema` contracts and docstring requirements.
- `ChatHistory`, `BaseChatHistory`, `SystemPromptGenerator`, and `BaseDynamicContextProvider`.
- Sync, async, streaming, and async-streaming agent execution.
- Hooks, token counting, context trimming, and multimodal history serialization.
- `VideoURL` and other core content-shaping helpers that belong to the agent layer.

## Does not own

- `BaseTool`, `BaseResource`, `BasePrompt`, Atomic Forge, or the `atomic` CLI; use `../tooling-and-forge/SKILL.md`.
- MCP transport and dynamic tool discovery; use `../mcp-integrations/SKILL.md`.
- Example project cataloging; use `../example-workflows/SKILL.md`.
- Repo maintenance, tests, docs, or release commands; use `../repo-development/SKILL.md`.

## Common triggers

- "How do I create a typed agent?"
- "Why does my schema need a docstring?"
- "How do I keep chat history across turns or custom backends?"
- "Why are token counts or context trimming behaving oddly?"
- "How do I add a context provider or hook?"
- "How do I handle multimodal content in history?"
- "Why does the agent need different sync/async methods?"
