---
name: "frontend-integration"
description: "Covers MaxKB Vue/Vite admin and chat SPAs, routing, build
  contract, and workflow-canvas UI."
disable-model-invocation: true
metadata:
  disco-role: operating
license: GPL 3.0
---

# frontend-integration

Use this sub-skill for MaxKB UI, router, build, and static-asset tasks.

## Owns
- `ui/` build and runtime commands.
- Admin/chat router layout and Vite proxy/base-path behavior.
- Workflow canvas node UI alignment with backend node families.
- Static asset and i18n/theme integration.

## Do not own
- Backend bootstrap and Celery -> `runtime-architecture`.
- Workflow execution semantics -> `workflow-chat-mcp`.
- Knowledge/provider internals -> `knowledge-models`.
- Management-only backend pages and APIs -> `admin-access`.

## Key files
- `references/frontend-contract.md`
- `references/troubleshooting.md`
- `scripts/frontend_contract_check.py`

## Guidance
- Treat the UI as a contract with the backend prefixes and API families.
- Call out when a change needs a rebuilt `ui/dist`.
- Keep route and proxy advice aligned with the actual Vite config.
