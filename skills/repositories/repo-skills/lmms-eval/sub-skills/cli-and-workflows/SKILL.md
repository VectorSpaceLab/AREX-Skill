---
name: cli-and-workflows
description: "Guide for running lmms-eval from the CLI or Python API, including
  configs, cache, reasoning tags, task/model browsing, and quick smoke checks."
metadata:
  disco-role: operating
disable-model-invocation: true
license: NOASSERTION
---

# cli-and-workflows

Use this route when the user wants to run or inspect lmms-eval directly from the command line or from Python code.
It covers the no-arg wizard, explicit eval commands, task and model browsing, YAML config runs, caching, and reasoning-tag behavior.

## Read first

- `../../references/cli-reference.md`
- `../../references/api-reference.md`
- `../../references/troubleshooting.md`

## What this route covers

- `lmms-eval eval` with explicit CLI arguments or the interactive wizard when no args are supplied.
- Task and model discovery with `tasks list` and `models --aliases`.
- Config-driven runs with `--config` plus CLI overrides.
- Programmatic evaluation with `simple_evaluate()` and `evaluate()`.
- Cache and reasoning-tag workflows that affect deterministic evaluation and output cleaning.
- Smoke checks, power analysis, and version/environment checks that confirm the package is installed, importable, and wired to the expected entry points.

## Typical workflow

1. Decide whether the request is CLI-first or Python-first.
2. Use `lmms-eval tasks list` and `lmms-eval models --aliases` to confirm the names the user should pass.
3. Keep early runs small with `--limit 5` or `--limit 8`.
4. Prefer `--config` when the user wants a repeatable evaluation recipe or several CLI overrides.
5. Use `--use_cache` and `--cache_requests` only when the user wants cache reuse, refresh, or deletion intentionally.
6. Check `--reasoning_tags` when `<think>` blocks or other reasoning markers appear in outputs.
7. If the user is scripting around the evaluator, route them to `api-reference.md` and verify the Python signature they need.

## Helpful commands

```bash
lmms-eval eval --help
lmms-eval tasks list
lmms-eval models --aliases
lmms-eval version
lmms-eval power --help
```

## Bundled scripts

- `../../scripts/runtime_smoke.py` — package/version/CLI smoke for the installed framework.
- `../../scripts/cache_reasoning_smoke.py` — reasoning-tag stripping and cache-determinism helper smoke.

## Cross-route handoff

- Send backend selection, `is_simple`, media protocol, aliasing, and optional dependency issues to `model-backends`.
- Send YAML structure, request shapes, metrics, and `utils.py` authoring to `task-authoring`.
- Send HTTP server, client, MCP, TUI, and job lifecycle concerns to `service-ops`.

## Common failure modes

- Unknown task or model names.
- Stale or unintended cache reuse.
- Reasoning tags that are disabled or overridden unexpectedly.
- YAML or config typos that surface as unknown keys.
- Missing optional service extras when the user tries to reach the web, MCP, or server commands from a minimal install.

When the issue is not purely about direct evaluation flow, switch to the owning sub-skill rather than stretching this one.
