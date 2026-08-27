---
name: agent-core
description: "Guides agents building, running, streaming, testing, and composing
  Pydantic AI Agent instances with dependencies, instructions, history, usage
  limits, specs, and handoffs."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Agent Core

Use this sub-skill when the task is to create, configure, run, stream, persist, test, or compose `pydantic_ai.Agent` instances.

## Read First

- Read [references/agent-api.md](references/agent-api.md) when choosing `Agent(...)`, `run*`, `iter`, retry, usage-limit, dependency, or `AgentSpec` parameters.
- Read [references/workflows.md](references/workflows.md) when implementing a minimal agent, typed dependencies, streaming/events, message-history continuation, multi-agent handoff, or declarative spec loading.
- Read [references/testing-and-debugging.md](references/testing-and-debugging.md) when writing deterministic tests with `TestModel`, `FunctionModel`, `Agent.override`, `capture_run_messages`, usage limits, or diagnosing common runtime failures.
- Run [scripts/agent_smoke.py](scripts/agent_smoke.py) when you need a safe, no-network import/construction/run smoke check for the installed Pydantic AI package.

## Core Routing

- Build agents with `Agent(model, instructions=..., deps_type=..., output_type=...)`; prefer `instructions` over `system_prompt` unless previous system prompts must be retained in `message_history`.
- Use `RunContext[Deps]` only as the first parameter for dynamic instructions, system prompts, tools, output validators, and history processors that need runtime context.
- Use `run()` for async full results, `run_sync()` for synchronous callers, `run_stream()` for final-output streaming, `run_stream_events()` for all raw model/tool events, and `iter()` for graph-node control.
- Use `message_history=result.new_messages()` or `result.all_messages()` to continue a conversation; route deep message serialization, trimming, and output-tool handoff details to `../outputs-and-messages/SKILL.md`.
- Use `Agent.from_spec()`, `Agent.from_file()`, or the `spec=` run/override parameter when agent configuration is declarative YAML/JSON/dict.
- Use `TestModel`, `FunctionModel`, `models.ALLOW_MODEL_REQUESTS = False`, and `Agent.override(...)` for tests; never rely on live provider credentials for unit tests.

## Boundaries

- For function tools, tool schemas, toolsets, approvals, deferred tools, and tool search, read `../tools-and-toolsets/SKILL.md`.
- For structured output modes, output functions, message-part serialization, multimodal inputs, and final-output handoff history, read `../outputs-and-messages/SKILL.md`.
- For provider-prefixed model strings, optional provider extras, model settings depth, wrappers, native provider tools, and embeddings, read `../models-and-providers/SKILL.md`.
- For MCP, capabilities/hooks depth, durable execution, Logfire, A2A, and UI adapters beyond core agent methods, read `../mcp-and-integrations/SKILL.md`.
- For `Agent.to_cli()`, `Agent.to_web()`, `pai`, `clai`, and application entry points, read `../cli-and-apps/SKILL.md`.

## Non-Negotiables

- Keep examples deterministic unless explicitly writing production provider code; use provider-prefixed model strings such as `openai:gpt-5.2` only where live provider access is intentional.
- Do not use deprecated split retry kwargs (`tool_retries`, `output_retries`) in new code; use `retries={'tools': N, 'output': M}` at construction and `retries={'output': N}` per run.
- Do not add legacy `history_processors=` in new agents; use `capabilities=[ProcessHistory(...)]` for history processing and route advanced capability design to `mcp-and-integrations`.
- Do not assume `run_stream()` executes tool calls after an early final-looking text/output; use `run_stream_events()` or `iter()` when every tool event matters.
