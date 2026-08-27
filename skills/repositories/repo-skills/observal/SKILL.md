---
name: observal
description: "Route repository work for Observal, an AI agent registry and
  observability platform with Python CLI, FastAPI server, harness telemetry, and
  Vite web UI."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# Observal Repo Skill

Use this skill when working in or reasoning about the Observal repository: the `observal` CLI, registry/agent component workflows, FastAPI backend, harness adapters and telemetry, session traces, web UI, self-hosting/developer operations, tests, or contribution policy.

Observal is a monorepo for an agent-centric registry and observability platform. Its primary product surfaces are:

- Python CLI (`observal`) for auth, scan, doctor, registry components, agents, teams, ops/admin, server lifecycle, reconciliation, and support bundles.
- FastAPI server for registry APIs, auth/SSO/SCIM, telemetry ingest, ClickHouse/Postgres storage, insights, admin/review, teams, inbox, and GraphQL.
- Vite/React/TanStack Router web UI for registry browsing, traces, admin dashboards, settings, insights, teams, and account flows.
- Shared harness registry/adapters for Claude Code, Kiro, Cursor, Pi, Codex, Copilot, OpenCode, Antigravity, and Goose.

## First read

- For repo freshness and evidence baseline, read [repo provenance](references/repo-provenance.md).
- For a compact architecture map, read [overview](references/overview.md).
- For install/test commands and optional heavy checks, read [quick commands](references/quick-commands.md).
- For cross-cutting failure triage, read [troubleshooting](references/troubleshooting.md).

## Route by task

| User task | Use |
| --- | --- |
| Add, rename, test, or operate a Typer command; keep JSON/table/error contracts and bundled skills in sync | [cli](sub-skills/cli/SKILL.md) |
| Change REST/GraphQL routes, schemas, models, services, auth, insights, jobs, migrations, dynamic settings, or backend tests | [server](sub-skills/server/SKILL.md) |
| Add/promote/debug a harness, scan/doctor/layer behavior, hook specs, session push/reconcile, session parsers, telemetry ingest, or model catalog coverage | [harness-telemetry](sub-skills/harness-telemetry/SKILL.md) |
| Modify Vite/React routes, pages, components, query hooks, auth storage, UI types, theme tokens, Playwright specs, or screenshots | [web](sub-skills/web/SKILL.md) |
| Choose setup/lint/test/release/compliance scripts, docs/changelog obligations, SPDX/pre-commit policy, AI contribution disclosure, or PR readiness checks | [repo-development](sub-skills/repo-development/SKILL.md) |

When a task crosses layers, start with the implementation owner, then return to `repo-development` for broad tests, docs, changelog, screenshots, and contributor-policy checks.

## Minimal setup and smoke checks

For CLI users, install the released tool with one of:

```bash
uv tool install observal-cli
pipx install observal-cli
```

For source work inside a checkout, the repo documents Python 3.11+, uv, Node/pnpm, and Docker for the optional stack. A fast local source smoke is:

```bash
uv tool install --editable .
observal --version
observal --help
```

For server-aware unit tests, the native pattern runs from the server directory while pointing pytest at root tests. The default Make target wraps this:

```bash
make test
make lint
```

Do not run Docker Compose or Playwright E2E by default. Use them only for live stack, browser, or Kiro-specific coverage and state that requirement in the handoff.

## Bundled helper checks

These helpers are copied into the skill so future agents can check contracts without reopening the source docs:

```bash
python scripts/check_observal_skill_tree.py --skill-root skills/disco/observal --pretty
python sub-skills/cli/scripts/check_cli_contract.py --repo-root . --pretty
python sub-skills/server/scripts/check_server_routes.py --server-path . --pretty
python sub-skills/harness-telemetry/scripts/check_harness_registry.py --repo-root . --pretty
python sub-skills/web/scripts/check_web_contract.py --repo-root .
python sub-skills/repo-development/scripts/inspect_observal_repo.py --repo-root . --pretty
```

Expected signals: valid skill frontmatter, known CLI groups, server route registry import, ten registered harnesses with parser coverage, frontend contract markers, and repository markers/test counts.

## Operating invariants

- No telemetry wrappers or OTLP environment variables: harness telemetry flows through session push hooks and reconciliation.
- Harness-specific behavior belongs in adapters and shared registry entries, not orchestrator if/elif chains.
- CLI command changes must update CLI docs and bundled skills; run the sync command before handoff.
- ClickHouse schema changes live in ClickHouse SQL migrations; Alembic is for Postgres only.
- Frontend harness data comes from the server; do not hardcode harness lists in React.
- Log with Loguru positional placeholders and never log secrets, tokens, JWT payloads, keys, or credential values.
- Tests mock external services by default; E2E specs are the exception and require a running stack.
- Keep AI-assisted contribution claims explainable and human-reviewed; autonomous PR submission is out of scope.
