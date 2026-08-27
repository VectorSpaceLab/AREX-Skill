# Chat and LLM flow

## Entry points

- `process_message` is the top-level request path. It validates the request, builds chat history, stages files, reserves message IDs, sets processing status, and hands off to `_run_models`.
- `build_chat_turn` assembles a detached `ChatTurnSetup` for the workers. It resolves the session, user identity, LLMs, search params, available files, context files, and stop signal.
- `_run_models` runs one worker per model inside a `ThreadPoolExecutor`, then drains the merged packet queue in arrival order.
- `run_llm_loop` is the general chat agent loop.
- `run_deep_research_llm_loop` is the deep-research branch.

## Context order and precedence

- Custom persona prompt beats project instructions.
- If a persona replaces the base system prompt, the custom-agent slot is omitted instead of being layered on top.
- Custom persona files supersede project files.
- The default persona inside a project uses the project files and project instructions.
- User uploads are point-in-time inclusions; project context is treated as persistent enough to stay close to the end of the prompt window.
- File IDs are collected before summary truncation so older files remain available to the FileReader tool.
- Query-processing hooks run before the user message is persisted.
- Search params depend on persona/project/context-file state and can suppress a forced search tool when search is disabled.

Prompt order to preserve:

1. system prompt
2. truncated history before the last user message
3. custom-agent prompt
4. context-file documents or file metadata
5. forgotten-file metadata
6. last user message
7. messages after the last user message
8. reminder message

## Streaming and state

- `ChatStateContainer` is state only. It accumulates tool calls, reasoning tokens, answer tokens, citation mappings, emitted citation numbers, and pre-answer latency.
- `Emitter` is transport only. It tags packets with `model_index` and enqueues them. Do not put policy or branching logic in it.
- `AnswerStream` can yield `CreateChatSessionID`, `MessageResponseIDInfo`, `MultiModelMessageResponseIDInfo`, streamed `Packet`s, `StreamingError`, and terminal `OverallStop` packets.
- Frontend `turn_index` is a rendering slot, not the backend turn number.

## Multi-model, stop, resume

- Each model gets its own worker thread and its own short-lived DB sessions.
- Workers write into a shared merged queue; the main thread yields packets as they arrive.
- Stop handling comes from Redis-backed cancel state. On disconnect, partial state is saved, an `OverallStop(stop_reason="user_cancelled")` packet is emitted, and the drain loop returns.
- `drain_done` lets emitters stop blocking when the drain loop exits early.
- Single-model and multi-model share the same execution path.
- Multi-model turns reserve multiple assistant message IDs up front.

## Deep research

- Deep research is only supported on the single-model path.
- It is not supported for projects.
- It uses the deep-research orchestration flow plus the search/web/open_url tool family.
- Skip the clarification step when the last assistant message was already a clarification question.

## Tracing

- Wrap chat and deep-research loops with `trace(...)` and `ChatTraceMetadata`.
- Every LLM invocation must be tagged with an `LLMFlow` value.
- Use `llm_generation_span` for calls that already go through an `LLM` subclass.
- Use `traced_llm_call` for direct provider or model-server calls.
- Missing flow tags show up as `LLMFlow.UNTAGGED_*` sentinels. Treat those as instrumentation bugs.

## Test focus

- Unit: prompt ordering, file precedence, reserved IDs, orphaned tool-response cleanup, stop helpers.
- Integration: full streaming turn, multi-model interleaving, deep research, partial-stop persistence.
- External-dependency unit: provider/tool boundary checks and tracing assertions when a real backend call is needed.
