---
name: development
description: "Safely modify, test, lint, and maintain the Khoj repository as a contributor."
disable-model-invocation: true
metadata:
  disco-role: operating
license: AGPL 3.0
---

# Khoj Development

Use this sub-skill when a task is about changing Khoj source code, selecting focused tests, preparing local contributor workflows, editing Django models or migrations, updating routers with tests, maintaining docs/client awareness, or respecting development/release script boundaries.

## Start Here

- For local setup, Docker-vs-pip development choices, frontend/docs/client awareness, and script boundaries, read [development-workflows.md](references/development-workflows.md).
- For changed-area-to-test mapping and safe focused commands, read [test-selection.md](references/test-selection.md).
- For Django model, migration, admin, adapter, fixture, and database-safety considerations, read [migrations-and-models.md](references/migrations-and-models.md).
- For PostgreSQL, admin env vars, frontend/static assets, model/API mocks, ML dependency slowness, and external-service test failures, read [troubleshooting.md](references/troubleshooting.md).
- To map paths or capability names to candidate pytest files without running tests, run [select_focused_tests.py](scripts/select_focused_tests.py).

## Safe Workflow

1. Classify the change area before editing: parser/content, search/filter, chat/agent, automation/memory, API/router, Django model/migration, CLI/config, frontend/client, or documentation.
2. Prefer focused tests from the mapping first; reserve full `pytest` for final confidence or broad refactors, and avoid expensive evals unless explicitly requested.
3. For router changes, update request/response validation, auth/rate-limit behavior, database adapters, and a FastAPI `TestClient` or async test together.
4. For model changes, plan the Django model edit, migration, admin/adapters impact, fixtures/factories, and rollback/data-migration behavior before touching runtime code.
5. For frontend, docs, desktop, Obsidian, or Emacs-visible changes, update the relevant client/docs surface but do not run release-version mutation scripts.

## Boundaries

This sub-skill owns contributor workflows, focused testing, lint/format conventions, model/migration planning, and development-script safety. Route user-facing endpoint contracts to [deployment-api](../deployment-api/SKILL.md), ingestion details to [content-indexing](../content-indexing/SKILL.md), search behavior to [search-retrieval](../search-retrieval/SKILL.md), chat/agent payload behavior to [chat-agents](../chat-agents/SKILL.md), and automations or memory product behavior to [automations-memory](../automations-memory/SKILL.md).

## Safety Notes

- Do not use `khoj --help` as a harmless parser check in an unconfigured checkout; import `khoj.utils.cli.cli` or run parser-only tests instead.
- Do not run `scripts/dev_setup.sh` automatically for an agent task; it installs dependencies, builds clients, and mutates git hooks.
- Do not run `scripts/bump_version.sh` unless the user is explicitly performing a maintainer release; it edits version files, commits, and tags.
- Do not start Docker services, migrate a real database, install packages, or run external-service/chat-quality tests unless the user has approved operational side effects.
