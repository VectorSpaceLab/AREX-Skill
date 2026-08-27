---
name: agent-core
description: "AgentScope agent, toolkit, permission, event, and local
  skill-loading workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# agent-core

Use this sub-skill for the day-to-day AgentScope SDK surface: agents, toolkits, built-in tools, task tools, permissions, message and event streams, and local skills.

## Read first

- `references/api-reference.md` for the verified constructors, exported classes, and key defaults.
- `references/workflows.md` for end-to-end agent setup patterns.
- `references/troubleshooting.md` for import, permission, tool, and skill-loading failures.

## Typical triggers

- Build an `Agent` with a `Toolkit` and a model.
- Add or debug built-in tools like Bash, Read, Write, Edit, Glob, Grep, or PowerShell.
- Use task tools, MCP tools, or function-wrapped tools.
- Load local skills with `LocalSkillLoader` and inspect skill instructions.
- Handle `reply_stream` events, interruption, or structured output.

## What belongs here

- `Agent`, `ContextConfig`, `InjectionConfig`, `ModelConfig`, `ReActConfig`
- `Toolkit`, `ToolGroup`, `FunctionTool`, `MCPTool`, `ToolBase`
- `Msg`, `UserMsg`, `AssistantMsg`, `SystemMsg`, event classes, permission types, state types
- `Skill`, `SkillLoaderBase`, `LocalSkillLoader`
- task tools and built-in shell/file/search helpers

## What does not belong here

- Provider selection, credentials, or model-family specifics → `provider-connectors`
- RAG, vector stores, or memory backends → `rag-memory`
- Service deployment and backend wiring → `service-platform`
- Workspace/sandbox backend setup → `workspace-sandboxes`

## Use pattern

1. Start with the `Agent` and the smallest `Toolkit` that covers the task.
2. Add permission or injection config only when the workflow needs it.
3. Read `reply_stream` events when you need tool-call or interruption detail.
4. Use `LocalSkillLoader` and `Toolkit(skills_or_loaders=...)` when the task depends on reusable skills.
5. Escalate to the other sub-skills only when the problem is actually provider-, retrieval-, service-, or workspace-specific.

## Shared diagnostics

- Run `../../scripts/check_env.py` first if imports or exports look stale.
- Read `references/troubleshooting.md` before editing if the failure looks like a config or permission issue.

## Cross-links

- If the model itself is the problem, switch to `provider-connectors`.
- If the task uses a sandboxed workspace backend, switch to `workspace-sandboxes`.
- If the task is about retrieval or memory, switch to `rag-memory`.
