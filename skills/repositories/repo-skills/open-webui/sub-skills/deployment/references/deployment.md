# Deployment Guide

This page summarizes the deployment paths that are safe to use from the generated skill tree after the original repository checkout is gone.

## 1. Local install or editable source install

Typical PyPI flow:

```bash
python -m pip install open-webui
open-webui serve
```

Typical source-editable flow:

```bash
python -m pip install -e .
open-webui serve
```

Useful variant for live-reload development:

```bash
open-webui dev --host 0.0.0.0 --port 8080
```

Notes:
- The direct backend wants a secret key; `open-webui serve` is the most forgiving local startup path.
- Source installs may trigger the frontend build hook and therefore need Node.js/npm.
- `open-webui dev` is for source-level inspection and local iteration, not for long-lived production use.
- The generated helper `scripts/run-dev-server.sh` wraps the dev path and can generate an ephemeral secret when needed.

## 2. Published container image

Use the public image when you want a self-contained runtime:

```bash
docker run -d \
  -p 3000:8080 \
  --add-host=host.docker.internal:host-gateway \
  -v open-webui:/app/backend/data \
  --name open-webui \
  --restart always \
  ghcr.io/open-webui/open-webui:main
```

CUDA-enabled variant:

```bash
docker run -d \
  -p 3000:8080 \
  --gpus all \
  --add-host=host.docker.internal:host-gateway \
  -v open-webui:/app/backend/data \
  --name open-webui \
  --restart always \
  ghcr.io/open-webui/open-webui:cuda
```

Bundled Ollama variant:

```bash
docker run -d \
  -p 3000:8080 \
  -v ollama:/root/.ollama \
  -v open-webui:/app/backend/data \
  --name open-webui \
  --restart always \
  ghcr.io/open-webui/open-webui:ollama
```

The generated helper `scripts/docker-run-public.sh` turns these patterns into a reusable wrapper with explicit image tags and optional environment pass-through.

## 3. Common runtime settings

- `OLLAMA_BASE_URL` — point at the model backend.
- `OPENAI_API_KEY` or provider-specific keys — enable hosted provider access.
- `WEBUI_SECRET_KEY` — required when you bypass the usual startup helpers.
- `DATA_DIR` / Docker volume mount — keep user data persistent.
- `WEB_LOADER_ENGINE=playwright` — enable browser-assisted loaders when the browser helper is available.

## 4. Variants worth knowing

The source repository also defines compose overlays for GPU, API exposure, data mounts, Playwright, AMD/ROCm, and observability. This generated skill does not depend on those source compose files at runtime, so treat them as evidence for variant behavior rather than as runtime dependencies.

## 5. Verification sequence

When a deployment path changes, verify in this order:

1. `python -I -c "from importlib.metadata import version; print(version('open-webui'))"`
2. `open-webui --help`
3. `open-webui serve --help`
4. `open-webui dev --help` if the user asked for local development
5. Optional CUDA smoke if the host is GPU-capable

## 6. Failure patterns

Read `references/troubleshooting.md` for the shared recovery steps.
