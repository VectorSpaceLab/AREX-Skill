---
name: core-primitives
description: "Work on langchain-core primitives: runnables, messages/content
  blocks, prompts, tools, documents, embeddings, vector stores, language model
  interfaces, callbacks, output parsers, serialization, and API/deprecation
  utilities."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Core Primitives

Use this sub-skill when a task touches stable `langchain-core` abstractions that other LangChain packages build on: LCEL `Runnable` composition, message and content-block conversion, prompt templates, tool schemas, documents, embeddings, vector stores, chat/LLM interfaces, callbacks/tracing hooks, output parsers, serialization, or deprecation/API utilities.

Route app-level agent construction, middleware, model/tool orchestration, and `create_agent` behavior to `../agents-and-middleware/SKILL.md` when that sibling exists. Route legacy `langchain-classic` chains, memory, agents, callbacks, and retrievers to `../classic-chains/SKILL.md` when that sibling exists.

## Start Here

1. Identify the primitive family involved and read `references/api-surfaces.md` for the public classes, helpers, and compatibility expectations.
2. Follow the matching workflow in `references/workflows.md` before editing, including package-local commands and skip conditions.
3. For failures involving provider content conversion, runnable mode mismatches, Pydantic schemas, tool docstrings, optional imports, deprecation warnings, or serialization, use `references/troubleshooting.md`.
4. Run `scripts/core_import_smoke.py` as a fast, non-mutating import/API smoke check when a Python environment with `langchain-core` is available.

## Scope

- Prefer public imports from `langchain_core.*` package surfaces; avoid depending on private helpers unless the task is explicitly internal maintenance.
- Preserve stable public signatures. For new public parameters, prefer keyword-only defaults and add tests that fail when the compatibility promise is broken.
- Keep core primitives provider-agnostic. Provider payload details belong in integrations; core should define normalized interfaces and safe translation hooks.
- Use Pydantic v2-native models and helpers while respecting existing v1 compatibility paths where the code already supports them.
- Treat network calls, provider credentials, and heavy integration execution as out of scope for this sub-skill; use fakes, unit tests, and import/schema checks instead.

## Local References

- `references/api-surfaces.md` — distilled map of core public APIs, expected extension points, and evidence-backed validation targets.
- `references/workflows.md` — concrete edit/test workflows for runnables, messages, tools, prompts, vector stores, model interfaces, parsers, callbacks, serialization, and deprecations.
- `references/troubleshooting.md` — failure-mode guide for the common core primitive regressions this sub-skill owns.
- `scripts/core_import_smoke.py` — safe import and minimal behavior smoke check for installed or checkout-backed `langchain-core`.

## Validation Signals

Good changes usually include targeted unit tests around the affected primitive, pass the relevant package-local `uv run --group test pytest ...` command when `uv` is available, and keep import smoke output at `OK core_import_smoke`. If `uv` or dependencies are unavailable, record the skip clearly and still run static checks such as Python syntax compilation for bundled scripts.
