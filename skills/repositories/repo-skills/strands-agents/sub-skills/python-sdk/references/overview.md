# Python SDK overview

This reference distills the Strands Python SDK into the smallest usable mental model for future agents.

## Source basis

Evidence distilled into this sub-skill includes Python SDK contributor guidance, package metadata, developer docs, source structure, tests, and verified package-inspection facts. Use the bundled references below rather than reopening the original evidence files unless the downstream task is editing those files directly.

## Package identity

- Project name: `strands-agents`
- Python floor: `>=3.10`
- Build backend: `hatchling` with `hatch-vcs`
- Public package root: `strands`
- Main source tree: `strands-py/src/strands/`
- Primary unit tests: `strands-py/tests/`
- Optional live tests: `strands-py/tests_integ/`

## What this sub-skill owns

| Area | What it covers |
| --- | --- |
| Agent loop | `Agent`, event loop, concurrency, checkpointing, structured output, tool execution, direct tool calls |
| Tools | `@tool`, `ToolContext`, tool loading, schema generation, hot reload, MCP tool wrappers |
| Models | provider classes, config objects, streaming, token counting, structured output, error translation |
| Conversations | `SlidingWindowConversationManager`, `SummarizingConversationManager`, `NullConversationManager`, context manager facade |
| Sessions | file, S3, repository, and snapshot session managers |
| Memory | `MemoryManager`, memory stores, injection, extraction, search/add tools |
| Hooks and interventions | lifecycle callbacks, event naming, intervention actions |
| Plugins | `Plugin`, `MultiAgentPlugin`, model plugin, context offloader, goal loop, skills |
| Sandbox | host default, POSIX shell, Docker, SSH backends |
| Telemetry | tracing, metrics, redaction, span helpers |
| Multi-agent | graph, swarm, A2A helpers, shared result/state objects |
| Experimental features | checkpointing and bidirectional streaming modules |

## Core runtime model

- `Agent` is the main entry point.
- When `model=None`, the agent falls back to Bedrock.
- When `model` is a string, the SDK wraps it in a Bedrock model by model id.
- `tool` turns a Python function into an SDK tool and still allows direct Python calls.
- `MCPClient` is the bridge to external MCP tool servers.
- `MemoryManager` is a plugin that adds search/add tools and can also inject or extract memory context.
- `SessionManager` is a hook provider that persists agent state and conversation data.
- `SnapshotSessionManager` stores one agent as a snapshot; it does not replace a full session manager for every use case.
- `Sandbox` is the execution environment for command, code, and file operations; the host default is explicitly non-isolated.
- `GraphBuilder` and `Swarm` are the two primary multi-agent orchestrators.

## Public-surface discipline

- Public exports are defined in `__all__` files.
- Heavy or optional provider modules stay lazy-loaded.
- Provider-backed integrations, AWS-backed storage, and live-network checks are optional unless a task explicitly needs them.
- Keep docs-site, TypeScript SDK, and docs-search server work in their own sub-skills instead of widening this one.
