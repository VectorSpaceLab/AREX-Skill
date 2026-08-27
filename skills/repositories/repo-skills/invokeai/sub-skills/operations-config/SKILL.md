---
name: operations-config
description: "Start and configure InvokeAI server operations, CLI entry points,
  config precedence, API discovery, and multiuser auth administration."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Operations Config

Use this sub-skill when a task is about running or inspecting InvokeAI as an installed application: `invokeai-web`, root/config resolution, operational settings, FastAPI routes/OpenAPI, or multiuser/auth user administration.

## Read First

- Start with `references/configuration.md` for package metadata, entry points, `--root`/`--config`/env/YAML precedence, root layout, and server startup ordering.
- Use `references/api-and-auth.md` for FastAPI route families, OpenAPI discovery, auth endpoints, user service behavior, and user-management CLI cautions.
- Use `references/troubleshooting.md` for Python/dependency/runtime failures, port/CORS/SSL/log issues, auth mistakes, and safe diagnostics.

## Safe Scripts

- `scripts/inspect_cli_help.py` prints help and entry-point facts for `invokeai-web` and `invoke-user*` commands without starting the server or mutating users.
- `scripts/summarize_settings.py` summarizes the bundled generated settings catalog by category, setting, or JSON output.
- `scripts/inspect_openapi_routes.py` summarizes live OpenAPI routes when full runtime dependencies are installed; otherwise it falls back to bundled route-family knowledge with an actionable warning.

## Routing Boundaries

- Route custom node authoring/import/runtime problems to `../workflow-nodes/SKILL.md`.
- Route workflow record CRUD and session queue behavior to `../workflows-queues/SKILL.md`.
- Route model installation, cache sizing, Hugging Face login, and model download failures to `../model-management/SKILL.md`.
- Route broad install/backend/Torch/CUDA issues that are not operations-specific to `../../references/troubleshooting.md`.
- Frontend React internals, Docker image maintenance, and gallery maintenance mutations are outside this sub-skill; this subtree only records operational cautions for those surfaces.
