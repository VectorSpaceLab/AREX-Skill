# Frontend Architecture

## Purpose

Read this when you need to understand where a Nexent frontend change belongs: page, component, hook, store, service, type, constant, runtime proxy, or localization file.

## What the frontend owns

Nexent's frontend is a Next.js App Router application with locale-aware routing, a shared layout shell, a service layer built on `fetch`, and a typed contract layer that mirrors backend responses.

### Core runtime layers

| Layer | Main paths | Responsibility |
| --- | --- | --- |
| App shell | `frontend/app/[locale]/layout.tsx`, `layout.client.tsx`, `middleware.ts`, `app/[locale]/i18n.tsx` | Locale routing, providers, auth gating, global navigation, and metadata. |
| Runtime proxy | `frontend/server.js`, `frontend/base-path.mjs`, `frontend/next.config.mjs`, `frontend/build-config.js` | Proxy API/runtime traffic, apply base path, and normalize production startup. |
| UI pages | `frontend/app/[locale]/*` | Feature routes for chat, models, knowledge, memory, agents, skills, MCP, market, and repository management. |
| Shared presentation | `frontend/components/`, `frontend/features/` | Reusable UI, dialogs, panels, and feature-specific composites. |
| State and behavior | `frontend/hooks/`, `frontend/stores/`, `frontend/lib/` | Query hooks, Zustand stores, auth/session helpers, chat helpers, and view utilities. |
| Typed contracts | `frontend/services/`, `frontend/types/`, `frontend/const/` | API clients, response shapes, error codes, endpoint maps, and stream message constants. |

## Route map

| Route family | Main page / module | What it owns |
| --- | --- | --- |
| `/chat` | `app/[locale]/chat/page.tsx`, `internal/chatInterface.tsx`, `streaming/*` | Legacy chat UI, attachment handling, stream rendering, and conversation actions. |
| `/newchat` (via `/chat` nav target) | `app/[locale]/newchat/page.tsx`, `assistant-ui/*`, `adapter/*` | assistant-ui runtime, persistent thread list, SSE-to-UI translation, dictation, and sub-agent grouping. |
| `/agents` | `app/[locale]/agents/page.tsx` | Agent configuration, version management, prompt/tool/skill selection, and creation/edit flows. |
| `/models` | `app/[locale]/models/page.tsx` | Model catalog management, provider configuration, and capacity validation. |
| `/knowledges` | `app/[locale]/knowledges/page.tsx` | Knowledge base creation, document upload, chunk management, summaries, and external KB backends. |
| `/memory` | `app/[locale]/memory/page.tsx` | Tenant/user/agent memory configuration, retention policy, and embedding status. |
| `/skill-space` | `app/[locale]/skill-space/page.tsx` | Skill repository browse/mine/review flows and skill publication management. |
| `/agent-space` | `app/[locale]/agent-space/page.tsx` | Agent repository browse/mine/review flows and copy/import prechecks. |
| `/mcp-space` | `app/[locale]/mcp-space/page.tsx` | MCP server/service management, review, community publishing, and transport configuration. |
| `/market` | `app/[locale]/market/page.tsx` | Agent marketplace browsing, detail, and import. |
| `/agent-tasks` | `app/[locale]/agent-tasks/page.tsx` | Automation task workflow and proposal management. |
| `/space/evaluation`, `/space/evaluators` | `app/[locale]/space/*` | Evaluation-set and evaluator management. |
| `/resource-manage`, `/owner-manage` | `app/[locale]/resource-manage/`, `owner-manage/` | Tenant/user and asset-owner administration surfaces. |
| `/aidp-knowledges` | `app/[locale]/aidp-knowledges/page.tsx` | AIDP-backed knowledge base surface. |
| `/oauth/complete`, `/share/[shareId]` | OAuth and shared conversation views | Auth completion and read-only share rendering. |

## Shared architecture notes

### Layout and providers

- `middleware.ts` injects locale redirects for `zh` and `en`.
- `app/[locale]/layout.tsx` sets document metadata and wraps the app with theme, deployment, root, and i18n providers.
- `components/providers/rootProvider.tsx` adds React Query, auth, authorization, and global UI dialogs.
- `components/navigation/SideNavigation.tsx` owns the visible route tree and role-gated navigation.

### Locale and base path

- `app/[locale]/i18n.tsx` loads `public/locales/{zh,en}/common.json` and `custom.json`.
- `base-path.mjs` and `lib/basePath.ts` keep the frontend aware of `NEXT_PUBLIC_BASE_PATH`.
- `server.js` and `next.config.mjs` must stay aligned with base path, standalone output, and production startup.

### Service layer shape

- `services/api.ts` is the canonical endpoint map.
- `lib/auth.ts` and `services/api.ts` centralize auth headers, session expiry handling, and error normalization.
- Service modules transform backend JSON into UI-friendly shapes before pages consume them.

### Frontend checks

- `npm run type-check` catches contract drift first.
- `npm run lint` catches component and hook mistakes.
- `npm run format:check` catches style drift.
- `npm run build` verifies production build assumptions.
- `npm run check-all` runs all four in sequence.

## When to update what

| Change type | Update together |
| --- | --- |
| Backend response shape changes | `services/api.ts`, the affected `services/*.ts`, the matching `types/*.ts`, and the consuming page/hook/store. |
| Chat stream event changes | `const/chatConfig.ts`, `types/chat.ts`, `app/[locale]/chat/streaming/*`, `app/[locale]/newchat/adapter/*`, and the affected chat UI component. |
| New route or page family | `app/[locale]/*`, `SideNavigation.tsx`, any relevant hooks/services/types, and locale strings. |
| Locale text changes | `public/locales/zh/common.json`, `public/locales/en/common.json`, and any `custom.json` overrides. |
| Base-path or proxy change | `base-path.mjs`, `lib/basePath.ts`, `middleware.ts`, `server.js`, and `next.config.mjs`. |

## Related sibling skills

- Backend route ownership and request/response shape decisions live in `../backend-services-api/SKILL.md`.
- Stream event semantics and SDK-side execution markers are owned by `../sdk-agent-runtime/SKILL.md`.
