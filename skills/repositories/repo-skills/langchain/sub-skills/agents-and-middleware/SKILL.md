---
name: agents-and-middleware
description: "Work on the actively maintained LangChain v1 agent package:
  init_chat_model, create_agent, structured output, tools, middleware,
  embeddings initialization, provider routing, and agent runtime customization.
  Use for libs/langchain_v1 agent workflows and route low-level core primitives
  or provider implementation details to sibling skills."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Agents and Middleware

Use this sub-skill for practical work in the actively maintained `langchain` package around v1 agents, middleware, model initialization, structured output, tools, and embeddings. This guidance is distilled from the LangChain v1 source and tests and is self-contained for future coding agents.

## When to Use

- User asks about `init_chat_model`, `create_agent`, `response_format`, tool schemas, injected tool runtime, or configurable chat models.
- User asks to add, configure, or debug middleware such as retry, fallback, human-in-the-loop, summarization, tool/model call limits, PII redaction, file search, shell execution, todo planning, provider tool search, tool retry, or tool selection.
- User asks why provider resolution fails for a chat or embedding model, especially when optional integration packages or credentials are missing.
- User asks to customize agent state, runtime context, checkpointer/store usage, interrupts, streaming, or debug behavior at the `langchain` v1 layer.

## Route Elsewhere

- For low-level runnable, message, tool, callback, language-model, or embedding primitives from `langchain_core`, use `../core-primitives/SKILL.md`.
- For provider implementation packages such as `langchain-openai`, `langchain-anthropic`, `langchain-ollama`, or provider-specific parameters/classes, use `../integrations/SKILL.md`.
- For legacy `langchain-classic` imports, chains, retrievers, or classic agents, use the sibling skill that owns classic APIs instead of rewriting v1 guidance.

## Reference Map

- Start with [references/agent-workflows.md](references/agent-workflows.md) for source layout, import paths, common edit workflows, validation commands, structured output, tools, embeddings, and provider initialization.
- Use [references/middleware-reference.md](references/middleware-reference.md) for middleware families, exported classes, hook styles, ordering, state/context patterns, and safety constraints.
- Use [references/troubleshooting.md](references/troubleshooting.md) for missing provider packages, credentials/network skips, structured output/tool validation, middleware ordering, HITL/shell/file-search safety, and v1-vs-classic confusion.
- Run [scripts/agent_import_smoke.py](scripts/agent_import_smoke.py) as a safe import-only smoke check when an environment is available.

## Fast Workflow

1. Confirm the target package is `libs/langchain_v1`; its distribution name is `langchain` and its package imports are `langchain.*`.
2. Inspect the nearest v1 public API files first: `langchain/chat_models/base.py`, `langchain/agents/factory.py`, `langchain/agents/structured_output.py`, `langchain/agents/middleware/`, `langchain/tools/`, and `langchain/embeddings/base.py`.
3. Prefer tests under `tests/unit_tests/agents`, `tests/unit_tests/chat_models`, `tests/unit_tests/tools`, and `tests/unit_tests/embeddings` for expected public behavior.
4. For package validation, use `uv` from `libs/langchain_v1`; do not use `pip`, `poetry`, or `conda` directly for this monorepo.
5. Skip network-backed model invocations unless credentials, provider packages, and user permission are present; use fake models or import checks for local validation.

## Safe Validation

From `libs/langchain_v1`, use targeted package tests when `uv` is available:

```bash
uv run --group test pytest tests/unit_tests/chat_models/test_chat_models.py tests/unit_tests/agents/test_response_format.py tests/unit_tests/tools/test_imports.py tests/unit_tests/embeddings/test_base.py
```

From this sub-skill directory, use the bundled smoke script with any Python environment that already has `langchain` installed:

```bash
python scripts/agent_import_smoke.py
```

The smoke script imports public APIs only and does not call providers, networks, shell commands, or external files.

## Guardrails

- Keep v1 import paths explicit: `langchain.chat_models`, `langchain.agents`, `langchain.agents.middleware`, `langchain.tools`, and `langchain.embeddings`.
- Do not add provider-specific hard dependencies to `langchain` core code unless the package metadata intentionally lists them as optional extras.
- Do not run shell/file-search/HITL examples as unattended validation; these require user-reviewed safety decisions.
- Do not link future runtime instructions to source-checkout docs, examples, tests, or absolute local paths; distill facts into this sub-skill or bundled references.
