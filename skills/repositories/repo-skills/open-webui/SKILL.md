---
name: open-webui
description: "Router for installing, running, configuring, and troubleshooting
  Open WebUI as a self-hosted AI web app."
metadata:
  disco-role: operating
disable-model-invocation: true
license: NOASSERTION
---

# Open WebUI

Use this skill for the Open WebUI repository when the user asks about installing, launching, configuring, extending, or operating the app.

Open WebUI is a self-hosted AI web application with a FastAPI backend, a Svelte frontend, and multiple deployment and integration surfaces. This root skill is a router, not a full manual.

## Start here

- Read `references/repo-provenance.md` if you need to confirm which repository snapshot this skill came from.
- Read `references/overview.md` for the high-level workflow map.
- Read `references/configuration.md` for cross-cutting environment variables and runtime knobs.
- Read `references/troubleshooting.md` for shared failure patterns.
- Run `scripts/check-install.sh` when you want a fast install/import/CLI smoke check.

## Route map

### `deployment`
Use this route for installation, local development, Docker/Compose, GPU or Playwright overlays, source startup, and startup troubleshooting.

Common signals:
- install, run, serve, dev, Docker, Compose, image, container, port, volume, secret key
- `OLLAMA_BASE_URL`, `WEBUI_SECRET_KEY`, `docker-compose.yaml`, `docker run`, `open-webui serve`

Read:
- `sub-skills/deployment/SKILL.md`
- `sub-skills/deployment/references/deployment.md`
- `sub-skills/deployment/references/troubleshooting.md`

### `chat-models`
Use this route for chat, model selection, prompt behavior, provider routing, playground usage, and model/provider troubleshooting.

Common signals:
- chat, model, provider, Ollama, OpenAI-compatible, prompt, streaming, playground, access control, fallback
- `OPENAI_API_KEY`, `OLLAMA_BASE_URL`, `ENABLE_OPENAI_API_PASSTHROUGH`, `ENABLE_CUSTOM_MODEL_FALLBACK`

Read:
- `sub-skills/chat-models/SKILL.md`
- `sub-skills/chat-models/references/workflows.md`
- `sub-skills/chat-models/references/troubleshooting.md`

### `knowledge-files`
Use this route for files, folders, notes, memories, knowledge bases, retrieval, RAG, document ingestion, and local search.

Common signals:
- file upload, folder, note, memory, knowledge base, retrieval, RAG, vector DB, loader, document format, knowledge search
- `ENABLE_RETRIEVAL_UNSCOPED_COLLECTIONS`, `KB_EXEC_MAX_OUTPUT_CHARS`, `VIEW_FILE_MAX_CHARS`

Read:
- `sub-skills/knowledge-files/SKILL.md`
- `sub-skills/knowledge-files/references/workflows.md`
- `sub-skills/knowledge-files/references/troubleshooting.md`

### `extensions`
Use this route for plugins, tools, skills, functions, pipelines, MCP/OpenAPI tool servers, browser helpers, image/audio extensions, and terminal-backed helpers.

Common signals:
- function, tool, skill, pipeline, MCP, MCPO, OpenAPI tool server, Playwright, image generation, voice, audio, terminal, webhook
- `ENABLE_PLUGINS`, `WEB_LOADER_ENGINE`, `PLAYWRIGHT_WS_URL`, `ENABLE_IMAGE_GENERATION`, `AUTOMATIC1111_BASE_URL`

Read:
- `sub-skills/extensions/SKILL.md`
- `sub-skills/extensions/references/workflows.md`
- `sub-skills/extensions/references/troubleshooting.md`

### `admin-collaboration`
Use this route for auth, users, groups, SCIM, OAuth, LDAP, storage, channels, calendar, automations, analytics, telemetry, and other operator-facing controls.

Common signals:
- auth, SSO, trusted headers, SCIM, LDAP, OAuth, users, groups, channels, calendar, automations, analytics, storage, telemetry
- `WEBUI_AUTH`, `WEBUI_ADMIN_EMAIL`, `DATABASE_URL`, `REDIS_URL`, `ENABLE_SCIM`, `ENABLE_OTEL`

Read:
- `sub-skills/admin-collaboration/SKILL.md`
- `sub-skills/admin-collaboration/references/workflows.md`
- `sub-skills/admin-collaboration/references/troubleshooting.md`

## Choosing between routes

- If the user asks how to get Open WebUI running at all, start with `deployment`.
- If the user is connecting providers or comparing models, start with `chat-models`.
- If the user is working with uploaded documents, notes, memory, or retrieval, start with `knowledge-files`.
- If the user is adding tool/server functionality or browser/image/audio extensions, start with `extensions`.
- If the user is configuring identity, storage, users, groups, channels, or observability, start with `admin-collaboration`.

## Helpful cross-cutting checks

- `open-webui --help`
- `open-webui serve --help`
- `open-webui dev --help`
- `python -I -c "from importlib.metadata import version; print(version('open-webui'))"`

## Notes

- This generated skill must stay self-contained. Runtime instructions should only point to files inside this skill tree.
- Keep broad reference material in `references/` and concise routing text in this file.
- Do not route users to the original repository checkout from runtime guidance.
