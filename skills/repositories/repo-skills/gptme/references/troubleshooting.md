# Cross-cutting Troubleshooting

## Purpose

Start here for failures that span installation, imports, optional extras, credentials, and interface selection. Then route to the nearest sub-skill troubleshooting page.

## Install or import fails

Symptoms:

- `ModuleNotFoundError: gptme`
- console script not found (`gptme`, `gptme-server`, `gptme-auth`, ...)
- help commands fail immediately after installation

Checks:

```bash
python scripts/check_gptme_environment.py --check-server-app
python scripts/run_gptme_help_matrix.py --skip-eval-list
```

Recovery:

1. Verify the active Python environment is the one where `gptme` was installed.
2. For isolated CLI use, prefer `pipx install gptme` or `uv tool install gptme`.
3. For a checkout, reinstall editable entry points after changing metadata: `pipx install -e .` or the environment-specific editable install command.
4. If only an optional interface fails, install the targeted extra instead of `[all]`.

## Optional extra missing

Common symptoms and fixes:

| Symptom | Likely missing piece | Route |
| --- | --- | --- |
| `gptme-server` says server extras are missing or Flask cannot import | `gptme[server]` | `server-webui-and-protocols` |
| Browser tool cannot start Playwright | `gptme[browser]` plus Playwright browser binaries | `tools-and-extensibility` |
| `gptme-acp` cannot import `agent-client-protocol` | `gptme[acp]` or the `gptme-acp` shim | `server-webui-and-protocols` |
| `gptme-tui` cannot import Textual | `gptme[tui]` | `server-webui-and-protocols` |
| Eval integrations complain about `dspy`, datasets, SWE-bench, or terminal-bench | eval-specific extras and possibly Docker/network | `evals-and-benchmarks` |
| Computer-use workflows fail on display/browser/system tooling | GUI/X11/VNC/Docker/system dependencies | `tools-and-extensibility` |

Do not install every extra just to clear one error; choose the smallest surface that matches the task.

## Provider credentials or model selection fails

Symptoms:

- `No API key found` or `No model specified`
- a local model is ignored even though `OPENAI_BASE_URL` is set
- OpenRouter routes to an unsuitable provider
- OAuth needs a browser/device flow

Route to `configuration-and-providers`. Key reminders:

- `--model` / `-m` wins over per-chat, global, and environment defaults.
- `[models].default` wins over `MODEL` for default chat model selection.
- `OPENAI_BASE_URL` is for `local/...` models, not for every provider prefix.
- Store secrets in local override files, credential stores, or process environment; never print raw key values.

## Server/Web UI connectivity fails

Symptoms:

- hosted Web UI cannot reach a local `gptme-server`
- 401/403 responses, token mismatch, or Host-header rejection
- streaming appears buffered behind a proxy
- Web UI metadata looks stale or inconsistent

Route to `server-webui-and-protocols`. Key checks:

- Use loopback for local development unless explicitly deploying.
- Configure `GPTME_SERVER_TOKEN` for persistent auth.
- Set CORS only for the actual Web UI origin.
- For Chrome local-network prompts, the user must allow Local Network Access in the browser.
- Reverse proxies for SSE must disable response buffering and use long read timeouts.

## Tool/plugin/MCP/browser failures

Route to `tools-and-extensibility`. Key checks:

- Inventory tool availability with that sub-skill's `list_gptme_tools.py` helper.
- Distinguish built-in tools, custom ToolSpec files, plugins, script tools, MCP servers, skills, and lessons.
- Confirm tool allowlist syntax: exact list replaces defaults; `+tool` adds; `-tool` removes.
- Browser and computer tools often fail from missing optional runtime, not from core `gptme` import.

## Eval or benchmark failures

Route to `evals-and-benchmarks`. Key checks:

- `gptme-eval --list` is safe; actual eval runs may require model keys, network, Docker, and time.
- Use Docker isolation when comparing model behavior across tasks.
- Record model, provider, tool format, timeout, and result directory in every benchmark note.
- Treat API/provider failures as benchmark-environment failures, not necessarily package failures.

## Maintainer checkout failures

Route to `repo-development` when editing the repository itself.

- Follow branch/commit/staging policy before changing files.
- Use focused tests, not the full suite by reflex.
- Web UI changes usually need both backend and frontend checks.
- Release/package validation is order-sensitive: build frontend, bundle Web UI, build package, then validate archive contents.

## Privacy and safety boundaries

Do not copy local environment prefixes, private token values, OAuth files, API keys, proxy settings, or generated verification logs into public docs or user-facing output. For this generated skill, public runtime files should only contain reusable commands, distilled workflows, and generic troubleshooting guidance.
