---
name: langbot
description: "Operate, extend, test, and troubleshoot the LangBot repo: Quart
  backend, React web UI, IM bots, pipelines, providers, plugins, Box, MCP, RAG,
  persistence, deployment, and QA workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# LangBot Repo Skill

Use this repo skill when a task is about the LangBot main repository or an
installed `langbot` package. LangBot is a production IM-bot platform that wires
messaging adapters, LLM providers, agents, tools, plugins, RAG, MCP, Box
sandboxing, persistence, and a web management panel into one runtime.

## Fast Orientation

- Python package: `langbot`, import root `langbot`, console script `langbot`.
- Supported Python from package metadata: `>=3.11,<4.0`.
- Backend service: Quart/Hypercorn, default `api.port: 5300`.
- Frontend: Vite + React Router + shadcn/ui + Tailwind under `web/`.
- Plugin and Box contracts come from the `langbot-plugin` SDK package; shared
  SDK changes must be made in the sibling SDK repository and then installed into
  LangBot for cross-repo checks.
- Generated skill provenance and refresh baseline: read
  [references/repo-provenance.md](references/repo-provenance.md).

Minimal package smoke for a checkout or installed package:

```bash
python - <<'PY'
from importlib.metadata import version
import langbot
print('langbot', version('langbot'))
PY
langbot --help
```

Common local commands:

```bash
uv sync --dev
uv run main.py
uv run pytest tests/unit_tests -q
cd web && pnpm install && pnpm dev
```

## Route by Task

| User task | Read |
|---|---|
| Start LangBot, inspect boot stages, configure `config.yaml`, choose Docker/Compose/Kubernetes/runtime flags, diagnose `/healthz`, or reason about resource probes | [core-runtime](sub-skills/core-runtime/SKILL.md) |
| Add/change HTTP API endpoints, permissions, API keys, MCP tools, web UI calls, Page Bot embed, frontend build/lint/i18n | [api-mcp-web](sub-skills/api-mcp-web/SKILL.md) |
| Debug message delivery, platform adapters, HTTP Bot callbacks, pipeline stages, providers/runners, model/tool loading, local agent request flow | [platform-pipeline-provider](sub-skills/platform-pipeline-provider/SKILL.md) |
| Work with Plugin Runtime, plugin connector/handler, Box sandbox runtime, native tools, stdio MCP hosting, skill CRUD, or in-repo skill assets | [plugin-box-skills](sub-skills/plugin-box-skills/SKILL.md) |
| Change persistence schemas, migrations, Workspace tenancy, RAG, vector backends, storage, monitoring, telemetry, or cloud tenant resource behavior | [persistence-rag-workspaces](sub-skills/persistence-rag-workspaces/SKILL.md) |
| Choose verification scope, run focused pytest/pnpm/lbs gates, collect QA evidence, or interpret test readiness/fixtures/manual checks | [testing-qa](sub-skills/testing-qa/SKILL.md) |

## Shared References and Helpers

- [references/troubleshooting.md](references/troubleshooting.md) covers
  cross-cutting install/import/config/service/credential failures before you
  open a workflow-specific troubleshooting page.
- [references/testing-and-verification.md](references/testing-and-verification.md)
  summarizes safe native candidate checks and when broader gates are justified.
- [references/api-route-map.md](references/api-route-map.md) explains how to
  extract the current HTTP route and MCP tool surface from a checkout.
- Run [scripts/langbot_repo_doctor.py](scripts/langbot_repo_doctor.py) to inspect
  a target checkout/package layout, metadata, config-template keys, and selected
  imports without starting LangBot.
- Run [scripts/extract_langbot_routes.py](scripts/extract_langbot_routes.py) to
  statically extract HTTP routes and MCP tools from a checkout.
- Run [scripts/select_langbot_checks.py](scripts/select_langbot_checks.py) to
  print or optionally execute focused verification command groups.

## Change Rules to Preserve

- For non-trivial backend, frontend, runtime, plugin, Box, MCP, persistence, or
  SDK-boundary work, start from the architecture map and then the owning
  sub-skill; do not jump directly into a random module.
- HTTP API changes that should be agent-accessible must keep the service layer,
  route group, MCP tool surface, and relevant skill/testing guidance aligned.
- New schema changes use Alembic migrations; do not add new legacy `dbmXXX`
  migrations.
- Platform adapters translate external platform shapes into LangBot's common
  message/event entities; pipeline/business logic belongs in pipeline stages or
  services, not vendor adapters.
- User-facing strings in product code need i18n coverage (`en_US`, `zh_Hans`,
  and `ja_JP` when nearby code already does).
- Do not require real provider keys, platform credentials, Docker, PostgreSQL,
  vector services, browsers, or cloud cgroups unless the selected task truly
  touches that surface; use focused fake/unit checks first.

## Boundaries

This skill teaches future Researcher sessions how to operate on LangBot. It is
not an import/export workflow and it does not install itself into live routing.
Use the generated references/scripts bundled here; do not rely on external docs
or examples being present when answering a task.
