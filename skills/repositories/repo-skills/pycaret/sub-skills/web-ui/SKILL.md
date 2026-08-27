---
name: web-ui
description: "Guides React/Vite PyCaret Control Plane UI work: routes, typed API
  client, auth state, data-driven experiment forms, run/trial/deployment pages,
  LLM widgets, and npm verification."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# web-ui

Use this sub-skill for PyCaret Control Plane frontend work under `apps/web`: route wiring, page/component edits, the typed API client, auth state, TanStack Query integration, dynamic experiment forms, live run/trial screens, deployment/model-registry views, LLM advisory widgets, and npm-based verification.

## First read

- [Component and route map](references/component-and-route-map.md) for the route table, major page roles, component ownership, and where to add a screen.
- [API client and state](references/api-client-and-state.md) before changing HTTP calls, WebSocket URLs, auth refresh, Zustand stores, query keys, or API type mirrors.
- [Testing and build](references/testing-and-build.md) before editing tests or running checks.
- [Troubleshooting](references/troubleshooting.md) when the browser shows auth loops, 404s, schema/form issues, WebSocket failures, Plotly problems, or npm/Node mismatch.

Helper scripts bundled with this sub-skill:

```bash
bash scripts/ui_static_check.sh --help
node scripts/list_ui_routes.mjs --help
```

## Route this way

- **Frontend UI implementation**: stay here.
- **Backend route behavior, database rows, schemas, auth policy, or LLM provider semantics**: route to the control-plane API skill.
- **Engine task semantics, `describe_setup_params`, model registry contents, RunConfig execution, or event-kind generation**: route to the engine workflow skill.
- **Docker, nginx production proxy, Compose, Helm, Terraform, ports in deploy files**: route to platform operations.

## Non-negotiables for UI edits

- Keep `DynamicForm` data-driven from the `describe/setup-params` schema. Do not hard-code setup parameter names inside `DynamicForm`; it renders only structural kinds (`bool`, `int`, `float`, `enum`, `column`, `string`) and honors `schema.groups`, `choices`, `minimum`, `maximum`, `required`, `default`, and `description`.
- If using the curated `ExperimentConfigForm`, read defaults and descriptions from the schema and keep the fallback for engine parameters that do not have a dedicated widget.
- Add or change API calls in `src/api/endpoints.ts` and mirror response/request shapes in `src/api/types.ts`; call sites should import endpoint groups, not raw axios.
- Preserve the axios auth contract: bearer token attached by interceptor, refresh once on 401, no refresh recursion on `/auth/refresh`.
- Use `@/` imports for `src/`, prefer named exports, and use `import type` for TypeScript types because `verbatimModuleSyntax` is enabled.
- Keep React Query keys stable and scoped by entity IDs. Poll only while useful, and stop on terminal states when possible.
- Use existing design primitives (`card`, `btn-*`, `input`, `field`, `hint`, `error`, `h-page`, `h-section`, `pill-*`) before inventing new styles.
- LLM UI is advisory only: render `suggested_config_json`, `suggested_action`, `reasoning_summary`, and `risk_flags`; do not let an LLM response directly trigger a destructive action.
- Run relevant npm checks from `apps/web` before handoff. For a full frontend gate: `npm run typecheck && npm run lint && npm test && npm run build`.

## Common workflows

### Add a page

1. Add or reuse typed endpoint methods and types first; see [API client and state](references/api-client-and-state.md).
2. Create a named-export page under `src/pages/<Name>.tsx`.
3. Import it in `src/App.tsx` and add a `<Route>` under the authenticated `<Layout>` unless it is intentionally public (`/setup`, `/login`) or a catch-all.
4. Add sidebar/command-palette links only when the page is a first-class navigation surface.
5. Add at least one Vitest/Testing Library test for non-trivial UI behavior.
6. Verify with `bash scripts/ui_static_check.sh --typecheck --lint --test --build`.

### Add a component that calls the API

1. Put all HTTP functions in `src/api/endpoints.ts` and all mirrors in `src/api/types.ts`.
2. Wrap reads with `useQuery` and writes with `useMutation`; invalidate only the affected query keys.
3. Use `errorMessage()` for user-facing axios errors.
4. Mock endpoint groups in tests instead of making network calls.

### Work on run/trial/deployment experiences

Read [Component and route map](references/component-and-route-map.md) first. The important split is:

- `RunDetail`: run status, event drawer, worker/load charting, trials leaderboard, request snapshot, promoted versions.
- `TrialsCard` / `ExperimentTrialsCard`: run-level vs experiment-level trial lists.
- `TrialDetail`: one candidate model, metrics, pipeline diagram, plots, prediction tester, validation, tune/ensemble/promote actions.
- `DeploymentDetail`: endpoint metrics, interactive prediction, versions/rollback, prediction logs, drift reports.

## Quick validation commands

From the repository root:

```bash
cd apps/web
npm run typecheck
npm run lint
npm test
npm run build
```

Or use the bundled wrapper:

```bash
bash scripts/ui_static_check.sh --typecheck --test
bash scripts/ui_static_check.sh --lint --build
```

To inspect route wiring without installing packages:

```bash
node scripts/list_ui_routes.mjs REPO_ROOT
```
