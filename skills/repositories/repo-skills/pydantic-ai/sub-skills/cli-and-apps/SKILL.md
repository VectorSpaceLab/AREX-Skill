---
name: cli-and-apps
description: "Guides agents using Pydantic AI CLI entry points, clai chat, clai
  web, Agent.to_cli, Agent.to_web, installed examples, and safe app scaffolds."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# CLI and Apps

Use this sub-skill when the task is to run or troubleshoot `clai`, `pai`, `python -m pydantic_ai`, browser chat UI, installed example packages, or application scaffolds built around Pydantic AI agents.

## Read First

- Read [references/cli-reference.md](references/cli-reference.md) when choosing CLI commands, flags, model options, custom agent loading, `Agent.to_cli()`, `Agent.to_web()`, or `clai web` behavior.
- Read [references/example-app-recipes.md](references/example-app-recipes.md) when turning maintained Pydantic AI example patterns into a self-contained app scaffold without relying on original example files.
- Read [references/troubleshooting.md](references/troubleshooting.md) when diagnosing CLI imports, missing API keys, invalid custom agent paths, web UI startup, optional extras, native-tool flags, or example dependency failures.
- Run [scripts/check_cli_help.py](scripts/check_cli_help.py) when you need a safe no-network check that installed `clai`/`pai` help entry points are available.

## Core Routing

- Use `clai "prompt"` for one-shot terminal questions and bare `clai` for interactive chat with slash commands.
- Use `clai --list-models` to inspect provider-prefixed model strings; route model/provider credential decisions to `../models-and-providers/SKILL.md`.
- Use `clai --agent module:variable` or an AgentSpec YAML/JSON path when the user already has an importable `Agent`; route agent construction details to `../agent-core/SKILL.md`.
- Use `Agent.to_cli()` or `Agent.to_cli_sync()` when a Python app should expose an existing `Agent` as an interactive terminal session.
- Use `clai web` for a local development browser chat UI and `Agent.to_web()` when embedding the generated Starlette app in an ASGI stack; route deeper UI event streams, AG-UI, MCP, durable execution, and hooks to `../mcp-and-integrations/SKILL.md`.
- Use installed `pydantic_ai_examples` modules as runnable examples only when the examples package and required services/credentials are installed; otherwise distill the recipe into local app code.

## Boundaries

- For `Agent(...)`, dependencies, run methods, streaming semantics, `AgentSpec`, deterministic testing, and message-history continuation mechanics, read `../agent-core/SKILL.md`.
- For function tools, toolsets, retries, approvals, deferred tools, and tool schemas used inside apps, read `../tools-and-toolsets/SKILL.md`.
- For structured outputs, message serialization, multimodal inputs, and browser/chat history formats, read `../outputs-and-messages/SKILL.md`.
- For model strings, optional provider extras, API key environment variables, native tool compatibility, embeddings, and provider failures, read `../models-and-providers/SKILL.md`.
- For AG-UI, Vercel AI SDK event streams, Logfire, MCP, A2A, capabilities, and durable backends, read `../mcp-and-integrations/SKILL.md`.

## Non-Negotiables

- Prefer `clai` over legacy `pai` in new user instructions; mention `pai` only for compatibility with existing installations or smoke checks.
- Do not make runtime guidance depend on an original repository checkout, source examples, source tests, or local paths; use installed packages or bundled recipes.
- Do not run live provider calls, browser servers, databases, Docker, or cloud examples unless the user explicitly asked and has configured credentials/services.
- Treat `clai web` and `Agent.to_web()` as local development/debugging surfaces, not production frontend architecture.
