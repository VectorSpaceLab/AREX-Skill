# Frontend contract

## Application layout
- `ui/src/main.ts` is the admin SPA entrypoint.
- `ui/src/chat.ts` is the chat/embed SPA entrypoint.
- `ui/src/router/index.ts` and `ui/src/router/chat/routes.ts` define the route sets, while `ui/src/router/chat/index.ts` applies the guard logic.
- Route modules under `ui/src/router/modules/` mirror the backend surface families.

## Build and serve contract
- `ui/package.json` defines the normal frontend scripts for dev, chat, build, build-chat, lint, and type-check.
- `ui/vite.config.ts` uses a fixed local backend proxy plus a configurable base path from env files.
- The build output is written to `ui/dist` and then served by Django staticfiles.
- `ui/env/*` provides the mode-specific environment values.

## Workflow canvas alignment
- The workflow canvas uses the backend node families exposed through `apps/application/flow/step_node`.
- When a backend node family changes, the matching UI node/component tree must be checked for naming and affordance drift.
- Application/knowledge/tool workflow pages share the same underlying canvas contract.

## Route and API alignment
- Admin APIs are under `/admin/api` and chat APIs are under `/chat/api` by default.
- The UI route modules and API families are organized by application, knowledge, model, tool, trigger, system, and workspace concerns.
- If the prefix changes, the Vite proxy and the Django route config must both be updated together.

## Validation notes
- `npm run lint`, `npm run type-check`, `npm run build`, and `npm run build-chat` are the main static checks when Node dependencies are installed.
- If the build output is stale, note whether the issue is source code, env config, or a missing rebuild.
