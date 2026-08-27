---
name: frontend-apps
description: "Operate on BiSheng's two React frontends: Platform
  Vite/Zustand/react-query v3/bs-ui and Client Vite/Recoil/TanStack Query
  v4/shadcn."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# frontend-apps

Use this sub-skill when a task touches either BiSheng React frontend: the Platform admin/builder app under `src/frontend/platform/` or the Client workspace/chat app under `src/frontend/client/`.

## Start Here

Run bundled helper commands from this sub-skill directory, or adjust the script path to this directory after import.


1. Decide which app owns the requested change. The two frontends are separate SPAs and must not be mixed.
2. Inspect the installed stack and available package scripts:
   ```bash
   python scripts/check_frontend_packages.py --repo-root <bisheng-checkout>
   ```
3. Read [references/workflows.md](references/workflows.md) for app-specific routes, request wrappers, stores, i18n, theme, test commands, and review checklists.
4. If setup, proxying, i18n, routing, API, or state behavior is failing, read [references/troubleshooting.md](references/troubleshooting.md).

## Owned Responsibilities

- Platform app: `src/frontend/platform/`, Vite 5, React 18, TypeScript, Zustand + React Context, `react-query` v3, Radix-based `bs-ui`, `@/` alias.
- Client app: `src/frontend/client/`, Vite 6, React 18, TypeScript, Recoil, `@tanstack/react-query` v4, shadcn/Radix UI, `/workspace` base path, `~/` or `@/` alias.
- Routes and route guards in each app's `src/routes/index.tsx`.
- Wrapped HTTP layers: Platform `src/controllers/request.ts` plus `src/controllers/API/`; Client `src/api/request.ts` plus `src/api/` and query hooks.
- Frontend state boundaries: Platform stores/contexts; Client Recoil atoms/selectors.
- Frontend i18n files, brand runtime/theme tokens, UI components, icons, unit tests, and Vite dev/build behavior.

## Route Sibling Areas Instead of Duplicating Them

- Use `backend-core` for FastAPI routers, response envelopes, error-code definitions, backend schemas, and backend tests.
- Use `identity-permissions-tenancy` for OpenFGA/ReBAC semantics, tenant hierarchy, menu permission source data, SSO/org sync, and quota rules.
- Use `workflow-engine` for backend workflow execution, node semantics, LangGraph/Celery behavior, and workflow persistence.
- Use `knowledge-rag` for knowledge ingestion, file parsing, Milvus/Elasticsearch recall, and knowledge worker behavior.
- Use `linsight-mcp` for Linsight worker/runtime, MCP integrations, task-mode backend events, and deepagents concerns.
- Use `deployment-maintenance` for Docker Compose, Nginx, production rollout, middleware, and environment operations.

## Non-Negotiables

- Never mix Platform and Client stacks, aliases, state libraries, query libraries, or UI component systems.
- TypeScript only for edited frontend files (`.ts` / `.tsx`); functional components only; named component exports.
- Never import `axios` directly from business code. Use the app's wrapped request module; stores must not call HTTP directly.
- Do not introduce new UI, routing, query, or state-management libraries.
- Let response interceptors handle 403/401 flows. Do not add local 403 branches in business components.
- Keep comments in English and split any file that grows beyond 600 lines.
