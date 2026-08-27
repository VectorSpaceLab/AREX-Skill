---
name: run-rails
description: "Run configured NeMo Guardrails through Python APIs, CLI chat and
  servers, OpenAI-compatible endpoints, streaming, state and thread handling,
  and LangChain integrations."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# run-rails

Use this sub-skill when a guardrails configuration already exists and you need to run it, serve it, stream it, or integrate it into LangChain or LangGraph.

## Route here for

- Python runtime choice: `Guardrails`, `LLMRails`, `IORails`, `generate`, `check`, `stream_async`, `generate_events`, `process_events`.
- CLI usage: `nemoguardrails chat`, `server`, `actions-server`, `convert`.
- HTTP usage: `/v1/chat/completions`, `/v1/checks`, `/v1/rails/configs`, `/v1/models`, `/v1/health`, `/v1/challenges`.
- LangChain and LangGraph wrapping, tool-call handling, and framework selection.
- Local no-provider smoke checks before live provider or server deployment work.

## Route away

- Config authoring, rail catalog design, prompts, Colang, custom actions, or provider registration -> `../configure-rails/SKILL.md`
- Eval, tracing, metrics, telemetry, or reporting -> `../evaluate-and-observe/SKILL.md`
- Source checkout edits, tests, pre-commit, docs authoring, or PR policy -> `../repo-development/SKILL.md`
- Install, import, or CLI discovery only -> `../setup-and-basics/SKILL.md`

## Important runtime rules

- `Guardrails` tries `IORails` first when the config and arguments are compatible, then falls back to `LLMRails` unless `require_iorails=True`.
- `LLMRails` is the direct Colang runtime. Use it when you need `process_events_async`, `generate_events`, or explicit state control.
- `IORails` is stateless, Colang 1.0 only, and supports only the narrow input/output/tool rail set it can serve.
- The top-level `LLMRails` import can be aliased to the wrapper when `NEMO_GUARDRAILS_IORAILS_ENGINE` is set; if behavior looks unexpected, check that compatibility mode first.

## Working order

1. Read `references/python-api.md` for engine selection, method signatures, message/state shapes, and return shapes.
2. Read `references/cli-and-server.md` for CLI flags, endpoint contracts, and HTTP guardrails fields.
3. Read `references/integrations.md` for RunnableRails, LangGraph, and tool-call patterns.
4. Run `scripts/deterministic_chat_smoke.py` for a no-provider local chat/stream check.
5. Run `scripts/server_schema_smoke.py` for schema normalization plus health/config discovery.
6. Use `references/troubleshooting.md` when a request fails or a runtime restriction appears.

## Safe bundled helpers

- `python scripts/deterministic_chat_smoke.py`
- `python scripts/deterministic_chat_smoke.py --json`
- `python scripts/server_schema_smoke.py`
- `python scripts/server_schema_smoke.py --json`

These helpers use only bundled deterministic checks and public package APIs. They do not call live providers or depend on the source checkout.
