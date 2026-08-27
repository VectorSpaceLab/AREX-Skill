---
name: nemoguardrails
description: "Route NVIDIA NeMo Guardrails package work across installation,
  config and Colang authoring, runtime APIs and servers,
  evaluation/observability, and source-checkout development."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# nemoguardrails

Use this repo skill when the task names NVIDIA NeMo Guardrails, the `nemoguardrails` Python package, Colang, rails configs, guardrail catalog rails, Guardrails/LLMRails runtime APIs, the NeMo Guardrails server, evaluation CLI, tracing/telemetry behavior, or maintenance of the NeMo Guardrails source checkout.

## Fast routing

| User need | Read |
| --- | --- |
| Install the package, choose extras, verify imports, check CLI availability, or diagnose optional dependency import errors | [`sub-skills/setup-and-basics/SKILL.md`](sub-skills/setup-and-basics/SKILL.md) |
| Create or validate `config.yml`, `prompts.yml`, Colang `.co` files, guardrail catalog rails, custom actions/providers, or config migration | [`sub-skills/configure-rails/SKILL.md`](sub-skills/configure-rails/SKILL.md) |
| Run an existing config through Python APIs, CLI chat, FastAPI/OpenAI-compatible server endpoints, streaming, state/thread handling, or LangChain/LangGraph integrations | [`sub-skills/run-rails/SKILL.md`](sub-skills/run-rails/SKILL.md) |
| Evaluate guardrail behavior, inspect eval outputs, or reason about logging, tracing, metrics, telemetry, privacy, and operational diagnostics | [`sub-skills/evaluate-and-observe/SKILL.md`](sub-skills/evaluate-and-observe/SKILL.md) |
| Edit the source checkout, add providers, change public APIs, run repo tests, update docs, prepare PR text, or apply contribution policy | [`sub-skills/repo-development/SKILL.md`](sub-skills/repo-development/SKILL.md) |

## Operating defaults

- Treat install/runtime verification as no-live-provider by default. Do not call OpenAI, NVIDIA, NIM, Google Cloud, telemetry staging, or other provider services unless the user explicitly supplies credentials and asks for a live check.
- Python support is `>=3.10,<3.14`; install only the smallest extras needed for the requested workflow.
- Public install and minimal verification path:
  - `python -m pip install 'nemoguardrails'`
  - `python -m nemoguardrails --help`
  - `python sub-skills/setup-and-basics/scripts/check_install.py`
- Prefer bundled helpers for safe preflight checks before live work:
  - `sub-skills/setup-and-basics/scripts/check_install.py`
  - `sub-skills/configure-rails/scripts/validate_config.py`
  - `sub-skills/run-rails/scripts/deterministic_chat_smoke.py`
  - `sub-skills/run-rails/scripts/server_schema_smoke.py`
- Keep product-usage tasks separate from source-checkout maintenance. Only recommend checkout-scoped `make`/`uv` commands when the user is actually working in a cloned NeMo Guardrails repository.
- For cross-cutting failures, start with [`references/troubleshooting.md`](references/troubleshooting.md), then route to the nearest sub-skill troubleshooting reference.

## Key entry points

- Public package imports: `Guardrails`, `LLMRails`, `RailsConfig`, LLM message/response types, `register_provider`, `set_default_framework`, and testing helpers such as `FakeLLMModel` and `TestChat`.
- LangChain integration: import `RunnableRails` from `nemoguardrails.integrations.langchain.runnable_rails`.
- CLI commands: `chat`, `server`, `convert`, `actions-server`, `find-providers`, and `eval`.
- Server endpoints: `/v1/health`, `/healthz`, `/v1/rails/configs`, `/v1/models`, `/v1/chat/completions`, `/v1/checks`, and `/v1/challenges`.

## Provenance and routing metadata

- Source provenance and staleness signals: [`references/repo-provenance.md`](references/repo-provenance.md).
- Router placement metadata for repo-skill imports: [`references/repo-routing-metadata.json`](references/repo-routing-metadata.json).
