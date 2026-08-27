---
name: nexent
description: "Route Nexent SDK, backend, frontend, knowledge/memory, and
  deployment tasks across the zero-code AI agent platform monorepo."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Nexent Repo Skill

Use this repo skill when a task involves Nexent, a zero-code platform and SDK for generating and operating AI agents. It routes future agents to the right operating context for SDK runtime, backend APIs, document/knowledge/memory workflows, frontend integration, and deployment operations.

## Read first

- [`references/repo-provenance.md`](references/repo-provenance.md) before deciding whether this skill is current for a checkout.
- [`references/package-overview.md`](references/package-overview.md) for the monorepo layout, package roles, install surfaces, and cross-layer rules.
- [`references/testing-and-verification.md`](references/testing-and-verification.md) before selecting native tests, static checks, or optional live-service verification.
- [`references/troubleshooting.md`](references/troubleshooting.md) for cross-cutting install/import, dependency, env, service, and routing failures.

## Route by task

| User task | Use |
| --- | --- |
| Build, test, or debug SDK agents, `AgentConfig`, `ModelConfig`, streaming `agent_run`, model/tool/MCP/A2A setup, sandbox, scheduler, monitoring, or SDK skill manager behavior | [`sub-skills/sdk-agent-runtime/SKILL.md`](sub-skills/sdk-agent-runtime/SKILL.md) |
| Change or diagnose FastAPI routes, services, database helpers, backend env constants, errors, prompt templates, auth/tenant permissions, model/agent/skill APIs, or backend tests | [`sub-skills/backend-services-api/SKILL.md`](sub-skills/backend-services-api/SKILL.md) |
| Work on document ingestion, file splitting/conversion, vector DB, knowledge-base search, MinIO/storage, memory records/retrieval/dreaming, or data-process worker boundaries | [`sub-skills/knowledge-data-memory/SKILL.md`](sub-skills/knowledge-data-memory/SKILL.md) |
| Update Next.js pages/components, frontend services/types, chat streaming UI, i18n, stores/hooks, or `npm run check-all` failures | [`sub-skills/frontend-integration/SKILL.md`](sub-skills/frontend-integration/SKILL.md) |
| Operate or modify Docker/Kubernetes/offline deployment, env examples, image builds, SQL migrations/init sync, monitoring deployment, uninstall/upgrade behavior | [`sub-skills/deployment-operations/SKILL.md`](sub-skills/deployment-operations/SKILL.md) |

## Common setup surfaces

- Python work targets Python 3.11. The SDK package is distributed as `nexent`; the backend has its own project metadata and depends on the SDK source for application behavior.
- Backend development normally installs backend dependencies and the local SDK package; SDK-only work can install the SDK package alone.
- Frontend work uses the frontend package scripts: development server, type check, lint, format check, and build.
- Full-stack runtime needs deployment-managed services such as PostgreSQL/Supabase, Redis, Elasticsearch, MinIO, data-process workers, and optional monitoring/provider integrations.

## Bundled helper

Run [`scripts/nexent_static_probe.py`](scripts/nexent_static_probe.py) for a safe high-level checkout probe. It prints package metadata, important directories, and whether sub-skill static helpers can see their expected files. It does not start services, call providers, or run native tests.

## Global guardrails

- Keep backend environment-variable reads centralized in backend constants; SDK code receives explicit configuration objects and parameters.
- Do not run live model, MCP, provider, Docker, Kubernetes, Redis, Elasticsearch, MinIO, Ray, Celery, or database checks unless the task explicitly asks and the user supplies the needed environment/credentials.
- Prefer focused pytest/static checks to the full suite unless validating a release or broad refactor.
- For schema changes, coordinate backend models/helpers, migration SQL, fresh-deploy init SQL, and frontend types where public payloads change.
- Keep generated skill usage self-contained: use bundled references and scripts here for orientation, then inspect the task checkout only for the files you are actively changing.
