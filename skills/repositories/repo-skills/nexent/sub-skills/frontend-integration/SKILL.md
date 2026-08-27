---
name: frontend-integration
description: "Routes Nexent frontend App Router work, service clients, typed API
  contracts, streaming chat, i18n, and frontend build checks."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Frontend Integration

Use this sub-skill for Nexent frontend tasks that touch the Next.js App Router, service clients, typed response contracts, streaming chat, localization, or frontend build checks.

## Route here when the task is about
- `frontend/app/[locale]/` pages and layouts
- `frontend/components/`, `frontend/features/`, `frontend/hooks/`, `frontend/stores/`, `frontend/services/`, `frontend/types/`, and `frontend/const/`
- chat streaming, assistant-ui, dictation, attachments, resume/replay, or share rendering
- locale routing, translation JSON, or base-path/proxy behavior
- `npm run check-all`, `npm run type-check`, `npm run lint`, or `npm run build`

## Read first
- [Frontend architecture](references/frontend-architecture.md)
- [API contracts](references/api-contracts.md)
- [Streaming and chat](references/streaming-and-chat.md)
- [Troubleshooting](references/troubleshooting.md)

## Bundled helper
- `scripts/extract_frontend_api_calls.py --repo-root <repo-root>`
  - Add `--json` for machine-readable output.
  - Use it to inventory `API_ENDPOINTS` call sites before changing client contracts.

## Keep these layers in sync
When backend payloads or route behavior change, update the frontend in this order:
1. `frontend/services/api.ts`
2. the affected `frontend/services/*.ts` client mapper
3. the matching `frontend/types/*.ts`
4. the consuming page, hook, store, or component
5. any chat-stream mapping in `frontend/app/[locale]/chat/streaming/` or `frontend/app/[locale]/newchat/adapter/`

## Route elsewhere
- Backend app/service/database internals -> `../backend-services-api/SKILL.md`
- SDK runtime, model, tool, or observer semantics -> `../sdk-agent-runtime/SKILL.md`
- Deployment scripts, env templates, SQL/init sync, or rollout behavior -> `../deployment-operations/SKILL.md`

## Main frontend surfaces
- Chat and streaming: `app/[locale]/chat/`, `app/[locale]/newchat/`
- Agent/model/knowledge/memory setup: `app/[locale]/agents/`, `models/`, `knowledges/`, `memory/`
- Repository and marketplace: `agent-space/`, `skill-space/`, `mcp-space/`, `market/`
- Shared runtime: `components/providers/`, `hooks/`, `services/`, `stores/`, `types/`, `lib/`, `public/locales/`
