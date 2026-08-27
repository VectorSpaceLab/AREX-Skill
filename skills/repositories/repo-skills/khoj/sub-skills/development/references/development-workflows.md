# Development Workflows

## Contributor Shape

Khoj is a Python package and server with FastAPI routes, Django ORM/admin, content processors, search/filter code, AI chat/agent tooling, and multiple clients. Most backend work lives under `src/khoj`, tests live under `tests`, frontend web code lives under `src/interface/web`, and contributor documentation lives under `documentation`.

Use this source-area checklist before changing code:

- `src/khoj/routers`: FastAPI endpoint definitions, auth/dependency checks, request parsing, response shapes, and route-specific side effects.
- `src/khoj/database/models`, `src/khoj/database/adapters`, `src/khoj/database/admin.py`, `src/khoj/database/migrations`: Django schema, ORM access patterns, admin visibility, and data migration behavior.
- `src/khoj/processor/content`: parser and ingestion transforms for Markdown, Org, plaintext/HTML/XML, PDF, DOCX, images, GitHub, and Notion.
- `src/khoj/search_filter` and `src/khoj/search_type`: query filters, text search setup/update/delete, embeddings/cross-encoder usage, and search isolation.
- `src/khoj/processor/conversation`, `src/khoj/processor/tools`, `src/khoj/routers/api_chat.py`, `src/khoj/routers/api_agents.py`, `src/khoj/routers/research.py`: chat, tools, agents, web search, code execution, and online-retrieval orchestration.
- `src/interface/web`, `src/interface/desktop`, `src/interface/obsidian`, `src/interface/emacs`, and `documentation`: client-visible behavior, docs, static assets, and release metadata.

## Local Setup Choices

Prefer the smallest setup that supports the requested change.

- Parser-only, filter-only, CLI parser, and pure utility changes usually need only the Python development environment plus focused tests.
- API, adapter, search-indexing, memory, automation, and model changes need a configured Django test database; Khoj expects PostgreSQL with pgvector for realistic server/test runs.
- Frontend web changes need the web client dependencies and an export/build check when the change affects shipped static assets.
- Docker development is useful when validating service wiring, PostgreSQL/pgvector, sandbox/search sidecars, static-file serving, or container env vars; it is heavier than focused Python tests.

The development metadata is in `pyproject.toml` and `pytest.ini`: Python `>=3.10,<3.13`, package name `khoj`, console script `khoj = khoj.main:run`, development extra dependencies include pytest, pytest-django, pytest-asyncio, pytest-xdist, mypy, ruff, pre-commit, factory-boy, datasets, and pandas. Pytest uses `DJANGO_SETTINGS_MODULE = khoj.app.settings`, `pythonpath = . src`, `testpaths = tests`, and `--reuse-db`.

## Safe Commands

Use commands from the repo root unless a client package requires its own directory.

- Install Python development dependencies when the user asks for setup: `uv sync --all-extras`. If `uv` is unavailable, the development script falls back to a virtualenv and editable `.[dev]` install.
- Run focused Python tests first: `pytest tests/test_cli.py`, `pytest tests/test_markdown_to_entries.py`, or another file from the focused map.
- Exclude expensive chat-quality tests during broad backend validation: `pytest -m "not chatquality"`.
- Run ruff checks directly for Python style/import validation: `ruff check src/khoj tests` and `ruff format --check src/khoj tests`.
- Run mypy only when the change affects typed backend contracts or before final PR confidence: `mypy`.
- For parser-only CLI checks, use code paths that import `khoj.utils.cli.cli`; avoid the `khoj` console script on unconfigured hosts because resolving `khoj.main:run` can initialize Django and migrations before argparse handles help.

## Docker Development

`docker-compose.yml` defines a PostgreSQL/pgvector database, a Terrarium sandbox, SearxNG search, optional computer service, and the Khoj server. The server maps port `42110`, sets database env vars, admin credentials, model-provider placeholders, telemetry and domain options, and starts with `--host="0.0.0.0" --port=42110 -vv --anonymous-mode --non-interactive`.

Use Docker only when the task needs service integration. For code-only tasks, a targeted pytest command is safer and faster. If building the server image from source, switch the server service from image usage to build usage intentionally and expect a slower build. Do not mount production secrets into a development validation run.

## Frontend, Client, And Docs Awareness

Backend route or payload changes often require client and docs follow-up:

- Web UI: check `src/interface/web` when changing API paths, auth/session behavior, streaming chat, content upload flows, agent controls, automations, memory, settings pages, static assets, or user-visible response payloads.
- Documentation: update `documentation/docs` when behavior, setup, config, API semantics, or troubleshooting changes.
- Desktop and Obsidian clients: inspect `src/interface/desktop` and `src/interface/obsidian` when server URL, authentication, sync, content upload, search, or chat semantics change.
- Emacs client metadata can be release-sensitive; avoid changing it unless the task targets that client.

The contributor docs recommend `bun install` and `bun export` for the web app, with `bun dev` only for interactive frontend development. Streaming behavior differs in the web dev server, so validate shipped behavior against exported/static-server flow when the change is streaming-sensitive.

## Script Boundaries

`scripts/dev_setup.sh` is a setup reference, not a safe default helper for autonomous coding tasks. It can create or use a virtual environment, install all extras, install web dependencies, optionally install Obsidian/Desktop dependencies with `--full`, install pre-commit hooks, and prepend a custom prettier hook into `.git/hooks/pre-commit`. Run it only when the user explicitly wants local setup mutation.

`scripts/bump_version.sh` is maintainer-only release automation. It changes web, desktop, Obsidian, Emacs, manifest, and versions files; may build the Obsidian plugin; runs pre-commit; creates release commits; and tags releases. Do not use it for normal development validation or version edits unless the user explicitly asks for a release operation.

CI workflow evidence shows Python tests run across 3.10, 3.11, and 3.12 with PostgreSQL/pgvector, CPU torch index settings, `uv sync --all-extras`, and `uv run pytest`, with `tests/evals` excluded from trigger paths. Treat `tests/evals` and chat-quality/external-service tests as opt-in, not the first validation target.
