---
name: configuration-and-providers
description: "Configure gptme config files, credential storage, provider/model
  selection, local/custom providers, auth helpers, and optional dependency
  requirements."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# configuration-and-providers

Use this sub-skill when the task is about gptme configuration files, default model selection, provider prefixes, API-key storage, `/account` or `gptme-auth`, OpenRouter routing/privacy settings, local OpenAI-compatible backends such as Ollama, custom provider entries or provider packages, and optional extras/system dependency planning.

Route away when the task is mainly about:

- custom tools, plugin tools, hooks, MCP runtime behavior, skills, lessons, browser tools, or computer-use operation: use the tools/extensibility sub-skill.
- `gptme-server` auth tokens, CORS, Host validation, REST/SSE, Web UI, TUI, ACP, or deployment: use the server/protocols sub-skill.
- eval model benchmarking, SWE-bench/T-bench, leaderboard generation, or pass-rate gates: use the evals/benchmarks sub-skill.
- maintainer-only changes inside a gptme checkout, test/lint/typecheck/doc/release workflows, or CI policy: use the repo-development sub-skill.

## Read first

- [references/configuration.md](references/configuration.md) for global, local, project, and per-chat config files; merge/precedence rules; safe secret placement; model default conflicts; and static config review steps.
- [references/providers-and-models.md](references/providers-and-models.md) for provider prefixes, API-key variables, `/account`, `gptme-auth`, OpenRouter privacy/routing, local/Ollama setup, custom `[[providers]]`, provider plugins, and extras/system dependencies.
- [references/troubleshooting.md](references/troubleshooting.md) for missing key errors, model-prefix mistakes, duplicate TOML keys, local model and summary-model issues, OpenRouter routing/privacy failures, OAuth/browser problems, and custom-provider pitfalls.

## Safe helpers

- [scripts/validate_gptme_config.py](scripts/validate_gptme_config.py) statically checks TOML config/env/provider setup without API calls and without printing secret values.
- [scripts/explain_model_selection.py](scripts/explain_model_selection.py) explains which model would win from supplied CLI, chat, config, and environment inputs without importing gptme or making network calls.

Example static passes:

```sh
python scripts/validate_gptme_config.py --help
python scripts/explain_model_selection.py --help
python scripts/explain_model_selection.py \
  --models-default anthropic/claude-sonnet-4-6 \
  --model-env openai/gpt-5 \
  --api-key-env ANTHROPIC_API_KEY
```

## Fast operating checklist

1. Identify the scope: user-global config, project `gptme.toml`, an existing chat log config, credentials/auth, or provider/model routing.
2. If both `[models].default` and `MODEL` are set, prefer `[models].default` for the default chat model and treat the differing `MODEL` value as a conflict to explain.
3. Keep secrets out of committable config. Put provider keys in `config.local.toml`, `gptme.local.toml`, the credential store, or shell environment; never print the raw values.
4. Require provider-prefixed models for unambiguous selection: `anthropic/...`, `openai/...`, `openrouter/...`, `local/...`, `gptme/...`, or a configured custom provider prefix.
5. For local Ollama/OpenAI-compatible backends, pair `local/<exact-model-tag>` with `OPENAI_BASE_URL` and do not expect `OPENAI_BASE_URL` to affect non-local providers.
6. Prefer static checks and help commands (`gptme-auth --help`, `gptme-doctor --help`) before launching browsers, making model calls, testing custom provider connectivity, or running checkout-maintainer tests.
