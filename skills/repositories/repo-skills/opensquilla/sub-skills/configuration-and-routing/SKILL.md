---
name: configuration-and-routing
description: "Configure OpenSquilla providers, models, SquillaRouter modes, web
  search providers, and config precedence without starting the gateway
  workflow."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# Configuration and Routing

Use this sub-skill for OpenSquilla provider setup, model selection, SquillaRouter routing modes, search provider setup, model catalog inspection, and configuration precedence. Treat provider routing and web search as the main task family.

This skill was distilled against OpenSquilla 0.5.3. The verification envelope was CPU-only: `opensquilla --help` worked, the provider/channel/search catalogs loaded, and imports for `mcp`, `lightgbm`, `onnxruntime`, `tokenizers`, `tiktoken`, and `jieba` succeeded. Live provider calls, provider billing behavior, and credentialed web search were not assumed to be available.

## Route here when the user asks to

- Choose or change an LLM provider, model id, base URL, API-key environment variable, or proxy.
- Inspect provider support with `providers`, model support with `models`, or setup catalogs with `onboard catalog`.
- Enable, disable, or explain SquillaRouter modes: `recommended`, `openrouter-mix`, direct/`disabled`, and advanced custom tiers.
- Configure or troubleshoot web search providers, fallback behavior, search diagnostics, or `search query`.
- Explain whether a value comes from TOML, environment, provider defaults, router presets, or the model catalog.
- Use `configure image-generation` or `configure memory-embedding` only to explain the shared configuration surface and credential precedence.

## Route elsewhere

- Installation, first-run setup preconditions, gateway lifecycle, Web UI launch, `doctor`, and gateway bind/port issues: [setup-and-gateway](../setup-and-gateway/SKILL.md).
- Chat, agent turns, sessions, memory operations, cron, diagnostics capture, replay, migration, recovery, sandbox posture, and general runtime automation: [cli-and-automation](../cli-and-automation/SKILL.md).
- Messaging adapters, channel credentials, channel status/certification, and MCP bridge setup: [channels-and-integrations](../channels-and-integrations/SKILL.md).
- TUI/OpenTUI, desktop shell, desktop-owned gateway behavior, and UI-specific routing displays: [tui-and-desktop](../tui-and-desktop/SKILL.md).

## Operating rules

1. Prefer non-mutating inspection first: `providers list`, `search list`, `onboard catalog ...`, and `config get`.
2. Prefer environment-variable references for secrets. Do not recommend committing raw API keys to TOML, shell history, examples, or issue reports.
3. Separate local catalog checks from live checks. `providers list` and `search list` are local; `providers status`, `models list`, ordinary `search query`, and gateway-backed status/query commands need a running gateway or network/provider credentials as documented in [commands](references/commands.md).
4. For exact-model debugging, billing audits, or provider comparison, recommend direct mode by disabling the router. For ordinary personal-agent use, start with `recommended`.
5. When config behavior is surprising, resolve the value source instead of guessing. Use [config precedence](references/config-precedence.md) before proposing edits.
6. For failures, use the symptom-first matrix in [troubleshooting](references/troubleshooting.md) and keep live-provider assumptions explicit.

## Reference map

- [commands](references/commands.md) — command groups for providers, models, router, search, and config.
- [config-precedence](references/config-precedence.md) — TOML/env/default load order and provider/search credential precedence.
- [provider-model-router](references/provider-model-router.md) — provider catalog facts, model catalog inspection, router mode choices, and cross-provider tier boundaries.
- [search](references/search.md) — search provider catalog, setup recipes, automatic selection, fallback, and query testing.
- [troubleshooting](references/troubleshooting.md) — auth, base URL, router fallback, search fallback, optional-dependency, and config confusion fixes.
