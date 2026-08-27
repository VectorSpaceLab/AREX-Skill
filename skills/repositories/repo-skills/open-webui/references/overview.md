# Open WebUI Overview

Open WebUI is a self-hosted AI web app that combines a FastAPI backend, a Svelte frontend, and a large set of model, knowledge, extension, and admin workflows.

## Route map

| Workflow family | Use this when the user asks about... | Owning sub-skill | Helpful entry points |
| --- | --- | --- | --- |
| Deployment | Install, start, update, Docker, Compose, GPU/Playwright overlays, secret keys, port mapping, local dev, startup errors | `deployment` | `open-webui/SKILL.md`, `open-webui/sub-skills/deployment/SKILL.md`, `open-webui/references/troubleshooting.md` |
| Chat and models | Chats, model selection, prompt behavior, provider routing, OpenAI-compatible APIs, Ollama, playground, response streaming | `chat-models` | `open-webui/sub-skills/chat-models/SKILL.md` |
| Knowledge and files | Files, folders, notes, memories, knowledge bases, retrieval, RAG, document ingestion, local search | `knowledge-files` | `open-webui/sub-skills/knowledge-files/SKILL.md` |
| Extensions and multimodal | Functions, tools, skills, pipelines, MCP, OpenAPI tool servers, image/audio extensions, browser helpers, terminals | `extensions` | `open-webui/sub-skills/extensions/SKILL.md` |
| Admin and collaboration | Auth, users, groups, SCIM, OAuth, LDAP, storage, channels, calendar, automations, analytics, telemetry | `admin-collaboration` | `open-webui/sub-skills/admin-collaboration/SKILL.md` |

## Core runtime facts

- Package name: `open-webui`
- Console entry point: `open-webui`
- Common runtime subcommands: `serve`, `dev`
- Package version source: `importlib.metadata.version('open-webui')`
- Source install can build frontend assets through the project build hook, so Node.js/npm availability matters for editable/source installs.
- The backend honors many environment variables, but the most common ones are `WEBUI_SECRET_KEY`, `OLLAMA_BASE_URL`, `DATABASE_URL`, `REDIS_URL`, `WEBUI_AUTH`, `ENABLE_PLUGINS`, `ENABLE_OTEL`, and storage-provider variables.

## High-value reading order

1. Read the root `SKILL.md` to pick the right sub-skill.
2. Read `references/configuration.md` for cross-cutting environment variables and backend knobs.
3. Read the sub-skill `SKILL.md` for the workflow family.
4. Read the sub-skill's troubleshooting reference before changing a deployment or provider configuration.

## Common cross-cutting checks

- `open-webui --help`
- `open-webui serve --help`
- `open-webui dev --help`
- `python -I -c "from importlib.metadata import version; print(version('open-webui'))"`

## Common failure patterns

- Missing `WEBUI_SECRET_KEY` when starting the backend directly.
- Ollama URL / provider / API-key mismatches.
- File-size, file-format, or loader problems in knowledge workflows.
- Missing optional extension dependencies, browser helpers, or tool-server timeouts.
- Auth / SCIM / storage / Redis / telemetry misconfiguration.
