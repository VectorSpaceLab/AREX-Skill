---
name: deployment
description: "Install, launch, containerize, and troubleshoot Open WebUI
  deployment workflows."
metadata:
  disco-role: operating
disable-model-invocation: true
license: NOASSERTION
---

# Deployment

Use this sub-skill for installing Open WebUI, starting it locally, running it from the published container images, and diagnosing startup failures.

This sub-skill is intentionally focused on runtime access. It is not a build-system manual and it does not depend on the original repository checkout at runtime.

## When to use this sub-skill

Use `deployment` when the user asks about:

- `pip install`, `open-webui serve`, `open-webui dev`, or source-startup commands
- Docker or container deployment
- GPU or Ollama image variants
- reverse-proxy, port, volume, secret-key, or startup problems
- updating or redeploying an existing instance

## Read these bundled files first

- `references/deployment.md` for the command patterns and deployment variants.
- `references/troubleshooting.md` for startup, container, and secret-key failures.
- `../../scripts/check-install.sh` for a quick install/import/CLI smoke check.
- `scripts/run-dev-server.sh` for a local dev-server wrapper.
- `scripts/docker-run-public.sh` for a helper that launches the published Open WebUI image.

## Primary workflows

### 1) Local source or editable install

Use this path when you want a local Python-backed deployment for inspection or development.

Typical signals:
- `pip`, `uv`, `conda`, editable install, source install, `open-webui dev`
- `WEBUI_SECRET_KEY`, `CORS_ALLOW_ORIGIN`, backend secret/bootstrap questions

Typical checks:
- `python -I -c "from importlib.metadata import version; print(version('open-webui'))"`
- `open-webui --help`
- `open-webui dev --help`

### 2) Published Docker image

Use this path when the user wants the packaged image rather than a local build.

Typical signals:
- `docker run`, `ghcr.io/open-webui/open-webui`, `main`, `cuda`, `ollama`, `slim`
- remote Ollama URL, public API key, persistent data volume

Typical checks:
- container image tag is correct
- data volume is mounted
- `OLLAMA_BASE_URL` points at the right backend

### 3) GPU / browser / deployment variants

Use this path when the user needs a CUDA-enabled host, bundled Ollama, or browser-assisted loaders.

Typical signals:
- `cuda`, `GPU`, `nvidia-smi`, `Playwright`, `WEB_LOADER_ENGINE=playwright`, `offline mode`

Typical checks:
- GPU image tag matches the host runtime
- browser helper is reachable if Playwright is enabled
- the deployment path matches the chosen runtime variant

## Common decision points

- Prefer `open-webui serve` for normal local startup; it is the most forgiving entry point for a direct deployment.
- Use `open-webui dev` when you want live reload and are comfortable with local-development behavior.
- Use the published image path when the user does not need source-level inspection.
- If the user is asking about a startup failure, read `references/troubleshooting.md` before suggesting another install.

## What this sub-skill does not cover

- Provider-specific model routing details belong in `chat-models`.
- File, note, memory, and retrieval workflows belong in `knowledge-files`.
- Plugins, tools, skills, MCP, and multimodal add-ons belong in `extensions`.
- Auth, storage, channels, calendar, and observability belong in `admin-collaboration`.

## Success shape

A future agent should be able to:

1. Pick the right deployment path.
2. Explain the required variables and runtime services.
3. Launch the app or container with concrete commands.
4. Diagnose the most likely startup and connectivity failures without reopening the repo.
