---
name: agent-core
description: "Routes local OpenHands SDK agent construction, LLM configuration,
  conversation lifecycle, callbacks, persistence, interruption, condensation,
  and title-generation workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Agent Core

Use this sub-skill for the local SDK path: creating `LLM`, `Agent`, `Conversation`, `LocalConversation`, `RemoteConversation`, and `AgentContext` objects; configuring callbacks, tokens, tags, persistence, interrupts, condensation, and model/provider behavior; and understanding how conversations move through the SDK.

## What this route owns

- `LLM` construction, provider selection, and model settings.
- `Agent` creation and tool lists, including `mcp_config`, `system_prompt`, `condenser`, and `critic`.
- `Conversation` factory routing to `LocalConversation` or `RemoteConversation`.
- Conversation callbacks, token callbacks, `ConversationState`, persistence, tags, and observability metadata.
- Interrupt and pause behavior, condensation recovery, title generation, and async/sync parity.

## Start here

Read [`references/api-reference.md`](references/api-reference.md) for the concrete constructor signatures and major attributes. Read [`references/workflows.md`](references/workflows.md) for common local and remote conversation flows. Read [`references/troubleshooting.md`](references/troubleshooting.md) when a conversation fails, pauses unexpectedly, or runs with the wrong model/provider.

## Typical triggers

- "Create an agent that edits files and runs shell commands."
- "Use a local conversation with custom callbacks."
- "Why did the run pause or get interrupted?"
- "How do I attach persistence, tags, or a custom condenser?"
- "How do I generate or rename a conversation title?"

## Cross-links

- For skill loading, plugins, hooks, MCP, and secrets, go to [`../extensions/SKILL.md`](../extensions/SKILL.md).
- For built-in tool names, registration, and presets, go to [`../built-in-tools/SKILL.md`](../built-in-tools/SKILL.md).
- For remote workspace and agent-server transport details, go to [`../remote-runtime/SKILL.md`](../remote-runtime/SKILL.md).

## Minimum workflow

1. Choose a model and build `LLM`.
2. Build an `Agent` with the desired tools, skills, and optional MCP or condenser settings.
3. Create a `Conversation` with a local path or `Workspace`.
4. Add callbacks or tags if the use case needs observability.
5. Call `send_message()` and `run()` or use the async methods in a matching async flow.
6. Use `interrupt()`/`close()`/persistence APIs when the conversation must stop or resume later.

## Do not bury these details here

- Full API tables belong in `references/api-reference.md`.
- End-to-end examples belong in `references/workflows.md`.
- Error handling and recovery belong in `references/troubleshooting.md`.
