---
name: outputs-and-messages
description: "Guides agents designing Pydantic AI output contracts, structured
  outputs, output functions, multimodal message content, and message history
  serialization or replay."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Outputs and Messages

Use this sub-skill when a task is about what an agent returns, how output is validated, how model messages are represented, or how previous messages should be serialized, trimmed, replayed, or adapted for application frontends.

## Read First

- Read [references/output-api.md](references/output-api.md) when choosing `output_type`, `TextOutput`, `ToolOutput`, `NativeOutput`, `PromptedOutput`, `StructuredDict`, output functions, or output validators.
- Read [references/message-formats.md](references/message-formats.md) when handling `ModelMessage` objects, multimodal content, tool-call/return message pairs, JSON persistence, or UI adapter message boundaries.
- Read [references/troubleshooting.md](references/troubleshooting.md) when structured outputs retry unexpectedly, a model returns text instead of JSON, message history replay fails, or media/message parts do not round-trip.
- Run [scripts/output_schema_smoke.py](scripts/output_schema_smoke.py) for a local no-network smoke check that structured output, `TestModel`, message serialization, and multimodal parts are importable and usable.

## Route Elsewhere

- Use `../agent-core/` for `Agent.run`, `run_sync`, `run_stream`, `iter`, dependencies, usage limits, basic message-history continuation, and testing strategy.
- Use `../tools-and-toolsets/` when deciding whether something should be a normal function tool/toolset instead of a final output function.
- Use `../models-and-providers/` for provider-specific native structured-output compatibility, model profiles, settings, optional extras, and provider media support.
- Use `../cli-and-apps/` or `../mcp-and-integrations/` for CLI/web rendering, AG-UI, Vercel AI, MCP, durable execution, or deep adapter wiring beyond message boundary rules.

## Fast Decisions

- Prefer a Pydantic model/dataclass/`TypedDict` output type for ordinary typed final answers; omit `str` when plain text must not be accepted as a fallback.
- Prefer default tool output or `ToolOutput(...)` for provider-portable structured output; use `NativeOutput(...)` only after checking provider compatibility.
- Use `PromptedOutput(...)` as the broadest fallback for models without reliable tool or native structured output, accepting lower enforcement.
- Use output functions when the final model-provided arguments need app-side validation, transformation, `ModelRetry`, or handoff logic that ends the run.
- Persist histories with `ModelMessagesTypeAdapter` or result JSON helpers, and preserve complete tool-call/return adjacency when trimming or replaying history.
