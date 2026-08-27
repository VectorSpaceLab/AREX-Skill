---
name: core-runtime
description: "Define and run OpenAI Agents Python core agents, interpret run
  results and streams, configure core Runner behavior, and resume interrupted
  RunState flows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Core Runtime

Use this sub-skill when the task is to define a plain `Agent`, call `Runner.run`, `Runner.run_sync`, or `Runner.run_streamed`, inspect `RunResult` / `RunResultStreaming`, reason about `new_items` and stream events, configure core `RunConfig` behavior, or resume a paused `RunState` after human approval.

## Start Here

- For verified signatures and object relationships, read [references/api-reference.md](references/api-reference.md).
- For implementation recipes, read [references/workflows.md](references/workflows.md).
- For failure diagnosis, read [references/troubleshooting.md](references/troubleshooting.md).
- To inspect the installed/core import surface without network calls, run [scripts/inspect_core_runtime.py](scripts/inspect_core_runtime.py).

## Routing Boundaries

- Stay here for agent construction, Runner loops, sync/async/streamed execution, `RunResult` properties, `RunState` pause/resume, `previous_response_id`, `conversation_id`, `max_turns`, `call_model_input_filter`, and stream-event interpretation.
- Route function tools, handoffs, approvals declarations, guardrails, and tool-specific error policy depth to ../tools-handoffs-guardrails/SKILL.md.
- Route persistent session backends and memory-store choices to ../sessions-memory/SKILL.md.
- Route provider/model transport, OpenAI provider setup, websocket provider selection, and model retries to ../models-providers/SKILL.md.
- Route tracing/export details to ../tracing-observability/SKILL.md.
- Route sandbox-specific `RunConfig.sandbox`, manifests, and sandbox agents to ../sandbox-agents/SKILL.md.

## Core Decisions

- Prefer `Runner.run` inside async applications and `Runner.run_sync` only from synchronous code with no active event loop.
- Use `Runner.run_streamed` when UI code needs raw model deltas or semantic progress events; keep consuming `stream_events()` until it finishes.
- Use exactly one conversation-state strategy per turn: local `to_input_list()`, a `session`, `conversation_id`, or `previous_response_id`.
- Resume approvals with `result.to_state()`, `state.approve(...)` / `state.reject(...)`, then pass the `RunState` back to the same original top-level agent.
- Inspect `new_items` for SDK-rich metadata and `to_input_list()` for replay-ready Responses input items.

## Safety Notes

- Do not tell future agents to run original repo examples or tests; the patterns are distilled into the bundled references.
- Do not store API keys, local paths, or environment details in `RunState.context` unless the application intentionally wants them serialized.
- If a streamed run is canceled or paused for approval, drain `stream_events()` before inspecting final result fields or resuming.
