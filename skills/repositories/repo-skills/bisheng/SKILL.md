---
name: bisheng
description: "Use BiSheng's enterprise LLM application DevOps platform
  repository, including FastAPI backend, workflow/RAG/Linsight runtimes,
  permissions, dual React frontends, deployment, and maintainer workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# BiSheng

Use this repo skill when a task names BiSheng, 毕昇, `dataelement/bisheng`, or asks about this enterprise LLM application DevOps platform's backend, workflow engine, knowledge/RAG pipeline, Linsight agent, permissions/tenancy, dual React frontends, Docker deployment, or repository maintenance.

This root skill is a router. Read the focused sub-skill first, then return here for cross-cutting checks.

## First checks

1. If you are checking whether this skill matches a checkout, read [repo provenance](references/repo-provenance.md).
2. For the monorepo and runtime topology, read [architecture map](references/architecture-map.md).
3. `references/repo-routing-metadata.json` is structured metadata for managed repo-skill routing and import checks.
4. For cross-cutting install/config/runtime failures, read [troubleshooting](references/troubleshooting.md).
5. For a safe checkout inventory, run the bundled helper against a BiSheng checkout:
   ```bash
   python scripts/check_repo_surface.py --repo-root <bisheng-checkout>
   ```

## Install and verify a checkout

For backend work, install from the backend root with the repository-supported lockfile:

```bash
cd <bisheng-checkout>/src/backend
uv sync --frozen
uv run python -c "import bisheng, bisheng_langchain; print(getattr(bisheng, '__version__', 'unknown'))"
```

For frontend work, install and test from the owning app directory only:

```bash
cd <bisheng-checkout>/src/frontend/platform && npm install && npm test
cd <bisheng-checkout>/src/frontend/client && npm install && npm run test:ci
```

Use narrower sub-skill commands before running broad suites; many integration/e2e paths require MySQL, Redis, Milvus, Elasticsearch, MinIO, OpenFGA, or the commercial gateway.

## Route by task

| User task | Read |
| --- | --- |
| Add or debug FastAPI routes, DDD modules, response envelopes, settings/context, SQLModel DAO/model behavior, backend tests, or error-code handling | [backend-core](sub-skills/backend-core/SKILL.md) |
| Work on workflow canvas execution, LangGraph graph compilation, node types, callbacks, interruption/resume, workflow Celery tasks, or new workflow nodes | [workflow-engine](sub-skills/workflow-engine/SKILL.md) |
| Work on knowledge libraries/spaces, file upload states, document parsing, Load → Transform → Ingest, Milvus + Elasticsearch recall, MinIO artifacts, QA libraries, or knowledge workers | [knowledge-rag](sub-skills/knowledge-rag/SKILL.md) |
| Work on Linsight task mode, SOP/Skill migration, Redis worker queue, task/session state events, deepagents runtime, built-in tools, or MCP integrations | [linsight-mcp](sub-skills/linsight-mcp/SKILL.md) |
| Work on JWT auth, RBAC/ReBAC/OpenFGA, PermissionService, tenant isolation, admin scope, approval center, org/SSO sync, commercial gateway, or cursor-pagination permission performance | [identity-permissions-tenancy](sub-skills/identity-permissions-tenancy/SKILL.md) |
| Modify Platform or Client React apps, routes, stores, request wrappers, UI systems, i18n, brand theme, tests, or Vite config | [frontend-apps](sub-skills/frontend-apps/SKILL.md) |
| Install, run, deploy, configure, migrate, operate, or maintain the repo, Docker Compose stack, backend scripts, arch guard, uv/npm commands, or SDD workflow | [deployment-maintenance](sub-skills/deployment-maintenance/SKILL.md) |

## Cross-route decisions

- **Backend versus frontend:** API contract or permission semantics belong to backend/identity sub-skills; rendering, request wrappers, route guards, and state belong to `frontend-apps`.
- **Workflow versus Linsight:** visual flow DAGs and workflow nodes belong to `workflow-engine`; autonomous task-mode execution, SOP/Skill runtime, Redis Linsight worker, and MCP tool wrapping belong to `linsight-mcp`.
- **Knowledge versus permissions:** document ingestion/retrieval belongs to `knowledge-rag`; resource visibility, ReBAC checks, approval modes, tenant filters, and cursor permission performance belong to `identity-permissions-tenancy`.
- **Deployment versus code change:** runtime service wiring, Docker, config layering, migrations, and operational scripts belong to `deployment-maintenance`; feature implementation details route to the owning code sub-skill.

## Non-negotiable repository laws

- Backend layering is Router → Endpoint → Service → Repository/DAO → DB. Do not bypass it for new work.
- Every resource authorization path goes through PermissionService/OpenFGA-aware services; do not query role-access tables as a new permission shortcut.
- Multi-tenancy is ContextVar-driven. ORM SELECTs are auto-filtered, but raw SQL and bulk update/delete need explicit tenant-safe design.
- MySQL and DM8 compatibility are both mandatory. Use dialect helpers for JSON, large text, timestamp defaults, and keyset predicates.
- The two frontends are separate SPAs. Do not mix Platform's Zustand/react-query v3/bs-ui stack with Client's Recoil/TanStack Query v4/shadcn stack.
- Never import `axios` directly in business frontend code; use the app's wrapped request layer.
- Do not write plaintext secrets into config files. Password fields in BiSheng config are Fernet-encrypted.

## Verification and helper scope

The bundled scripts are read-only inspectors. They accept `--repo-root` so they can be used with any BiSheng checkout; they do not depend on the checkout used to create this skill.

Use repository-native tests only after selecting the focused surface. Many end-to-end and integration tests require MySQL, Redis, Milvus, Elasticsearch, MinIO, OpenFGA, frontend browsers, or the commercial gateway; prefer the narrow safe test listed by the owning sub-skill before running broad suites.
