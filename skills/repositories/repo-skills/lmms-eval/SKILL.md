---
name: lmms-eval
description: "Router for using lmms-eval to run evaluations, inspect models and
  tasks, and operate its server and UI."
metadata:
  disco-role: operating
disable-model-invocation: true
license: NOASSERTION
---

# lmms-eval

`lmms-eval` is the router for the multimodal evaluation framework. Use it when a user wants to run an eval, inspect available tasks or models, add or debug a backend, author a task YAML, or operate the HTTP server, TUI, or MCP tooling.

This skill is intentionally router-like. For concrete command tables, API shapes, and troubleshooting detail, read the bundled references first, then use the matching sub-skill.

## Start here

1. Read `references/installation.md` for install and smoke commands.
2. Use the route map below to choose a sub-skill.
3. When the workflow is specific, read that sub-skill's troubleshooting note.
4. Keep smoke tests small: prefer `--help`, `version`, `tasks list`, `models --aliases`, or a `--limit 5/8` eval.

## Route map

| If the user asks for... | Use this sub-skill | Read first |
| --- | --- | --- |
| Run an evaluation from the CLI or Python API, browse tasks/models, use the no-arg wizard, set config/caching/reasoning flags, or debug a direct run | `cli-and-workflows` | `references/cli-reference.md`, `references/api-reference.md`, `references/troubleshooting.md` |
| Add/fix a model backend, choose chat vs simple, inspect `model_args`, or troubleshoot a backend/registry issue | `model-backends` | `references/model-backends.md`, `references/troubleshooting.md` |
| Add/update a task YAML, `utils.py`, metrics, groups/tags, or request-shape contracts | `task-authoring` | `references/task-authoring.md`, `references/troubleshooting.md` |
| Start or debug the HTTP server, client, TUI, or MCP tooling | `service-ops` | `references/service-ops.md`, `references/troubleshooting.md` |

## Common entry commands

- `lmms-eval --help`
- `lmms-eval eval --help`
- `lmms-eval tasks list`
- `lmms-eval models --aliases`
- `lmms-eval version`
- `lmms-eval serve --help`
- `lmms-eval mcp --help`
- `lmms-eval ui --help`

## Working rules

- Use `--limit 5` or `--limit 8` for smoke checks.
- Do not assume a GPU path is required just because the host has one; check the chosen workflow first.
- Keep external API, large dataset, and full-benchmark runs out of default smoke checks.
- When a command fails because of a missing dependency, route to the nearest troubleshooting reference before guessing.
- If a user is only trying to inspect the framework, prefer safe imports and CLI help over launching long-running jobs.

## Bundled references

- `references/installation.md` — install variants, package identity, and safe smoke checks.
- `references/cli-reference.md` — direct eval, browsing, config, cache, and debug flags.
- `references/api-reference.md` — Python evaluation, registry, protocol, and service-layer signatures.
- `references/model-backends.md` — model registry, chat/simple split, media protocol, and backend notes.
- `references/task-authoring.md` — task YAMLs, request shapes, metrics, and task discovery patterns.
- `references/service-ops.md` — server, client, MCP, TUI, and job scheduler usage.
- `references/troubleshooting.md` — cross-cutting failure symptoms and recovery steps.
- `references/repo-provenance.md` — staleness baseline for this generated skill.
- `references/repo-routing-metadata.json` — router metadata used by managed imports.

## Bundled scripts

- `scripts/runtime_smoke.py` — package/version/CLI smoke for the installed framework.
- `scripts/cache_reasoning_smoke.py` — reasoning-tag stripping and cache-determinism helper smoke.
- `scripts/model_registry_smoke.py` — inspect canonical models, aliases, and resolution.
- `scripts/video_decode_smoke.py` — inspect video decode backends and optionally decode a local clip.
- `scripts/task_registry_smoke.py` — inspect the built-in task registry.
- `scripts/task_yaml_audit.py` — audit task YAML parseability and key presence.
- `scripts/task_input_capture.py` — capture built request-boundary summaries for task debugging.
- `scripts/service_api_smoke.py` — inspect the server, client, MCP, and TUI backend APIs.
- `scripts/batch_watchdog.py` — monitor heartbeats and fail fast on hung distributed jobs.
- `scripts/job_scheduler_smoke.py` — safe subprocess-log smoke for the evaluation job scheduler.

## When to leave this skill

If the task is no longer about lmms-eval itself — for example, a downstream benchmark result, a paper recovery, or a repository unrelated to evaluation — switch to the appropriate skill instead of stretching this one.
